"""Forbid Figma-transliterated redundant CSS.

- no_fixed_height: fixed px height/min-height/max-height + block-size (Figma frame height)
- no_margin_first_child_reset: :first/:last-child margin reset → use flex gap
  is forbidden; 0/auto/%/vh/var() allowed.
- no_redundant_white_background: background:#fff is redundant (white is default)
  unless the element is scoped under a colored section (white over color).
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic_redundant", SCRIPT_PATH)
validate_semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_semantic)

HTML = "<html><body><div class='cont'></div></body></html>"


def _results(tmp_path: Path, css_text: str, profile: str = "landing") -> dict:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    html_path.write_text(HTML, encoding="utf-8")
    css_path.write_text(css_text + "\n", encoding="utf-8")
    results = validate_semantic.run_validation(
        rules_path=str(RULES_PATH), html_path=str(html_path),
        css_path=str(css_path), profile=profile,
    )
    return {r.rule_id: r for r in results}


# ---- no_fixed_height (min/max/plain all forbidden) ----

def test_fixed_height_px_flagged(tmp_path):
    r = _results(tmp_path, ".box{height:448px;}")
    assert r["no_fixed_height"].passed is False


def test_min_height_px_flagged(tmp_path):
    r = _results(tmp_path, ".visual_box{min-height:448px;}")
    assert r["no_fixed_height"].passed is False


def test_max_height_px_flagged(tmp_path):
    # user: min이든 max든 넣지마 — max-height fixed px is now flagged too
    r = _results(tmp_path, ".card{max-height:300px;}")
    assert r["no_fixed_height"].passed is False


def test_block_size_logical_px_flagged(tmp_path):
    r = _results(tmp_path, ".visual_box{min-block-size:685px;}")
    assert r["no_fixed_height"].passed is False


def test_height_vh_allowed(tmp_path):
    r = _results(tmp_path, ".hero{min-height:100vh;}")
    assert r["no_fixed_height"].passed is True


def test_height_zero_allowed(tmp_path):
    r = _results(tmp_path, ".flex_child{min-height:0;}")
    assert r["no_fixed_height"].passed is True


def test_line_height_not_confused(tmp_path):
    # line-height is typography, must not be flagged as a fixed height
    r = _results(tmp_path, ".x{line-height:1.5;width:100px;}")
    assert r["no_fixed_height"].passed is True


# ---- no_logical_box_properties (logical → physical) ----

def test_inline_size_flagged(tmp_path):
    r = _results(tmp_path, ".box{inline-size:340px;}")
    assert r["no_logical_box_properties"].passed is False


def test_block_size_flagged(tmp_path):
    r = _results(tmp_path, ".box{block-size:200px;}")
    assert r["no_logical_box_properties"].passed is False


def test_min_max_logical_flagged(tmp_path):
    r = _results(tmp_path, ".box{min-inline-size:100px;max-block-size:50%;}")
    assert r["no_logical_box_properties"].passed is False


def test_margin_inline_flagged(tmp_path):
    r = _results(tmp_path, ".box{margin-inline:auto;}")
    assert r["no_logical_box_properties"].passed is False


def test_physical_properties_not_flagged(tmp_path):
    r = _results(tmp_path, ".box{width:340px;height:200px;margin-left:30px;}")
    assert r["no_logical_box_properties"].passed is True


# ---- no_margin_first_child_reset (margin spacing → gap) ----

def test_first_child_margin_reset_flagged(tmp_path):
    css = (".program_list li{inline-size:340px;margin-left:30px;}\n"
           ".program_list li:first-child{margin-left:0;}")
    r = _results(tmp_path, css)
    assert r["no_margin_first_child_reset"].passed is False


def test_last_child_margin_reset_flagged(tmp_path):
    r = _results(tmp_path, ".list li:last-child{margin-right:0;}")
    assert r["no_margin_first_child_reset"].passed is False


def test_first_child_without_margin_reset_ok(tmp_path):
    # first-child changing a non-margin property is fine
    r = _results(tmp_path, ".list li:first-child{color:#f00;}")
    assert r["no_margin_first_child_reset"].passed is True


def test_gap_layout_not_flagged(tmp_path):
    r = _results(tmp_path, ".program_list{display:flex;gap:30px;}\n.program_list li{inline-size:340px;}")
    assert r["no_margin_first_child_reset"].passed is True


# ---- no_redundant_white_background ----

def test_standalone_white_background_flagged(tmp_path):
    r = _results(tmp_path, ".card{background:#fff;}")
    assert r["no_redundant_white_background"].passed is False


def test_white_over_colored_section_allowed(tmp_path):
    css = (".main_visual{background:#eef4f7;}\n"
           ".main_visual .visual_box{background:#fff;}")
    r = _results(tmp_path, css)
    assert r["no_redundant_white_background"].passed is True


def test_colored_background_not_flagged(tmp_path):
    r = _results(tmp_path, ".main_visual{background:#eef4f7;}")
    assert r["no_redundant_white_background"].passed is True


def test_white_color_property_not_flagged(tmp_path):
    # color:#fff is text color, not background — must not flag
    r = _results(tmp_path, ".x{color:#fff;}")
    assert r["no_redundant_white_background"].passed is True


def test_white_with_bg_image_not_flagged(tmp_path):
    # background:#fff url(...) is an image bg, not redundant white
    r = _results(tmp_path, ".banner{background:#fff url('../img/bg.png') no-repeat;}")
    assert r["no_redundant_white_background"].passed is True

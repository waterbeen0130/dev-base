"""제천한방힐링아카데미 landing review → encoded rules.

Each rule: a violating CSS must FAIL and a clean CSS must PASS (no false positive).
Driven through run_validation() so rule registration + handler wiring are covered.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic_landing", SCRIPT_PATH)
validate_semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_semantic)

HTML = "<html><body><div class='header'></div></body></html>"


def _results(tmp_path: Path, css_text: str, profile: str = "landing") -> dict:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    html_path.write_text(HTML, encoding="utf-8")
    css_path.write_text(css_text + "\n", encoding="utf-8")
    results = validate_semantic.run_validation(
        rules_path=str(RULES_PATH),
        html_path=str(html_path),
        css_path=str(css_path),
        profile=profile,
    )
    return {r.rule_id: r for r in results}


# ---- no_body_background ----

def test_body_background_color_is_flagged(tmp_path):
    r = _results(tmp_path, "body{background:#eef4f7;}")
    assert r["no_body_background"].passed is False


def test_html_body_background_image_is_flagged(tmp_path):
    r = _results(tmp_path, "html,body{background:url('../img/bg.jpg');}")
    assert r["no_body_background"].passed is False


def test_section_background_is_not_flagged(tmp_path):
    # page background belongs on a section, not body
    r = _results(tmp_path, ".main_visual{padding:40px 0;background:#eef4f7;}")
    assert r["no_body_background"].passed is True


def test_body_white_or_transparent_not_flagged(tmp_path):
    r = _results(tmp_path, "body{background:#fff;}\nhtml{background:transparent;}")
    assert r["no_body_background"].passed is True


# ---- no_img_area_declaration ----

def test_img_area_standalone_declaration_is_flagged(tmp_path):
    r = _results(tmp_path, ".img_area{display:block;overflow:hidden;}")
    assert r["no_img_area_declaration"].passed is False


def test_no_img_area_declaration_clean(tmp_path):
    r = _results(tmp_path, ".cont{margin:0 auto;max-width:var(--width);}")
    assert r["no_img_area_declaration"].passed is True


# ---- cont_redundant_scoping ----

def test_redundant_cont_scoping_is_flagged(tmp_path):
    css = ".header .cont,.footer .cont{width:min(100%,var(--width));margin:0 auto;}"
    r = _results(tmp_path, css)
    assert r["cont_redundant_scoping"].passed is False


def test_special_cont_override_not_flagged(tmp_path):
    # different values (special case) — legit, must not flag
    css = ".header .cont{max-width:1920px;padding:0 50px;}"
    r = _results(tmp_path, css)
    assert r["cont_redundant_scoping"].passed is True


def test_cont_with_layout_not_flagged(tmp_path):
    # adds display:flex (layout), not a redundant width/margin restate
    css = ".main_visual .cont{display:flex;align-items:stretch;}"
    r = _results(tmp_path, css)
    assert r["cont_redundant_scoping"].passed is True


def test_global_cont_base_not_flagged(tmp_path):
    # the global .cont base itself is not a scoped selector
    css = ".cont{margin:0 auto;max-width:var(--width);padding:0 var(--padding);}"
    r = _results(tmp_path, css)
    assert r["cont_redundant_scoping"].passed is True


# ---- no_duplicate_ir_class ----

def test_ir_pattern_new_class_is_flagged(tmp_path):
    css = ".text_bank{position:absolute;left:-10000px;inline-size:1px;block-size:1px;overflow:hidden;}"
    r = _results(tmp_path, css)
    assert r["no_duplicate_ir_class"].passed is False


def test_reset_ir_class_itself_not_flagged(tmp_path):
    css = ".ir{position:absolute;left:-10000px;overflow:hidden;}"
    r = _results(tmp_path, css)
    assert r["no_duplicate_ir_class"].passed is True


def test_normal_class_not_flagged(tmp_path):
    css = ".main_visual .title{position:absolute;left:20px;}"
    r = _results(tmp_path, css)
    assert r["no_duplicate_ir_class"].passed is True

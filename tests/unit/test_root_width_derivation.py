"""root_width_derivation: --width must equal Figma content width + 2×--padding.

content_width is read from extracted/*_spec.json (frame inner width minus figma
padding). When no spec is discoverable the check skips gracefully (non-blocking).
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic_width", SCRIPT_PATH)
validate_semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_semantic)

HTML = "<html><body><div class='cont'></div></body></html>"


def _results(tmp_path: Path, css_text: str, *, spec_frame: dict | None = None) -> dict:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    html_path.write_text(HTML, encoding="utf-8")
    css_path.write_text(css_text + "\n", encoding="utf-8")
    if spec_frame is not None:
        extracted = tmp_path / "extracted"
        extracted.mkdir(exist_ok=True)
        (extracted / "sec_spec.json").write_text(
            json.dumps({"frame_nodes": [spec_frame]}), encoding="utf-8"
        )
    results = validate_semantic.run_validation(
        rules_path=str(RULES_PATH),
        html_path=str(html_path),
        css_path=str(css_path),
        profile="landing",
    )
    return {r.rule_id: r for r in results}


# frame: inner content width = 1480 - 20 - 20 = 1440 → expected --width = 1440 + 2*20 = 1480
_FRAME = {"bbox": {"w": 1480}, "paddingLeft": 20, "paddingRight": 20}


def test_correct_width_passes(tmp_path):
    css = ":root{--padding:20px;--header_h:90px;--width:1480px;--point-color-1:#199bce;}"
    r = _results(tmp_path, css, spec_frame=_FRAME)
    assert r["root_width_derivation"].passed is True
    assert r["root_width_derivation"].skipped is False


def test_wrong_width_fails(tmp_path):
    css = ":root{--padding:20px;--header_h:90px;--width:1400px;--point-color-1:#199bce;}"
    r = _results(tmp_path, css, spec_frame=_FRAME)
    assert r["root_width_derivation"].passed is False
    assert "1480px" in r["root_width_derivation"].message  # expected value surfaced


def test_width_respects_actual_padding(tmp_path):
    # padding 30 → expected --width = 1440 + 60 = 1500
    css = ":root{--padding:30px;--header_h:90px;--width:1500px;--point-color-1:#199bce;}"
    r = _results(tmp_path, css, spec_frame=_FRAME)
    assert r["root_width_derivation"].passed is True


def test_no_spec_skips_gracefully(tmp_path):
    css = ":root{--padding:20px;--header_h:90px;--width:9999px;--point-color-1:#199bce;}"
    r = _results(tmp_path, css, spec_frame=None)  # no extracted/ → cannot verify
    assert r["root_width_derivation"].passed is True
    assert r["root_width_derivation"].skipped is True


def test_missing_vars_does_not_false_fail(tmp_path):
    # presence is root_vars_required's job; this rule must not fail on absence
    css = ".cont{margin:0 auto;}"
    r = _results(tmp_path, css, spec_frame=_FRAME)
    assert r["root_width_derivation"].passed is True

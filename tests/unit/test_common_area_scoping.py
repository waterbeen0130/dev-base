"""Regression fixtures for DOD-002: common-area child scoping + global class standalone.

- common_area_child_scope: common-area child classes (.logo/.gnb/.copyright ...)
  must be parent-scoped (.header .logo); standalone declaration is flagged.
- global_class_standalone: global classes (.header/.footer/.cont/.img_area) must
  not carry a body/html ancestor.
Clean cases must pass (zero false positives, DOD-010 / risk R2).
"""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic", SCRIPT_PATH)
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


# ---- common_area_child_scope ----

def test_common_area_child_standalone_is_flagged(tmp_path):
    css = ".logo{color:#fff}\n.gnb a{color:#000}\n.copyright{font-size:12px}"
    r = _results(tmp_path, css)
    assert "common_area_child_scope" in r
    assert r["common_area_child_scope"].passed is False


def test_common_area_child_parent_scoped_passes(tmp_path):
    css = ".header .logo{color:#fff}\n.header .gnb a{color:#000}\n.footer .copyright{font-size:12px}"
    r = _results(tmp_path, css)
    assert "common_area_child_scope" in r
    assert r["common_area_child_scope"].passed is True


# ---- global_class_standalone ----

def test_global_class_with_body_parent_is_flagged(tmp_path):
    css = "body .header{display:flex}\nhtml .cont{margin:0 auto}"
    r = _results(tmp_path, css)
    assert "global_class_standalone" in r
    assert r["global_class_standalone"].passed is False


def test_global_class_standalone_passes(tmp_path):
    # .cont section-level override (.main_intro .cont) is allowed; bare globals fine.
    css = ".header{display:flex}\n.cont{margin:0 auto}\n.main_intro .cont{max-width:1200px}\n.img_area{display:block}"
    r = _results(tmp_path, css)
    assert "global_class_standalone" in r
    assert r["global_class_standalone"].passed is True

"""Follow-up: no_guess_prefix — site_/g_/common_ 추측 prefix 클래스 금지 (CLAUDE.md)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic", SCRIPT_PATH)
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)

RULE_ID = "no_guess_prefix"


def _results(tmp_path, html):
    h = tmp_path / "index.html"
    c = tmp_path / "common.css"
    h.write_text(html, encoding="utf-8")
    c.write_text(".main_intro{display:flex}", encoding="utf-8")
    return {r.rule_id: r for r in vs.run_validation(
        rules_path=str(RULES_PATH), html_path=str(h), css_path=str(c), profile="landing")}


def test_guess_prefix_flagged(tmp_path):
    r = _results(tmp_path, "<html><body><div class='site_header'><span class='common_wrap'></span></div></body></html>")
    assert RULE_ID in r and r[RULE_ID].passed is False


def test_clean_classes_pass(tmp_path):
    # bg_ contains 'g_' but not at a word boundary; legit page/common classes pass.
    r = _results(tmp_path, "<html><body><div class='main_intro'><span class='bg_dark header'></span></div></body></html>")
    assert RULE_ID in r and r[RULE_ID].passed is True

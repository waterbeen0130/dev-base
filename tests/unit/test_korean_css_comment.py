"""Follow-up: korean_css_comment — CSS 주석은 영어만 (CLAUDE.md). 한글 주석 검출."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic", SCRIPT_PATH)
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)

RULE_ID = "no_korean_css_comment"


def _results(tmp_path, css):
    h = tmp_path / "index.html"
    c = tmp_path / "common.css"
    h.write_text("<html><body><div class='main_intro'></div></body></html>", encoding="utf-8")
    c.write_text(css, encoding="utf-8")
    return {r.rule_id: r for r in vs.run_validation(
        rules_path=str(RULES_PATH), html_path=str(h), css_path=str(c), profile="landing")}


def test_korean_comment_flagged(tmp_path):
    r = _results(tmp_path, "/* 헤더 영역 스타일 */\n.main_intro{display:flex}")
    assert RULE_ID in r and r[RULE_ID].passed is False


def test_english_comment_passes(tmp_path):
    r = _results(tmp_path, "/* header area */\n.main_intro{display:flex}")
    assert RULE_ID in r and r[RULE_ID].passed is True

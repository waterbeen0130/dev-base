"""Regression fixtures for no_figma_nodeid_class (DOD-001).

Violation cases must be flagged; clean cases (legitimate page-prefix and common
classes) must pass to prove zero false positives (DOD-010, risk R2).
"""

import importlib.util
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic", SCRIPT_PATH)
validate_semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_semantic)

RULE_ID = "no_figma_nodeid_class"


def _results_by_rule(tmp_path: Path, html_text: str, profile: str = "landing") -> dict:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    html_path.write_text(html_text, encoding="utf-8")
    css_path.write_text(".main_intro{display:flex}\n", encoding="utf-8")
    results = validate_semantic.run_validation(
        rules_path=str(RULES_PATH),
        html_path=str(html_path),
        css_path=str(css_path),
        profile=profile,
    )
    return {result.rule_id: result for result in results}


def test_violation_figma_node_name_classes_are_flagged(tmp_path):
    html = textwrap.dedent(
        """
        <html><body>
        <div class="main_f0">
            <span class="main_v53"><img src="x.png" alt="a"></span>
            <p class="main_t12">x</p>
        </div>
        </body></html>
        """
    ).strip()
    results = _results_by_rule(tmp_path, html)
    assert RULE_ID in results
    assert results[RULE_ID].passed is False


def test_clean_semantic_classes_pass(tmp_path):
    # Legitimate user page-prefix + common area classes must NOT trip the rule.
    html = textwrap.dedent(
        """
        <html><body>
        <header class="header"><nav class="gnb"><ul><li><a href="#"><span>x</span></a></li></ul></nav></header>
        <div class="main_intro">
            <div class="main_visual"><h2 class="greeting_title">x</h2></div>
            <div class="products_card"><span class="img_area"><img src="x.png" alt="a"></span></div>
        </div>
        <footer class="footer"><span class="copyright">x</span></footer>
        </body></html>
        """
    ).strip()
    results = _results_by_rule(tmp_path, html)
    assert RULE_ID in results
    assert results[RULE_ID].passed is True


def test_designer_identifier_suffix_is_flagged(tmp_path):
    # _v2 / _f1 style designer suffixes (CLAUDE.md forbids header_b, _v2, etc.)
    html = '<html><body><div class="hero_v2"><span class="box_f1">x</span></div></body></html>'
    results = _results_by_rule(tmp_path, html)
    assert RULE_ID in results
    assert results[RULE_ID].passed is False

"""Regression fixtures for check_selector_format grouped-selector breaking.

Comma selector groups of 3+ collapsed onto one line must be flagged; the
per-selector line-break format and property-level commas must pass clean
(zero false positives).
"""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"

spec = importlib.util.spec_from_file_location("validate_semantic", SCRIPT_PATH)
validate_semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_semantic)

FINDING = "grouped-selector-newline"


def _check(css: str):
    validator = validate_semantic.SemanticValidator()
    validator.check_selector_format(css, "common.css")
    return [v for v in validator.violations if v.rule == FINDING]


def test_three_collapsed_selectors_are_flagged():
    css = (
        ".intro_summary .head h3,.intro_benefit .head h3,"
        ".intro_program .head h3{position:relative;color:#212121;}\n"
    )
    assert _check(css), "3 comma selectors on one line must be flagged"


def test_per_selector_linebreak_passes():
    css = (
        ".intro_summary .head h3,\n"
        ".intro_benefit .head h3,\n"
        ".intro_program .head h3{position:relative;color:#212121;}\n"
    )
    assert not _check(css), "per-selector line-break format must pass clean"


def test_two_selectors_one_line_allowed():
    # threshold is 3+ ("콤마 셀렉터 3개 이상")
    assert not _check(".a,.b{color:red;}\n")


def test_property_commas_not_flagged():
    css = '.box{font-family:Arial, sans-serif, "Noto Sans";}\n'
    assert not _check(css), "commas inside a property value must not be flagged"

from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_semantic_comments", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_no_forbidden_class_rule() -> dict:
    payload = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
    return next(rule for rule in payload["rules"] if rule["id"] == "no_forbidden_class")


def test_forbidden_class_ignores_html_comments() -> None:
    module = _load_validator_module()
    ctx = module.ValidationContext(
        html_text='<!-- sec_1 --><div class="main_hero">Content</div>',
        css_text="",
        html_path="index.html",
        css_path="common.css",
        profile="landing",
    )
    rule = _load_no_forbidden_class_rule()

    result = module.validate_forbidden_substring(rule, ctx)

    assert result.passed is True

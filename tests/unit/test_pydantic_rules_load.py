from __future__ import annotations

from rules.models import EXPECTED_RULE_COUNT, RuleDefinition, load_rules


def test_load_rules_returns_expected_pydantic_rule_definitions() -> None:
    rules = load_rules()

    assert len(rules) == EXPECTED_RULE_COUNT
    assert all(isinstance(rule, RuleDefinition) for rule in rules)

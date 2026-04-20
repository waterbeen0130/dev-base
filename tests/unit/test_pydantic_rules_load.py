from __future__ import annotations

from rules.models import RuleDefinition, load_rules


def test_load_rules_returns_65_pydantic_rule_definitions() -> None:
    rules = load_rules()

    assert len(rules) == 65
    assert all(isinstance(rule, RuleDefinition) for rule in rules)

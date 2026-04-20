from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from rules.models import RuleDefinition, load_rules


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def _load_figma_validate_module():
    spec = importlib.util.spec_from_file_location("figma_validate_pydantic_signature", FIGMA_VALIDATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_dispatch_handler_accepts_rule_definition_instance() -> None:
    module = _load_figma_validate_module()
    rule = next(item for item in load_rules() if item.id == "vertical_frame_itemspacing_uses_margin_bottom")

    result = module.dispatch_rule_handler(rule, module.RuleDispatchContext())

    assert isinstance(rule, RuleDefinition)
    assert result.rule_id == rule.id
    assert result.passed is True
    assert result.skipped is True
    assert result.message == "validated_by_figma_validate_runtime"


def test_missing_pydantic_handler_returns_major_fail() -> None:
    module = _load_figma_validate_module()
    rule = RuleDefinition.model_validate(
        {
            "applies_to": ["figma"],
            "category": "figma.mapping",
            "description": "Synthetic missing handler fixture.",
            "id": "synthetic_missing_handler_rule",
            "severity": "warning",
            "target": "spec",
            "type": "custom",
            "custom_handler": "missing_handler_impl",
        }
    )

    result = module.dispatch_rule_handler(rule, module.RuleDispatchContext())

    assert result.passed is False
    assert result.skipped is False
    assert result.severity == "warning"
    assert "[STUB-PASS BLOCKED]" in result.message
    assert "MAJOR FAIL" in result.message
    assert "missing_handler_impl" in result.message


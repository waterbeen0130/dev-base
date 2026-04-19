from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate-semantic.py"


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_semantic", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_stub_handler_blocks_with_major_failure() -> None:
    module = _load_validator_module()
    ctx = module.ValidationContext(
        html_text="",
        css_text="",
        html_path="index.html",
        css_path="common.css",
        profile="all",
    )
    rule = {
        "id": "stub_rule",
        "severity": "info",
        "validation": {"custom_handler": "missing_handler_impl"},
    }

    result = module._stub_handler(rule, ctx)

    assert result.passed is False
    assert result.skipped is False
    assert result.severity == "warning"
    assert "[STUB-PASS BLOCKED]" in result.message
    assert "missing_handler_impl" in result.message

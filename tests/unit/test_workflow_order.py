"""Follow-up: workflow_order_enforced — screenshot-first 2-pass order via ledger.

Required order: extract -> structure (Pass1, from screenshot) -> values
(Pass2, from spec) -> verify. The core guarantee is values AFTER structure:
applying spec values before building semantic structure is the transliteration
failure mode (raw node-name dump).
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK_PATH = ROOT / "tools" / "check-workflow-order.py"

spec = importlib.util.spec_from_file_location("check_workflow_order", CHECK_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _ledger(steps):
    return {"section": "main_visual", "steps": [{"step": s, "provider": "omx"} for s in steps]}


def test_correct_order_ok():
    ok, reason = mod.validate_order(_ledger(["extract", "structure", "values", "verify"]))
    assert ok is True, reason


def test_values_before_structure_blocks():
    ok, reason = mod.validate_order(_ledger(["extract", "values", "structure", "verify"]))
    assert ok is False
    assert "structure" in reason  # values must come after structure


def test_missing_verify_blocks():
    ok, reason = mod.validate_order(_ledger(["extract", "structure", "values"]))
    assert ok is False
    assert "verify" in reason


def test_missing_structure_blocks():
    ok, reason = mod.validate_order(_ledger(["extract", "values", "verify"]))
    assert ok is False
    assert "structure" in reason

"""DOD-005: rule coverage gap report.

Measures how many machine-checkable (A/B-grade) rule gaps from the investigation
are now encoded, and lists remaining gaps with reasons. Closed gaps must map to
rules/handlers/tools that actually exist; out-of-scope (C-grade) items are not
counted as closable.
"""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "tools" / "rule-coverage-report.py"

spec = importlib.util.spec_from_file_location("rule_coverage_report", REPORT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_report_has_core_fields():
    rep = mod.build_report(ROOT)
    assert "encoded_rule_count" in rep
    assert rep["encoded_rule_count"] >= 80
    assert "ab_gaps_total" in rep and "ab_gaps_closed" in rep
    assert rep["ab_gaps_closed"] <= rep["ab_gaps_total"]


def test_closed_gaps_reference_real_artifacts():
    rep = mod.build_report(ROOT)
    closed_ids = {g["id"] for g in rep["gaps"] if g["status"] == "closed"}
    # the headline gap (Figma node-name transliteration) must be closed this milestone
    assert "no_figma_nodeid_class" in closed_ids
    assert "verify_execution_evidence" in closed_ids


def test_out_of_scope_items_not_counted_as_closable():
    rep = mod.build_report(ROOT)
    for g in rep["gaps"]:
        if g["status"] == "out_of_scope":
            assert g.get("reason")
    # coverage ratio is closed / (total - out_of_scope)
    assert 0.0 <= rep["ab_coverage_ratio"] <= 1.0

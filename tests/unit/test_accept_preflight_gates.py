"""AGI-004 follow-up: accept-preflight gate pipeline wiring.

Verifies that the deliverable/repo/ledger checkers are actually wired into the
accept gate, each gate gracefully SKIPs when its inputs are absent, and a real
violation produces a BLOCK that summarize() collapses to decision=block.
"""
import importlib.util
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools"

# Load the hyphenated module file directly.
_spec = importlib.util.spec_from_file_location(
    "accept_preflight_verify", TOOLS / "accept-preflight-verify.py"
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


# --- output-boundary --------------------------------------------------------

def test_output_boundary_skips_without_dir():
    assert gate.gate_output_boundary(None)["status"] == gate.SKIP


def test_output_boundary_passes_on_clean_dir(tmp_path: Path):
    (tmp_path / "index.html").write_text("<main><section>ok</section></main>", encoding="utf-8")
    assert gate.gate_output_boundary(tmp_path)["status"] == gate.PASS


def test_output_boundary_blocks_on_raw_extraction_dir(tmp_path: Path):
    (tmp_path / "extracted").mkdir()
    res = gate.gate_output_boundary(tmp_path)
    assert res["status"] == gate.BLOCK


def test_output_boundary_blocks_on_node_name_dump(tmp_path: Path):
    classes = " ".join(f'<div class="main_f{i}"></div>' for i in range(10))
    (tmp_path / "dump.html").write_text(f"<html>{classes}</html>", encoding="utf-8")
    assert gate.gate_output_boundary(tmp_path)["status"] == gate.BLOCK


# --- mixed-styles -----------------------------------------------------------

def test_mixed_styles_skips_without_spec(tmp_path: Path):
    html = tmp_path / "i.html"; html.write_text("x", encoding="utf-8")
    css = tmp_path / "c.css"; css.write_text("x", encoding="utf-8")
    assert gate.gate_mixed_styles(None, html, css)["status"] == gate.SKIP


def test_mixed_styles_blocks_on_dropped_segment_color(tmp_path: Path):
    spec = tmp_path / "sec_spec.json"
    spec.write_text(
        '{"text_nodes":[{"characters":"hi","has_mixed_styles":true,'
        '"color":"#000000","character_segments":'
        '[{"color":"#000000"},{"color":"#ff0000"}]}]}',
        encoding="utf-8",
    )
    html = tmp_path / "i.html"; html.write_text("<p>hi</p>", encoding="utf-8")
    css = tmp_path / "c.css"; css.write_text("p{color:#000}", encoding="utf-8")
    assert gate.gate_mixed_styles(spec, html, css)["status"] == gate.BLOCK


# --- ledger gates -----------------------------------------------------------

def test_workflow_order_skips_without_ledger():
    assert gate.gate_workflow_order(None)["status"] == gate.SKIP


def test_extraction_provenance_skips_without_ledger():
    assert gate.gate_extraction_provenance(None)["status"] == gate.SKIP


def test_workflow_order_blocks_on_out_of_order_ledger(tmp_path: Path):
    ledger = tmp_path / "workflow-ledger.json"
    ledger.write_text(
        '{"steps":[{"step":"extract"},{"step":"values"},'
        '{"step":"structure"},{"step":"verify"}]}',
        encoding="utf-8",
    )
    assert gate.gate_workflow_order(ledger)["status"] == gate.BLOCK


def test_workflow_order_passes_on_correct_ledger(tmp_path: Path):
    ledger = tmp_path / "workflow-ledger.json"
    ledger.write_text(
        '{"steps":[{"step":"extract"},{"step":"structure"},'
        '{"step":"values"},{"step":"verify"}]}',
        encoding="utf-8",
    )
    assert gate.gate_workflow_order(ledger)["status"] == gate.PASS


# --- summarize --------------------------------------------------------------

def test_summarize_allows_when_all_pass_or_skip():
    results = [
        {"name": "a", "status": gate.PASS, "detail": ""},
        {"name": "b", "status": gate.SKIP, "detail": ""},
    ]
    decision, reason = gate.summarize(results)
    assert decision == "allow"
    assert "PASS" in reason


def test_summarize_blocks_when_any_gate_blocks():
    results = [
        {"name": "a", "status": gate.PASS, "detail": ""},
        {"name": "b", "status": gate.BLOCK, "detail": "raw dump"},
    ]
    decision, reason = gate.summarize(results)
    assert decision == "block"
    assert "BLOCKED" in reason and "raw dump" in reason


def test_find_ledger_returns_none_when_absent(tmp_path: Path):
    assert gate.find_ledger(tmp_path, tmp_path) is None

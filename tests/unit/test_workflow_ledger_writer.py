"""AGI-004 #4: workflow ledger writer.

The writer must produce ledgers that the existing checkers
(check-workflow-order.py / check-extraction-provenance.py) accept, record steps
in order, reset on `extract`, and fail loudly on misuse.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools"

_spec = importlib.util.spec_from_file_location("workflow_ledger", TOOLS / "workflow-ledger.py")
wl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wl)


def _ledger(tmp_path: Path) -> Path:
    return tmp_path / "workflow-ledger.json"


def test_init_creates_empty_section(tmp_path: Path):
    p = _ledger(tmp_path)
    wl.init_ledger(p, "main_visual")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data == {"section": "main_visual", "steps": []}


def test_append_records_step_provider_and_ts(tmp_path: Path):
    p = _ledger(tmp_path)
    wl.append_step(p, "extract", "figma-section-spec", section="hero")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["section"] == "hero"
    assert len(data["steps"]) == 1
    step = data["steps"][0]
    assert step["step"] == "extract"
    assert step["provider"] == "figma-section-spec"
    assert step["ts"]  # non-empty timestamp


def test_extract_resets_section(tmp_path: Path):
    p = _ledger(tmp_path)
    wl.append_step(p, "extract", "figma-section-spec", section="hero")
    wl.append_step(p, "structure", "omx")
    # new section extract resets
    wl.append_step(p, "extract", "figma-section-spec", section="footer")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["section"] == "footer"
    assert [s["step"] for s in data["steps"]] == ["extract"]


def test_non_extract_without_ledger_raises(tmp_path: Path):
    p = _ledger(tmp_path)
    with pytest.raises(ValueError):
        wl.append_step(p, "structure", "omx")


def test_invalid_step_raises(tmp_path: Path):
    p = _ledger(tmp_path)
    with pytest.raises(ValueError):
        wl.append_step(p, "deploy", "omx", section="x")


def test_section_mismatch_raises(tmp_path: Path):
    p = _ledger(tmp_path)
    wl.append_step(p, "extract", "figma-section-spec", section="hero")
    with pytest.raises(ValueError):
        wl.append_step(p, "structure", "omx", section="footer")


def test_full_sequence_passes_order_checker(tmp_path: Path):
    p = _ledger(tmp_path)
    wl.append_step(p, "extract", "figma-section-spec", section="hero")
    wl.append_step(p, "structure", "omx")
    wl.append_step(p, "values", "omx")
    wl.append_step(p, "verify", "pm-verify")
    r = subprocess.run(
        [sys.executable, str(TOOLS / "check-workflow-order.py"), "--ledger", str(p)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_full_sequence_passes_provenance_checker(tmp_path: Path):
    p = _ledger(tmp_path)
    wl.append_step(p, "extract", "figma-section-spec", section="hero")
    wl.append_step(p, "structure", "omx")
    wl.append_step(p, "values", "claude")
    wl.append_step(p, "verify", "pm-verify")
    r = subprocess.run(
        [sys.executable, str(TOOLS / "check-extraction-provenance.py"), "--ledger", str(p)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_out_of_order_caught_by_checker(tmp_path: Path):
    """values before structure must be rejected by the order checker."""
    p = _ledger(tmp_path)
    wl.append_step(p, "extract", "figma-section-spec", section="hero")
    wl.append_step(p, "values", "omx")
    wl.append_step(p, "structure", "omx")
    wl.append_step(p, "verify", "pm-verify")
    r = subprocess.run(
        [sys.executable, str(TOOLS / "check-workflow-order.py"), "--ledger", str(p)],
        capture_output=True, text=True,
    )
    assert r.returncode == 1


def test_cli_append_and_show(tmp_path: Path):
    p = _ledger(tmp_path)
    base = [sys.executable, str(TOOLS / "workflow-ledger.py"), "--ledger", str(p)]
    r1 = subprocess.run(base + ["append", "--step", "extract", "--provider", "figma-section-spec",
                                "--section", "hero"], capture_output=True, text=True)
    assert r1.returncode == 0, r1.stderr
    r2 = subprocess.run(base + ["show"], capture_output=True, text=True)
    assert r2.returncode == 0
    assert "hero" in r2.stdout


def test_cli_append_unknown_step_errors(tmp_path: Path):
    p = _ledger(tmp_path)
    base = [sys.executable, str(TOOLS / "workflow-ledger.py"), "--ledger", str(p)]
    r = subprocess.run(base + ["append", "--step", "bogus", "--provider", "omx",
                               "--section", "x"], capture_output=True, text=True)
    assert r.returncode != 0  # argparse choices rejects it

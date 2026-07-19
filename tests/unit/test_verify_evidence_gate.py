"""DOD-006: verification execution evidence gate.

Completion/delivery must be blocked unless a fresh pm-verify report proves
verification actually ran and passed on the CURRENT deliverable (sha-matched).
"""

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "tools" / "verify-evidence-gate.py"

spec = importlib.util.spec_from_file_location("verify_evidence_gate", GATE_PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _setup(tmp_path):
    html = tmp_path / "index.html"
    css = tmp_path / "common.css"
    html.write_text("<html><body></body></html>", encoding="utf-8")
    css.write_text(".main_intro{display:flex}", encoding="utf-8")
    spec = tmp_path / "section_spec.json"
    spec.write_text(
        json.dumps({"text_nodes": [{"id": "1", "characters": "hi", "fontSize": 16}]}),
        encoding="utf-8",
    )
    return html, css, spec


def _write_report(tmp_path, html, css, spec=None, passed=True, spec_shas=None):
    report = tmp_path / "pm-verify-report.json"
    payload = {
        "verified_at": "2026-06-15T00:00:00+00:00",
        "html_path": str(html),
        "css_path": str(css),
        "html_sha256": _sha(html),
        "css_sha256": _sha(css),
        "exit_code": 0 if passed else 1,
        "passed": passed,
    }
    if spec_shas is not None:
        payload["spec_coverage"] = {"spec_shas": spec_shas}
    elif spec is not None:
        payload["spec_coverage"] = {"spec_shas": {str(spec): _sha(spec)}}
    report.write_text(json.dumps(payload), encoding="utf-8")
    return report


def test_matching_passing_report_allows(tmp_path):
    html, css, spec_path = _setup(tmp_path)
    report = _write_report(tmp_path, html, css, spec_path, passed=True)
    ok, reason = gate.check_evidence(html, css, report)
    assert ok is True, reason


def test_missing_report_blocks(tmp_path):
    html, css, _ = _setup(tmp_path)
    ok, reason = gate.check_evidence(html, css, tmp_path / "nope.json")
    assert ok is False
    assert "no_evidence" in reason


def test_stale_report_after_file_change_blocks(tmp_path):
    html, css, spec_path = _setup(tmp_path)
    report = _write_report(tmp_path, html, css, spec_path, passed=True)
    html.write_text("<html><body>changed after verify</body></html>", encoding="utf-8")
    ok, reason = gate.check_evidence(html, css, report)
    assert ok is False
    assert "stale_evidence" in reason


def test_failed_verification_report_blocks(tmp_path):
    html, css, spec_path = _setup(tmp_path)
    report = _write_report(tmp_path, html, css, spec_path, passed=False)
    ok, reason = gate.check_evidence(html, css, report)
    assert ok is False
    assert "verification_failed" in reason


def test_spec_sha_binding_blocks_when_current_spec_changed(tmp_path):
    html, css, spec_path = _setup(tmp_path)
    report = _write_report(tmp_path, html, css, spec_path, passed=True)
    spec_path.write_text(
        json.dumps({"text_nodes": [{"id": "1", "characters": "changed", "fontSize": 16}]}),
        encoding="utf-8",
    )
    ok, reason = gate.check_evidence(html, css, report, spec_paths=[spec_path])
    assert ok is False
    assert "stale_spec_evidence" in reason


def test_spec_sha_binding_legacy_report_stays_compatible(tmp_path):
    html, css, spec_path = _setup(tmp_path)
    report = _write_report(tmp_path, html, css, spec=None, passed=True, spec_shas=None)
    ok, reason = gate.check_evidence(html, css, report, spec_paths=[spec_path])
    assert ok is True, reason

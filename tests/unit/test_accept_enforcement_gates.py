"""Force Figma 실측 + 검증툴 실행 at the accept gate.

- gate_spec_measured: publishing deliverable must ship extracted/*_spec.json with
  real typography; no spec / no fontSize → BLOCK (no silent skip).
- gate_verify_evidence: a fresh sha-bound pm-verify report must exist; missing
  (pm-verify never run) or stale → BLOCK.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "tools"
_spec = importlib.util.spec_from_file_location(
    "accept_preflight_verify_enf", TOOLS / "accept-preflight-verify.py"
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def _spec_json(tmp_path: Path, *, with_font: bool) -> Path:
    node = {"id": "1", "characters": "hi"}
    if with_font:
        node["fontSize"] = 24
    p = tmp_path / "sec_spec.json"
    p.write_text(json.dumps({"text_nodes": [node]}), encoding="utf-8")
    return p


# ---- gate_spec_measured (force Figma 실측) ----

def test_spec_measured_blocks_when_no_spec():
    assert gate.gate_spec_measured([])["status"] == gate.BLOCK


def test_spec_measured_blocks_when_no_font_metadata(tmp_path):
    sf = _spec_json(tmp_path, with_font=False)
    assert gate.gate_spec_measured([sf])["status"] == gate.BLOCK


def test_spec_measured_passes_with_real_typography(tmp_path):
    sf = _spec_json(tmp_path, with_font=True)
    assert gate.gate_spec_measured([sf])["status"] == gate.PASS


# ---- gate_verify_evidence (force 검증툴 실행) ----

def _deliverable(tmp_path: Path):
    html = tmp_path / "index.html"
    css = tmp_path / "common.css"
    html.write_text("<html><body>x</body></html>", encoding="utf-8")
    css.write_text("body{margin:0}", encoding="utf-8")
    return html, css


def _report(tmp_path: Path, html: Path, css: Path, *, fresh: bool, passed: bool = True) -> Path:
    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()
    rep = {
        "passed": passed,
        "exit_code": 0 if passed else 1,
        "html_sha256": sha(html) if fresh else "stale0000",
        "css_sha256": sha(css) if fresh else "stale0000",
    }
    p = tmp_path / "pm-verify-report.json"
    p.write_text(json.dumps(rep), encoding="utf-8")
    return p


def _visual_report(
    tmp_path: Path,
    html: Path,
    design: Path,
    *,
    fresh: bool,
    passed: bool = True,
    allow_visual_mismatch: bool = False,
    css: Path | None = None,
    section: str | None = None,
) -> Path:
    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()
    rep = {
        "passed": passed,
        "exit_code": 0 if passed else 1,
        "html_path": str(html),
        "css_path": str(css) if css else None,
        "design_path": str(design),
        "html_sha256": sha(html) if fresh else "stale-html",
        "css_sha256": sha(css) if css and fresh else ("stale-css" if css else None),
        "design_sha256": sha(design) if fresh else "stale-design",
        "allow_visual_mismatch": allow_visual_mismatch,
        "threshold_passed": passed and not allow_visual_mismatch,
        "section": section,
    }
    p = tmp_path / "visual-compare-report.json"
    p.write_text(json.dumps(rep), encoding="utf-8")
    return p


def test_verify_evidence_blocks_when_no_report(tmp_path):
    html, css = _deliverable(tmp_path)
    missing = tmp_path / "nope.json"
    assert gate.gate_verify_evidence(html, css, missing)["status"] == gate.BLOCK


def test_verify_evidence_blocks_when_stale(tmp_path):
    html, css = _deliverable(tmp_path)
    rep = _report(tmp_path, html, css, fresh=False)
    assert gate.gate_verify_evidence(html, css, rep)["status"] == gate.BLOCK


def test_verify_evidence_blocks_when_verification_failed(tmp_path):
    html, css = _deliverable(tmp_path)
    rep = _report(tmp_path, html, css, fresh=True, passed=False)
    assert gate.gate_verify_evidence(html, css, rep)["status"] == gate.BLOCK


def test_verify_evidence_passes_with_fresh_report(tmp_path):
    html, css = _deliverable(tmp_path)
    rep = _report(tmp_path, html, css, fresh=True, passed=True)
    assert gate.gate_verify_evidence(html, css, rep)["status"] == gate.PASS


# ---- gate_visual_compare (opt-in visual evidence) ----

def test_gate_visual_skips_when_no_report(tmp_path):
    html, _ = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"design")
    missing = tmp_path / "no-visual-report.json"
    assert gate.gate_visual_compare(html, design, missing)["status"] == gate.SKIP


def test_gate_visual_blocks_when_stale(tmp_path):
    html, _ = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"design")
    rep = _visual_report(tmp_path, html, design, fresh=False)
    assert gate.gate_visual_compare(html, design, rep)["status"] == gate.BLOCK


def test_gate_visual_blocks_when_visual_failed_without_allowance(tmp_path):
    html, _ = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"design")
    rep = _visual_report(
        tmp_path,
        html,
        design,
        fresh=True,
        passed=False,
        allow_visual_mismatch=False,
    )
    assert gate.gate_visual_compare(html, design, rep)["status"] == gate.BLOCK


def test_gate_visual_passes_with_allowance_and_audit_detail(tmp_path):
    html, _ = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"design")
    rep = _visual_report(
        tmp_path,
        html,
        design,
        fresh=True,
        passed=True,
        allow_visual_mismatch=True,
    )
    result = gate.gate_visual_compare(html, design, rep)
    assert result["status"] == gate.PASS
    assert "allow_visual_mismatch=true" in result["detail"]


def test_gate_visual_blocks_when_css_sha_mismatch(tmp_path):
    html, css = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"design")
    rep = _visual_report(tmp_path, html, design, fresh=True, css=css)
    css.write_text("body{margin:8px}", encoding="utf-8")

    result = gate.gate_visual_compare(html, design, rep, css_path=css)

    assert result["status"] == gate.BLOCK
    assert "css sha mismatch" in result["detail"]


def test_visual_freshness_blocks_when_design_file_replaced(tmp_path):
    html, css = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"old-design")
    rep = _visual_report(tmp_path, html, design, fresh=True, css=css)
    design.write_bytes(b"new-design")

    result = gate.gate_visual_compare(html, design, rep, css_path=css)

    assert result["status"] == gate.BLOCK
    assert "design sha mismatch" in result["detail"]


def test_visual_freshness_blocks_when_report_design_path_differs_from_expected(tmp_path):
    html, css = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    old_design = tmp_path / "design-old.png"
    design.write_bytes(b"current-design")
    old_design.write_bytes(b"old-design")
    rep = _visual_report(tmp_path, html, old_design, fresh=True, css=css)

    result = gate.gate_visual_compare(html, design, rep, css_path=css)

    assert result["status"] == gate.BLOCK
    assert "design path mismatch" in result["detail"]


def test_visual_freshness_blocks_when_report_section_differs_from_ledger(tmp_path):
    html, css = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"design")
    ledger = tmp_path / "workflow-ledger.json"
    ledger.write_text(
        json.dumps({"section": "main_visual", "steps": [{"step": "extract", "provider": "figma-section-spec"}]}),
        encoding="utf-8",
    )
    rep = _visual_report(tmp_path, html, design, fresh=True, css=css, section="other_section")

    result = gate.gate_visual_compare(html, design, rep, css_path=css, ledger_path=ledger)

    assert result["status"] == gate.BLOCK
    assert "section mismatch" in result["detail"]


def test_gate_visual_allowance_passes_even_when_passed_false(tmp_path):
    html, css = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"design")
    rep = _visual_report(tmp_path, html, design, fresh=True, passed=False, allow_visual_mismatch=True, css=css)

    result = gate.gate_visual_compare(html, design, rep, css_path=css)

    assert result["status"] == gate.PASS
    assert "threshold override audited" in result["detail"]


# ---- evaluate_gates wiring: the two enforcement gates are present and lead ----

def test_evaluate_gates_includes_enforcement_first(tmp_path):
    html, css = _deliverable(tmp_path)
    design = tmp_path / "design.png"
    design.write_bytes(b"design")
    results = gate.evaluate_gates(
        deliverable_dir=tmp_path, html_path=html, css_path=css, spec_file=None,
        project_root=tmp_path, ledger=None, profile="basic",
        spec_files=[], verify_report=tmp_path / "absent.json", visual_report=None,
        design_asset=design,
    )
    names = [r["name"] for r in results]
    assert names[0] == "spec-measured"
    assert names[1] == "verify-evidence"
    assert names[2] == "visual-compare"
    # both block on an unmeasured, unverified deliverable
    decision, _ = gate.summarize(results)
    assert decision == "block"

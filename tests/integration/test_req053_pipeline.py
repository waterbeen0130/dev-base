from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
VISUAL_COMPARE = TOOLS / "visual-compare.py"
ACCEPT_PRECHECK = TOOLS / "accept-preflight-verify.py"
WORKFLOW_LEDGER = TOOLS / "workflow-ledger.py"
CHECK_WORKFLOW_ORDER = TOOLS / "check-workflow-order.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_playwright_unavailable(output: str) -> bool:
    lowered = output.lower()
    return (
        "playwright" in lowered
        and ("executable doesn't exist" in lowered or "please run the following command" in lowered)
    )


def _skip_if_playwright_unavailable(exc: Exception) -> None:
    if _is_playwright_unavailable(str(exc)):
        pytest.skip("Playwright browser runtime unavailable")


def _run_tool(script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd or ROOT,
    )
    if _is_playwright_unavailable(result.stdout + result.stderr):
        pytest.skip("Playwright browser runtime unavailable")
    return result


def _write_visual_fixture(tmp_path: Path, *, primary_height: int = 200) -> tuple[Path, Path]:
    html = tmp_path / "index.html"
    css = tmp_path / "common.css"
    html.write_text(
        textwrap.dedent(
            """
            <!doctype html>
            <html lang="ko">
            <head>
            <meta charset="utf-8">
            <title>REQ053 Visual Fixture</title>
            <link rel="stylesheet" href="common.css">
            </head>
            <body>
            <section class="main_visual">
            <div class="main_visual_panel">
            <div class="main_visual_primary"></div>
            <div class="main_visual_secondary"></div>
            </div>
            </section>
            </body>
            </html>
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    css.write_text(
        textwrap.dedent(
            f"""
            html,body{{margin:0}}
            .main_visual{{display:flex;justify-content:center}}
            .main_visual .main_visual_panel{{display:flex;flex-direction:column;width:1920px}}
            .main_visual .main_visual_primary{{width:1920px;height:{primary_height}px;background:#112233}}
            .main_visual .main_visual_secondary{{width:1920px;height:180px;background:#445566}}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return html, css


def _write_spec(spec_path: Path) -> Path:
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        json.dumps(
            {
                "section": {"id": "main", "name": "main"},
                "text_nodes": [
                    {
                        "id": "1:1",
                        "name": "headline",
                        "characters": "REQ053",
                        "fontFamily": "Pretendard",
                        "fontSize": 32,
                        "fontWeight": 700,
                        "lineHeightPx": 45,
                        "lineHeightRatio": 1.4,
                        "letterSpacing": 0,
                        "color": "#111111",
                        "has_mixed_styles": False,
                        "character_segments": [],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return spec_path


def _write_verify_report(report_path: Path, html: Path, css: Path, spec_files: list[Path]) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "passed": True,
                "exit_code": 0,
                "html_sha256": _sha256(html),
                "css_sha256": _sha256(css),
                "spec_coverage": {
                    "spec_shas": {str(spec_file): _sha256(spec_file) for spec_file in spec_files},
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


@pytest.mark.browser
def test_req053_pipeline_visual_compare_report_passes_then_failed_report_blocks(tmp_path: Path) -> None:
    pytest.importorskip("playwright.sync_api")
    visual = _load_module(VISUAL_COMPARE, "visual_compare_req053")
    accept = _load_module(ACCEPT_PRECHECK, "accept_preflight_req053")

    html, css = _write_visual_fixture(tmp_path, primary_height=200)
    design = tmp_path / "design.png"
    try:
        visual.render_html_to_png(html, 1920, design)
    except Exception as exc:  # noqa: BLE001
        _skip_if_playwright_unavailable(exc)
        raise

    report = tmp_path / "visual-compare-pass.json"
    out_dir = tmp_path / "artifacts"
    passed = _run_tool(
        VISUAL_COMPARE,
        "--html",
        str(html),
        "--css",
        str(css),
        "--design",
        str(design),
        "--emit-report",
        str(report),
        "--out-dir",
        str(out_dir),
    )
    assert passed.returncode == 0, passed.stdout + passed.stderr

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert Path(payload["diff_image_path"]).is_file()

    gate_result = accept.gate_visual_compare(html, design, report)
    assert gate_result["status"] == accept.PASS

    _, css = _write_visual_fixture(tmp_path, primary_height=260)
    failed_report = tmp_path / "visual-compare-fail.json"
    failed = _run_tool(
        VISUAL_COMPARE,
        "--html",
        str(html),
        "--css",
        str(css),
        "--design",
        str(design),
        "--emit-report",
        str(failed_report),
        "--out-dir",
        str(out_dir),
    )
    assert failed.returncode == 1, failed.stdout + failed.stderr

    failed_payload = json.loads(failed_report.read_text(encoding="utf-8"))
    assert failed_payload["passed"] is False

    failed_gate = accept.gate_visual_compare(html, design, failed_report)
    assert failed_gate["status"] == accept.BLOCK
    assert "visual compare failed" in failed_gate["detail"]


def test_req053_pipeline_visual_freshness_blocks_css_and_design_bypasses(tmp_path: Path) -> None:
    accept = _load_module(ACCEPT_PRECHECK, "accept_preflight_req053_freshness")
    html, css = _write_visual_fixture(tmp_path, primary_height=200)
    design = tmp_path / "design-current.png"
    design.write_bytes(b"current-design")
    report = tmp_path / "visual-compare-report.json"
    report.write_text(
        json.dumps(
            {
                "passed": True,
                "html_path": str(html),
                "css_path": str(css),
                "design_path": str(design),
                "html_sha256": _sha256(html),
                "css_sha256": _sha256(css),
                "design_sha256": _sha256(design),
                "section": "main_visual",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    ledger = tmp_path / "workflow-ledger.json"
    ledger.write_text(
        json.dumps({"section": "main_visual", "steps": [{"step": "extract", "provider": "figma-section-spec"}]}),
        encoding="utf-8",
    )

    css.write_text(css.read_text(encoding="utf-8").replace("height:200px", "height:260px"), encoding="utf-8")
    css_result = accept.gate_visual_compare(html, design, report, css_path=css, ledger_path=ledger)
    assert css_result["status"] == accept.BLOCK
    assert "css sha mismatch" in css_result["detail"]

    css = _write_visual_fixture(tmp_path, primary_height=200)[1]
    old_design = tmp_path / "design-old.png"
    old_design.write_bytes(b"old-design")
    report.write_text(
        json.dumps(
            {
                "passed": True,
                "html_path": str(html),
                "css_path": str(css),
                "design_path": str(old_design),
                "html_sha256": _sha256(html),
                "css_sha256": _sha256(css),
                "design_sha256": _sha256(old_design),
                "section": "main_visual",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    design_path_result = accept.gate_visual_compare(html, design, report, css_path=css, ledger_path=ledger)
    assert design_path_result["status"] == accept.BLOCK
    assert "design path mismatch" in design_path_result["detail"]

    design.write_bytes(b"replaced-design")
    report.write_text(
        json.dumps(
            {
                "passed": True,
                "html_path": str(html),
                "css_path": str(css),
                "design_path": str(design),
                "html_sha256": _sha256(html),
                "css_sha256": _sha256(css),
                "design_sha256": hashlib.sha256(b"stale-design").hexdigest(),
                "section": "main_visual",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    design_sha_result = accept.gate_visual_compare(html, design, report, css_path=css, ledger_path=ledger)
    assert design_sha_result["status"] == accept.BLOCK
    assert "design sha mismatch" in design_sha_result["detail"]


@pytest.mark.browser
def test_req053_pipeline_workflow_order_accepts_visual_compare_step(tmp_path: Path) -> None:
    pytest.importorskip("playwright.sync_api")
    visual = _load_module(VISUAL_COMPARE, "visual_compare_req053_ledger")

    ledger = tmp_path / "workflow-ledger.json"
    first = _run_tool(
        WORKFLOW_LEDGER,
        "--ledger",
        str(ledger),
        "append",
        "--step",
        "extract",
        "--provider",
        "figma-section-spec",
        "--section",
        "main",
    )
    assert first.returncode == 0, first.stdout + first.stderr

    for step, provider in (("structure", "omx"), ("values", "omx"), ("verify", "pm-verify")):
        result = _run_tool(
            WORKFLOW_LEDGER,
            "--ledger",
            str(ledger),
            "append",
            "--step",
            step,
            "--provider",
            provider,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    html, _ = _write_visual_fixture(tmp_path, primary_height=100)
    design = tmp_path / "design.png"
    try:
        visual.render_html_to_png(html, 1920, design)
    except Exception as exc:  # noqa: BLE001
        _skip_if_playwright_unavailable(exc)
        raise

    compare = _run_tool(
        VISUAL_COMPARE,
        "--html",
        str(html),
        "--design",
        str(design),
        "--section",
        "main",
        "--ledger",
        str(ledger),
    )
    assert compare.returncode == 0, compare.stdout + compare.stderr

    payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert payload["steps"][-1]["step"] == "visual-compare"
    assert payload["steps"][-1]["provider"] == "visual-compare"

    order = _run_tool(CHECK_WORKFLOW_ORDER, "--ledger", str(ledger))
    assert order.returncode == 0, order.stdout + order.stderr


def test_req053_pipeline_visual_report_absence_keeps_accept_decision_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    accept = _load_module(ACCEPT_PRECHECK, "accept_preflight_req053_regression")
    deliverable_dir = tmp_path / "deliverable"
    deliverable_dir.mkdir()
    html, css = _write_visual_fixture(deliverable_dir, primary_height=200)
    spec_file = _write_spec(tmp_path / "spec-fixtures" / "main_spec.json")
    verify_report = _write_verify_report(
        tmp_path / ".gran-maestro" / "pm-verify-report.json",
        html,
        css,
        [spec_file],
    )

    monkeypatch.setattr(
        accept,
        "gate_validate_semantic",
        lambda html_path, css_path, profile: accept._result("validate-semantic", accept.PASS, "stubbed pass"),
    )

    results = accept.evaluate_gates(
        deliverable_dir=deliverable_dir,
        html_path=html,
        css_path=css,
        spec_file=spec_file,
        project_root=ROOT,
        ledger=None,
        profile="basic",
        spec_files=[spec_file],
        verify_report=verify_report,
        visual_report=None,
        design_asset=None,
    )

    decision, reason = accept.summarize(results)
    statuses = {result["name"]: result["status"] for result in results}

    assert decision == "allow", reason
    assert statuses["spec-measured"] == accept.PASS
    assert statuses["verify-evidence"] == accept.PASS
    assert statuses["visual-compare"] == accept.SKIP
    assert statuses["output-boundary"] == accept.PASS
    assert statuses["mixed-styles"] == accept.PASS
    assert statuses["deprecated-tools"] == accept.PASS
    assert statuses["workflow-order"] == accept.SKIP
    assert statuses["extraction-provenance"] == accept.SKIP

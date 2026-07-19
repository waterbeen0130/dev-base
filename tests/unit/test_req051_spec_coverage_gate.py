from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


accept_preflight = _load_module("accept_preflight_verify_req051_coverage", TOOLS / "accept-preflight-verify.py")


def _write_spec(path: Path, *, node_count: int, include_font: bool = True) -> Path:
    text_nodes = []
    for index in range(node_count):
        node = {
            "id": f"1:{index + 1}",
            "name": f"text_{index + 1}",
            "characters": f"Spec Text {index + 1}",
            "fontFamily": "Pretendard",
            "fontWeight": 400,
            "lineHeightPx": 24,
            "lineHeightRatio": 1.5,
            "letterSpacing": 0,
            "color": "#111111",
        }
        if include_font:
            node["fontSize"] = 16
        text_nodes.append(node)
    path.write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "text_nodes": text_nodes,
                "frame_nodes": [],
                "interactions": [],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_html_css(path: Path, *, block_count: int) -> tuple[Path, Path]:
    html_path = path / "index.html"
    css_path = path / "common.css"
    blocks = "\n".join(
        f'<p class="copy copy_{index + 1}">Visible block {index + 1}</p>'
        for index in range(block_count)
    )
    html_path.write_text(
        textwrap.dedent(
            f"""
            <!doctype html>
            <html lang="ko">
            <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="common.css">
            </head>
            <body>
            <section class="main_visual">
            {blocks}
            </section>
            </body>
            </html>
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    css_path.write_text(
        ".main_visual{display:flex;flex-direction:column}\n"
        ".main_visual .copy{font-size:16px;color:#111111}\n",
        encoding="utf-8",
    )
    return html_path, css_path


def _write_inline_markup_html_css(path: Path) -> tuple[Path, Path]:
    html_path = path / "index.html"
    css_path = path / "common.css"
    html_path.write_text(
        textwrap.dedent(
            """
            <!doctype html>
            <html lang="ko">
            <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="common.css">
            </head>
            <body>
            <section class="main_visual">
            <p class="copy">Hello <strong>bold</strong> world</p>
            <h2 class="title">t <a href="#x">x</a></h2>
            </section>
            </body>
            </html>
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    css_path.write_text(
        ".main_visual{display:flex;flex-direction:column}\n"
        ".main_visual .copy,.main_visual .title{font-size:16px;color:#111111}\n",
        encoding="utf-8",
    )
    return html_path, css_path


def _run_pm_verify(
    tmp_path: Path,
    *,
    spec_nodes: int,
    html_blocks: int,
    extra_args: list[str] | None = None,
    emit_report: bool = False,
) -> subprocess.CompletedProcess[str]:
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    _write_spec(spec_dir / "section_spec.json", node_count=spec_nodes)
    html_path, css_path = _write_html_css(tmp_path, block_count=html_blocks)

    wrapper = textwrap.dedent(
        """
        import importlib.util
        import sys
        from pathlib import Path

        module_path = Path(sys.argv[1])
        spec = importlib.util.spec_from_file_location("pm_verify_req051_coverage_subprocess", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        module.run = lambda cmd: (0, "")
        module.check_broken_links = lambda html_path, img_dir: []

        argv = [
            "pm-verify.py",
            "--spec-dir", sys.argv[2],
            "--html", sys.argv[3],
            "--css", sys.argv[4],
            "--profile", "basic",
        ] + sys.argv[5:]
        sys.argv = argv
        raise SystemExit(module.main())
        """
    )

    argv = [
        sys.executable,
        "-c",
        wrapper,
        str(TOOLS / "pm-verify.py"),
        str(spec_dir),
        str(html_path),
        str(css_path),
    ]
    if emit_report:
        argv.extend(["--emit-report", str(tmp_path / "pm-verify-report.json")])
    if extra_args:
        argv.extend(extra_args)
    return subprocess.run(argv, text=True, capture_output=True, check=False)


def test_nested_inline_text_blocks_are_counted_once(tmp_path: Path):
    _write_spec(tmp_path / "section_spec.json", node_count=2)
    html_path, _ = _write_inline_markup_html_css(tmp_path)

    assert accept_preflight.count_html_text_blocks(html_path) == 2


def test_spec_coverage_pm_verify_blocks_low_coverage_shell_spec(tmp_path: Path):
    result = _run_pm_verify(tmp_path, spec_nodes=1, html_blocks=20)
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert "spec 커버리지" in output
    assert "spec_text_nodes=1" in output
    assert "html_text_blocks=20" in output
    assert "ratio=0.05" in output


def test_spec_coverage_pm_verify_allows_when_thresholds_met(tmp_path: Path):
    result = _run_pm_verify(tmp_path, spec_nodes=6, html_blocks=20)
    output = result.stdout + result.stderr

    assert result.returncode == 0
    assert "spec 커버리지" not in output
    assert "결과: ✓ PASS" in output


def test_allow_low_coverage_flag_warns_and_passes(tmp_path: Path):
    result = _run_pm_verify(
        tmp_path,
        spec_nodes=1,
        html_blocks=20,
        extra_args=["--allow-low-coverage"],
        emit_report=True,
    )
    output = result.stdout + result.stderr
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert "WARNING: spec 커버리지 낮음" in output
    assert report["spec_coverage"]["allow_low_coverage"] is True
    assert report["spec_coverage"]["passed"] is True


def test_spec_coverage_masking_is_blocked_per_current_spec(tmp_path: Path):
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    _write_spec(spec_dir / "current_spec.json", node_count=1)
    _write_spec(spec_dir / "old_spec.json", node_count=6)
    html_path, _ = _write_html_css(tmp_path, block_count=20)

    measurement = accept_preflight.measure_spec_coverage(
        [spec_dir / "current_spec.json", spec_dir / "old_spec.json"],
        html_path,
    )

    assert measurement["spec_text_nodes"] == 1
    assert measurement["target_spec_paths"] == [str(spec_dir / "current_spec.json")]
    assert measurement["passed"] is False


def test_gate_coverage_accept_blocks_when_spec_coverage_is_too_low(tmp_path: Path):
    spec_path = _write_spec(tmp_path / "section_spec.json", node_count=1)
    html_path, _ = _write_html_css(tmp_path, block_count=20)

    result = accept_preflight.gate_spec_measured([spec_path], html_path=html_path)

    assert result["status"] == accept_preflight.BLOCK
    assert "spec 커버리지" in result["detail"]
    assert "spec_text_nodes=1" in result["detail"]
    assert "html_text_blocks=20" in result["detail"]


def test_gate_coverage_accept_consumes_allow_low_coverage_report(tmp_path: Path):
    spec_path = _write_spec(tmp_path / "section_spec.json", node_count=1)
    html_path, _ = _write_html_css(tmp_path, block_count=20)
    report_path = tmp_path / "pm-verify-report.json"
    report_path.write_text(
        json.dumps(
            {
                "spec_coverage": {
                    "allow_low_coverage": True,
                    "spec_text_nodes": 1,
                    "html_text_blocks": 20,
                    "ratio": 0.05,
                    "threshold_ratio": 0.3,
                    "min_nodes": 5,
                    "effective_min_nodes": 5,
                    "passed": True,
                    "spec_shas": {
                        str(spec_path): _sha(spec_path),
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    result = accept_preflight.gate_spec_measured(
        [spec_path],
        html_path=html_path,
        verify_report=report_path,
    )

    assert result["status"] == accept_preflight.PASS
    assert "allow_low_coverage" in result["detail"]


def test_spec_sha_binding_accept_rejects_stale_allow_low_coverage_report(tmp_path: Path):
    spec_path = _write_spec(tmp_path / "section_spec.json", node_count=1)
    html_path, _ = _write_html_css(tmp_path, block_count=20)
    report_path = tmp_path / "pm-verify-report.json"
    report_path.write_text(
        json.dumps(
            {
                "spec_coverage": {
                    "allow_low_coverage": True,
                    "spec_text_nodes": 1,
                    "html_text_blocks": 20,
                    "ratio": 0.05,
                    "threshold_ratio": 0.3,
                    "min_nodes": 5,
                    "effective_min_nodes": 5,
                    "passed": True,
                    "spec_shas": {
                        str(spec_path): "stale-spec-sha",
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    result = accept_preflight.gate_spec_measured(
        [spec_path],
        html_path=html_path,
        verify_report=report_path,
    )

    assert result["status"] == accept_preflight.BLOCK
    assert "spec sha" in result["detail"]


def test_spec_sha_binding_accept_requires_spec_shas_for_allow_low_coverage(tmp_path: Path):
    spec_path = _write_spec(tmp_path / "section_spec.json", node_count=1)
    html_path, _ = _write_html_css(tmp_path, block_count=20)
    report_path = tmp_path / "pm-verify-report.json"
    report_path.write_text(
        json.dumps(
            {
                "spec_coverage": {
                    "allow_low_coverage": True,
                    "spec_text_nodes": 1,
                    "html_text_blocks": 20,
                    "ratio": 0.05,
                    "threshold_ratio": 0.3,
                    "min_nodes": 5,
                    "effective_min_nodes": 5,
                    "passed": True,
                }
            }
        ),
        encoding="utf-8",
    )

    result = accept_preflight.gate_spec_measured(
        [spec_path],
        html_path=html_path,
        verify_report=report_path,
    )

    assert result["status"] == accept_preflight.BLOCK
    assert "spec_shas" in result["detail"]


def test_gate_coverage_accept_keeps_existing_behavior_without_html():
    spec_path = ROOT / "tests" / "fixtures" / "req051" / "valid_spec.json"

    result = accept_preflight.gate_spec_measured([spec_path])

    assert result["status"] == accept_preflight.PASS
    assert "typography ok" in result["detail"]


def test_coverage_report_includes_spec_coverage_block(tmp_path: Path):
    result = _run_pm_verify(
        tmp_path,
        spec_nodes=6,
        html_blocks=20,
        emit_report=True,
    )
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert report["passed"] is True
    assert report["spec_coverage"]["spec_text_nodes"] == 6
    assert report["spec_coverage"]["html_text_blocks"] == 20
    assert report["spec_coverage"]["ratio"] == 0.3
    assert report["spec_coverage"]["threshold_ratio"] == 0.3
    assert report["spec_coverage"]["min_nodes"] == 5
    assert report["spec_coverage"]["effective_min_nodes"] == 5
    assert report["spec_coverage"]["allow_low_coverage"] is False
    assert report["spec_coverage"]["passed"] is True


def test_spec_sha_binding_report_includes_current_spec_sha(tmp_path: Path):
    result = _run_pm_verify(
        tmp_path,
        spec_nodes=6,
        html_blocks=20,
        emit_report=True,
    )
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))
    spec_path = tmp_path / "spec" / "section_spec.json"

    assert result.returncode == 0
    assert report["spec_coverage"]["spec_shas"][str(spec_path)]

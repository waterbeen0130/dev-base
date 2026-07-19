from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
FIXTURES = ROOT / "tests" / "fixtures" / "req051"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


accept_preflight = _load_module("accept_preflight_verify_req051", TOOLS / "accept-preflight-verify.py")
pm_verify = _load_module("pm_verify_req051", TOOLS / "pm-verify.py")


def _copy_spec_fixture(tmp_path: Path, fixture_name: str) -> Path:
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    shutil.copy(FIXTURES / fixture_name, spec_dir / "section_spec.json")
    return spec_dir


def _write_minimal_html_css(tmp_path: Path) -> tuple[Path, Path]:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
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
            <h2 class="title">Baseline Title</h2>
            <div class="desc">Baseline description for measured spec.</div>
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
        ".main_visual .title{font-size:32px}\n"
        ".main_visual .desc{font-size:18px}\n",
        encoding="utf-8",
    )
    return html_path, css_path


def _run_pm_verify_baseline_subprocess(
    tmp_path: Path,
    fixture_name: str,
    *,
    allow_missing_spec: bool = False,
) -> subprocess.CompletedProcess[str]:
    spec_dir = _copy_spec_fixture(tmp_path, fixture_name)
    html_path, css_path = _write_minimal_html_css(tmp_path)
    wrapper = textwrap.dedent(
        """
        import importlib.util
        import sys
        from pathlib import Path

        module_path = Path(sys.argv[1])
        spec_dir = sys.argv[2]
        html_path = sys.argv[3]
        css_path = sys.argv[4]
        allow_missing = sys.argv[5] == "1"

        spec = importlib.util.spec_from_file_location("pm_verify_req051_subprocess", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        module.run = lambda cmd: (0, "")
        module.check_broken_links = lambda html_path, img_dir: []

        argv = [
            "pm-verify.py",
            "--spec-dir", spec_dir,
            "--html", html_path,
            "--css", css_path,
            "--profile", "basic",
        ]
        if allow_missing:
            argv.append("--allow-missing-spec")
        sys.argv = argv
        raise SystemExit(module.main())
        """
    )
    return subprocess.run(
        [
            sys.executable,
            "-c",
            wrapper,
            str(TOOLS / "pm-verify.py"),
            str(spec_dir),
            str(html_path),
            str(css_path),
            "1" if allow_missing_spec else "0",
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_accept_gate_baseline_spec_has_font_metadata_passes_with_valid_spec():
    assert accept_preflight.spec_has_font_metadata([FIXTURES / "valid_spec.json"]) is True


def test_accept_gate_baseline_gate_spec_measured_blocks_without_spec():
    result = accept_preflight.gate_spec_measured([])
    assert result["status"] == accept_preflight.BLOCK
    assert "Figma 실측 누락" in result["detail"]


def test_accept_gate_baseline_gate_spec_measured_blocks_without_font_metadata():
    result = accept_preflight.gate_spec_measured([FIXTURES / "no_font_spec.json"])
    assert result["status"] == accept_preflight.BLOCK
    assert "fontSize" in result["detail"]
    assert "MCP 폴백/추측 의심" in result["detail"]


def test_accept_gate_baseline_gate_spec_measured_passes_with_valid_spec():
    result = accept_preflight.gate_spec_measured([FIXTURES / "valid_spec.json"])
    assert result["status"] == accept_preflight.PASS
    assert "typography ok" in result["detail"]


def test_pm_verify_baseline_valid_spec_passes_spec_precheck(tmp_path: Path):
    result = _run_pm_verify_baseline_subprocess(tmp_path, "valid_spec.json")
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "FAIL: spec.json 폰트 메타데이터" not in output
    assert "spec실측누락" not in output
    assert "결과: ✓ PASS" in output


def test_pm_verify_baseline_no_font_spec_hard_fails_without_allow_missing_spec(tmp_path: Path):
    result = _run_pm_verify_baseline_subprocess(tmp_path, "no_font_spec.json")
    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "FAIL: spec.json 폰트 메타데이터(fontSize) 없음" in output
    assert "spec실측누락" in output


def test_pm_verify_baseline_no_font_spec_warns_and_passes_with_allow_missing_spec(tmp_path: Path):
    result = _run_pm_verify_baseline_subprocess(
        tmp_path,
        "no_font_spec.json",
        allow_missing_spec=True,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "WARNING: spec에 font 메타데이터 없음" in output
    assert "결과: ✓ PASS" in output
    assert "spec실측누락" not in output


def test_parse_semantic_baseline_trusts_critical_major_and_demotes_noisy_rules():
    output = "\n".join(
        [
            "[CRITICAL] page_prefix_required — missing prefix (/tmp/index.html:1)",
            "[MAJOR] selector_scoped — selector not scoped enough (/tmp/common.css:1)",
            "[MAJOR] reset_duplicate — reset.css와 중복 (/tmp/common.css)",
            "[MINOR] p-tag-misuse — short text (/tmp/index.html:3)",
        ]
    )
    trusted, noisy = pm_verify.parse_semantic(output)

    assert "[CRITICAL] page_prefix_required" in trusted[0]
    assert any("selector_scoped" in line for line in trusted)
    assert any("reset_duplicate" in line for line in noisy)
    assert all("p-tag-misuse" not in line for line in trusted)
    assert all("p-tag-misuse" not in line for line in noisy)


def test_parse_figma_validate_baseline_keeps_trusted_and_demotes_noisy_lines():
    output = "\n".join(
        [
            "v2.cornerRadii.match | 1:1 (box) | [24] | ['8px'] @ .box",
            "v2.cornerRadii.match | 1:1 (box) | [24] | - @ 미매칭 (frame 1:1)",
            "fills color hex 일치 | 1:2 (copy) | #111111 | #111111 @ .main_visual > span",
            "v2.opacity.match | 1:1 (box) | 1 | 0.8 @ .box",
        ]
    )

    trusted, noisy = pm_verify.parse_figma_validate(output)

    assert any("v2.cornerRadii.match" in line for line in trusted)
    assert any("unmatched-frame" in line for line in noisy)
    assert any("span-inherit" in line for line in noisy)
    assert any("v2.opacity.match" in line for line in noisy)

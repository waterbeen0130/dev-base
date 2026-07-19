from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
XD_SHARE_URL = "https://xd.adobe.com/view/11db8676-2905-4680-a419-ba4ead8c1c9d-4488/"
TARGET_ARTBOARD = "엔덴틱스_v2_main"


def _resolve_repo_checkout_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    if result.returncode != 0:
        pytest.fail(
            "failed_to_resolve_git_common_dir\n"
            "cmd=git rev-parse --path-format=absolute --git-common-dir\n"
            f"cwd={ROOT}\n"
            f"returncode={result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    git_common_dir = Path(result.stdout.strip())
    if git_common_dir.name != ".git":
        pytest.fail(
            "unexpected_git_common_dir\n"
            f"resolved={git_common_dir}\n"
            "expected basename=.git"
        )

    checkout_root = git_common_dir.parent
    if not checkout_root.exists():
        pytest.fail(
            "resolved_checkout_root_missing\n"
            f"git_common_dir={git_common_dir}\n"
            f"checkout_root={checkout_root}"
        )
    return checkout_root


def _resolve_xd_capture_source() -> Path:
    capture_source = (
        _resolve_repo_checkout_root()
        / ".gran-maestro"
        / "requests"
        / "REQ-051"
        / "discussion"
        / "xd-capture-main-artboard.json"
    )
    if not capture_source.is_file():
        pytest.fail(
            "offline_xd_capture_fixture_missing\n"
            f"expected_path={capture_source}"
        )
    return capture_source


def _copy_offline_capture(tmp_path: Path) -> Path:
    capture_source = _resolve_xd_capture_source()
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    shutil.copy(capture_source, capture_dir / capture_source.name)
    return capture_dir


def _run_xd_extract(
    *,
    capture_dir: Path | None = None,
    url: str | None = None,
    section: str = "main",
    output_dir: Path,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(TOOLS / "xd-section-spec.py")]
    if capture_dir is not None:
        cmd.extend(["--capture-dir", str(capture_dir)])
    elif url is not None:
        cmd.extend(["--url", url])
    else:
        raise ValueError("capture_dir or url is required")
    cmd.extend(
        [
            "--artboard",
            TARGET_ARTBOARD,
            "--section",
            section,
            "--output",
            str(output_dir),
        ]
    )
    return subprocess.run(cmd, text=True, capture_output=True, check=False, cwd=ROOT)


def _run_xd_list_artboards(*, url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(TOOLS / "xd-section-spec.py"),
            "--url",
            url,
            "--list-artboards",
        ],
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )


def _write_text_heavy_fixture(tmp_path: Path, *, block_count: int) -> tuple[Path, Path]:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    blocks = "\n".join(
        f'<p class="copy copy_{index + 1}">Visible copy block {index + 1}</p>'
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
            <div class="main_visual_inner">
            <h2 class="main_visual_title">Integration Fixture</h2>
            {blocks}
            </div>
            </section>
            </body>
            </html>
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    css_path.write_text(
        ".main_visual{display:flex;justify-content:center;padding:40px 0}\n"
        ".main_visual .main_visual_inner{display:flex;flex-direction:column;gap:8px;width:1200px}\n"
        ".main_visual .main_visual_title{font-size:32px;line-height:1.4;color:#111111}\n"
        ".main_visual .copy{font-size:16px;line-height:1.5;color:#222222}\n",
        encoding="utf-8",
    )
    return html_path, css_path


def _write_shell_spec(spec_path: Path) -> None:
    spec_path.write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "section": {
                    "id": "shell",
                    "name": "shell",
                    "bbox": {"x": 0, "y": 0, "w": 1920, "h": 1080},
                    "_extra": None,
                },
                "text_nodes": [
                    {
                        "id": "1:1",
                        "name": "shell_text",
                        "characters": "Only one node",
                        "fontFamily": "Pretendard",
                        "fontSize": 16,
                        "fontWeight": 400,
                        "lineHeightPx": 24,
                        "lineHeightRatio": 1.5,
                        "letterSpacing": 0,
                        "color": "#111111",
                        "textAlignHorizontal": "LEFT",
                        "textAlignVertical": None,
                        "bbox": {"x": 0, "y": 0, "w": 100, "h": 24},
                        "has_mixed_styles": False,
                        "character_segments": [],
                        "characterStyleOverrides": None,
                        "styleOverrideTable": None,
                        "textCase": None,
                        "textDecoration": None,
                        "paragraphSpacing": None,
                        "paragraphIndent": None,
                        "_extra": None,
                    }
                ],
                "frame_nodes": [],
                "vector_nodes": [],
                "interactions": [],
                "images": {},
                "_meta": {"provider": "xd-web-spec"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _run_pm_verify_subprocess(
    *,
    spec_dir: Path,
    html_path: Path,
    css_path: Path,
    report_path: Path,
    figma_output: str = "",
    semantic_output: str = "",
) -> subprocess.CompletedProcess[str]:
    wrapper = textwrap.dedent(
        """
        import importlib.util
        import sys
        from pathlib import Path

        module_path = Path(sys.argv[1])
        spec = importlib.util.spec_from_file_location("pm_verify_req051_integration", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        figma_output = sys.argv[6]
        semantic_output = sys.argv[7]

        def fake_run(cmd):
            target = Path(cmd[1]).name
            if target == "figma-validate.py":
                return 1 if figma_output else 0, figma_output
            if target == "validate-semantic.py":
                return 1 if semantic_output else 0, semantic_output
            return 0, ""

        module.run = fake_run
        module.check_broken_links = lambda html_path, img_dir: []

        sys.argv = [
            "pm-verify.py",
            "--spec-dir", sys.argv[2],
            "--html", sys.argv[3],
            "--css", sys.argv[4],
            "--profile", "basic",
            "--emit-report", sys.argv[5],
        ]
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
            str(report_path),
            figma_output,
            semantic_output,
        ],
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_real_xd_spec(tmp_path: Path) -> Path:
    capture_dir = _copy_offline_capture(tmp_path)
    extract_dir = tmp_path / "extracted"
    extract_result = _run_xd_extract(capture_dir=capture_dir, output_dir=extract_dir)
    assert extract_result.returncode == 0, extract_result.stdout + extract_result.stderr
    return extract_dir


def _render_spec_text(text: str, *, preserve_linebreaks: bool) -> str:
    escaped = html.escape(text, quote=False)
    if preserve_linebreaks:
        return escaped.replace("\n", "<br>\n")
    return escaped.replace("\n", " ")


def _write_spec_mirrored_fixture(
    tmp_path: Path,
    *,
    spec_payload: dict,
    multiline_text_id: str,
    preserve_linebreaks: bool,
    extra_css: str,
) -> tuple[Path, Path]:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    blocks = []
    for index, node in enumerate(spec_payload["text_nodes"], start=1):
        node_id = node["id"]
        text = node["characters"]
        rendered_text = _render_spec_text(
            text,
            preserve_linebreaks=preserve_linebreaks if node_id == multiline_text_id else True,
        )
        blocks.append(f'<p class="copy copy_{index}" data-node-id="{html.escape(node_id)}">{rendered_text}</p>')

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
            <div class="main_visual_inner">
            {'\n'.join(blocks)}
            </div>
            </section>
            </body>
            </html>
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    css_path.write_text(
        textwrap.dedent(
            f"""
            .main_visual{{display:flex;justify-content:center;padding:40px 0}}
            .main_visual .main_visual_inner{{display:flex;flex-direction:column;gap:8px;width:1200px}}
            .main_visual .copy{{font-size:16px;line-height:1.5;color:#222222}}
            {extra_css}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return html_path, css_path


def _write_capture_payload(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _make_linebreak_violation(node: dict) -> str:
    expected = node["characters"]
    actual = expected.replace("\n", " ")
    return f"줄바꿈 보존 | {node['id']} ({node['name']}) | {expected!r} | {actual!r} @ .copy"


def test_xd_pipeline_offline_extracts_real_capture_and_emits_coverage_report(tmp_path: Path):
    capture_dir = _copy_offline_capture(tmp_path)
    extract_dir = tmp_path / "extracted"

    extract_result = _run_xd_extract(capture_dir=capture_dir, output_dir=extract_dir)
    assert extract_result.returncode == 0, extract_result.stdout + extract_result.stderr

    spec_path = extract_dir / "main_spec.json"
    assert spec_path.exists()
    spec_payload = _load_json(spec_path)
    assert spec_payload["section"]["bbox"] == {"x": -8180, "y": -22987, "w": 1920, "h": 6114}
    assert len(spec_payload["text_nodes"]) == 63

    html_path, css_path = _write_text_heavy_fixture(tmp_path, block_count=63)
    report_path = tmp_path / "pm-verify-report.json"
    verify_result = _run_pm_verify_subprocess(
        spec_dir=extract_dir,
        html_path=html_path,
        css_path=css_path,
        report_path=report_path,
    )
    output = verify_result.stdout + verify_result.stderr
    report = _load_json(report_path)

    assert "FAIL: spec.json 폰트 메타데이터(fontSize) 없음" not in output
    assert "spec_coverage" in report
    assert report["spec_coverage"]["spec_text_nodes"] == 63
    assert report["spec_coverage"]["html_text_blocks"] == 64
    assert report["spec_coverage"]["passed"] is True


def test_xd_pipeline_offline_shell_spec_is_blocked_by_coverage_gate(tmp_path: Path):
    spec_dir = tmp_path / "extracted"
    spec_dir.mkdir()
    _write_shell_spec(spec_dir / "main_spec.json")
    html_path, css_path = _write_text_heavy_fixture(tmp_path, block_count=20)
    report_path = tmp_path / "pm-verify-report.json"

    verify_result = _run_pm_verify_subprocess(
        spec_dir=spec_dir,
        html_path=html_path,
        css_path=css_path,
        report_path=report_path,
    )
    output = verify_result.stdout + verify_result.stderr
    report = _load_json(report_path)

    assert verify_result.returncode == 1
    assert "FAIL: spec 커버리지 부족" in output
    assert "spec_text_nodes=1" in output
    assert report["spec_coverage"]["spec_text_nodes"] == 1
    assert report["spec_coverage"]["passed"] is False


def test_xd_pipeline_prefers_richest_duplicate_artboard_payload(tmp_path: Path):
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    sparse_payload = {
        "artboards": {
            "artboard-main": {
                "width": 1920,
                "height": 1080,
                "name": TARGET_ARTBOARD,
                "x": 0,
                "y": 0,
            }
        },
        "children": [
            {
                "type": "artboard",
                "id": "artboard-main",
                "artboard": {"children": []},
            }
        ],
    }
    rich_payload = {
        "artboards": {
            "artboard-main": {
                "width": 1920,
                "height": 1080,
                "name": TARGET_ARTBOARD,
                "x": 0,
                "y": 0,
            }
        },
        "children": [
            {
                "type": "artboard",
                "id": "artboard-main",
                "artboard": {
                    "children": [
                        {
                            "id": "text-1",
                            "name": "Hero",
                            "type": "text",
                            "text": {"rawText": "Richer payload wins"},
                            "transform": {"tx": 0, "ty": 0},
                            "style": {
                                "font": {"family": "Pretendard", "size": 20, "style": "Bold"},
                                "textAttributes": {
                                    "lineHeight": 28,
                                    "letterSpacing": 0,
                                    "paragraphAlign": "left",
                                },
                                "fill": {"color": {"value": {"r": 17, "g": 17, "b": 17}}},
                            },
                            "meta": {
                                "ux": {
                                    "width": 100,
                                    "height": 28,
                                    "rangedStyles": [
                                        {
                                            "length": 19,
                                            "fontSize": 20,
                                            "fontStyle": "Bold",
                                            "lineHeight": 28,
                                            "charSpacing": 0,
                                        }
                                    ],
                                    "outlinesLayout": {"static": {"paragraphs": []}},
                                }
                            },
                        }
                    ]
                },
            }
        ],
    }
    _write_capture_payload(capture_dir / "001_sparse.json", sparse_payload)
    _write_capture_payload(capture_dir / "002_rich.json", rich_payload)

    extract_dir = tmp_path / "extracted"
    extract_result = _run_xd_extract(capture_dir=capture_dir, output_dir=extract_dir)

    assert extract_result.returncode == 0, extract_result.stdout + extract_result.stderr
    spec_payload = _load_json(extract_dir / "main_spec.json")
    assert len(spec_payload["text_nodes"]) == 1
    assert spec_payload["text_nodes"][0]["characters"] == "Richer payload wins"


def test_req052_pipeline_violations_reports_linebreak_and_radius_failures(tmp_path: Path):
    extract_dir = _extract_real_xd_spec(tmp_path)
    spec_payload = _load_json(extract_dir / "main_spec.json")
    multiline_node = next(node for node in spec_payload["text_nodes"] if "\n" in node["characters"])

    html_path, css_path = _write_spec_mirrored_fixture(
        tmp_path,
        spec_payload=spec_payload,
        multiline_text_id=multiline_node["id"],
        preserve_linebreaks=False,
        extra_css=".main_visual .copy_1{border-radius:999px}",
    )
    report_path = tmp_path / "pm-verify-report.json"
    verify_result = _run_pm_verify_subprocess(
        spec_dir=extract_dir,
        html_path=html_path,
        css_path=css_path,
        report_path=report_path,
        figma_output=_make_linebreak_violation(multiline_node),
    )
    output = verify_result.stdout + verify_result.stderr
    report = _load_json(report_path)

    assert verify_result.returncode == 1
    assert "줄바꿈 보존" in output
    assert "border-radius" in output
    assert "999px" in output
    assert report["border_radius_check"]["status"] == "failed"
    assert report["border_radius_check"]["passed"] is False
    assert report["border_radius_check"]["violations"] == ["999px"]
    assert report["border_radius_check"]["spec_radius_set"] == [7, 7.5, 8, 12, 20, 21, 24, 29, 32, 187]


def test_req052_pipeline_clean_avoids_new_gate_failures(tmp_path: Path):
    extract_dir = _extract_real_xd_spec(tmp_path)
    spec_payload = _load_json(extract_dir / "main_spec.json")
    multiline_node = next(node for node in spec_payload["text_nodes"] if "\n" in node["characters"])

    html_path, css_path = _write_spec_mirrored_fixture(
        tmp_path,
        spec_payload=spec_payload,
        multiline_text_id=multiline_node["id"],
        preserve_linebreaks=True,
        extra_css=".main_visual .copy_1{border-radius:24px}\n.main_visual .copy_2{border-radius:50%}\n",
    )
    report_path = tmp_path / "pm-verify-report.json"
    verify_result = _run_pm_verify_subprocess(
        spec_dir=extract_dir,
        html_path=html_path,
        css_path=css_path,
        report_path=report_path,
    )
    output = verify_result.stdout + verify_result.stderr
    report = _load_json(report_path)

    assert "줄바꿈 보존" not in output
    assert "border-radius 검사 failed" not in output
    assert report["border_radius_check"]["status"] == "passed"
    assert report["border_radius_check"]["passed"] is True
    assert report["border_radius_check"]["violations"] == []


@pytest.mark.network
def test_xd_pipeline_network_live_share_link_extracts_target_artboard(tmp_path: Path):
    list_result = _run_xd_list_artboards(url=XD_SHARE_URL)
    if list_result.returncode != 0:
        pytest.fail(
            "network_live_list_artboards_failed\n"
            f"cmd=python3 tools/xd-section-spec.py --url {XD_SHARE_URL} --list-artboards\n"
            f"returncode={list_result.returncode}\n"
            f"stdout:\n{list_result.stdout}\n"
            f"stderr:\n{list_result.stderr}"
        )
    assert TARGET_ARTBOARD in list_result.stdout

    extract_dir = tmp_path / "extracted"
    extract_result = _run_xd_extract(url=XD_SHARE_URL, output_dir=extract_dir)
    if extract_result.returncode != 0:
        pytest.fail(
            "network_live_extract_failed\n"
            f"cmd=python3 tools/xd-section-spec.py --url {XD_SHARE_URL} --artboard '{TARGET_ARTBOARD}' --section main --output {extract_dir}\n"
            f"returncode={extract_result.returncode}\n"
            f"stdout:\n{extract_result.stdout}\n"
            f"stderr:\n{extract_result.stderr}"
        )

    spec_payload = _load_json(extract_dir / "main_spec.json")
    assert spec_payload["section"]["bbox"]["w"] == 1920
    assert spec_payload["section"]["bbox"]["h"] == 6114
    assert len(spec_payload["text_nodes"]) >= 50

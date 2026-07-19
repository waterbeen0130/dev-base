from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PM_VERIFY = ROOT / "tools" / "pm-verify.py"
XD_SECTION_SPEC = ROOT / "tools" / "xd-section-spec.py"
SPEC_COVERAGE = ROOT / "tools" / "spec_coverage.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_spec_coverage_module():
    return _load_module("spec_coverage_req052", SPEC_COVERAGE)


def _write_html(path: Path, body_html: str | None = None) -> Path:
    html_path = path / "index.html"
    body = body_html or "<section class='main_visual'><div class='card'>Radius</div></section>"
    html_path.write_text(
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'></head>"
        f"<body>{body}</body></html>\n",
        encoding="utf-8",
    )
    return html_path


def _write_css(path: Path, css_text: str) -> Path:
    css_path = path / "common.css"
    css_path.write_text(css_text.strip() + "\n", encoding="utf-8")
    return css_path


def _write_spec(
    spec_dir: Path,
    *,
    frame_nodes: list[dict] | None,
    include_font: bool = True,
    include_text_node: bool = True,
) -> Path:
    spec_dir.mkdir(parents=True, exist_ok=True)
    text_nodes = []
    if include_text_node:
        node = {
            "id": "1:100",
            "name": "copy",
            "characters": "Radius",
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
    spec_path = spec_dir / "section_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "section": {"id": "1:1", "name": "main", "bbox": {"x": 0, "y": 0, "w": 100, "h": 100}},
                "text_nodes": text_nodes,
                "frame_nodes": frame_nodes,
                "interactions": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return spec_path


def _run_pm_verify(
    tmp_path: Path,
    *,
    frame_nodes: list[dict] | None,
    css_text: str,
    emit_report: bool = True,
    body_html: str | None = None,
) -> subprocess.CompletedProcess[str]:
    spec_dir = tmp_path / "spec"
    _write_spec(spec_dir, frame_nodes=frame_nodes)
    html_path = _write_html(tmp_path, body_html=body_html)
    css_path = _write_css(tmp_path, css_text)
    wrapper = """
import importlib.util
import sys
from pathlib import Path

module_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("pm_verify_req052_subprocess", module_path)
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
    argv = [
        sys.executable,
        "-c",
        wrapper,
        str(PM_VERIFY),
        str(spec_dir),
        str(html_path),
        str(css_path),
    ]
    if emit_report:
        argv.extend(["--emit-report", str(tmp_path / "pm-verify-report.json")])
    return subprocess.run(argv, capture_output=True, text=True, check=False)


def _frame(radius: object, *, rect_radii: list[object] | None = None) -> dict:
    return {
        "id": "1:2",
        "name": "card",
        "bbox": {"x": 0, "y": 0, "w": 100, "h": 60},
        "cornerRadius": radius,
        "rectangleCornerRadii": rect_radii if rect_radii is not None else [radius, radius, radius, radius],
    }


def test_radius_unauthorized_pm_verify_fails_when_spec_has_no_radius(tmp_path: Path) -> None:
    result = _run_pm_verify(
        tmp_path,
        frame_nodes=[_frame(0)],
        css_text=".card{display:flex;flex-direction:row;border-radius:8px;color:#111111}",
    )
    output = result.stdout + result.stderr
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 1
    assert "border-radius" in output
    assert "spec_radius_set=[]" in output
    assert "css_radius_values=['8px']" in output
    assert report["border_radius_check"]["passed"] is False
    assert report["border_radius_check"]["spec_radius_set"] == []
    assert report["border_radius_check"]["css_radius_values"] == ["8px"]


def test_radius_unauthorized_pm_verify_passes_when_css_matches_spec_set(tmp_path: Path) -> None:
    result = _run_pm_verify(
        tmp_path,
        frame_nodes=[_frame(8)],
        css_text=".card{display:flex;flex-direction:row;border-radius:8px;color:#111111}",
    )
    output = result.stdout + result.stderr
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert "결과: ✓ PASS" in output
    assert report["border_radius_check"]["passed"] is True
    assert report["border_radius_check"]["spec_radius_set"] == [8]


def test_radius_set_match_allows_tolerance_and_conventions_but_blocks_outlier(tmp_path: Path) -> None:
    result = _run_pm_verify(
        tmp_path,
        frame_nodes=[_frame(10)],
        css_text="\n".join(
            [
                ".card{display:flex;flex-direction:row;border-radius:10px;color:#111111}",
                ".avatar{border-radius:50%}",
                ".pill{border-radius:2em}",
                ".soft{border-radius:11px}",
                ".bad{border-radius:23px}",
            ]
        ),
        body_html=(
            "<section class='main_visual'>"
            "<div class='card'>Radius</div>"
            "<div class='avatar'>Avatar</div>"
            "<div class='pill'>Pill</div>"
            "<div class='soft'>Soft</div>"
            "<div class='bad'>Bad</div>"
            "</section>"
        ),
    )
    output = result.stdout + result.stderr
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 1
    assert "23px" in output
    assert "11px" not in report["border_radius_check"]["violations"]
    assert report["border_radius_check"]["passed"] is False
    assert report["border_radius_check"]["spec_radius_set"] == [10]
    assert "10px" in report["border_radius_check"]["css_radius_values"]
    assert "50%" in report["border_radius_check"]["css_radius_values"]
    assert "2em" in report["border_radius_check"]["css_radius_values"]
    assert report["border_radius_check"]["violations"] == ["23px"]


def test_radius_false_positive_accepts_exact_asymmetric_values(tmp_path: Path) -> None:
    module = _load_spec_coverage_module()
    spec_file = _write_spec(tmp_path / "spec", frame_nodes=[_frame(8, rect_radii=[8, 8, 0, 0])])

    measurement = module.measure_border_radius_check([spec_file], ".card{border-radius:8px 8px 0 0}")

    assert measurement["status"] == "passed"
    assert measurement["violations"] == []
    assert measurement["spec_radius_set"] == [8]
    assert measurement["spec_corner_sets"] == [[8, 8, 0, 0]]


def test_radius_false_positive_accepts_zero_reset_with_spec_and_without_spec(tmp_path: Path) -> None:
    module = _load_spec_coverage_module()
    with_spec = _write_spec(tmp_path / "with_spec", frame_nodes=[_frame(32, rect_radii=[32, 0, 0, 32])])
    without_radius = _write_spec(tmp_path / "without_radius", frame_nodes=[_frame(0)])

    measured_with_spec = module.measure_border_radius_check([with_spec], ".card{border-radius:32px 0 0 32px}")
    measured_without_radius = module.measure_border_radius_check([without_radius], ".card{border-radius:0}")

    assert measured_with_spec["status"] == "passed"
    assert measured_with_spec["violations"] == []
    assert measured_without_radius["status"] == "passed"
    assert measured_without_radius["css_radius_values"] == []
    assert measured_without_radius["violations"] == []


def test_radius_scope_excludes_unused_selector_and_reports_unscanned(tmp_path: Path) -> None:
    result = _run_pm_verify(
        tmp_path,
        frame_nodes=[_frame(8)],
        css_text="\n".join(
            [
                ".card{display:flex;flex-direction:row;border-radius:8px;color:#111111}",
                ".unused-chip{border-radius:24px}",
            ]
        ),
    )
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert report["border_radius_check"]["status"] == "passed"
    assert report["border_radius_check"]["css_radius_values"] == ["8px"]
    assert report["border_radius_check"]["unscanned"] == [".unused-chip"]


def test_radius_scope_preserves_corner_meaning_and_blocks_shorthand_false_negative(tmp_path: Path) -> None:
    module = _load_spec_coverage_module()
    spec_file = _write_spec(tmp_path / "spec", frame_nodes=[_frame(32, rect_radii=[32, 0, 0, 32])])

    measurement = module.measure_border_radius_check([spec_file], ".card{border-radius:32px}")

    assert measurement["status"] == "failed"
    assert measurement["violations"] == ["32px"]


def test_radius_legacy_skip_warns_for_placeholder_none_frames(tmp_path: Path) -> None:
    result = _run_pm_verify(
        tmp_path,
        frame_nodes=[
            {
                "id": "1:2",
                "name": "card",
                "bbox": {"x": 0, "y": 0, "w": 100, "h": 60},
                "cornerRadius": None,
                "rectangleCornerRadii": [0, 0, 0, 0],
            }
        ],
        css_text=".card{display:flex;flex-direction:row;border-radius:12px;color:#111111}",
    )
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert report["border_radius_check"]["status"] == "skipped"
    assert "legacy" in report["border_radius_check"]["reason"]


def test_radius_legacy_skip_warns_when_frame_nodes_or_radius_fields_missing(tmp_path: Path) -> None:
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    (spec_dir / "section_spec.json").write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "section": {"id": "1:1", "name": "main", "bbox": {"x": 0, "y": 0, "w": 100, "h": 100}},
                "text_nodes": [
                    {
                        "id": "1:100",
                        "name": "copy",
                        "characters": "Radius",
                        "fontFamily": "Pretendard",
                        "fontSize": 16,
                        "fontWeight": 400,
                        "lineHeightPx": 24,
                        "lineHeightRatio": 1.5,
                        "letterSpacing": 0,
                        "color": "#111111",
                    }
                ],
                "interactions": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    html_path = _write_html(tmp_path)
    css_path = _write_css(tmp_path, ".card{display:flex;flex-direction:row;border-radius:8px;color:#111111}")
    wrapper = """
import importlib.util
import sys
from pathlib import Path

module_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("pm_verify_req052_legacy_subprocess", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.run = lambda cmd: (0, "")
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
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            wrapper,
            str(PM_VERIFY),
            str(spec_dir),
            str(html_path),
            str(css_path),
            str(tmp_path / "pm-verify-report.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert "skip" in output.lower()
    assert report["border_radius_check"]["status"] == "skipped"
    assert "legacy" in report["border_radius_check"]["reason"]


def test_radius_legacy_skip_warns_when_frame_has_no_radius_fields(tmp_path: Path) -> None:
    result = _run_pm_verify(
        tmp_path,
        frame_nodes=[
            {
                "id": "1:2",
                "name": "card",
                "bbox": {"x": 0, "y": 0, "w": 100, "h": 60},
            }
        ],
        css_text=".card{display:flex;flex-direction:row;border-radius:8px;color:#111111}",
    )
    report = json.loads((tmp_path / "pm-verify-report.json").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert report["border_radius_check"]["status"] == "skipped"
    assert "legacy" in report["border_radius_check"]["reason"]


def test_xd_radius_extract_populates_corner_radius_from_shape_r(tmp_path: Path) -> None:
    module = _load_module("xd_section_spec_req052", XD_SECTION_SPEC)
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    payload = {
        "version": "1.0.0",
        "artboards": {
            "href": "/resources/graphics/graphicContent.agc",
            "artboard-main": {"width": 300, "height": 200, "name": "Radius", "x": 0, "y": 0},
        },
        "children": [
            {
                "type": "artboard",
                "id": "artboard-main",
                "meta": {"ux": {"width": 300, "height": 200}},
                "artboard": {
                    "children": [
                        {
                            "type": "group",
                            "id": "group-1",
                            "name": "Group",
                            "transform": {"a": 1, "b": 0, "c": 0, "d": 1, "tx": 0, "ty": 0},
                            "meta": {"ux": {"width": 300, "height": 200}},
                            "children": [
                                {
                                    "type": "shape",
                                    "id": "shape-1",
                                    "name": "Card",
                                    "transform": {"a": 1, "b": 0, "c": 0, "d": 1, "tx": 10, "ty": 20},
                                    "meta": {"ux": {"width": 120, "height": 80}},
                                    "shape": {"r": [12, 12, 12, 12], "x": 0, "y": 0, "width": 120, "height": 80},
                                },
                                {
                                    "type": "shape",
                                    "id": "shape-2",
                                    "name": "Badge",
                                    "transform": {"a": 1, "b": 0, "c": 0, "d": 1, "tx": 140, "ty": 20},
                                    "meta": {"ux": {"width": 120, "height": 80}},
                                    "shape": {"r": [32, 0, 0, 32], "x": 0, "y": 0, "width": 120, "height": 80},
                                },
                                {
                                    "type": "text",
                                    "id": "text-1",
                                    "name": "Copy",
                                    "transform": {"a": 1, "b": 0, "c": 0, "d": 1, "tx": 20, "ty": 120},
                                    "style": {
                                        "font": {"family": "Pretendard", "style": "Regular", "size": 16},
                                        "fill": {"type": "solid", "color": {"mode": "RGB", "value": {"r": 17, "g": 17, "b": 17}}},
                                        "textAttributes": {"lineHeight": 24, "letterSpacing": 0, "paragraphAlign": "left"},
                                    },
                                    "text": {"frame": {"type": "positioned"}, "rawText": "Radius"},
                                    "meta": {"ux": {"singleTextObject": True, "rangedStyles": [{"length": 6, "fontFamily": "Pretendard", "fontStyle": "Regular", "postscriptName": "Pretendard-Regular", "fontSize": 16, "charSpacing": 0, "fill": {"value": 4279308561}}]}},
                                },
                            ],
                        }
                    ]
                },
            }
        ],
    }
    (capture_dir / "capture.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    artboard = module.select_artboard(module.load_capture_payloads(capture_dir), "Radius")
    spec_payload = module.build_spec_payload(artboard, "main")
    frames = {frame["id"]: frame for frame in spec_payload["frame_nodes"]}

    assert frames["shape-1"]["cornerRadius"] == 12
    assert frames["shape-1"]["rectangleCornerRadii"] == [12, 12, 12, 12]
    assert frames["shape-2"]["cornerRadius"] is None
    assert frames["shape-2"]["rectangleCornerRadii"] == [32, 0, 0, 32]


def test_xd_radius_guard_skips_ellipse_and_invalid_rect_values() -> None:
    module = _load_module("xd_section_spec_req052_invalid", XD_SECTION_SPEC)

    ellipse = module.normalize_frame_node(
        {
            "type": "ellipse",
            "id": "ellipse-1",
            "name": "Circle",
            "transform": {"tx": 0, "ty": 0},
            "meta": {"ux": {"width": 40, "height": 40}},
            "shape": {"r": [20, 20, 20, 20]},
        }
    )
    invalid_rect = module.normalize_frame_node(
        {
            "type": "shape",
            "id": "shape-bad",
            "name": "Bad",
            "transform": {"tx": 0, "ty": 0},
            "meta": {"ux": {"width": 40, "height": 40}},
            "shape": {"r": [-5, 999, 0, 0]},
        }
    )

    assert ellipse["cornerRadius"] is None
    assert ellipse["rectangleCornerRadii"] == [0, 0, 0, 0]
    assert invalid_rect["cornerRadius"] is None
    assert invalid_rect["rectangleCornerRadii"] == [0, 0, 0, 0]

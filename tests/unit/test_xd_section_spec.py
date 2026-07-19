from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
XD_SECTION_SPEC = ROOT / "tools" / "xd-section-spec.py"
FIXTURE_CAPTURE = ROOT / "tests" / "fixtures" / "xd_capture_minimal.json"
NESTED_FIXTURE_CAPTURE = ROOT / "tests" / "fixtures" / "xd_capture_nested_subset.json"


def _load_module():
    module_name = "xd_section_spec_test_module"
    spec = importlib.util.spec_from_file_location(module_name, XD_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_capture_dir(tmp_path: Path, payload: dict | None = None) -> Path:
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    if payload is None:
        shutil.copy(FIXTURE_CAPTURE, capture_dir / "capture.json")
    else:
        (capture_dir / "capture.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return capture_dir


def _write_invalid_capture_file(path: Path) -> None:
    path.write_bytes(bytes([0xFF, 0xFE, 0x00, 0x81]))


def _write_capture_dir_from_fixture(tmp_path: Path, fixture_path: Path) -> Path:
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    shutil.copy(fixture_path, capture_dir / "capture.json")
    return capture_dir


def _run_cli(tmp_path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(XD_SECTION_SPEC), *extra_args],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(ROOT),
    )


def test_xd_section_spec_cli_extracts_spec_json(tmp_path: Path) -> None:
    capture_dir = _write_capture_dir(tmp_path)
    output_dir = tmp_path / "extracted"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "엔덴틱스_v2_main",
        "--section",
        "main",
        "--output",
        str(output_dir),
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    spec_path = output_dir / "main_spec.json"
    assert spec_path.is_file()
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    assert set(["schema_version", "section", "text_nodes", "frame_nodes", "interactions"]).issubset(payload)
    assert payload["schema_version"] == "2.0.0"
    assert payload["section"]["name"] == "엔덴틱스_v2_main"
    assert payload["section"]["bbox"]["w"] == 1920
    assert payload["section"]["bbox"]["h"] == 6114
    assert payload["text_nodes"]
    required_fields = {
        "characters",
        "fontFamily",
        "fontSize",
        "fontWeight",
        "lineHeightPx",
        "lineHeightRatio",
        "letterSpacing",
        "color",
        "textAlignHorizontal",
        "has_mixed_styles",
    }
    for text_node in payload["text_nodes"]:
        assert required_fields.issubset(text_node)


def test_xd_section_spec_cli_extracts_nested_real_structure_subset(tmp_path: Path) -> None:
    capture_dir = _write_capture_dir_from_fixture(tmp_path, NESTED_FIXTURE_CAPTURE)
    output_dir = tmp_path / "extracted"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "엔덴틱스_v2_main",
        "--section",
        "main",
        "--output",
        str(output_dir),
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    spec_path = output_dir / "main_spec.json"
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    assert len(payload["text_nodes"]) >= 3
    assert payload["text_nodes"][0]["characters"] == "Request a Demo"
    assert payload["text_nodes"][0]["fontSize"] == 48
    assert payload["text_nodes"][0]["color"] == "#ffffff"


def test_argb_conversion_normalizes_hex_and_alpha() -> None:
    module = _load_module()

    assert module.argb_int_to_css_color(4294967295) == "#ffffff"
    assert module.argb_int_to_css_color(0xFF111111) == "#111111"
    assert module.argb_int_to_css_color(0x80111111) == "rgba(17, 17, 17, 0.502)"


def test_mixed_styles_generate_character_segments() -> None:
    module = _load_module()
    capture = json.loads(FIXTURE_CAPTURE.read_text(encoding="utf-8"))
    artboard = capture["children"][0]
    mixed_text = artboard["artboard"]["children"][0]["children"][1]

    normalized = module.normalize_text_node(mixed_text)

    assert normalized["has_mixed_styles"] is True
    assert len(normalized["character_segments"]) == 2
    assert normalized["character_segments"][0]["start"] == 0
    assert normalized["character_segments"][0]["end"] == 4
    assert normalized["character_segments"][1]["fontSize"] == 20
    assert normalized["character_segments"][1]["color"] == "#4b5fb1"


def test_line_spacing_only_text_node_uses_same_line_height_rule_as_segments() -> None:
    module = _load_module()
    capture = json.loads(FIXTURE_CAPTURE.read_text(encoding="utf-8"))
    text_node = capture["children"][0]["artboard"]["children"][0]["children"][0]
    text_node["style"]["textAttributes"] = {
        "lineSpacing": 24,
        "letterSpacing": 0,
        "paragraphAlign": "left",
    }
    text_node["meta"]["ux"]["rangedStyles"] = [
        {
            "length": len(text_node["text"]["rawText"]),
            "fontSize": text_node["style"]["font"]["size"],
            "fontStyle": text_node["style"]["font"]["style"],
            "lineSpacing": 24,
            "charSpacing": 0,
            "fill": {"value": 4294967295},
        }
    ]

    normalized = module.normalize_text_node(text_node)

    assert normalized["lineHeightPx"] == 24
    assert normalized["lineHeightRatio"] == module.compute_line_height_ratio(
        normalized["lineHeightPx"],
        normalized["fontSize"],
    )
    assert normalized["character_segments"][0]["lineHeightPx"] == 24


def test_empty_ranged_styles_falls_back_to_global_style_segment() -> None:
    module = _load_module()
    capture = json.loads(FIXTURE_CAPTURE.read_text(encoding="utf-8"))
    text_node = capture["children"][0]["artboard"]["children"][0]["children"][0]
    text_node["meta"]["ux"]["rangedStyles"] = []

    normalized = module.normalize_text_node(text_node)

    assert normalized["has_mixed_styles"] is False
    assert len(normalized["character_segments"]) == 1
    assert normalized["character_segments"][0]["start"] == 0
    assert normalized["character_segments"][0]["end"] == len(text_node["text"]["rawText"])
    assert normalized["character_segments"][0]["fontFamily"] == normalized["fontFamily"]
    assert normalized["character_segments"][0]["fontSize"] == normalized["fontSize"]
    assert normalized["character_segments"][0]["lineHeightPx"] == normalized["lineHeightPx"]


def test_xd_field_compat_text_node_defaults_match_figma_contract() -> None:
    module = _load_module()
    capture = json.loads(FIXTURE_CAPTURE.read_text(encoding="utf-8"))
    text_node = capture["children"][0]["artboard"]["children"][0]["children"][0]

    normalized = module.normalize_text_node(text_node)

    assert normalized["opacity"] == 1.0
    assert normalized["blendMode"] == "PASS_THROUGH"
    assert normalized["effects"] == []
    assert normalized["textCase"] == "ORIGINAL"
    assert normalized["textDecoration"] == "NONE"
    assert normalized["paragraphSpacing"] == 0.0
    assert normalized["paragraphIndent"] == 0.0
    assert "_extra" not in normalized


def test_xd_fail_loud_for_password_gate_detection() -> None:
    module = _load_module()
    with_text = "Password protected link. Enter password to continue."

    assert module.detect_password_gate("Adobe XD", with_text) is True
    assert module.detect_password_gate("Shared Design", "Normal viewer text") is False


def test_xd_fail_loud_when_capture_has_no_design_payload(tmp_path: Path) -> None:
    capture_dir = _write_capture_dir(tmp_path, {"hello": "world"})
    output_dir = tmp_path / "extracted"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "엔덴틱스_v2_main",
        "--section",
        "main",
        "--output",
        str(output_dir),
    )

    assert proc.returncode != 0
    assert "No Adobe XD artboard payload" in (proc.stdout + proc.stderr)
    assert not output_dir.exists()


def test_xd_capture_dir_skips_invalid_binary_payload_when_valid_json_exists(tmp_path: Path) -> None:
    capture_dir = _write_capture_dir(tmp_path)
    _write_invalid_capture_file(capture_dir / "broken.json")
    output_dir = tmp_path / "extracted"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "엔덴틱스_v2_main",
        "--section",
        "main",
        "--output",
        str(output_dir),
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (output_dir / "main_spec.json").is_file()
    assert "Skipping non-UTF-8 Adobe XD capture payload" in proc.stderr


def test_xd_capture_dir_fails_loud_when_only_invalid_binary_payloads_exist(tmp_path: Path) -> None:
    capture_dir = tmp_path / "capture"
    capture_dir.mkdir()
    _write_invalid_capture_file(capture_dir / "broken.json")
    output_dir = tmp_path / "extracted"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "엔덴틱스_v2_main",
        "--section",
        "main",
        "--output",
        str(output_dir),
    )

    assert proc.returncode != 0
    assert "Skipping non-UTF-8 Adobe XD capture payload" in proc.stderr
    assert "No Adobe XD artboard payload found in capture directory" in (proc.stdout + proc.stderr)
    assert not output_dir.exists()


def test_xd_fail_loud_when_artboard_missing(tmp_path: Path) -> None:
    capture_dir = _write_capture_dir(tmp_path)
    output_dir = tmp_path / "extracted"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "missing-artboard",
        "--section",
        "main",
        "--output",
        str(output_dir),
    )

    assert proc.returncode != 0
    assert "Artboard not found" in (proc.stdout + proc.stderr)
    assert not output_dir.exists()


def test_xd_fail_loud_when_capture_schema_is_invalid(tmp_path: Path) -> None:
    invalid_payload = {
        "artboards": {"artboard-main": {"width": 10, "height": 10, "name": "엔덴틱스_v2_main", "x": 0, "y": 0}},
        "children": [{"type": "artboard", "id": "artboard-main", "artboard": {}}],
    }
    capture_dir = _write_capture_dir(tmp_path, invalid_payload)
    output_dir = tmp_path / "extracted"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "엔덴틱스_v2_main",
        "--section",
        "main",
        "--output",
        str(output_dir),
    )

    assert proc.returncode != 0
    assert "Invalid Adobe XD capture schema" in (proc.stdout + proc.stderr)
    assert not output_dir.exists()


def test_xd_fail_loud_when_text_extraction_returns_zero_nodes(tmp_path: Path) -> None:
    capture = json.loads(FIXTURE_CAPTURE.read_text(encoding="utf-8"))
    capture["children"][0]["artboard"]["children"] = []
    capture_dir = _write_capture_dir(tmp_path, capture)
    output_dir = tmp_path / "extracted"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "엔덴틱스_v2_main",
        "--section",
        "main",
        "--output",
        str(output_dir),
    )

    assert proc.returncode != 0
    assert "0 text nodes" in (proc.stdout + proc.stderr)
    assert not (output_dir / "main_spec.json").exists()


def test_xd_ledger_append_records_extract_step(tmp_path: Path) -> None:
    capture_dir = _write_capture_dir(tmp_path)
    output_dir = tmp_path / "extracted"
    ledger_path = tmp_path / "workflow-ledger.json"

    proc = _run_cli(
        tmp_path,
        "--capture-dir",
        str(capture_dir),
        "--artboard",
        "엔덴틱스_v2_main",
        "--section",
        "main",
        "--output",
        str(output_dir),
        "--ledger",
        str(ledger_path),
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["section"] == "main"
    assert ledger["steps"][0]["step"] == "extract"
    assert ledger["steps"][0]["provider"] == "xd-web-spec"


def test_select_artboard_prefers_richest_matching_payload() -> None:
    module = _load_module()
    sparse_payload = {
        "artboards": {
            "artboard-main": {"width": 1920, "height": 1080, "name": "main", "x": 0, "y": 0}
        },
        "children": [
            {
                "type": "artboard",
                "id": "artboard-main",
                "artboard": {"children": [{"id": "group-1", "type": "group", "children": []}]},
            }
        ],
    }
    rich_payload = {
        "artboards": {
            "artboard-main": {"width": 1920, "height": 1080, "name": "main", "x": 0, "y": 0}
        },
        "children": [
            {
                "type": "artboard",
                "id": "artboard-main",
                "artboard": {
                    "children": [
                        {"id": "text-1", "type": "text"},
                        {"id": "text-2", "type": "text"},
                        {"id": "group-2", "type": "group", "children": [{"id": "text-3", "type": "text"}]},
                    ]
                },
            }
        ],
    }

    selected = module.select_artboard([sparse_payload, rich_payload], "main")

    assert selected["meta"]["name"] == "main"
    assert len(selected["node"]["artboard"]["children"]) == 3

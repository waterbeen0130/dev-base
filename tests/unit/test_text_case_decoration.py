from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def _load_module():
    module_name = "figma_section_spec_req031_text_case_decoration"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _run_validator(tmp_path: Path, spec_payload: dict, css_text: str) -> subprocess.CompletedProcess[str]:
    spec_path = tmp_path / "spec.json"
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    spec_path.write_text(json.dumps(spec_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text("<html><body><p class='title'>abc</p></body></html>\n", encoding="utf-8")
    css_path.write_text(css_text.strip() + "\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--spec", str(spec_path), "--html", str(html_path), "--css", str(css_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_text_case_decoration_and_paragraph_values_are_extracted() -> None:
    module = _load_module()
    node = {
        "id": "1:50",
        "name": "Title",
        "type": "TEXT",
        "characters": "abc",
        "fills": [{"type": "SOLID", "color": {"r": 0.0, "g": 0.0, "b": 0.0}}],
        "style": {
            "fontFamily": "Inter",
            "fontSize": 16,
            "fontWeight": 600,
            "lineHeightPx": 24,
            "letterSpacing": 0,
            "textCase": "UPPER",
            "textDecoration": "UNDERLINE",
            "paragraphSpacing": 12,
            "paragraphIndent": 4,
        },
    }

    normalized = module.normalize_text_node(node)

    assert normalized["textCase"] == "UPPER"
    assert normalized["textDecoration"] == "UNDERLINE"
    assert normalized["paragraphSpacing"] == 12
    assert normalized["paragraphIndent"] == 4


def test_text_case_decoration_defaults_are_explicit() -> None:
    module = _load_module()
    node = {
        "id": "1:51",
        "name": "Body",
        "type": "TEXT",
        "characters": "abc",
        "fills": [{"type": "SOLID", "color": {"r": 0.0, "g": 0.0, "b": 0.0}}],
        "style": {
            "fontFamily": "Inter",
            "fontSize": 16,
            "fontWeight": 400,
            "lineHeightPx": 24,
            "letterSpacing": 0,
        },
    }

    normalized = module.normalize_text_node(node)

    assert normalized["textCase"] == "ORIGINAL"
    assert normalized["textDecoration"] == "NONE"
    assert normalized["paragraphSpacing"] == 0
    assert normalized["paragraphIndent"] == 0


def test_v2_text_case_and_decoration_categories_report_mismatch(tmp_path: Path) -> None:
    spec_payload = {
        "schema_version": "2.0.0",
        "section": {"id": "1:1", "name": "S", "bbox": {"x": 0, "y": 0, "w": 100, "h": 100}},
        "text_nodes": [
            {
                "id": "1:2",
                "name": "title",
                "characters": "abc",
                "fontFamily": "Inter",
                "fontSize": 16,
                "fontWeight": 400,
                "lineHeightPx": 24,
                "lineHeightRatio": 1.5,
                "letterSpacing": 0,
                "color": "#000000",
                "opacity": 1.0,
                "blendMode": "PASS_THROUGH",
                "effects": [],
                "textAlignHorizontal": None,
                "textAlignVertical": None,
                "bbox": {"x": 0, "y": 0, "w": 100, "h": 20},
                "character_segments": [],
                "textCase": "UPPER",
                "textDecoration": "UNDERLINE",
                "paragraphSpacing": 0,
                "paragraphIndent": 0,
            }
        ],
        "frame_nodes": [],
        "vector_nodes": [],
        "interactions": [],
        "images": {},
    }

    proc = _run_validator(
        tmp_path,
        spec_payload,
        """
        .title {
          font-family: Inter;
          font-size: 16px;
          font-weight: 400;
          line-height: 1.5;
          color: #000000;
          text-transform: lowercase;
          text-decoration: none;
        }
        """,
    )

    output = proc.stdout + proc.stderr
    assert proc.returncode == 1
    assert "v2.textCase.match" in output
    assert "v2.textDecoration.match" in output

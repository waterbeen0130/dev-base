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
    module_name = "figma_section_spec_req031_strokes"
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
    html_path.write_text("<html><body><div class='card'></div></body></html>\n", encoding="utf-8")
    css_path.write_text(css_text.strip() + "\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--spec", str(spec_path), "--html", str(html_path), "--css", str(css_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_strokes_are_extracted_with_weight_and_align() -> None:
    module = _load_module()
    image_refs: set[str] = set()
    node = {
        "id": "1:10",
        "name": "Stroke Frame",
        "type": "FRAME",
        "strokes": [
            {
                "type": "SOLID",
                "color": {"r": 17 / 255, "g": 34 / 255, "b": 51 / 255},
                "opacity": 0.8,
            }
        ],
        "strokeWeight": 2.5,
        "strokeAlign": "OUTSIDE",
    }

    normalized = module.normalize_frame_node(node, image_refs)

    assert normalized["strokes"] == [
        {
            "type": "SOLID",
            "color": "#112233",
            "opacity": 0.8,
        }
    ]
    assert normalized["strokeWeight"] == 2.5
    assert normalized["strokeAlign"] == "OUTSIDE"


def test_v2_strokes_category_reports_border_mismatch(tmp_path: Path) -> None:
    spec_payload = {
        "schema_version": "2.0.0",
        "section": {"id": "1:1", "name": "S", "bbox": {"x": 0, "y": 0, "w": 100, "h": 100}},
        "text_nodes": [],
        "frame_nodes": [
            {
                "id": "1:2",
                "name": "card",
                "bbox": {"x": 0, "y": 0, "w": 100, "h": 100},
                "layoutMode": "HORIZONTAL",
                "paddingTop": None,
                "paddingRight": None,
                "paddingBottom": None,
                "paddingLeft": None,
                "itemSpacing": None,
                "primaryAxisAlignItems": None,
                "counterAxisAlignItems": None,
                "fills": None,
                "fills_v2": [],
                "effects": [],
                "opacity": 1.0,
                "blendMode": "PASS_THROUGH",
                "strokes": [{"type": "SOLID", "color": "#112233", "opacity": 1.0}],
                "strokeWeight": 3,
                "strokeAlign": "CENTER",
            }
        ],
        "vector_nodes": [],
        "interactions": [],
        "images": {},
    }

    proc = _run_validator(
        tmp_path,
        spec_payload,
        """
        .card { display: flex; flex-direction: row; border: 1px solid #aabbcc; }
        """,
    )

    output = proc.stdout + proc.stderr
    assert proc.returncode == 1
    assert "v2.strokes.match" in output

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
    module_name = "figma_section_spec_req031_corner_radii"
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


def test_single_corner_radius_is_expanded_to_four_corners() -> None:
    module = _load_module()
    image_refs: set[str] = set()
    node = {
        "id": "1:20",
        "name": "Single Radius",
        "type": "FRAME",
        "cornerRadius": 8,
    }

    normalized = module.normalize_frame_node(node, image_refs)

    assert normalized["rectangleCornerRadii"] == [8, 8, 8, 8]


def test_individual_corner_radii_order_is_preserved() -> None:
    module = _load_module()
    image_refs: set[str] = set()
    node = {
        "id": "1:21",
        "name": "Individual Radius",
        "type": "FRAME",
        "rectangleCornerRadii": [4, 8, 12, 16],
    }

    normalized = module.normalize_frame_node(node, image_refs)

    assert normalized["rectangleCornerRadii"] == [4, 8, 12, 16]


def test_v2_corner_radii_category_reports_mismatch(tmp_path: Path) -> None:
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
                "cornerRadius": None,
                "rectangleCornerRadii": [4, 8, 12, 16],
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
        .card { display: flex; flex-direction: row; border-radius: 0; }
        """,
    )

    output = proc.stdout + proc.stderr
    assert proc.returncode == 1
    assert "v2.cornerRadii.match" in output

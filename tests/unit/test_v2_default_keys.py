from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req030_defaults"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_v2_default_keys_are_explicit_for_frame_and_text_nodes() -> None:
    module = _load_module()
    payload = {
        "schema_version": "2.0.0",
        "section": {"id": "1:1", "name": "S", "bbox": {"x": 0, "y": 0, "w": 1, "h": 1}},
        "text_nodes": [
            {
                "id": "1:2",
                "name": "T",
                "characters": "x",
                "fontFamily": None,
                "fontSize": None,
                "fontWeight": None,
                "lineHeightPx": None,
                "lineHeightRatio": None,
                "letterSpacing": None,
                "color": None,
                "textAlignHorizontal": None,
                "textAlignVertical": None,
                "bbox": {"x": 0, "y": 0, "w": 1, "h": 1},
                "character_segments": [],
            }
        ],
        "frame_nodes": [
            {
                "id": "1:3",
                "name": "F",
                "bbox": {"x": 0, "y": 0, "w": 1, "h": 1},
                "layoutMode": None,
                "paddingTop": None,
                "paddingRight": None,
                "paddingBottom": None,
                "paddingLeft": None,
                "itemSpacing": None,
                "primaryAxisAlignItems": None,
                "counterAxisAlignItems": None,
                "fills": None,
                "cornerRadius": None,
                "rectangleCornerRadii": None,
                "border_radius_hint": None,
            }
        ],
        "vector_nodes": [],
        "interactions": [],
        "images": {},
    }

    normalized = module.ensure_v2_payload_shape(payload)
    text_node = normalized["text_nodes"][0]
    frame_node = normalized["frame_nodes"][0]

    assert text_node["effects"] == []
    assert text_node["opacity"] == 1.0
    assert text_node["blendMode"] == "PASS_THROUGH"

    assert frame_node["fills_v2"] == []
    assert frame_node["effects"] == []
    assert frame_node["opacity"] == 1.0
    assert frame_node["blendMode"] == "PASS_THROUGH"

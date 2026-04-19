from __future__ import annotations

import importlib.util
import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req031_paragraph_defaults"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_paragraph_spacing_indent_defaults_are_zero_in_normalize_text_node() -> None:
    module = _load_module()
    node = {
        "id": "1:60",
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

    assert normalized["paragraphSpacing"] == 0
    assert normalized["paragraphIndent"] == 0


def test_paragraph_spacing_indent_defaults_are_zero_in_ensure_v2_payload_shape() -> None:
    module = _load_module()
    payload = {
        "schema_version": "2.0.0",
        "section": {"id": "1:1", "name": "S", "bbox": {"x": 0, "y": 0, "w": 1, "h": 1}},
        "text_nodes": [
            {
                "id": "1:2",
                "name": "T",
                "characters": "x",
                "fontFamily": "Inter",
                "fontSize": 16,
                "fontWeight": 400,
                "lineHeightPx": 24,
                "lineHeightRatio": 1.5,
                "letterSpacing": 0,
                "color": "#000000",
                "textAlignHorizontal": None,
                "textAlignVertical": None,
                "bbox": {"x": 0, "y": 0, "w": 1, "h": 1},
                "character_segments": [],
            }
        ],
        "frame_nodes": [],
        "vector_nodes": [],
        "interactions": [],
        "images": {},
    }

    normalized = module.ensure_v2_payload_shape(copy.deepcopy(payload))
    text_node = normalized["text_nodes"][0]

    assert text_node["paragraphSpacing"] == 0
    assert text_node["paragraphIndent"] == 0

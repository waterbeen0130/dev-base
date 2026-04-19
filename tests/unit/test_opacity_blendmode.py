from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req030_opacity_blend"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_opacity_and_blendmode_are_explicit_on_frame_and_text() -> None:
    module = _load_module()
    frame_node = {
        "id": "1:5",
        "name": "Frame",
        "type": "FRAME",
        "opacity": 0.8,
        "blendMode": "MULTIPLY",
    }
    text_node = {
        "id": "1:6",
        "name": "Text",
        "type": "TEXT",
        "characters": "hello",
        "style": {},
        "fills": [],
        "opacity": 0.6,
        "blendMode": "SCREEN",
    }

    normalized_frame = module.normalize_frame_node(frame_node, set())
    normalized_text = module.normalize_text_node(text_node)

    assert normalized_frame["opacity"] == 0.8
    assert normalized_frame["blendMode"] == "MULTIPLY"
    assert normalized_text["opacity"] == 0.6
    assert normalized_text["blendMode"] == "SCREEN"

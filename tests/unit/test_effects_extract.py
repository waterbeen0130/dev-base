from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req030_effects"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_effects_drop_shadow_and_layer_blur_are_extracted() -> None:
    module = _load_module()
    node = {
        "id": "1:4",
        "name": "Effect Frame",
        "type": "FRAME",
        "effects": [
            {
                "type": "DROP_SHADOW",
                "visible": True,
                "color": {"r": 0.2, "g": 0.3, "b": 0.4, "a": 0.5},
                "offset": {"x": 2, "y": 4},
                "radius": 8,
                "spread": 1,
                "blendMode": "MULTIPLY",
            },
            {
                "type": "LAYER_BLUR",
                "visible": False,
                "radius": 10,
            },
        ],
    }

    normalized = module.normalize_frame_node(node, set())

    assert normalized["effects"] == [
        {
            "type": "DROP_SHADOW",
            "visible": True,
            "color": "#334c66",
            "offset": {"x": 2.0, "y": 4.0},
            "radius": 8.0,
            "spread": 1.0,
            "blendMode": "MULTIPLY",
        },
        {
            "type": "LAYER_BLUR",
            "visible": False,
            "radius": 10.0,
        },
    ]

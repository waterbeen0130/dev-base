from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req030_solid"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_solid_fill_is_extracted_as_v2_list_of_dict() -> None:
    module = _load_module()
    image_refs: set[str] = set()
    node = {
        "id": "1:1",
        "name": "Solid Frame",
        "type": "FRAME",
        "fills": [
            {
                "type": "SOLID",
                "color": {"r": 0.6666667, "g": 0.7333333, "b": 0.8},
                "opacity": 1,
            }
        ],
    }

    normalized = module.normalize_frame_node(node, image_refs)

    assert normalized["fills_v2"] == [
        {
            "type": "SOLID",
            "color": "#aabbcc",
            "opacity": 1.0,
        }
    ]

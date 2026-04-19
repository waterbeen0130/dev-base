from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req030_gradient"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_gradient_linear_fill_is_extracted_with_stops_and_handles() -> None:
    module = _load_module()
    image_refs: set[str] = set()
    node = {
        "id": "1:2",
        "name": "Gradient Frame",
        "type": "FRAME",
        "fills": [
            {
                "type": "GRADIENT_LINEAR",
                "opacity": 0.9,
                "gradientStops": [
                    {"position": 0, "color": {"r": 0.6666667, "g": 0.7333333, "b": 0.8, "a": 0.5}},
                    {"position": 1, "color": {"r": 0.8666667, "g": 0.9333333, "b": 1.0, "a": 1}},
                ],
                "gradientHandlePositions": [
                    {"x": 0.12349, "y": 0.98764},
                    {"x": 0.54321, "y": 0.11119},
                    {"x": 0.22229, "y": 0.33331},
                ],
            }
        ],
    }

    normalized = module.normalize_frame_node(node, image_refs)

    assert normalized["fills_v2"] == [
        {
            "type": "GRADIENT_LINEAR",
            "opacity": 0.9,
            "gradientStops": [
                {"position": 0.0, "color": "#aabbcc"},
                {"position": 1.0, "color": "#ddeeff"},
            ],
            "gradientHandlePositions": [
                {"x": 0.123, "y": 0.988},
                {"x": 0.543, "y": 0.111},
                {"x": 0.222, "y": 0.333},
            ],
        }
    ]

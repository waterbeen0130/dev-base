from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req030_image"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_image_fill_is_extracted_with_image_fields() -> None:
    module = _load_module()
    image_refs: set[str] = set()
    node = {
        "id": "1:3",
        "name": "Image Frame",
        "type": "FRAME",
        "fills": [
            {
                "type": "IMAGE",
                "imageRef": "img_hash_123",
                "scaleMode": "FILL",
                "imageTransform": [[1, 0, 0], [0, 1, 0]],
                "scalingFactor": 0.75,
                "rotation": 12.3456,
            }
        ],
    }

    normalized = module.normalize_frame_node(node, image_refs)

    assert normalized["fills_v2"] == [
        {
            "type": "IMAGE",
            "imageRef": "img_hash_123",
            "scaleMode": "FILL",
            "imageTransform": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            "scalingFactor": 0.75,
            "rotation": 12.346,
            "opacity": 1.0,
        }
    ]
    assert image_refs == {"img_hash_123"}

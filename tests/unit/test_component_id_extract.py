from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req032_component_id"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_component_id_fields_are_extracted_and_default_to_null() -> None:
    module = _load_module()
    image_refs: set[str] = set()

    with_component = module.normalize_frame_node(
        {
            "id": "1:10",
            "name": "Instance",
            "type": "FRAME",
            "componentId": "100:200",
            "componentSetId": "100:201",
        },
        image_refs,
    )
    without_component = module.normalize_frame_node({"id": "1:11", "name": "Frame", "type": "FRAME"}, image_refs)

    assert with_component["componentId"] == "100:200"
    assert with_component["componentSetId"] == "100:201"
    assert without_component["componentId"] is None
    assert without_component["componentSetId"] is None

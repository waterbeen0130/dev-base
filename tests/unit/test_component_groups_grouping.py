from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req037_grouping"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_same_component_id_instances_are_grouped_across_text_and_frame_nodes() -> None:
    module = _load_module()
    spec = {
        "text_nodes": [
            {"id": "1:1", "name": "Label A", "componentId": "component:card", "characters": "A"},
            {"id": "1:2", "name": "Label B", "componentId": "component:card", "characters": "B"},
            {"id": "1:3", "name": "Standalone", "componentId": "component:single", "characters": "C"},
        ],
        "frame_nodes": [
            {"id": "1:4", "name": "Container", "componentId": "component:card", "fills": "#ffffff"},
        ],
    }

    groups = module.extract_component_groups(spec)

    assert len(groups) == 1
    assert groups[0]["componentId"] == "component:card"
    assert groups[0]["instances"] == ["1:1", "1:2", "1:4"]

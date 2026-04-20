from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req037_override_split"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_component_group_splits_shared_style_from_scoped_overrides() -> None:
    module = _load_module()
    spec = {
        "text_nodes": [
            {
                "id": "2:1",
                "name": "Primary",
                "componentId": "component:button",
                "characters": "Buy",
                "fontFamily": "Inter",
                "fontSize": 16,
                "fontWeight": 600,
                "lineHeightPx": 24,
                "color": "#111111",
                "bbox": {"x": 0, "y": 0, "w": 100, "h": 24},
            },
            {
                "id": "2:2",
                "name": "Secondary",
                "componentId": "component:button",
                "characters": "Sell",
                "fontFamily": "Inter",
                "fontSize": 14,
                "fontWeight": 600,
                "lineHeightPx": 24,
                "color": "#222222",
                "bbox": {"x": 0, "y": 30, "w": 100, "h": 24},
            },
            {
                "id": "2:3",
                "name": "Tertiary",
                "componentId": "component:button",
                "characters": "Hold",
                "fontFamily": "Inter",
                "fontSize": 16,
                "fontWeight": 700,
                "lineHeightPx": 24,
                "color": "#333333",
                "bbox": {"x": 0, "y": 60, "w": 100, "h": 24},
            },
        ],
        "frame_nodes": [],
    }

    group = module.extract_component_groups(spec)[0]
    overrides = {override["node_id"]: override["diff"] for override in group["overrides"]}

    assert group["shared_style"]["componentId"] == "component:button"
    assert group["shared_style"]["fontFamily"] == "Inter"
    assert group["shared_style"]["lineHeightPx"] == 24
    assert "characters" not in group["shared_style"]
    assert "fontSize" not in group["shared_style"]
    assert "fontWeight" not in group["shared_style"]
    assert "color" not in group["shared_style"]
    assert "bbox" not in group["shared_style"]

    assert overrides["2:1"] == {
        "characters": "Buy",
        "fontWeight": 600,
        "fontSize": 16,
        "fills_color": "#111111",
    }
    assert overrides["2:2"] == {
        "characters": "Sell",
        "fontWeight": 600,
        "fontSize": 14,
        "fills_color": "#222222",
    }
    assert overrides["2:3"] == {
        "characters": "Hold",
        "fontWeight": 700,
        "fontSize": 16,
        "fills_color": "#333333",
    }

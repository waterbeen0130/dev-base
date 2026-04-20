from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"
CSS_STYLE_KEYS = ("fontFamily", "fontSize", "fontWeight", "lineHeightPx", "color")


def _load_module():
    module_name = "figma_section_spec_req037_reduction_metric"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _independent_line_count(nodes: list[dict]) -> int:
    return sum(1 for node in nodes for key in CSS_STYLE_KEYS if key in node)


def _grouped_line_count(group: dict) -> int:
    shared_style = group["shared_style"]
    shared_lines = sum(1 for key in CSS_STYLE_KEYS if key in shared_style)
    override_lines = sum(len(override["diff"]) for override in group["overrides"])
    return shared_lines + override_lines


def test_component_grouping_reduces_fixture_style_line_count() -> None:
    module = _load_module()
    nodes = [
        {
            "id": "3:1",
            "componentId": "component:stat",
            "characters": "Revenue",
            "fontFamily": "Inter",
            "fontSize": 18,
            "fontWeight": 700,
            "lineHeightPx": 24,
            "color": "#111111",
        },
        {
            "id": "3:2",
            "componentId": "component:stat",
            "characters": "Margin",
            "fontFamily": "Inter",
            "fontSize": 18,
            "fontWeight": 700,
            "lineHeightPx": 24,
            "color": "#111111",
        },
        {
            "id": "3:3",
            "componentId": "component:stat",
            "characters": "Growth",
            "fontFamily": "Inter",
            "fontSize": 18,
            "fontWeight": 700,
            "lineHeightPx": 24,
            "color": "#111111",
        },
    ]

    group = module.extract_component_groups({"text_nodes": nodes, "frame_nodes": []})[0]
    independent_lines = _independent_line_count(nodes)
    grouped_lines = _grouped_line_count(group)
    reduction = (independent_lines - grouped_lines) / independent_lines

    assert independent_lines == 15
    assert grouped_lines == 8
    assert reduction > 0

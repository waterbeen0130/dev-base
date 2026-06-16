"""AGI-004 #5 prep: spec.json mixed-style extraction in figma-section-spec.py.

Verifies the previously-uncommitted change that (a) parses styleOverrideTable
props at the TOP LEVEL (Figma API shape) instead of under a nested `style` key,
and (b) emits the `has_mixed_styles` flag. This flag is the input the
check-mixed-styles.py accept gate consumes — without correct extraction the
gate can never fire. The top-level-vs-nested distinction is what the old code
got wrong, so these tests fail against the pre-fix version.
"""
import importlib.util
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "tools"
_MODNAME = "figma_section_spec_mixed_styles_test"
_spec = importlib.util.spec_from_file_location(_MODNAME, TOOLS / "figma-section-spec.py")
fss = importlib.util.module_from_spec(_spec)
sys.modules[_MODNAME] = fss  # required: dataclasses resolves field types via sys.modules
_spec.loader.exec_module(fss)


def _node_two_color() -> dict:
    """'AB' where A uses base (black) and B overrides to red + bold."""
    return {
        "characters": "AB",
        "style": {"fontFamily": "Pretendard", "fontSize": 16, "fontWeight": 400},
        "fills": [{"type": "SOLID", "color": {"r": 0.0, "g": 0.0, "b": 0.0}}],
        "characterStyleOverrides": [0, 1],
        "styleOverrideTable": {
            # Figma API: override props live at the TOP LEVEL, not under "style".
            "1": {
                "fills": [{"type": "SOLID", "color": {"r": 1.0, "g": 0.0, "b": 0.0}}],
                "fontWeight": 700,
            }
        },
    }


def test_segments_pick_up_top_level_override_props():
    segs = fss.build_character_segments(_node_two_color())
    assert len(segs) == 2
    # The override segment must reflect the top-level fills + fontWeight.
    assert segs[0]["color"] != segs[1]["color"]
    assert segs[1]["fontWeight"] == 700
    assert segs[0]["fontWeight"] == 400  # base unchanged


def test_normalize_text_node_sets_has_mixed_styles_true():
    node = fss.normalize_text_node(_node_two_color())
    assert node["has_mixed_styles"] is True
    assert len(node["character_segments"]) == 2


def test_uniform_text_is_not_mixed():
    node = {
        "characters": "AB",
        "style": {"fontFamily": "Pretendard", "fontSize": 16, "fontWeight": 400},
        "fills": [{"type": "SOLID", "color": {"r": 0.0, "g": 0.0, "b": 0.0}}],
        "characterStyleOverrides": [0, 0],
        "styleOverrideTable": {},
    }
    out = fss.normalize_text_node(node)
    assert out["has_mixed_styles"] is False


def test_detect_mixed_styles_pure_function():
    assert fss._detect_mixed_styles([]) is False
    assert fss._detect_mixed_styles([{"color": "#000"}]) is False
    assert fss._detect_mixed_styles(
        [{"color": "#000"}, {"color": "#000"}]
    ) is False
    assert fss._detect_mixed_styles(
        [{"color": "#000"}, {"color": "#f00"}]
    ) is True
    assert fss._detect_mixed_styles(
        [{"color": "#000", "fontWeight": 400}, {"color": "#000", "fontWeight": 700}]
    ) is True

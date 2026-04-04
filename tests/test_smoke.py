import sys
import os
import importlib.util

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

spec = importlib.util.spec_from_file_location(
    "figma_extract",
    os.path.join(os.path.dirname(__file__), "..", "tools", "figma-extract.py"),
)
figma_extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figma_extract)

rgba_to_hex = figma_extract.rgba_to_hex
extract_fill_color = figma_extract.extract_fill_color
line_height_to_ratio = figma_extract.line_height_to_ratio
figma_align_to_css = figma_extract.figma_align_to_css


def test_rgba_to_hex_red():
    assert rgba_to_hex(1, 0, 0) == "#f00"


def test_rgba_to_hex_white():
    assert rgba_to_hex(1, 1, 1) == "#fff"


def test_rgba_to_hex_with_opacity():
    result = rgba_to_hex(0.1, 0.2, 0.3, 0.5)
    assert result.startswith("rgba(")


def test_extract_fill_color_solid():
    fills = [{"type": "SOLID", "color": {"r": 1, "g": 0, "b": 0, "a": 1}}]
    assert extract_fill_color(fills) == "#f00"


def test_extract_fill_color_empty():
    assert extract_fill_color([]) is None
    assert extract_fill_color(None) is None


def test_line_height_to_ratio():
    assert line_height_to_ratio(24, 16) == 1.5


def test_figma_align_to_css():
    assert figma_align_to_css("CENTER", "primary") == "center"
    assert figma_align_to_css("SPACE_BETWEEN", "primary") == "space-between"
    assert figma_align_to_css("STRETCH", "counter") == "stretch"

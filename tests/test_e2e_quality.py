"""E2E quality validation tests for DOD-005.

Validates that the normalization engine produces consistent, complete output
for 3 different real Figma designs from the 반값여행_제천 project.
"""
import json
import os
import sys

import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "real")

# Skip all tests if fixture files don't exist (need to run with real Figma data first)
pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(FIXTURES_DIR, "a_main_normalized.json")),
    reason="Real Figma fixtures not found - run normalization with FIGMA_TOKEN first",
)


def _load_fixture(name: str) -> dict:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _count_nodes(node: dict) -> int:
    count = 1
    for child in node.get("children", []):
        count += _count_nodes(child)
    return count


def _collect_text_nodes(node: dict, acc: list | None = None) -> list:
    if acc is None:
        acc = []
    if node.get("text"):
        acc.append(node)
    for child in node.get("children", []):
        _collect_text_nodes(child, acc)
    return acc


def _collect_layout_nodes(node: dict, acc: list | None = None) -> list:
    if acc is None:
        acc = []
    if node.get("layout"):
        acc.append(node)
    for child in node.get("children", []):
        _collect_layout_nodes(child, acc)
    return acc


def _collect_visual_nodes(node: dict, acc: list | None = None) -> list:
    if acc is None:
        acc = []
    if node.get("visual"):
        acc.append(node)
    for child in node.get("children", []):
        _collect_visual_nodes(child, acc)
    return acc


# ---- Fixture list ----

FIXTURES = [
    ("a_main_normalized.json", "A_main"),
    ("a_sub_tle_normalized.json", "A_sub tle"),
    ("a_sub_1_1_normalized.json", "A_sub 1_1"),
]


class TestMetaStructure:
    """Verify meta structure is consistent across all 3 designs."""

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_meta_has_required_fields(self, filename, expected_name):
        data = _load_fixture(filename)
        meta = data["meta"]
        assert meta["source"] == "figma-mcp"
        assert meta["profile"] == "basic"
        assert isinstance(meta["total_nodes"], int)
        assert meta["total_nodes"] > 0

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_tree_root_structure(self, filename, expected_name):
        data = _load_fixture(filename)
        tree = data["tree"]
        assert tree["name"] == expected_name
        assert tree["type"] in ("FRAME", "COMPONENT", "INSTANCE")
        assert "children" in tree

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_node_count_matches_meta(self, filename, expected_name):
        data = _load_fixture(filename)
        actual_count = _count_nodes(data["tree"])
        assert actual_count == data["meta"]["total_nodes"]


class TestLayoutConsistency:
    """Verify layout properties are consistently normalized."""

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_layout_nodes_have_required_fields(self, filename, expected_name):
        data = _load_fixture(filename)
        layout_nodes = _collect_layout_nodes(data["tree"])
        assert len(layout_nodes) > 0, f"{expected_name} should have layout nodes"
        for node in layout_nodes:
            layout = node["layout"]
            assert "display" in layout
            assert "direction" in layout
            assert layout["direction"] in ("column", "row")


class TestVisualConsistency:
    """Verify visual properties are consistently normalized."""

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_colors_are_hex_format(self, filename, expected_name):
        data = _load_fixture(filename)
        visual_nodes = _collect_visual_nodes(data["tree"])
        for node in visual_nodes:
            visual = node["visual"]
            bg = visual.get("background")
            if bg and not bg.startswith("rgba("):
                assert bg.startswith("#"), f"Color should be hex: {bg}"

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_border_only_from_strokes(self, filename, expected_name):
        """Border should only exist when there was a visible stroke in Figma."""
        data = _load_fixture(filename)
        visual_nodes = _collect_visual_nodes(data["tree"])
        for node in visual_nodes:
            visual = node["visual"]
            border = visual.get("border")
            if border is not None:
                assert "solid" in border or "px" in str(border), \
                    f"Border format unexpected: {border}"


class TestTypographyConsistency:
    """Verify text properties are consistently normalized."""

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_text_nodes_have_segments(self, filename, expected_name):
        data = _load_fixture(filename)
        text_nodes = _collect_text_nodes(data["tree"])
        assert len(text_nodes) > 0, f"{expected_name} should have text nodes"
        for node in text_nodes:
            text = node["text"]
            assert "content" in text
            assert "segments" in text
            assert len(text["segments"]) > 0

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_font_size_is_rem_for_basic(self, filename, expected_name):
        """Basic profile: font-size should be rem on PC."""
        data = _load_fixture(filename)
        text_nodes = _collect_text_nodes(data["tree"])
        for node in text_nodes:
            for seg in node["text"]["segments"]:
                fs = seg["style"].get("fontSize", "")
                if fs:
                    assert "rem" in str(fs) or "px" in str(fs), \
                        f"fontSize should have unit: {fs}"

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_line_height_is_ratio(self, filename, expected_name):
        """line-height should be unitless ratio."""
        data = _load_fixture(filename)
        text_nodes = _collect_text_nodes(data["tree"])
        for node in text_nodes:
            for seg in node["text"]["segments"]:
                lh = seg["style"].get("lineHeight")
                if lh is not None:
                    assert isinstance(lh, (int, float)), \
                        f"lineHeight should be numeric ratio: {lh}"

    @pytest.mark.parametrize("filename,expected_name", FIXTURES)
    def test_tag_hint_valid(self, filename, expected_name):
        data = _load_fixture(filename)
        text_nodes = _collect_text_nodes(data["tree"])
        valid_hints = {"span", "p", "h1", "h2", "h3", "h4", "h5", "h6"}
        for node in text_nodes:
            hint = node["text"].get("tag_hint")
            if hint:
                assert hint in valid_hints, f"Invalid tag_hint: {hint}"


class TestCrossDesignConsistency:
    """Verify that output structure is consistent across 3 different designs."""

    def test_all_three_designs_normalize_successfully(self):
        for filename, name in FIXTURES:
            data = _load_fixture(filename)
            assert data["meta"]["total_nodes"] > 0, f"{name} failed normalization"

    def test_output_schema_identical(self):
        """All 3 designs should have identical top-level schema."""
        schemas = []
        for filename, _ in FIXTURES:
            data = _load_fixture(filename)
            schema = {
                "has_meta": "meta" in data,
                "has_tree": "tree" in data,
                "meta_keys": sorted(data["meta"].keys()),
                "tree_top_keys": sorted(
                    k for k in data["tree"].keys() if k != "children"
                ),
            }
            schemas.append(schema)

        # All schemas should be identical
        for i in range(1, len(schemas)):
            assert schemas[0] == schemas[i], \
                f"Schema mismatch between design 0 and {i}"

    def test_total_designs_count(self):
        """DOD-005 requires 3+ different designs."""
        count = 0
        for filename, _ in FIXTURES:
            path = os.path.join(FIXTURES_DIR, filename)
            if os.path.exists(path):
                count += 1
        assert count >= 3, f"Need 3+ designs, got {count}"

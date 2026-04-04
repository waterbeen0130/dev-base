import importlib.util
import json
import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
SCRIPT_PATH = os.path.join(ROOT, "tools", "figma-extract.py")


spec = importlib.util.spec_from_file_location("figma_extract", SCRIPT_PATH)
figma_extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figma_extract)


SAMPLE_TEXT = {
    "id": "2:1",
    "name": "title",
    "type": "TEXT",
    "visible": True,
    "characters": "Hello World",
    "fills": [{"type": "SOLID", "visible": True, "color": {"r": 0.035, "g": 0.035, "b": 0.266, "a": 1}}],
    "style": {
        "fontFamily": "Pretendard",
        "fontWeight": 700,
        "fontSize": 16,
        "lineHeightPx": 24,
        "letterSpacing": -0.4,
    },
    "characterStyleOverrides": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
    "styleOverrideTable": {
        "1": {
            "fontWeight": 400,
            "fills": [{"type": "SOLID", "visible": True, "color": {"r": 1, "g": 0, "b": 0, "a": 1}}],
        }
    },
}


def sample_payload():
    return {
        "id": "1:1",
        "name": "hero_section",
        "type": "FRAME",
        "visible": True,
        "layoutMode": "VERTICAL",
        "itemSpacing": 20,
        "paddingTop": 40,
        "paddingRight": 30,
        "paddingBottom": 40,
        "paddingLeft": 30,
        "primaryAxisAlignItems": "CENTER",
        "counterAxisAlignItems": "MIN",
        "layoutSizingHorizontal": "FILL",
        "layoutSizingVertical": "HUG",
        "absoluteBoundingBox": {"width": 1920, "height": 800},
        "fills": [{"type": "SOLID", "visible": True, "color": {"r": 1, "g": 1, "b": 1, "a": 1}}],
        "strokes": [{"type": "SOLID", "visible": True, "color": {"r": 0.8, "g": 0.8, "b": 0.8, "a": 1}}],
        "strokeWeight": 1,
        "cornerRadius": 8,
        "children": [
            SAMPLE_TEXT,
            {
                "id": "3:1",
                "name": "hidden",
                "type": "FRAME",
                "visible": False,
                "children": [],
            },
            {
                "id": "4:1",
                "name": "divider",
                "type": "FRAME",
                "visible": True,
                "absoluteBoundingBox": {"width": 2, "height": 100},
                "fills": [{"type": "SOLID", "visible": True, "color": {"r": 0, "g": 0, "b": 0, "a": 1}}],
                "children": [],
            },
        ],
    }


def test_normalize_payload_tree_meta_and_visibility():
    result = figma_extract.normalize_payload(sample_payload(), profile_name="basic")

    assert result["meta"]["source"] == "figma-mcp"
    assert result["meta"]["profile"] == "basic"
    assert result["meta"]["section_name"] == "hero_section"
    assert result["meta"]["section_id"] == "1:1"
    assert result["meta"]["total_nodes"] == 3

    tree = result["tree"]
    assert tree["layout"]["display"] == "flex"
    assert tree["layout"]["direction"] == "column"
    assert tree["layout"]["gap"] == "20px"
    assert tree["layout"]["padding"] == "40px 30px"
    assert tree["layout"]["justify"] == "center"
    assert tree["layout"]["align"] == "flex-start"
    assert tree["layout"]["sizing"] == {"horizontal": "FILL", "vertical": "HUG"}

    assert tree["visual"]["background"] == "#fff"
    assert tree["visual"]["border"] == "1px solid #ccc"
    assert tree["visual"]["borderRadius"] == "8px"

    child_ids = [child["id"] for child in tree["children"]]
    assert "3:1" not in child_ids
    assert "4:1" in child_ids


def test_text_segments_cumulative_override_and_typography_conversion():
    result = figma_extract.normalize_payload(sample_payload(), profile_name="basic")
    text_node = next(child for child in result["tree"]["children"] if child["type"] == "TEXT")
    text = text_node["text"]

    assert text["content"] == "Hello World"
    assert text["has_newline"] is False
    assert text["char_length"] == 11

    seg1, seg2 = text["segments"]
    assert seg1["text"] == "Hello "
    assert seg1["style"]["fontSize"] == "1rem"
    assert seg1["style"]["lineHeight"] == 1.5
    assert seg1["style"]["letterSpacing"] == "-0.025em"
    assert seg1["style"]["color"] == "#090944"
    assert seg1["is_override"] is False

    assert seg2["text"] == "World"
    assert seg2["style"]["fontWeight"] == 400
    assert seg2["style"]["color"] == "#f00"
    assert seg2["is_override"] is True


def test_profile_landing_uses_px_font_size():
    result = figma_extract.normalize_payload(sample_payload(), profile_name="landing")
    text_node = next(child for child in result["tree"]["children"] if child["type"] == "TEXT")
    first_segment = text_node["text"]["segments"][0]
    assert first_segment["style"]["fontSize"] == "16px"


def test_border_is_only_generated_from_visible_stroke():
    payload = sample_payload()
    payload["strokes"] = [{"type": "SOLID", "visible": False, "color": {"r": 1, "g": 0, "b": 0, "a": 1}}]

    result = figma_extract.normalize_payload(payload, profile_name="basic")
    assert result["tree"]["visual"]["border"] is None


def test_corner_radius_circle_and_pill():
    payload = {
        "id": "1:2",
        "name": "radius_test",
        "type": "FRAME",
        "visible": True,
        "children": [
            {
                "id": "1:2:1",
                "name": "circle",
                "type": "FRAME",
                "visible": True,
                "absoluteBoundingBox": {"width": 100, "height": 100},
                "cornerRadius": 999,
                "children": [],
            },
            {
                "id": "1:2:2",
                "name": "pill",
                "type": "FRAME",
                "visible": True,
                "absoluteBoundingBox": {"width": 200, "height": 40},
                "cornerRadius": 999,
                "children": [],
            },
        ],
    }

    result = figma_extract.normalize_payload(payload, profile_name="basic")
    circle = result["tree"]["children"][0]
    pill = result["tree"]["children"][1]

    assert circle["visual"]["borderRadius"] == "50%"
    assert pill["visual"]["borderRadius"] == "2em"


def test_cli_stdin_and_tree_mode():
    payload = {"type": "FRAME", "name": "test", "visible": True, "children": []}

    cmd = [sys.executable, SCRIPT_PATH, "--stdin", "--profile", "basic"]
    proc = subprocess.run(cmd, input=json.dumps(payload), text=True, capture_output=True, check=True)
    data = json.loads(proc.stdout)
    assert "meta" in data and "tree" in data

    tree_cmd = [sys.executable, SCRIPT_PATH, "--stdin", "--tree"]
    tree_proc = subprocess.run(tree_cmd, input=json.dumps(payload), text=True, capture_output=True, check=True)
    assert "test (FRAME)" in tree_proc.stdout

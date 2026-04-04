#!/usr/bin/env python3
"""Normalize Figma MCP JSON into a CSS-resolved intermediate JSON tree."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROFILE_DIR = Path(__file__).resolve().parent / "profiles"


# -----------------------------------------------------------------------------
# Compatibility helpers (required by tests/test_smoke.py)
# -----------------------------------------------------------------------------
def rgba_to_hex(r: float, g: float, b: float, a: float = 1.0) -> str:
    """Convert Figma RGBA (0-1 floats) to CSS color string."""
    ri = min(255, max(0, round(r * 255)))
    gi = min(255, max(0, round(g * 255)))
    bi = min(255, max(0, round(b * 255)))

    if a < 1.0:
        return f"rgba({ri},{gi},{bi},{_trim_float(a, 2)})"

    value = f"#{ri:02x}{gi:02x}{bi:02x}"
    if value[1] == value[2] and value[3] == value[4] and value[5] == value[6]:
        return f"#{value[1]}{value[3]}{value[5]}"
    return value


def extract_fill_color(fills: list[dict[str, Any]] | None) -> str | None:
    """Extract first visible SOLID fill as CSS color."""
    if not fills:
        return None

    for fill in fills:
        if fill.get("type") != "SOLID" or fill.get("visible", True) is False:
            continue
        color = fill.get("color") or {}
        fill_alpha = float(fill.get("opacity", 1.0)) * float(color.get("a", 1.0))
        return rgba_to_hex(
            float(color.get("r", 0.0)),
            float(color.get("g", 0.0)),
            float(color.get("b", 0.0)),
            fill_alpha,
        )

    return None


def line_height_to_ratio(line_height_px: float | int | None, font_size: float | int | None) -> float | None:
    """Convert line-height px into CSS unitless ratio."""
    if not line_height_px or not font_size:
        return None
    ratio = float(line_height_px) / float(font_size)
    one_decimal = round(ratio, 1)
    if abs(one_decimal - ratio) < 0.05:
        return one_decimal
    return round(ratio, 2)


def figma_align_to_css(value: str | None, axis: str = "primary") -> str:
    """Map Figma axis alignment to CSS flex alignment values."""
    mapping_primary = {
        "MIN": "flex-start",
        "CENTER": "center",
        "MAX": "flex-end",
        "SPACE_BETWEEN": "space-between",
    }
    mapping_counter = {
        "MIN": "flex-start",
        "CENTER": "center",
        "MAX": "flex-end",
        "BASELINE": "baseline",
        "STRETCH": "stretch",
    }
    mapping = mapping_primary if axis == "primary" else mapping_counter
    if value is None:
        return "flex-start"
    return mapping.get(value, value)


# -----------------------------------------------------------------------------
# Core utils
# -----------------------------------------------------------------------------
def _trim_float(value: float, precision: int = 3) -> str:
    text = f"{value:.{precision}f}".rstrip("0").rstrip(".")
    if text in {"", "-0"}:
        return "0"
    return text


def _fmt_px(value: float | int) -> str:
    rounded = round(float(value), 3)
    if rounded.is_integer():
        return f"{int(rounded)}px"
    return f"{_trim_float(rounded, 3)}px"


def _coerce_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _pick_node_size(node: dict[str, Any]) -> tuple[int | None, int | None]:
    bbox = node.get("absoluteBoundingBox") or {}
    width = bbox.get("width", node.get("width"))
    height = bbox.get("height", node.get("height"))

    w = None if width is None else round(float(width))
    h = None if height is None else round(float(height))
    return w, h


def _padding_shorthand(pt: Any, pr: Any, pb: Any, pl: Any) -> str:
    top = round(_coerce_float(pt, 0))
    right = round(_coerce_float(pr, 0))
    bottom = round(_coerce_float(pb, 0))
    left = round(_coerce_float(pl, 0))

    if top == right == bottom == left:
        return f"{top}px"
    if top == bottom and right == left:
        return f"{top}px {right}px"
    return f"{top}px {right}px {bottom}px {left}px"


def _load_profile(profile_name: str) -> dict[str, Any]:
    path = PROFILE_DIR / f"{profile_name}.json"
    if not path.exists():
        raise ValueError(f"unknown profile: {profile_name}")
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    data["name"] = profile_name
    return data


def _font_size_css(font_size: float | int | None, profile: dict[str, Any]) -> str | None:
    if font_size is None:
        return None

    font_size_value = float(font_size)
    unit = profile.get("font_size_pc", "rem")
    if unit == "rem":
        rem_base = _coerce_float(profile.get("rem_base", 16), 16)
        rem = font_size_value / rem_base
        return f"{_trim_float(rem, 4)}rem"
    return f"{_trim_float(font_size_value, 3)}px"


def _letter_spacing_css(letter_spacing: float | int | None, font_size: float | int | None) -> str | None:
    if letter_spacing is None or not font_size:
        return None
    em = float(letter_spacing) / float(font_size)
    return f"{_trim_float(em, 4)}em"


def _text_align_css(value: str | None) -> str | None:
    if value is None:
        return None
    mapping = {
        "LEFT": "left",
        "CENTER": "center",
        "RIGHT": "right",
        "JUSTIFIED": "justify",
    }
    return mapping.get(value, value.lower())


def _stroke_border(node: dict[str, Any]) -> str | None:
    strokes = node.get("strokes") or []
    for stroke in strokes:
        if stroke.get("type") != "SOLID" or stroke.get("visible", True) is False:
            continue
        color = extract_fill_color([stroke])
        if not color:
            continue
        weight = round(_coerce_float(node.get("strokeWeight", 1), 1))
        return f"{weight}px solid {color}"
    return None


def _radius_values(node: dict[str, Any]) -> list[float] | None:
    radii = node.get("rectangleCornerRadii")
    if isinstance(radii, list) and len(radii) == 4:
        return [float(v or 0) for v in radii]

    keys = ["topLeftRadius", "topRightRadius", "bottomRightRadius", "bottomLeftRadius"]
    corners = [node.get(k) for k in keys]
    if any(v is not None for v in corners):
        return [float(v or 0) for v in corners]

    corner_radius = node.get("cornerRadius")
    if corner_radius is not None:
        radius = float(corner_radius)
        return [radius, radius, radius, radius]

    return None


def _radius_to_css(node: dict[str, Any], width: int | None, height: int | None) -> str:
    values = _radius_values(node)
    if not values:
        return "0"

    if all(v == 0 for v in values):
        return "0"

    if len(set(round(v, 4) for v in values)) == 1:
        radius = values[0]
        if width and height and abs(width - height) <= 1 and radius >= (min(width, height) / 2):
            return "50%"
        if height and width and width > height and radius > (height / 2):
            return "2em"
        return _fmt_px(radius)

    return " ".join(_fmt_px(v) for v in values)


def _style_to_css(style: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    css: dict[str, Any] = {}

    font_family = style.get("fontFamily")
    if font_family:
        css["fontFamily"] = font_family

    font_weight = style.get("fontWeight")
    if font_weight is not None:
        css["fontWeight"] = font_weight

    font_size = style.get("fontSize")
    font_size_css = _font_size_css(font_size, profile)
    if font_size_css:
        css["fontSize"] = font_size_css

    line_height = line_height_to_ratio(style.get("lineHeightPx"), font_size)
    if line_height is not None:
        css["lineHeight"] = line_height

    letter_spacing = _letter_spacing_css(style.get("letterSpacing"), font_size)
    if letter_spacing is not None:
        css["letterSpacing"] = letter_spacing

    color = extract_fill_color(style.get("fills"))
    if color:
        css["color"] = color

    text_align = _text_align_css(style.get("textAlignHorizontal"))
    if text_align:
        css["textAlign"] = text_align

    decoration = style.get("textDecoration")
    if decoration == "UNDERLINE":
        css["textDecoration"] = "underline"
    elif decoration == "STRIKETHROUGH":
        css["textDecoration"] = "line-through"

    return css


def _split_override_segments(chars: str, overrides: list[int]) -> list[dict[str, Any]]:
    if not chars:
        return []

    if not overrides:
        return [{"text": chars, "override_id": 0}]

    padded = list(overrides)
    if len(padded) < len(chars):
        padded.extend([0] * (len(chars) - len(padded)))

    segments: list[dict[str, Any]] = []
    start = 0
    current = padded[0]

    for index in range(1, len(chars)):
        value = padded[index]
        if value != current:
            segments.append({"text": chars[start:index], "override_id": current})
            start = index
            current = value

    segments.append({"text": chars[start:], "override_id": current})
    return segments


def _resolved_text_segments(node: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, Any]]:
    chars = node.get("characters") or ""
    base_style = dict(node.get("style") or {})
    base_style["fills"] = node.get("fills") or base_style.get("fills") or []
    base_css = _style_to_css(base_style, profile)

    segments = _split_override_segments(chars, node.get("characterStyleOverrides") or [])
    override_table = node.get("styleOverrideTable") or {}

    resolved_segments: list[dict[str, Any]] = []
    prev_resolved: dict[str, Any] | None = None

    for segment in segments:
        override_id = segment["override_id"]
        override_key = str(override_id)

        if override_id == 0 or override_key not in override_table:
            resolved_style = copy.deepcopy(base_style)
        else:
            source = prev_resolved if prev_resolved is not None else base_style
            resolved_style = copy.deepcopy(source)
            override = override_table.get(override_key) or {}
            resolved_style.update(override)

        prev_resolved = resolved_style
        segment_css = _style_to_css(resolved_style, profile)

        resolved_segments.append(
            {
                "text": segment["text"],
                "style": segment_css,
                "is_override": segment_css != base_css,
            }
        )

    return resolved_segments


def _looks_sentence_like(text: str) -> bool:
    content = text.strip()
    if not content or " " not in content:
        return False
    return content.endswith(".") or content.endswith("!") or content.endswith("?")


def _is_short_label(text: str) -> bool:
    content = text.strip()
    if not content:
        return True
    if len(content) > 24:
        return False
    if any(ch in content for ch in ".!?,;:"):
        return False
    return "\n" not in content


def _tag_hint(node: dict[str, Any], content: str, depth: int) -> str:
    lowered_name = (node.get("name") or "").lower()

    if "title" in lowered_name or "heading" in lowered_name or "headline" in lowered_name:
        return "h2" if depth <= 1 else "h3"

    if "\n" in content or len(content) > 95 or _looks_sentence_like(content):
        if not _is_short_label(content):
            return "p"

    return "span"


def _extract_layout(node: dict[str, Any]) -> dict[str, Any] | None:
    if node.get("type") not in {"FRAME", "INSTANCE", "COMPONENT", "COMPONENT_SET"}:
        return None

    layout_mode = node.get("layoutMode")
    direction = "column" if layout_mode == "VERTICAL" else "row"

    item_spacing = node.get("itemSpacing")
    if item_spacing is None:
        gap = "0"
    else:
        gap = f"{round(float(item_spacing))}px" if float(item_spacing) > 1 else "0"

    has_padding = any(
        node.get(key) is not None
        for key in ["paddingTop", "paddingRight", "paddingBottom", "paddingLeft"]
    )
    padding = _padding_shorthand(
        node.get("paddingTop", 0),
        node.get("paddingRight", 0),
        node.get("paddingBottom", 0),
        node.get("paddingLeft", 0),
    )

    return {
        "display": "flex" if layout_mode in {"VERTICAL", "HORIZONTAL"} else "block",
        "direction": direction,
        "gap": gap,
        "padding": padding if has_padding else "0",
        "justify": figma_align_to_css(node.get("primaryAxisAlignItems"), axis="primary"),
        "align": figma_align_to_css(node.get("counterAxisAlignItems"), axis="counter"),
        "sizing": {
            "horizontal": node.get("layoutSizingHorizontal", "FIXED"),
            "vertical": node.get("layoutSizingVertical", "FIXED"),
        },
    }


def _extract_visual(node: dict[str, Any]) -> dict[str, Any]:
    width, height = _pick_node_size(node)

    return {
        "width": width,
        "height": height,
        "background": extract_fill_color(node.get("fills")),
        "border": _stroke_border(node),
        "borderRadius": _radius_to_css(node, width, height),
        "opacity": float(node.get("opacity", 1.0)),
    }


def _extract_text(node: dict[str, Any], profile: dict[str, Any], depth: int) -> dict[str, Any] | None:
    if node.get("type") != "TEXT":
        return None

    content = node.get("characters") or ""
    segments = _resolved_text_segments(node, profile)

    return {
        "content": content,
        "tag_hint": _tag_hint(node, content, depth),
        "has_newline": "\n" in content,
        "char_length": len(content),
        "segments": segments,
    }


def _normalize_node(node: dict[str, Any], profile: dict[str, Any], depth: int = 0) -> dict[str, Any] | None:
    if node.get("visible", True) is False:
        return None

    normalized_children = []
    for child in node.get("children") or []:
        item = _normalize_node(child, profile, depth + 1)
        if item is not None:
            normalized_children.append(item)

    return {
        "id": node.get("id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "layout": _extract_layout(node),
        "visual": _extract_visual(node),
        "text": _extract_text(node, profile, depth),
        "children": normalized_children,
    }


def _count_nodes(tree: dict[str, Any] | None) -> int:
    if not tree:
        return 0
    return 1 + sum(_count_nodes(child) for child in tree.get("children") or [])


def _try_parse_json_text(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```"):
            stripped = "\n".join(lines[1:-1]).strip()

    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return None

    if isinstance(value, dict):
        return value
    return None


def parse_mcp_response(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse known Figma MCP / API response envelopes into node candidates."""
    if not isinstance(data, dict):
        raise ValueError("input JSON root must be an object")

    for key in ("data", "result", "payload"):
        wrapped = data.get(key)
        if isinstance(wrapped, dict):
            return parse_mcp_response(wrapped)

    content = data.get("content")
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            parsed = _try_parse_json_text(str(item.get("text", "")))
            if parsed:
                return parse_mcp_response(parsed)

    if "nodes" in data and isinstance(data["nodes"], dict):
        nodes: list[dict[str, Any]] = []
        for wrapper in data["nodes"].values():
            if isinstance(wrapper, dict):
                doc = wrapper.get("document", wrapper)
                if isinstance(doc, dict):
                    nodes.append(doc)
        if nodes:
            return nodes

    if "document" in data and isinstance(data["document"], dict):
        document = data["document"]
        if document.get("children") and document.get("type") is None:
            return [child for child in document.get("children", []) if isinstance(child, dict)]
        return [document]

    if data.get("type"):
        return [data]

    if data.get("children") and isinstance(data.get("children"), list):
        return [data]

    raise ValueError("could not detect Figma node structure from input")


def normalize_payload(data: dict[str, Any], profile_name: str = "basic") -> dict[str, Any]:
    """Normalize Figma payload into the intermediate JSON format."""
    profile = _load_profile(profile_name)
    targets = parse_mcp_response(data)

    if not targets:
        raise ValueError("no extractable nodes found")

    root = targets[0] if len(targets) == 1 else {
        "id": "",
        "name": "root",
        "type": "FRAME",
        "visible": True,
        "children": targets,
    }

    tree = _normalize_node(root, profile, depth=0)
    total_nodes = _count_nodes(tree)

    return {
        "meta": {
            "source": "figma-mcp",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "profile": profile_name,
            "section_name": root.get("name", ""),
            "section_id": root.get("id", ""),
            "total_nodes": total_nodes,
        },
        "tree": tree,
    }


def find_node_by_id(data: dict[str, Any], target_id: str) -> dict[str, Any] | None:
    if data.get("id") == target_id:
        return data
    for child in data.get("children", []) or []:
        found = find_node_by_id(child, target_id)
        if found:
            return found
    return None


def find_node_by_name(data: dict[str, Any], target_name: str) -> dict[str, Any] | None:
    if target_name.lower() in str(data.get("name", "")).lower():
        return data
    for child in data.get("children", []) or []:
        found = find_node_by_name(child, target_name)
        if found:
            return found
    return None


def get_top_frames(data: dict[str, Any]) -> list[dict[str, Any]]:
    root = data.get("document", data)
    frames: list[dict[str, Any]] = []
    for child in root.get("children", []) or []:
        child_type = child.get("type")
        if child_type == "CANVAS":
            frames.extend([
                n
                for n in child.get("children", []) or []
                if n.get("type") in {"FRAME", "COMPONENT", "COMPONENT_SET"}
            ])
        elif child_type in {"FRAME", "COMPONENT", "COMPONENT_SET"}:
            frames.append(child)
    return frames


def fetch_figma_node(file_key: str, node_id: str, depth: int = 8) -> dict[str, Any]:
    """Fetch node data from Figma REST API."""
    import urllib.error
    import urllib.request

    token = os.environ.get("FIGMA_TOKEN") or os.environ.get("FIGMA_PERSONAL_ACCESS_TOKEN")
    if not token:
        token_path = Path.home() / ".figma_token"
        if token_path.exists():
            token = token_path.read_text(encoding="utf-8").strip()

    if not token:
        raise RuntimeError("Figma token not found. Set FIGMA_TOKEN or ~/.figma_token")

    api_node_id = node_id.replace("-", ":")
    url = f"https://api.figma.com/v1/files/{file_key}/nodes?ids={api_node_id}&depth={depth}"

    request = urllib.request.Request(url)
    request.add_header("X-Figma-Token", token)

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Figma API error {exc.code}: {exc.reason}") from exc


def _print_tree(node: dict[str, Any], indent: int = 0) -> None:
    if node.get("visible", True) is False:
        return

    name = node.get("name", "")
    node_type = node.get("type", "")
    print(f"{'  ' * indent}{name} ({node_type})")

    for child in node.get("children", []) or []:
        _print_tree(child, indent + 1)


def _read_input(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if args.node_id:
        if not args.file_key:
            raise ValueError("--file-key is required with --node-id")
        payload = fetch_figma_node(args.file_key, args.node_id, depth=args.depth)
    elif args.stdin:
        raw = sys.stdin.read()
        if not raw.strip():
            raise ValueError("empty stdin")
        payload = json.loads(raw)
    elif args.figma:
        with open(args.figma, "r", encoding="utf-8") as fp:
            payload = json.load(fp)
    else:
        raise ValueError("one of --stdin, --figma, or --node-id is required")

    if args.figma and any([args.frame, args.frame_name, args.all]):
        document = payload.get("document", payload)
        if args.frame:
            node = find_node_by_id(document, args.frame)
            if not node:
                raise ValueError(f"frame id not found: {args.frame}")
            return [node], payload
        if args.frame_name:
            node = find_node_by_name(document, args.frame_name)
            if not node:
                raise ValueError(f"frame name not found: {args.frame_name}")
            return [node], payload
        if args.all:
            frames = get_top_frames(payload)
            if not frames:
                raise ValueError("no top-level frames found")
            return frames, payload

    return parse_mcp_response(payload), payload


def _build_validate_mapping(tree: dict[str, Any]) -> dict[str, Any]:
    """Build validate.js-compatible mapping from normalized tree (DOD-006)."""
    mapping: dict[str, Any] = {}

    def _walk(node: dict[str, Any]) -> None:
        node_id = node.get("id", "")
        if not node_id:
            for child in node.get("children", []):
                _walk(child)
            return

        css_props: dict[str, Any] = {}
        layout = node.get("layout")
        visual = node.get("visual")
        text = node.get("text")

        if layout:
            if layout.get("direction"):
                css_props["flex-direction"] = layout["direction"]
            if layout.get("gap") and layout["gap"] != "0":
                css_props["gap"] = layout["gap"]
            if layout.get("padding") and layout["padding"] != "0":
                css_props["padding"] = layout["padding"]
            if layout.get("justify"):
                css_props["justify-content"] = layout["justify"]
            if layout.get("align"):
                css_props["align-items"] = layout["align"]

        if visual:
            bg = visual.get("background")
            if bg:
                css_props["background-color"] = bg
            border = visual.get("border")
            if border:
                css_props["border"] = border
            br = visual.get("borderRadius")
            if br and br != "0":
                css_props["border-radius"] = br

        if text and text.get("segments"):
            seg = text["segments"][0]["style"]
            for key in ("fontSize", "fontWeight", "lineHeight", "letterSpacing", "color"):
                val = seg.get(key)
                if val is not None:
                    css_key = {
                        "fontSize": "font-size",
                        "fontWeight": "font-weight",
                        "lineHeight": "line-height",
                        "letterSpacing": "letter-spacing",
                        "color": "color",
                    }[key]
                    css_props[css_key] = val

        if css_props:
            mapping[node_id] = {
                "name": node.get("name", ""),
                "type": node.get("type", ""),
                "css": css_props,
            }

        for child in node.get("children", []):
            _walk(child)

    _walk(tree)
    return mapping


def _print_rule_log(tree: dict[str, Any], file: Any = None) -> None:
    """Print normalization rule application log (DOD-007)."""
    if file is None:
        file = sys.stderr

    def _log_node(node: dict[str, Any], depth: int = 0) -> None:
        indent = "  " * depth
        name = node.get("name", "?")
        ntype = node.get("type", "?")
        layout = node.get("layout")
        visual = node.get("visual")
        text = node.get("text")

        rules_applied = []
        if layout:
            if layout.get("direction"):
                rules_applied.append(f"layoutMode → flex-direction:{layout['direction']}")
            if layout.get("gap") and layout["gap"] != "0":
                rules_applied.append(f"itemSpacing → gap:{layout['gap']}")
            if layout.get("padding") and layout["padding"] != "0":
                rules_applied.append(f"padding → {layout['padding']}")
        if visual:
            if visual.get("background"):
                rules_applied.append(f"fills → background:{visual['background']}")
            if visual.get("border"):
                rules_applied.append(f"strokes → border:{visual['border']}")
            if visual.get("borderRadius") and visual["borderRadius"] != "0":
                rules_applied.append(f"cornerRadius → border-radius:{visual['borderRadius']}")
        if text:
            segs = text.get("segments", [])
            if segs:
                s = segs[0]["style"]
                rules_applied.append(f"fontSize:{s.get('fontSize','?')}")
                rules_applied.append(f"lineHeight:{s.get('lineHeight','?')}")
            if len(segs) > 1:
                rules_applied.append(f"overrides:{len(segs)} segments")
            if text.get("tag_hint"):
                rules_applied.append(f"tag_hint:{text['tag_hint']}")

        if rules_applied:
            print(f"{indent}[NORM] {name} ({ntype})", file=file)
            for rule in rules_applied:
                print(f"{indent}  [RULE] {rule}", file=file)

        for child in node.get("children", []):
            _log_node(child, depth + 1)

    _log_node(tree)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Figma JSON to intermediate JSON tree")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    parser.add_argument("--figma", help="Read JSON from local file")
    parser.add_argument("--node-id", help="Fetch Figma node by ID via REST API")
    parser.add_argument("--file-key", help="Figma file key for --node-id")
    parser.add_argument("--frame", help="Frame ID for --figma mode")
    parser.add_argument("--frame-name", help="Frame name search for --figma mode")
    parser.add_argument("--all", action="store_true", help="Extract all top-level frames for --figma mode")
    parser.add_argument("--depth", type=int, default=10, help="Traversal depth for --node-id fetch")
    parser.add_argument("--tree", action="store_true", help="Print visible node tree")
    parser.add_argument("--profile", default="basic", help="Normalization profile (basic|landing)")
    parser.add_argument("--emit-mapping", action="store_true", help="Also emit validate.js-compatible mapping JSON to stderr")
    parser.add_argument("--verbose", action="store_true", help="Print normalization rule log to stderr")
    parser.add_argument("--output", help="Output directory for mapping files")

    args = parser.parse_args()

    try:
        targets, _ = _read_input(args)

        if args.tree:
            for target in targets:
                _print_tree(target)
            return

        if len(targets) == 1:
            selected_payload = targets[0]
        else:
            selected_payload = {
                "id": "",
                "name": "root",
                "type": "FRAME",
                "visible": True,
                "children": targets,
            }

        normalized = normalize_payload(selected_payload, profile_name=args.profile)

        # DOD-007: verbose rule log
        if args.verbose:
            _print_rule_log(normalized["tree"], file=sys.stderr)

        json.dump(normalized, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")

        # DOD-006: emit validate.js-compatible mapping
        if args.emit_mapping:
            mapping = _build_validate_mapping(normalized["tree"])
            if args.output:
                os.makedirs(args.output, exist_ok=True)
                name = normalized["meta"]["section_name"].replace(" ", "_")
                path = os.path.join(args.output, f"{name}_mapping.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(mapping, f, ensure_ascii=False, indent=2)
                print(f"  -> {path}", file=sys.stderr)
            else:
                json.dump(mapping, sys.stderr, ensure_ascii=False, indent=2)
                sys.stderr.write("\n")
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

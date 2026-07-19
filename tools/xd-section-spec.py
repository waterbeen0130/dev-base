#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


SCHEMA_VERSION = "2.0.0"
ARTBOARD_META_KEYS = {"width", "height", "name", "x", "y"}
FONT_WEIGHT_BY_STYLE = {
    "thin": 100,
    "extralight": 200,
    "ultralight": 200,
    "light": 300,
    "regular": 400,
    "normal": 400,
    "medium": 500,
    "semibold": 600,
    "demibold": 600,
    "bold": 700,
    "extrabold": 800,
    "ultrabold": 800,
    "black": 900,
    "heavy": 900,
}
ALIGN_MAP = {
    "left": "LEFT",
    "center": "CENTER",
    "right": "RIGHT",
    "justify": "JUSTIFIED",
}


def fail(message: str) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def safe_round_3(value: object) -> float | int | None:
    if value is None:
        return None
    try:
        rounded = round(float(value), 3)
    except (TypeError, ValueError):
        return None
    if rounded.is_integer():
        return int(rounded)
    return rounded


def compute_line_height_ratio(line_height_px: object, font_size: object) -> float | None:
    try:
        if line_height_px is None or font_size is None:
            return None
        denominator = float(font_size)
        if denominator == 0:
            return None
        return round(float(line_height_px) / denominator, 3)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def find_project_root() -> Path:
    candidate = Path.cwd().resolve()
    while candidate != candidate.parent:
        if (candidate / ".gran-maestro").is_dir():
            return candidate
        candidate = candidate.parent
    return Path.cwd().resolve()


def detect_password_gate(title: str, body_text: str) -> bool:
    haystack = f"{title}\n{body_text}".lower()
    markers = (
        "password protected",
        "enter password",
        "enter your password",
        "requires a password",
    )
    return any(marker in haystack for marker in markers)


def argb_int_to_css_color(value: object) -> str:
    if isinstance(value, str):
        text = value.strip().lower()
        base = 16 if text.startswith("0x") else 10
        try:
            value = int(text, base=base)
        except ValueError as exc:
            raise ValueError(f"invalid ARGB color '{value}'") from exc
    if not isinstance(value, int):
        raise ValueError(f"invalid ARGB color '{value}'")
    value &= 0xFFFFFFFF
    alpha = (value >> 24) & 0xFF
    red = (value >> 16) & 0xFF
    green = (value >> 8) & 0xFF
    blue = value & 0xFF
    if alpha == 0xFF:
        return f"#{red:02x}{green:02x}{blue:02x}"
    alpha_ratio = round(alpha / 255.0, 3)
    return f"rgba({red}, {green}, {blue}, {alpha_ratio:.3f})"


def load_json_file(path: Path, *, tolerant: bool = False) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        if tolerant:
            warn(f"Skipping non-UTF-8 Adobe XD capture payload: {path} ({exc})")
            return None
        fail(f"Invalid Adobe XD capture JSON: {path}\n{exc}")
    except json.JSONDecodeError as exc:
        if tolerant:
            warn(f"Skipping invalid Adobe XD capture JSON: {path} ({exc})")
            return None
        fail(f"Invalid Adobe XD capture JSON: {path}\n{exc}")


def is_design_payload(payload: object) -> bool:
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("artboards"), dict)
        and isinstance(payload.get("children"), list)
    )


def load_capture_payloads(capture_dir: Path) -> list[dict]:
    if not capture_dir.is_dir():
        fail(f"Capture directory not found: {capture_dir}")
    payloads: list[dict] = []
    for path in sorted(capture_dir.glob("*.json")):
        payload = load_json_file(path, tolerant=True)
        if payload is None:
            continue
        if is_design_payload(payload):
            payloads.append(payload)
    if not payloads:
        fail(f"No Adobe XD artboard payload found in capture directory: {capture_dir}")
    return payloads


def _validate_artboard_meta(artboard_id: str, meta: object) -> dict:
    if not isinstance(meta, dict):
        fail(f"Invalid Adobe XD capture schema: artboard '{artboard_id}' metadata missing")
    missing = [key for key in ARTBOARD_META_KEYS if key not in meta]
    if missing:
        fail(
            f"Invalid Adobe XD capture schema: artboard '{artboard_id}' missing keys "
            f"{', '.join(sorted(missing))}"
        )
    return meta


def iter_artboards(payload: dict) -> list[dict]:
    artboards_meta = payload.get("artboards")
    children = payload.get("children")
    if not isinstance(artboards_meta, dict) or not isinstance(children, list):
        fail("Invalid Adobe XD capture schema: missing 'artboards' or 'children'")

    artboards: list[dict] = []
    for child in children:
        if not isinstance(child, dict) or child.get("type") != "artboard":
            continue
        artboard_id = child.get("id")
        if not isinstance(artboard_id, str) or not artboard_id:
            fail("Invalid Adobe XD capture schema: artboard node missing id")
        artboard_meta = _validate_artboard_meta(artboard_id, artboards_meta.get(artboard_id))
        artboard_content = child.get("artboard")
        if not isinstance(artboard_content, dict) or not isinstance(artboard_content.get("children"), list):
            fail(f"Invalid Adobe XD capture schema: artboard '{artboard_id}' missing child tree")
        artboards.append(
            {
                "id": artboard_id,
                "node": child,
                "meta": artboard_meta,
            }
        )
    if not artboards:
        fail("Invalid Adobe XD capture schema: no artboard nodes found")
    return artboards


def select_artboard(payloads: list[dict], artboard_name: str | None) -> dict:
    found: list[dict] = []
    for payload in payloads:
        for artboard in iter_artboards(payload):
            name = artboard["meta"].get("name")
            if artboard_name is None or name == artboard_name:
                found.append(artboard)
    if artboard_name is None:
        if len(found) != 1:
            fail("Multiple artboards found. Use --artboard to select one.")
        return found[0]
    if not found:
        fail(f"Artboard not found: {artboard_name}")
    return max(found, key=artboard_richness)


def list_artboards(payloads: list[dict]) -> int:
    seen: set[str] = set()
    for payload in payloads:
        for artboard in iter_artboards(payload):
            artboard_id = artboard["id"]
            if artboard_id in seen:
                continue
            seen.add(artboard_id)
            meta = artboard["meta"]
            print(f"{meta['name']} {meta['width']}x{meta['height']}")
    return 0


def parse_font_weight(style_name: object) -> int | None:
    if not isinstance(style_name, str) or not style_name.strip():
        return None
    normalized = style_name.replace("-", "").replace(" ", "").lower()
    return FONT_WEIGHT_BY_STYLE.get(normalized)


def extract_text_align(style: dict) -> str | None:
    text_attributes = style.get("textAttributes")
    if not isinstance(text_attributes, dict):
        return None
    paragraph_align = text_attributes.get("paragraphAlign")
    if not isinstance(paragraph_align, str):
        return None
    return ALIGN_MAP.get(paragraph_align.lower())


def extract_transform_bbox(node: dict) -> dict:
    transform = node.get("transform")
    ux = node.get("meta", {}).get("ux", {}) if isinstance(node.get("meta"), dict) else {}
    if not isinstance(transform, dict) or not isinstance(ux, dict):
        return {"x": None, "y": None, "w": None, "h": None}
    return {
        "x": safe_round_3(transform.get("tx")),
        "y": safe_round_3(transform.get("ty")),
        "w": safe_round_3(ux.get("width")),
        "h": safe_round_3(ux.get("height")),
    }


def extract_shape_corner_data(node: dict) -> tuple[float | int | None, list[float | int], str | None, dict | None]:
    if node.get("type") not in {"shape", "rectangle"}:
        return None, [0, 0, 0, 0], None, None

    shape = node.get("shape")
    if not isinstance(shape, dict) or "r" not in shape:
        return None, [0, 0, 0, 0], None, None

    raw_radius = shape.get("r")
    normalized_radii: list[float | int] = [0, 0, 0, 0]
    extra: dict | None = None
    bbox = extract_transform_bbox(node)
    width = bbox.get("w")
    height = bbox.get("h")
    max_allowed_radius: float | None = None
    if isinstance(width, (int, float)) and isinstance(height, (int, float)):
        max_allowed_radius = min(float(width), float(height)) / 2.0

    if isinstance(raw_radius, list):
        values: list[float | int] = []
        for value in raw_radius[:4]:
            parsed = safe_round_3(value)
            if not isinstance(parsed, (int, float)):
                return None, [0, 0, 0, 0], None, None
            if float(parsed) < 0:
                return None, [0, 0, 0, 0], None, None
            if max_allowed_radius is not None and float(parsed) > max_allowed_radius:
                return None, [0, 0, 0, 0], None, None
            values.append(parsed)
        while len(values) < 4:
            values.append(0)
        normalized_radii = values[:4]
        if len(set(normalized_radii)) == 1:
            corner_radius = normalized_radii[0]
        else:
            corner_radius = None
    else:
        parsed = safe_round_3(raw_radius)
        if not isinstance(parsed, (int, float)):
            return None, [0, 0, 0, 0], None, None
        if float(parsed) < 0:
            return None, [0, 0, 0, 0], None, None
        if max_allowed_radius is not None and float(parsed) > max_allowed_radius:
            return None, [0, 0, 0, 0], None, None
        corner_radius = parsed
        normalized_radii = [parsed, parsed, parsed, parsed]

    hint = None
    if isinstance(corner_radius, (int, float)) and max_allowed_radius is not None:
        if float(corner_radius) >= max_allowed_radius:
            hint = "50%"

    return corner_radius, normalized_radii, hint, extra


def extract_text_bbox(node: dict) -> dict:
    transform = node.get("transform")
    if not isinstance(transform, dict):
        return {"x": None, "y": None, "w": None, "h": None}
    x = safe_round_3(transform.get("tx"))
    y = safe_round_3(transform.get("ty"))

    layout = node.get("meta", {}).get("ux", {}).get("outlinesLayout", {})
    paragraphs = layout.get("static", {}).get("paragraphs", []) if isinstance(layout, dict) else []
    max_left = min_top = max_right = max_bottom = None
    for paragraph in paragraphs:
        if not isinstance(paragraph, dict):
            continue
        for line_group in paragraph.get("lines", []):
            if not isinstance(line_group, dict):
                continue
            bounds = line_group.get("layoutBounds")
            if not isinstance(bounds, dict):
                continue
            left = float(bounds.get("left", 0))
            right = float(bounds.get("right", 0))
            ascent = float(bounds.get("ascent", 0))
            descent = float(bounds.get("descent", 0))
            position = float(line_group.get("position", 0))
            top = position + ascent
            bottom = position + descent
            max_left = left if max_left is None else min(max_left, left)
            min_top = top if min_top is None else min(min_top, top)
            max_right = right if max_right is None else max(max_right, right)
            max_bottom = bottom if max_bottom is None else max(max_bottom, bottom)
    if max_left is None or min_top is None or max_right is None or max_bottom is None:
        return {"x": x, "y": y, "w": None, "h": None}
    return {
        "x": safe_round_3((x or 0) + max_left),
        "y": safe_round_3((y or 0) + min_top),
        "w": safe_round_3(max_right - max_left),
        "h": safe_round_3(max_bottom - min_top),
    }


def ranged_styles_for_text(node: dict, text: str) -> list[dict]:
    meta = node.get("meta")
    if not isinstance(meta, dict):
        fail(f"Invalid Adobe XD capture schema: text node '{node.get('id')}' missing meta")
    ux = meta.get("ux")
    if not isinstance(ux, dict):
        fail(f"Invalid Adobe XD capture schema: text node '{node.get('id')}' missing meta.ux")
    ranged_styles = ux.get("rangedStyles")
    if not isinstance(ranged_styles, list):
        fail(f"Invalid Adobe XD capture schema: text node '{node.get('id')}' missing rangedStyles")
    if not ranged_styles:
        return [{"start": 0, "end": len(text), "style": {}}]
    normalized: list[dict] = []
    cursor = 0
    for index, style in enumerate(ranged_styles):
        if not isinstance(style, dict):
            fail(f"Invalid Adobe XD capture schema: text node '{node.get('id')}' has invalid rangedStyles entry")
        length = style.get("length")
        try:
            segment_length = int(length)
        except (TypeError, ValueError):
            fail(f"Invalid Adobe XD capture schema: text node '{node.get('id')}' has invalid rangedStyles length")
        if segment_length <= 0:
            segment_length = len(text) - cursor
        start = cursor
        end = min(len(text), cursor + segment_length)
        if index == len(ranged_styles) - 1:
            end = len(text)
        normalized.append({"start": start, "end": end, "style": style})
        cursor = end
    if not normalized or normalized[-1]["end"] != len(text):
        normalized[-1]["end"] = len(text)
    return normalized


def _font_family_from_style(style: dict, fallback_style: dict) -> str | None:
    for key in ("fontFamily",):
        value = style.get(key)
        if isinstance(value, str) and value:
            return value
    font = fallback_style.get("font")
    if isinstance(font, dict):
        family = font.get("family")
        if isinstance(family, str) and family:
            return family
    return None


def _font_size_from_style(style: dict, fallback_style: dict) -> int | float | None:
    value = safe_round_3(style.get("fontSize"))
    if value is not None:
        return value
    font = fallback_style.get("font")
    if isinstance(font, dict):
        return safe_round_3(font.get("size"))
    return None


def _font_weight_from_style(style: dict, fallback_style: dict) -> int | None:
    value = parse_font_weight(style.get("fontStyle"))
    if value is not None:
        return value
    font = fallback_style.get("font")
    if isinstance(font, dict):
        return parse_font_weight(font.get("style"))
    return None


def _letter_spacing_from_style(style: dict, fallback_style: dict) -> int | float | None:
    value = safe_round_3(style.get("charSpacing"))
    if value is not None:
        return value
    text_attributes = fallback_style.get("textAttributes")
    if isinstance(text_attributes, dict):
        return safe_round_3(text_attributes.get("letterSpacing", 0))
    return None


def _line_height_from_style(style: dict, fallback_style: dict) -> int | float | None:
    for key in ("lineHeight", "lineSpacing"):
        value = safe_round_3(style.get(key))
        if value is not None:
            return value
    text_attributes = fallback_style.get("textAttributes")
    if isinstance(text_attributes, dict):
        for key in ("lineHeight", "lineSpacing"):
            value = safe_round_3(text_attributes.get(key))
            if value is not None:
                return value
    return None


def _color_from_style(style: dict, fallback_style: dict) -> str | None:
    fill = style.get("fill")
    if isinstance(fill, dict) and "value" in fill:
        return argb_int_to_css_color(fill.get("value"))
    base_fill = fallback_style.get("fill")
    if isinstance(base_fill, dict):
        color = base_fill.get("color")
        if isinstance(color, dict):
            value = color.get("value")
            if isinstance(value, dict):
                red = int(value.get("r", 0))
                green = int(value.get("g", 0))
                blue = int(value.get("b", 0))
                return f"#{red:02x}{green:02x}{blue:02x}"
    return None


def build_character_segments(node: dict) -> list[dict]:
    text = node.get("text", {}).get("rawText")
    if not isinstance(text, str) or not text:
        return []
    fallback_style = node.get("style") if isinstance(node.get("style"), dict) else {}
    segments: list[dict] = []
    for segment in ranged_styles_for_text(node, text):
        style = segment["style"]
        start = segment["start"]
        end = segment["end"]
        font_size = _font_size_from_style(style, fallback_style)
        line_height_px = _line_height_from_style(style, fallback_style)
        segments.append(
            {
                "start": start,
                "end": end,
                "length": end - start,
                "text": text[start:end],
                "fontFamily": _font_family_from_style(style, fallback_style),
                "fontSize": font_size,
                "fontWeight": _font_weight_from_style(style, fallback_style),
                "lineHeightPx": line_height_px,
                "letterSpacing": _letter_spacing_from_style(style, fallback_style),
                "color": _color_from_style(style, fallback_style),
            }
        )
    return segments


def detect_mixed_styles(segments: list[dict]) -> bool:
    if len(segments) <= 1:
        return False
    first = segments[0]
    keys = ("fontSize", "fontWeight", "lineHeightPx", "letterSpacing", "color")
    for segment in segments[1:]:
        if any(segment.get(key) != first.get(key) for key in keys):
            return True
    return False


def artboard_richness(artboard: dict) -> tuple[int, int]:
    artboard_node = artboard.get("node")
    artboard_content = artboard_node.get("artboard") if isinstance(artboard_node, dict) else None
    root_children = artboard_content.get("children") if isinstance(artboard_content, dict) else []
    if not isinstance(root_children, list):
        return (0, 0)

    total_nodes = 0
    text_nodes = 0
    stack = list(root_children)
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        total_nodes += 1
        if node.get("type") == "text":
            text_nodes += 1
        stack.extend(iter_child_nodes(node))
    return (text_nodes, total_nodes)


def normalize_text_node(node: dict) -> dict:
    raw_text = node.get("text", {}).get("rawText")
    if not isinstance(raw_text, str):
        fail(f"Invalid Adobe XD capture schema: text node '{node.get('id')}' missing rawText")
    style = node.get("style")
    if not isinstance(style, dict):
        fail(f"Invalid Adobe XD capture schema: text node '{node.get('id')}' missing style")

    font = style.get("font") if isinstance(style.get("font"), dict) else {}
    text_attributes = style.get("textAttributes") if isinstance(style.get("textAttributes"), dict) else {}
    font_size = safe_round_3(font.get("size"))
    line_height_px = _line_height_from_style({}, style)
    letter_spacing = safe_round_3(text_attributes.get("letterSpacing", 0))
    segments = build_character_segments(node)
    has_mixed_styles = detect_mixed_styles(segments)

    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "characters": raw_text,
        "fontFamily": font.get("family"),
        "fontSize": font_size,
        "fontWeight": parse_font_weight(font.get("style")),
        "lineHeightPx": line_height_px,
        "lineHeightRatio": compute_line_height_ratio(line_height_px, font_size),
        "letterSpacing": letter_spacing,
        "color": _color_from_style({}, style),
        "opacity": 1.0,
        "blendMode": "PASS_THROUGH",
        "effects": [],
        "textAlignHorizontal": extract_text_align(style),
        "textAlignVertical": None,
        "bbox": extract_text_bbox(node),
        "has_mixed_styles": has_mixed_styles,
        "character_segments": segments,
        "characterStyleOverrides": None,
        "styleOverrideTable": None,
        "textCase": "ORIGINAL",
        "textDecoration": "NONE",
        "paragraphSpacing": 0.0,
        "paragraphIndent": 0.0,
    }


def normalize_frame_node(node: dict) -> dict:
    corner_radius, rectangle_corner_radii, hint, extra = extract_shape_corner_data(node)
    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "bbox": extract_transform_bbox(node),
        "layoutMode": None,
        "paddingTop": None,
        "paddingRight": None,
        "paddingBottom": None,
        "paddingLeft": None,
        "itemSpacing": None,
        "primaryAxisAlignItems": None,
        "counterAxisAlignItems": None,
        "fills": None,
        "fills_v2": [],
        "strokes": [],
        "strokeWeight": 0,
        "strokeAlign": "CENTER",
        "effects": [],
        "opacity": 1.0,
        "blendMode": "PASS_THROUGH",
        "layoutSizingHorizontal": "FIXED",
        "layoutSizingVertical": "FIXED",
        "layoutGrow": 0,
        "layoutAlign": "INHERIT",
        "componentId": None,
        "componentSetId": None,
        "cornerRadius": corner_radius,
        "rectangleCornerRadii": rectangle_corner_radii,
        "border_radius_hint": hint,
        "_extra": extra,
    }


def iter_child_nodes(node: dict) -> list[dict]:
    children: list[dict] = []
    direct_children = node.get("children")
    if isinstance(direct_children, list):
        children.extend(child for child in direct_children if isinstance(child, dict))
    for value in node.values():
        if not isinstance(value, dict):
            continue
        nested_children = value.get("children")
        if isinstance(nested_children, list):
            children.extend(child for child in nested_children if isinstance(child, dict))
    return children


def walk_artboard_nodes(root_nodes: list[dict]) -> tuple[list[dict], list[dict]]:
    text_nodes: list[dict] = []
    frame_nodes: list[dict] = []
    stack = list(reversed(root_nodes))
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        node_type = node.get("type")
        if node_type == "text":
            text_nodes.append(normalize_text_node(node))
        elif node_type in {"group", "shape", "rectangle", "ellipse"}:
            frame_nodes.append(normalize_frame_node(node))
        stack.extend(reversed(iter_child_nodes(node)))
    return text_nodes, frame_nodes


def build_spec_payload(artboard: dict, section_name: str) -> dict:
    artboard_node = artboard["node"]
    artboard_meta = artboard["meta"]
    root_children = artboard_node["artboard"]["children"]
    text_nodes, frame_nodes = walk_artboard_nodes(root_children)
    if not text_nodes:
        fail(
            "Adobe XD text extraction produced 0 text nodes for "
            f"artboard '{artboard_meta['name']}'. Refusing to write empty spec."
        )
    section_bbox = {
        "x": safe_round_3(artboard_meta["x"]),
        "y": safe_round_3(artboard_meta["y"]),
        "w": safe_round_3(artboard_meta["width"]),
        "h": safe_round_3(artboard_meta["height"]),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "section": {
            "id": artboard["id"],
            "name": artboard_meta["name"],
            "bbox": section_bbox,
            "_extra": None,
        },
        "text_nodes": text_nodes,
        "frame_nodes": frame_nodes,
        "vector_nodes": [],
        "interactions": [],
        "images": {},
        "_meta": {
            "provider": "xd-web-spec",
            "source_artboard": artboard_meta["name"],
            "output_section": section_name,
        },
    }


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def append_ledger(ledger_path: Path, section_name: str) -> None:
    root = find_project_root()
    cmd = [
        sys.executable,
        str(root / "tools" / "workflow-ledger.py"),
        "--ledger",
        str(ledger_path),
        "append",
        "--step",
        "extract",
        "--provider",
        "xd-web-spec",
        "--section",
        section_name,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(root))
    if proc.returncode != 0:
        fail((proc.stdout + proc.stderr).strip() or "workflow-ledger append failed")


def capture_from_url(url: str) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        fail(f"Playwright is required for --url mode: {exc}")

    captured_files: list[Path] = []
    with TemporaryDirectory(prefix="xd_capture_") as tmp_dir:
        output_dir = Path(tmp_dir)

        def on_response(response) -> None:
            try:
                content_type = response.headers.get("content-type", "")
                if response.status != 200:
                    return
                if "json" not in content_type and "cdn-sharing.adobecc.com" not in response.url:
                    return
                body = response.body()
                if not body:
                    return
                try:
                    payload = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return
                path = output_dir / f"resp_{len(captured_files):03d}.json"
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                captured_files.append(path)
            except Exception:
                return

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.on("response", on_response)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(8000)
            title = page.title()
            body_text = page.locator("body").inner_text(timeout=5000)
            if detect_password_gate(title, body_text):
                browser.close()
                fail("Adobe XD share link is password protected")
            browser.close()

        payloads: list[dict] = []
        for path in captured_files:
            payload = load_json_file(path, tolerant=True)
            if payload is None:
                continue
            if is_design_payload(payload):
                payloads.append(payload)
        if not payloads:
            fail("No Adobe XD artboard payload captured from share link")
        return payloads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract normalized section spec from Adobe XD")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="Adobe XD share URL")
    source.add_argument("--capture-dir", help="Directory containing captured Adobe XD JSON payloads")
    parser.add_argument("--artboard", help="Artboard name")
    parser.add_argument("--list-artboards", action="store_true", help="Print artboard names and sizes")
    parser.add_argument("--section", help="Output section name")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--ledger", help="Workflow ledger path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payloads = capture_from_url(args.url) if args.url else load_capture_payloads(Path(args.capture_dir))
    if args.list_artboards:
        return list_artboards(payloads)
    if not args.output:
        fail("--output is required unless --list-artboards is used")
    if not args.section:
        fail("--section is required unless --list-artboards is used")
    if not args.artboard:
        fail("--artboard is required unless --list-artboards is used")

    artboard = select_artboard(payloads, args.artboard)
    payload = build_spec_payload(artboard, args.section)
    output_path = Path(args.output) / f"{args.section}_spec.json"
    atomic_write_json(output_path, payload)
    if args.ledger:
        append_ledger(Path(args.ledger), args.section)
    print(str(output_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())

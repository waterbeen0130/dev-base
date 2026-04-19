#!/usr/bin/env python3
"""Extract a Figma section into stable spec.json + spec.md outputs.

Usage:
  python3 tools/figma-section-spec.py \
    --file-key <FILE_KEY> \
    --node-id <NODE_ID> \
    --output <OUTPUT_DIR> \
    [--name <PREFIX>]
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib import error, parse, request


FIGMA_API_BASE = "https://api.figma.com"
SCHEMA_VERSION_V2 = "2.0.0"
V2_TOP_LEVEL_NULL_KEYS = ("_extra",)
V2_SECTION_NULL_KEYS = ("_extra",)
V2_TEXT_NODE_NULL_KEYS = (
    "characterStyleOverrides",
    "textCase",
    "textDecoration",
    "paragraphSpacing",
    "paragraphIndent",
    "rules_conflict",
    "_extra",
)
V2_FRAME_NODE_NULL_KEYS = (
    "fills_v2",
    "effects",
    "strokes",
    "strokeWeight",
    "strokeAlign",
    "layoutSizingHorizontal",
    "layoutSizingVertical",
    "layoutGrow",
    "layoutAlign",
    "constraints",
    "rules_conflict",
    "_extra",
)
V2_VECTOR_NODE_NULL_KEYS = (
    "rules_conflict",
    "_extra",
)


@dataclass
class ExtractionResult:
    section: dict
    text_nodes: list[dict]
    frame_nodes: list[dict]
    vector_nodes: list[dict]
    interactions: list[dict]
    image_refs: set[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract normalized section spec from Figma node")
    parser.add_argument("--file-key", help="Figma file key")
    parser.add_argument("--node-id", help="Figma node id (e.g. 842:37)")
    parser.add_argument("--from-spec", help="Offline mode: existing *_spec.json path (no Figma API call)")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--name", help="Output filename prefix (default: section_<node-id>)")
    parser.add_argument("--codegen", action="store_true", help="Generate deterministic base HTML/CSS and tokens.json")
    args = parser.parse_args()

    if args.from_spec:
        if args.file_key or args.node_id:
            fail("--from-spec cannot be combined with --file-key/--node-id")
    else:
        if not args.file_key or not args.node_id:
            fail("--file-key and --node-id are required unless --from-spec is provided")

    return args


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def require_figma_token() -> str:
    token = os.environ.get("FIGMA_TOKEN", "").strip()
    if not token:
        fail("FIGMA_TOKEN environment variable is required")
    return token


def api_get_json(path: str, token: str) -> dict:
    url = f"{FIGMA_API_BASE}{path}"
    req = request.Request(url, headers={"X-Figma-Token": token, "Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        fail(f"Figma API request failed ({exc.code}): {path}\n{body}".strip())
    except error.URLError as exc:
        fail(f"Figma API request failed: {path}\n{exc}")

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON from Figma API: {path}\n{exc}")


def to_hex_from_rgb(color: dict | None) -> str | None:
    if not isinstance(color, dict):
        return None
    try:
        r = int(round(float(color.get("r", 0.0)) * 255))
        g = int(round(float(color.get("g", 0.0)) * 255))
        b = int(round(float(color.get("b", 0.0)) * 255))
    except (TypeError, ValueError):
        return None

    r = min(255, max(0, r))
    g = min(255, max(0, g))
    b = min(255, max(0, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def round_float_3(value: object, *, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        rounded = round(float(value), 3)
    except (TypeError, ValueError):
        return default
    return rounded


def normalize_unit_opacity(value: object, *, default: float = 1.0) -> float:
    opacity = round_float_3(value, default=default)
    if opacity is None:
        return float(default)
    if opacity < 0:
        return 0.0
    if opacity > 1:
        return 1.0
    return opacity


def extract_blend_mode(node: dict) -> str:
    value = node.get("blendMode")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "PASS_THROUGH"


def extract_node_opacity(node: dict) -> float:
    return normalize_unit_opacity(node.get("opacity"), default=1.0)


def normalize_gradient_stops(stops: object) -> list[dict]:
    if not isinstance(stops, list):
        return []
    normalized: list[dict] = []
    for stop in stops:
        if not isinstance(stop, dict):
            continue
        color = to_hex_from_rgb(stop.get("color"))
        if color is None:
            continue
        position = round_float_3(stop.get("position"), default=0.0)
        normalized.append(
            {
                "position": position if position is not None else 0.0,
                "color": color,
            }
        )
    return normalized


def normalize_gradient_handles(handles: object) -> list[dict]:
    if not isinstance(handles, list):
        return []
    normalized: list[dict] = []
    for handle in handles:
        if not isinstance(handle, dict):
            continue
        x = round_float_3(handle.get("x"), default=0.0)
        y = round_float_3(handle.get("y"), default=0.0)
        normalized.append({"x": x if x is not None else 0.0, "y": y if y is not None else 0.0})
    return normalized


def normalize_image_transform(transform: object) -> list[list[float]] | None:
    if not isinstance(transform, list):
        return None
    normalized_rows: list[list[float]] = []
    for row in transform:
        if not isinstance(row, list):
            return None
        normalized_row: list[float] = []
        for value in row:
            rounded = round_float_3(value)
            if rounded is None:
                return None
            normalized_row.append(rounded)
        normalized_rows.append(normalized_row)
    return normalized_rows


def extract_frame_fills_v2(fills: list | None, image_refs: set[str]) -> list[dict]:
    if not isinstance(fills, list):
        return []

    parsed: list[dict] = []
    for fill in fills:
        if not isinstance(fill, dict):
            continue
        fill_type = fill.get("type")
        if fill_type == "SOLID":
            color = to_hex_from_rgb(fill.get("color"))
            if color is None:
                continue
            parsed.append(
                {
                    "type": "SOLID",
                    "color": color,
                    "opacity": normalize_unit_opacity(fill.get("opacity"), default=1.0),
                }
            )
            continue

        if fill_type in {"GRADIENT_LINEAR", "GRADIENT_RADIAL"}:
            parsed.append(
                {
                    "type": fill_type,
                    "opacity": normalize_unit_opacity(fill.get("opacity"), default=1.0),
                    "gradientStops": normalize_gradient_stops(fill.get("gradientStops")),
                    "gradientHandlePositions": normalize_gradient_handles(fill.get("gradientHandlePositions")),
                }
            )
            continue

        if fill_type == "IMAGE":
            image_fill: dict[str, object] = {"type": "IMAGE"}
            image_ref = fill.get("imageRef")
            if isinstance(image_ref, str) and image_ref:
                image_fill["imageRef"] = image_ref
                image_refs.add(image_ref)
            scale_mode = fill.get("scaleMode")
            if isinstance(scale_mode, str) and scale_mode:
                image_fill["scaleMode"] = scale_mode
            image_transform = normalize_image_transform(fill.get("imageTransform"))
            if image_transform is not None:
                image_fill["imageTransform"] = image_transform
            scaling_factor = round_float_3(fill.get("scalingFactor"))
            if scaling_factor is not None:
                image_fill["scalingFactor"] = scaling_factor
            rotation = round_float_3(fill.get("rotation"))
            if rotation is not None:
                image_fill["rotation"] = rotation
            image_fill["opacity"] = normalize_unit_opacity(fill.get("opacity"), default=1.0)
            parsed.append(image_fill)

    return parsed


def extract_effects(effects: object) -> list[dict]:
    if not isinstance(effects, list):
        return []

    parsed: list[dict] = []
    for effect in effects:
        if not isinstance(effect, dict):
            continue
        effect_type = effect.get("type")
        if effect_type not in {"DROP_SHADOW", "INNER_SHADOW", "LAYER_BLUR", "BACKGROUND_BLUR"}:
            continue

        radius = round_float_3(effect.get("radius"), default=0.0)
        item: dict[str, object] = {
            "type": effect_type,
            "visible": bool(effect.get("visible", True)),
            "radius": radius if radius is not None else 0.0,
        }

        if effect_type in {"DROP_SHADOW", "INNER_SHADOW"}:
            color = to_hex_from_rgb(effect.get("color"))
            if color:
                item["color"] = color
            offset = effect.get("offset")
            if isinstance(offset, dict):
                item["offset"] = {
                    "x": round_float_3(offset.get("x"), default=0.0) or 0.0,
                    "y": round_float_3(offset.get("y"), default=0.0) or 0.0,
                }
            else:
                item["offset"] = {"x": 0.0, "y": 0.0}
            spread = round_float_3(effect.get("spread"))
            if spread is not None:
                item["spread"] = spread
            blend_mode = effect.get("blendMode")
            if isinstance(blend_mode, str) and blend_mode.strip():
                item["blendMode"] = blend_mode.strip()

        parsed.append(item)

    return parsed


def extract_text_color(fills: list | None) -> str | None:
    if not isinstance(fills, list):
        return None
    for fill in fills:
        if not isinstance(fill, dict):
            continue
        if fill.get("type") != "SOLID":
            continue
        color = to_hex_from_rgb(fill.get("color"))
        if color:
            return color
    return None


def extract_frame_fill(fills: list | None, image_refs: set[str]) -> str | None:
    if not isinstance(fills, list):
        return None

    for fill in fills:
        if not isinstance(fill, dict):
            continue

        kind = fill.get("type")
        if kind == "SOLID":
            color = to_hex_from_rgb(fill.get("color"))
            if color:
                return color

        if kind == "IMAGE":
            image_ref = fill.get("imageRef")
            if isinstance(image_ref, str) and image_ref:
                image_refs.add(image_ref)
                return image_ref

    return None


def safe_round_3(value) -> float | int | None:
    if value is None:
        return None
    try:
        rounded = round(float(value), 3)
    except (TypeError, ValueError):
        return None
    if rounded.is_integer():
        return int(rounded)
    return rounded


def compute_line_height_ratio(line_height_px, font_size):
    try:
        if line_height_px is None or font_size is None:
            return None
        denominator = float(font_size)
        if denominator == 0:
            return None
        return round(float(line_height_px) / denominator, 3)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def extract_bbox(node: dict) -> dict:
    bbox = node.get("absoluteBoundingBox") if isinstance(node, dict) else None
    if not isinstance(bbox, dict):
        return {"x": None, "y": None, "w": None, "h": None}
    return {
        "x": safe_round_3(bbox.get("x")),
        "y": safe_round_3(bbox.get("y")),
        "w": safe_round_3(bbox.get("width")),
        "h": safe_round_3(bbox.get("height")),
    }


def build_character_segments(node: dict) -> list[dict]:
    chars = node.get("characters", "")
    if not isinstance(chars, str) or not chars:
        return []

    overrides = node.get("characterStyleOverrides", []) or []
    table = node.get("styleOverrideTable", {}) or {}
    base_style = {**(node.get("style") or {})}
    base_fills = node.get("fills") or []

    segments: list[dict] = []
    previous_resolved = None

    def resolve(override_id):
        nonlocal previous_resolved
        if override_id == 0 or override_id is None:
            resolved = {**base_style, "fills": base_fills}
        else:
            override = table.get(str(override_id), {}) or {}
            override_style = override.get("style") or {}
            override_fills = override.get("fills")
            base_for_merge = previous_resolved if previous_resolved is not None else {**base_style, "fills": base_fills}
            resolved = {**base_for_merge, **override_style}
            if override_fills is not None:
                resolved["fills"] = override_fills
        previous_resolved = resolved
        return resolved

    override_ids = [overrides[i] if i < len(overrides) else 0 for i in range(len(chars))]

    i = 0
    while i < len(chars):
        j = i
        override_id = override_ids[i]
        while j + 1 < len(chars) and override_ids[j + 1] == override_id:
            j += 1
        resolved = resolve(override_id)
        segments.append(
            {
                "start": i,
                "end": j + 1,
                "text": chars[i : j + 1],
                "fontFamily": resolved.get("fontFamily"),
                "fontSize": safe_round_3(resolved.get("fontSize")),
                "fontWeight": safe_round_3(resolved.get("fontWeight")),
                "lineHeightPx": safe_round_3(resolved.get("lineHeightPx")),
                "letterSpacing": safe_round_3(resolved.get("letterSpacing")),
                "color": extract_text_color(resolved.get("fills")),
            }
        )
        i = j + 1

    return segments


def extract_corner_radius(node: dict, bbox: dict) -> dict:
    cr = node.get("cornerRadius")
    rcr = node.get("rectangleCornerRadii")
    hint = None
    w = bbox.get("w") or 0
    h = bbox.get("h") or 0
    if cr is not None and w and h:
        if cr >= min(w, h) / 2:
            hint = "50%"
    return {
        "cornerRadius": safe_round_3(cr),
        "rectangleCornerRadii": [safe_round_3(value) for value in rcr] if isinstance(rcr, list) else None,
        "border_radius_hint": hint,
    }


def normalize_text_node(node: dict) -> dict:
    style = node.get("style") if isinstance(node.get("style"), dict) else {}
    font_size = style.get("fontSize")
    line_height_px = style.get("lineHeightPx")

    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "characters": node.get("characters") if isinstance(node.get("characters"), str) else "",
        "fontFamily": style.get("fontFamily"),
        "fontSize": safe_round_3(font_size),
        "fontWeight": safe_round_3(style.get("fontWeight")),
        "lineHeightPx": safe_round_3(line_height_px),
        "lineHeightRatio": compute_line_height_ratio(line_height_px, font_size),
        "letterSpacing": safe_round_3(style.get("letterSpacing")),
        "color": extract_text_color(node.get("fills")),
        "opacity": extract_node_opacity(node),
        "blendMode": extract_blend_mode(node),
        "effects": extract_effects(node.get("effects")),
        "textAlignHorizontal": style.get("textAlignHorizontal"),
        "textAlignVertical": style.get("textAlignVertical"),
        "bbox": extract_bbox(node),
        "character_segments": build_character_segments(node),
    }


def normalize_frame_node(node: dict, image_refs: set[str]) -> dict:
    bbox = extract_bbox(node)
    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "bbox": bbox,
        "layoutMode": node.get("layoutMode"),
        "paddingTop": safe_round_3(node.get("paddingTop")),
        "paddingRight": safe_round_3(node.get("paddingRight")),
        "paddingBottom": safe_round_3(node.get("paddingBottom")),
        "paddingLeft": safe_round_3(node.get("paddingLeft")),
        "itemSpacing": safe_round_3(node.get("itemSpacing")),
        "primaryAxisAlignItems": node.get("primaryAxisAlignItems"),
        "counterAxisAlignItems": node.get("counterAxisAlignItems"),
        "fills": extract_frame_fill(node.get("fills"), image_refs),
        "fills_v2": extract_frame_fills_v2(node.get("fills"), image_refs),
        "effects": extract_effects(node.get("effects")),
        "opacity": extract_node_opacity(node),
        "blendMode": extract_blend_mode(node),
        **extract_corner_radius(node, bbox),
    }


def extract_url_interactions(node: dict) -> list[dict]:
    interactions = node.get("interactions")
    if not isinstance(interactions, list):
        return []

    found = []
    node_id = node.get("id")
    for interaction in interactions:
        if not isinstance(interaction, dict):
            continue

        actions = interaction.get("actions")
        if isinstance(actions, dict):
            actions = [actions]
        if actions is None and isinstance(interaction.get("action"), dict):
            actions = [interaction.get("action")]

        if not isinstance(actions, list):
            continue

        for action in actions:
            if not isinstance(action, dict):
                continue
            if action.get("type") != "URL":
                continue

            url = action.get("url")
            url = url.strip() if isinstance(url, str) else ""
            found.append(
                {
                    "node_id": node_id,
                    "url": url,
                    "openInNewTab": bool(action.get("openInNewTab", False)),
                }
            )

    return found


VECTOR_NODE_TYPES = {
    "VECTOR",
    "BOOLEAN_OPERATION",
    "STAR",
    "LINE",
    "ELLIPSE",
    "REGULAR_POLYGON",
}


def normalize_vector_node(node: dict) -> dict:
    """Capture vector-style graphic nodes so AI consumers don't silently miss
    logo/decorative elements (e.g. '1%' rendered as paths instead of text)."""
    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "type": node.get("type"),
        "bbox": extract_bbox(node),
        "fills_color": extract_text_color(node.get("fills")),
        "opacity": extract_node_opacity(node),
    }


def walk_and_extract(root: dict) -> ExtractionResult:
    section = {
        "id": root.get("id"),
        "name": root.get("name"),
        "bbox": extract_bbox(root),
    }

    text_nodes: list[dict] = []
    frame_nodes: list[dict] = []
    vector_nodes: list[dict] = []
    interactions: list[dict] = []
    image_refs: set[str] = set()

    def walk(node: dict, *, parent_id=None) -> None:
        if not isinstance(node, dict):
            return

        interactions.extend(extract_url_interactions(node))

        node_id = node.get("id")
        node_type = node.get("type")
        if node_type == "TEXT":
            normalized = normalize_text_node(node)
            normalized["parent_id"] = parent_id
            text_nodes.append(normalized)
        elif node_type == "FRAME":
            normalized = normalize_frame_node(node, image_refs)
            normalized["parent_id"] = parent_id
            frame_nodes.append(normalized)
        elif node_type in VECTOR_NODE_TYPES:
            normalized = normalize_vector_node(node)
            normalized["parent_id"] = parent_id
            vector_nodes.append(normalized)

        children = node.get("children")
        if isinstance(children, list):
            for child in children:
                walk(child, parent_id=node_id)

    walk(root, parent_id=None)

    return ExtractionResult(
        section=section,
        text_nodes=text_nodes,
        frame_nodes=frame_nodes,
        vector_nodes=vector_nodes,
        interactions=interactions,
        image_refs=image_refs,
    )


def fetch_node_document(file_key: str, node_id: str, token: str) -> dict:
    query = parse.urlencode({"ids": node_id, "depth": 8})
    data = api_get_json(f"/v1/files/{parse.quote(file_key)}/nodes?{query}", token)

    nodes = data.get("nodes")
    if not isinstance(nodes, dict):
        fail("Invalid Figma response: 'nodes' is missing")

    entry = nodes.get(node_id)
    if not isinstance(entry, dict):
        # fallback: sometimes ID keys are normalized by API
        for key, candidate in nodes.items():
            if key == node_id and isinstance(candidate, dict):
                entry = candidate
                break

    if not isinstance(entry, dict):
        fail(f"Figma node not found in response: {node_id}")

    doc = entry.get("document")
    if not isinstance(doc, dict):
        fail(f"Figma response missing document for node: {node_id}")

    return doc


def fetch_images_map(file_key: str, token: str, image_refs: set[str]) -> dict[str, str]:
    if not image_refs:
        return {}

    data = api_get_json(f"/v1/files/{parse.quote(file_key)}/images", token)
    # Figma API wraps the ref→url map under `meta.images`; fall back to `images`
    # for forward compatibility in case the shape ever changes.
    meta = data.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("images"), dict):
        images = meta["images"]
    else:
        images = data.get("images")
    if not isinstance(images, dict):
        return {}

    result: dict[str, str] = {}
    for ref in sorted(image_refs):
        url = images.get(ref)
        if isinstance(url, str) and url:
            result[ref] = url
    return result


def atomic_write_text(path: str, text: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=directory or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def atomic_write_json(path: str, data: dict) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=directory or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def ensure_null_keys(target: object, keys: tuple[str, ...]) -> None:
    if not isinstance(target, dict):
        return
    for key in keys:
        target.setdefault(key, None)


def ensure_v2_payload_shape(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return payload

    payload["schema_version"] = SCHEMA_VERSION_V2
    ensure_null_keys(payload, V2_TOP_LEVEL_NULL_KEYS)

    section = payload.get("section")
    ensure_null_keys(section, V2_SECTION_NULL_KEYS)

    text_nodes = payload.get("text_nodes")
    if isinstance(text_nodes, list):
        for node in text_nodes:
            ensure_null_keys(node, V2_TEXT_NODE_NULL_KEYS)
            if isinstance(node, dict):
                node["effects"] = node.get("effects") if isinstance(node.get("effects"), list) else []
                node["opacity"] = normalize_unit_opacity(node.get("opacity"), default=1.0)
                node["blendMode"] = extract_blend_mode(node)

    frame_nodes = payload.get("frame_nodes")
    if isinstance(frame_nodes, list):
        for node in frame_nodes:
            ensure_null_keys(node, V2_FRAME_NODE_NULL_KEYS)
            if isinstance(node, dict):
                node["fills_v2"] = node.get("fills_v2") if isinstance(node.get("fills_v2"), list) else []
                node["effects"] = node.get("effects") if isinstance(node.get("effects"), list) else []
                node["opacity"] = normalize_unit_opacity(node.get("opacity"), default=1.0)
                node["blendMode"] = extract_blend_mode(node)

    vector_nodes = payload.get("vector_nodes")
    if isinstance(vector_nodes, list):
        for node in vector_nodes:
            ensure_null_keys(node, V2_VECTOR_NODE_NULL_KEYS)

    return payload


def load_spec_payload(path_str: str) -> dict:
    path = Path(path_str)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"Failed to read spec JSON: {path}\n{exc}")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"Invalid spec JSON: {path}\n{exc}")
    if not isinstance(payload, dict):
        fail(f"Invalid spec JSON root (expected object): {path}")
    if not isinstance(payload.get("section"), dict):
        fail(f"Invalid spec JSON: missing section object ({path})")
    if not isinstance(payload.get("text_nodes"), list) or not isinstance(payload.get("frame_nodes"), list):
        fail(f"Invalid spec JSON: expected text_nodes/frame_nodes arrays ({path})")
    return payload


def extraction_result_from_payload(payload: dict) -> ExtractionResult:
    images = payload.get("images")
    image_refs = set(images.keys()) if isinstance(images, dict) else set()
    return ExtractionResult(
        section=payload.get("section", {}),
        text_nodes=payload.get("text_nodes", []),
        frame_nodes=payload.get("frame_nodes", []),
        vector_nodes=payload.get("vector_nodes", []),
        interactions=payload.get("interactions", []),
        image_refs=image_refs,
    )


def read_project_type(project_root: str | None = None) -> str | None:
    root = Path(project_root or os.getcwd())
    marker = root / ".project-type"
    try:
        value = marker.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return None
    if value in {"basic", "landing"}:
        return value
    return None


def tidy_line_height_ratio(raw_ratio: float) -> float:
    snap_step = 0.05
    tolerance = 0.03
    snapped = round(raw_ratio / snap_step) * snap_step
    if abs(raw_ratio - snapped) <= tolerance:
        return round(snapped, 2)
    return round(raw_ratio, 3)


def preprocess_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return payload

    text_nodes = payload.get("text_nodes")
    if not isinstance(text_nodes, list):
        text_nodes = []

    hints = payload.get("hints")
    if not isinstance(hints, dict):
        hints = {}
    hints["boxSizing"] = "global-reset-only"

    project_type = read_project_type()
    if project_type:
        hints["projectType"] = project_type

    font_counter = Counter()
    for node in text_nodes:
        if not isinstance(node, dict):
            continue
        family = node.get("fontFamily")
        if isinstance(family, str) and family.strip():
            font_counter[family.strip()] += 1
    if font_counter:
        hints["fontFamilyGlobal"] = sorted(font_counter.items(), key=lambda item: (-item[1], item[0]))[0][0]

    # NOTE: 8-digit color normalization from DSC-002 is skipped here because this extractor
    # already emits normalized 6-digit hex for extracted colors.
    for node in text_nodes:
        if not isinstance(node, dict):
            continue
        raw_ratio = compute_line_height_ratio(node.get("lineHeightPx"), node.get("fontSize"))
        if raw_ratio is None:
            continue
        node.setdefault("lineHeightRatioRaw", raw_ratio)
        node.setdefault("lineHeightRatioNormalized", tidy_line_height_ratio(raw_ratio))

    payload["hints"] = hints
    return payload


def default_name_from_spec_path(path_str: str) -> str:
    stem = Path(path_str).stem
    if stem.endswith("_spec"):
        return stem[: -len("_spec")]
    return stem or "section"


def section_slug(section_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", section_name.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "section"


def node_identifier(node: dict, prefix: str, index: int) -> str:
    node_id = node.get("id")
    if isinstance(node_id, str) and node_id.strip():
        return node_id.strip()
    return f"{prefix}@{index}"


def normalize_hex_color(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value.startswith("#"):
        return None
    digits = value[1:]
    if re.fullmatch(r"[0-9a-fA-F]{3}", digits):
        digits = "".join(ch * 2 for ch in digits)
    elif not re.fullmatch(r"[0-9a-fA-F]{6}", digits):
        return None
    return f"#{digits.lower()}"


def normalize_bbox_for_codegen(bbox: object) -> dict[str, float] | None:
    if not isinstance(bbox, dict):
        return None
    keys = ("x", "y", "w", "h")
    normalized: dict[str, float] = {}
    for key in keys:
        value = bbox.get(key)
        if not isinstance(value, (int, float)):
            return None
        normalized[key] = float(value)
    return normalized


def bbox_area_for_codegen(bbox: object) -> float | None:
    normalized = normalize_bbox_for_codegen(bbox)
    if not normalized:
        return None
    if normalized["w"] <= 0 or normalized["h"] <= 0:
        return None
    return normalized["w"] * normalized["h"]


def bbox_contains_for_codegen(outer_bbox: object, inner_bbox: object) -> bool:
    outer = normalize_bbox_for_codegen(outer_bbox)
    inner = normalize_bbox_for_codegen(inner_bbox)
    if not outer or not inner:
        return False
    return (
        outer["x"] <= inner["x"]
        and outer["y"] <= inner["y"]
        and outer["x"] + outer["w"] >= inner["x"] + inner["w"]
        and outer["y"] + outer["h"] >= inner["y"] + inner["h"]
    )


def infer_frame_parent_lookup(frame_nodes: list[dict]) -> dict[str, str | None]:
    parent_lookup: dict[str, str | None] = {}
    frame_ids = [node_identifier(frame, "frame", index) for index, frame in enumerate(frame_nodes)]
    frame_id_set = set(frame_ids)

    for index, frame in enumerate(frame_nodes):
        frame_id = frame_ids[index]
        declared_parent = frame.get("parent_id")
        if isinstance(declared_parent, str) and declared_parent.strip():
            parent = declared_parent.strip()
            parent_lookup[frame_id] = parent if parent in frame_id_set else None
            continue

        candidates: list[tuple[float, str]] = []
        for other_index, other in enumerate(frame_nodes):
            other_id = frame_ids[other_index]
            if other_id == frame_id:
                continue
            if not bbox_contains_for_codegen(other.get("bbox"), frame.get("bbox")):
                continue
            area = bbox_area_for_codegen(other.get("bbox"))
            if area is None:
                continue
            candidates.append((area, other_id))

        if candidates:
            candidates.sort(key=lambda item: item[0])
            parent_lookup[frame_id] = candidates[0][1]
        else:
            parent_lookup[frame_id] = None

    return parent_lookup


def infer_text_parent_lookup(text_nodes: list[dict], frame_nodes: list[dict]) -> dict[str, str | None]:
    parent_lookup: dict[str, str | None] = {}
    frame_ids = [node_identifier(frame, "frame", index) for index, frame in enumerate(frame_nodes)]
    frame_id_set = set(frame_ids)

    for index, text_node in enumerate(text_nodes):
        text_id = node_identifier(text_node, "text", index)
        declared_parent = text_node.get("parent_id")
        if isinstance(declared_parent, str) and declared_parent.strip():
            parent = declared_parent.strip()
            parent_lookup[text_id] = parent if parent in frame_id_set else None
            continue

        candidates: list[tuple[float, str]] = []
        for frame_index, frame in enumerate(frame_nodes):
            frame_id = frame_ids[frame_index]
            if not bbox_contains_for_codegen(frame.get("bbox"), text_node.get("bbox")):
                continue
            area = bbox_area_for_codegen(frame.get("bbox"))
            if area is None:
                continue
            candidates.append((area, frame_id))

        if candidates:
            candidates.sort(key=lambda item: item[0])
            parent_lookup[text_id] = candidates[0][1]
        else:
            parent_lookup[text_id] = None

    return parent_lookup


def normalize_text_for_html(raw_text: object) -> str:
    text = raw_text if isinstance(raw_text, str) else ""
    escaped = html.escape(text, quote=False)
    escaped = escaped.replace("\xa0", "&nbsp;")
    escaped = escaped.replace("\r\n", "\n").replace("\r", "\n")
    return escaped.replace("\n", "<br>")


def format_number(value: object, precision: int = 3) -> str:
    if not isinstance(value, (int, float)):
        return "0"
    numeric = float(value)
    if abs(numeric) < 1e-9:
        return "0"
    if numeric.is_integer():
        return str(int(numeric))
    text = f"{numeric:.{precision}f}".rstrip("0").rstrip(".")
    return text or "0"


def format_px(value: object, precision: int = 3) -> str:
    return f"{format_number(value, precision)}px"


def maybe_clamp_length(value: object) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    numeric = float(value)
    if abs(numeric) >= 100:
        minimum = numeric * 0.6
        maximum = numeric * 1.2
        return f"clamp({format_px(minimum)},{format_px(numeric)},{format_px(maximum)})"
    return format_px(numeric)


def border_radius_value(frame: dict) -> str | None:
    bbox = frame.get("bbox") if isinstance(frame.get("bbox"), dict) else {}
    width = bbox.get("w")
    height = bbox.get("h")
    corner_radius = frame.get("cornerRadius")
    hint = frame.get("border_radius_hint")
    if hint == "50%":
        return "50%"
    if isinstance(corner_radius, (int, float)):
        cr = float(corner_radius)
        if isinstance(width, (int, float)) and isinstance(height, (int, float)) and width == height and cr >= width / 2:
            return "50%"
        if int(round(cr)) in {999, 9999}:
            return "2em"
        return format_px(cr)
    return None


ALIGN_MAP = {
    "MIN": "flex-start",
    "MAX": "flex-end",
    "CENTER": "center",
    "SPACE_BETWEEN": "space-between",
    "STRETCH": "stretch",
}


def join_css_rule(selector: str, declarations: list[str]) -> str:
    return f"{selector}{{{''.join(f'{decl};' for decl in declarations)}}}"


def build_class_maps(result: ExtractionResult, section_name: str) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    slug = section_slug(section_name)
    frame_classes = {
        node_identifier(frame, "frame", index): f"{slug}_f{index}" for index, frame in enumerate(result.frame_nodes)
    }
    text_classes = {
        node_identifier(text, "text", index): f"{slug}_t{index}" for index, text in enumerate(result.text_nodes)
    }
    vector_classes = {
        node_identifier(vector, "vector", index): f"{slug}_v{index}" for index, vector in enumerate(result.vector_nodes)
    }
    return frame_classes, text_classes, vector_classes


def generate_base_html(result: ExtractionResult, section_name: str) -> str:
    slug = section_slug(section_name)
    frame_classes, text_classes, vector_classes = build_class_maps(result, section_name)

    frame_lookup = {
        node_identifier(frame, "frame", index): frame for index, frame in enumerate(result.frame_nodes)
    }
    text_lookup = {
        node_identifier(text, "text", index): text for index, text in enumerate(result.text_nodes)
    }
    vector_lookup = {
        node_identifier(vector, "vector", index): vector for index, vector in enumerate(result.vector_nodes)
    }

    frame_parent_lookup = infer_frame_parent_lookup(result.frame_nodes)
    text_parent_lookup = infer_text_parent_lookup(result.text_nodes, result.frame_nodes)

    children: dict[str | None, list[tuple[tuple[int, int], str, str]]] = defaultdict(list)

    def order_key(node_index: int, rank: int) -> tuple[int, int]:
        return (node_index, rank)

    for index, frame in enumerate(result.frame_nodes):
        frame_id = node_identifier(frame, "frame", index)
        parent = frame_parent_lookup.get(frame_id)
        children[parent].append((order_key(index, 0), "frame", frame_id))

    frame_id_set = set(frame_lookup.keys())
    for index, text_node in enumerate(result.text_nodes):
        text_id = node_identifier(text_node, "text", index)
        parent = text_parent_lookup.get(text_id)
        if parent not in frame_id_set:
            parent = None
        children[parent].append((order_key(index, 1), "text", text_id))

    for index, vector_node in enumerate(result.vector_nodes):
        vector_id = node_identifier(vector_node, "vector", index)
        declared_parent = vector_node.get("parent_id")
        parent = declared_parent.strip() if isinstance(declared_parent, str) and declared_parent.strip() in frame_id_set else None
        children[parent].append((order_key(index, 2), "vector", vector_id))

    for key in list(children.keys()):
        children[key].sort(key=lambda item: item[0])

    root_frame_id = None
    section_id = result.section.get("id")
    if isinstance(section_id, str) and section_id in frame_lookup:
        root_frame_id = section_id

    visited: set[tuple[str, str]] = set()
    lines: list[str] = [f'<div class="{slug}">']

    def render(kind: str, node_id: str, depth: int) -> None:
        marker = (kind, node_id)
        if marker in visited:
            return
        visited.add(marker)

        indent = "  " * depth
        if kind == "frame":
            class_name = frame_classes.get(node_id, "")
            lines.append(f'{indent}<div class="{class_name}">')
            for _, child_kind, child_id in children.get(node_id, []):
                render(child_kind, child_id, depth + 1)
            lines.append(f"{indent}</div>")
            return

        if kind == "text":
            class_name = text_classes.get(node_id, "")
            text_node = text_lookup.get(node_id, {})
            content = normalize_text_for_html(text_node.get("characters"))
            lines.append(f'{indent}<span class="{class_name}">{content}</span>')
            return

        if kind == "vector":
            class_name = vector_classes.get(node_id, "")
            vector_node = vector_lookup.get(node_id, {})
            alt_text = vector_node.get("name") if isinstance(vector_node.get("name"), str) else node_id
            lines.append(f'{indent}<img class="{class_name}" src="" alt="{html.escape(alt_text, quote=True)}"/>')

    if root_frame_id:
        render("frame", root_frame_id, 1)

    for _, kind, node_id in children.get(None, []):
        render(kind, node_id, 1)

    for frame_id in sorted(frame_lookup.keys()):
        render("frame", frame_id, 1)
    for text_id in sorted(text_lookup.keys()):
        render("text", text_id, 1)
    for vector_id in sorted(vector_lookup.keys()):
        render("vector", vector_id, 1)

    lines.append("</div>")
    return "\n".join(lines) + "\n"


def generate_base_css(result: ExtractionResult, section_name: str) -> str:
    frame_classes, text_classes, vector_classes = build_class_maps(result, section_name)
    lines: list[str] = []

    for index, frame in enumerate(result.frame_nodes):
        frame_id = node_identifier(frame, "frame", index)
        selector = f".{frame_classes[frame_id]}"
        declarations: list[str] = []

        layout_mode = frame.get("layoutMode")
        mode = layout_mode.upper() if isinstance(layout_mode, str) else "NONE"
        spacing = frame.get("itemSpacing")

        if mode == "HORIZONTAL":
            declarations.append("display:flex")
            declarations.append("flex-direction:row")
            if isinstance(spacing, (int, float)):
                declarations.append(f"gap:{format_px(spacing)}")
        elif mode == "VERTICAL":
            declarations.append("display:flex")
            declarations.append("flex-direction:column")
        else:
            declarations.append("display:block")

        main_align = frame.get("primaryAxisAlignItems")
        if isinstance(main_align, str) and main_align in ALIGN_MAP and mode in {"HORIZONTAL", "VERTICAL"}:
            declarations.append(f"justify-content:{ALIGN_MAP[main_align]}")

        cross_align = frame.get("counterAxisAlignItems")
        if isinstance(cross_align, str) and cross_align in ALIGN_MAP and mode in {"HORIZONTAL", "VERTICAL"}:
            declarations.append(f"align-items:{ALIGN_MAP[cross_align]}")

        paddings = [frame.get("paddingTop"), frame.get("paddingRight"), frame.get("paddingBottom"), frame.get("paddingLeft")]
        if any(value is not None for value in paddings):
            padding_values = [maybe_clamp_length(value) if value is not None else "0" for value in paddings]
            declarations.append(f"padding:{' '.join(padding_values)}")

        fill_color = normalize_hex_color(frame.get("fills"))
        if fill_color:
            declarations.append(f"background-color:{fill_color}")

        opacity = frame.get("opacity")
        if isinstance(opacity, (int, float)):
            declarations.append(f"opacity:{format_number(opacity)}")

        border_radius = border_radius_value(frame)
        if border_radius:
            declarations.append(f"border-radius:{border_radius}")

        lines.append(join_css_rule(selector, declarations))

        if mode == "VERTICAL" and isinstance(spacing, (int, float)) and spacing != 0:
            lines.append(join_css_rule(f"{selector} > *", [f"margin-bottom:{format_px(spacing)}"]))
            lines.append(join_css_rule(f"{selector} > *:last-child", ["margin-bottom:0"]))

    for index, text_node in enumerate(result.text_nodes):
        text_id = node_identifier(text_node, "text", index)
        selector = f".{text_classes[text_id]}"
        declarations: list[str] = []

        color = normalize_hex_color(text_node.get("color"))
        if color:
            declarations.append(f"color:{color}")

        font_family = text_node.get("fontFamily")
        if isinstance(font_family, str) and font_family.strip():
            declarations.append(f'font-family:"{font_family.strip()}"')

        font_size = text_node.get("fontSize")
        if isinstance(font_size, (int, float)):
            declarations.append(f"font-size:{format_px(font_size)}")

        font_weight = text_node.get("fontWeight")
        if isinstance(font_weight, (int, float)):
            declarations.append(f"font-weight:{int(round(float(font_weight)))}")

        ratio = compute_line_height_ratio(text_node.get("lineHeightPx"), font_size)
        if ratio is None and isinstance(text_node.get("lineHeightRatio"), (int, float)):
            ratio = float(text_node["lineHeightRatio"])
        if isinstance(ratio, (int, float)):
            declarations.append(f"line-height:{format_number(round(float(ratio), 2), precision=2)}")

        letter_spacing = text_node.get("letterSpacing")
        if isinstance(letter_spacing, (int, float)) and isinstance(font_size, (int, float)) and float(font_size) != 0:
            em_value = float(letter_spacing) / float(font_size)
            declarations.append(f"letter-spacing:{format_number(round(em_value, 3), precision=3)}em")

        text_align_horizontal = text_node.get("textAlignHorizontal")
        if isinstance(text_align_horizontal, str):
            align = {"LEFT": "left", "CENTER": "center", "RIGHT": "right", "JUSTIFIED": "justify"}.get(text_align_horizontal)
            if align:
                declarations.append(f"text-align:{align}")

        opacity = text_node.get("opacity")
        if isinstance(opacity, (int, float)):
            declarations.append(f"opacity:{format_number(opacity)}")

        lines.append(join_css_rule(selector, declarations))

    for index, vector_node in enumerate(result.vector_nodes):
        vector_id = node_identifier(vector_node, "vector", index)
        selector = f".{vector_classes[vector_id]}"
        declarations: list[str] = ["display:block"]

        bbox = vector_node.get("bbox")
        if isinstance(bbox, dict):
            width = bbox.get("w")
            height = bbox.get("h")
            if isinstance(width, (int, float)):
                declarations.append(f"width:{format_px(width)}")
            if isinstance(height, (int, float)):
                declarations.append(f"height:{format_px(height)}")

        lines.append(join_css_rule(selector, declarations))

    return "\n".join(lines) + ("\n" if lines else "")


def generate_tokens(result: ExtractionResult) -> dict:
    color_counter: Counter[str] = Counter()

    for frame in result.frame_nodes:
        color = normalize_hex_color(frame.get("fills"))
        if color:
            color_counter[color] += 1

    for text_node in result.text_nodes:
        color = normalize_hex_color(text_node.get("color"))
        if color:
            color_counter[color] += 1

    for vector_node in result.vector_nodes:
        color = normalize_hex_color(vector_node.get("fills_color"))
        if color:
            color_counter[color] += 1

    colors: dict[str, str] = {}
    for index, color in enumerate(sorted([hex_color for hex_color, count in color_counter.items() if count >= 3]), start=1):
        colors[f"--color-{index}"] = color

    typography_groups: dict[tuple[float, int], list[dict]] = defaultdict(list)
    for node in result.text_nodes:
        font_size = node.get("fontSize")
        font_weight = node.get("fontWeight")
        if not isinstance(font_size, (int, float)) or not isinstance(font_weight, (int, float)):
            continue
        key = (float(font_size), int(round(float(font_weight))))
        typography_groups[key].append(node)

    typography: dict[str, str] = {}
    token_index = 1
    for key in sorted(typography_groups.keys()):
        nodes = typography_groups[key]
        if len(nodes) < 2:
            continue
        font_size, font_weight = key
        exemplar = nodes[0]
        declaration_parts = [f"font-weight: {font_weight};", f"font-size: {format_px(font_size)};"]
        ratio = compute_line_height_ratio(exemplar.get("lineHeightPx"), font_size)
        if isinstance(ratio, (int, float)):
            declaration_parts.append(f"line-height: {format_number(round(float(ratio), 2), precision=2)};")
        typography[f"--font-{token_index}"] = " ".join(declaration_parts)
        token_index += 1

    return {"colors": colors, "typography": typography}


def md_cell(value) -> str:
    if value is None:
        text = ""
    elif isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)

    text = text.replace("|", r"\|")
    text = text.replace("\u2028", r"\u2028")
    text = text.replace("\xa0", r"\xa0")
    text = text.replace("\r\n", r"\n").replace("\n", r"\n")
    return text


def render_table(columns: list[str], rows: list[dict]) -> str:
    lines = []
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")

    for row in rows:
        lines.append("| " + " | ".join(md_cell(row.get(col)) for col in columns) + " |")

    return "\n".join(lines)


def render_markdown(payload: dict, node_id: str) -> str:
    section = payload.get("section", {})
    text_nodes = payload.get("text_nodes", [])
    frame_nodes = payload.get("frame_nodes", [])
    interactions = payload.get("interactions", [])
    images = payload.get("images", {})

    lines: list[str] = []
    lines.append(f"> AUTO-GENERATED FROM Figma node {node_id} — DO NOT EDIT MANUALLY")
    lines.append("> 이 spec의 모든 행을 빠짐없이 CSS로 표현하세요")
    lines.append(">")
    lines.append("> ⚠️ 텍스트 byte-exact 필수: text_nodes 표의 characters 열은 Figma 원본을 그대로 보존해야 합니다.")
    lines.append("> - 줄바꿈 \\n/\\r/\\r\\n → <br/>로 변환 (공백 없이)")
    lines.append("> - non-breaking space \\xa0 → &nbsp;")
    lines.append("> - 반복 텍스트는 횟수·공백까지 그대로 유지 (AI 축약 금지)")
    lines.append("> - 끝 공백·선행 개행도 보존")
    lines.append("> - 표의 characters가 길어 markdown pipe(|) 렌더링 문제로 잘린 것처럼 보이면 반드시 _spec.json의 text_nodes[].characters를 직접 읽으세요")
    lines.append("")

    lines.append("## section")
    section_rows = [
        {
            "id": section.get("id"),
            "name": section.get("name"),
            "bbox": section.get("bbox"),
        }
    ]
    lines.append(render_table(["id", "name", "bbox"], section_rows))
    lines.append("")

    lines.append(f"## text_nodes ({len(text_nodes)})")
    text_columns = [
        "id",
        "name",
        "characters",
        "fontFamily",
        "fontSize",
        "fontWeight",
        "lineHeightPx",
        "lineHeightRatio",
        "letterSpacing",
        "color",
        "opacity",
        "blendMode",
        "effects",
        "textAlignHorizontal",
        "textAlignVertical",
        "bbox",
        "parent_id",
        "character_segments",
    ]
    lines.append(render_table(text_columns, text_nodes))
    lines.append("")

    lines.append(f"## frame_nodes ({len(frame_nodes)})")
    frame_columns = [
        "id",
        "name",
        "bbox",
        "layoutMode",
        "paddingTop",
        "paddingRight",
        "paddingBottom",
        "paddingLeft",
        "itemSpacing",
        "primaryAxisAlignItems",
        "counterAxisAlignItems",
        "fills",
        "fills_v2",
        "effects",
        "opacity",
        "blendMode",
        "cornerRadius",
        "rectangleCornerRadii",
        "border_radius_hint",
        "parent_id",
    ]
    lines.append(render_table(frame_columns, frame_nodes))
    lines.append("")

    vector_nodes = payload.get("vector_nodes", [])
    lines.append(f"## vector_nodes ({len(vector_nodes)})")
    lines.append("> ⚠️ Non-text graphic nodes (logos, icons, decorative shapes). MUST be exported as image and inserted as `<img>` — never reconstruct as text/HTML.")
    vector_columns = ["id", "name", "type", "bbox", "fills_color", "opacity", "parent_id"]
    lines.append(render_table(vector_columns, vector_nodes))
    lines.append("")

    lines.append(f"## interactions ({len(interactions)})")
    interaction_columns = ["node_id", "url", "openInNewTab"]
    lines.append(render_table(interaction_columns, interactions))
    lines.append("")

    image_rows = [{"imageRef": key, "url": value} for key, value in images.items()]
    lines.append(f"## images ({len(image_rows)})")
    lines.append(render_table(["imageRef", "url"], image_rows))
    lines.append("")

    return "\n".join(lines)


def default_name(node_id: str) -> str:
    return f"section_{node_id.replace(':', '_')}"


def main() -> int:
    args = parse_args()
    if args.from_spec:
        payload = load_spec_payload(args.from_spec)
        payload["schema_version"] = SCHEMA_VERSION_V2
        if not isinstance(payload.get("vector_nodes"), list):
            payload["vector_nodes"] = []
        if not isinstance(payload.get("interactions"), list):
            payload["interactions"] = []
        images = payload.get("images")
        payload["images"] = {key: images[key] for key in sorted(images.keys())} if isinstance(images, dict) else {}
        payload = ensure_v2_payload_shape(payload)
        payload = preprocess_payload(payload)
        extracted = extraction_result_from_payload(payload)
        source_node_id = payload.get("section", {}).get("id")
        node_id = source_node_id if isinstance(source_node_id, str) and source_node_id.strip() else "from-spec"
        default_output_name = default_name_from_spec_path(args.from_spec)
    else:
        token = require_figma_token()
        root = fetch_node_document(args.file_key, args.node_id, token)
        extracted = walk_and_extract(root)
        images = fetch_images_map(args.file_key, token, extracted.image_refs)
        payload = {
            "schema_version": SCHEMA_VERSION_V2,
            "section": extracted.section,
            "text_nodes": extracted.text_nodes,
            "frame_nodes": extracted.frame_nodes,
            "vector_nodes": extracted.vector_nodes,
            "interactions": extracted.interactions,
            "images": {key: images[key] for key in sorted(images.keys())},
        }
        payload = ensure_v2_payload_shape(payload)
        payload = preprocess_payload(payload)
        extracted = extraction_result_from_payload(payload)
        node_id = args.node_id
        default_output_name = default_name(args.node_id)

    name = args.name.strip() if isinstance(args.name, str) and args.name.strip() else default_output_name
    os.makedirs(args.output, exist_ok=True)
    json_path = os.path.join(args.output, f"{name}_spec.json")
    md_path = os.path.join(args.output, f"{name}_spec.md")

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_markdown(payload, node_id))

    print(json_path)
    print(md_path)

    if args.codegen:
        html_path = os.path.join(args.output, f"{name}_base.html")
        css_path = os.path.join(args.output, f"{name}_base.css")
        tokens_path = os.path.join(args.output, "tokens.json")

        atomic_write_text(html_path, generate_base_html(extracted, name))
        atomic_write_text(css_path, generate_base_css(extracted, name))
        atomic_write_json(tokens_path, generate_tokens(extracted))

        print(html_path)
        print(css_path)
        print(tokens_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

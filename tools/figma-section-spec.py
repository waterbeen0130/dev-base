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
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from urllib import error, parse, request


FIGMA_API_BASE = "https://api.figma.com"


@dataclass
class ExtractionResult:
    section: dict
    text_nodes: list[dict]
    frame_nodes: list[dict]
    interactions: list[dict]
    image_refs: set[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract normalized section spec from Figma node")
    parser.add_argument("--file-key", required=True, help="Figma file key")
    parser.add_argument("--node-id", required=True, help="Figma node id (e.g. 842:37)")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--name", help="Output filename prefix (default: section_<node-id>)")
    return parser.parse_args()


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
        "textAlignHorizontal": style.get("textAlignHorizontal"),
        "textAlignVertical": style.get("textAlignVertical"),
    }


def normalize_frame_node(node: dict, image_refs: set[str]) -> dict:
    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "bbox": extract_bbox(node),
        "layoutMode": node.get("layoutMode"),
        "paddingTop": safe_round_3(node.get("paddingTop")),
        "paddingRight": safe_round_3(node.get("paddingRight")),
        "paddingBottom": safe_round_3(node.get("paddingBottom")),
        "paddingLeft": safe_round_3(node.get("paddingLeft")),
        "itemSpacing": safe_round_3(node.get("itemSpacing")),
        "primaryAxisAlignItems": node.get("primaryAxisAlignItems"),
        "counterAxisAlignItems": node.get("counterAxisAlignItems"),
        "fills": extract_frame_fill(node.get("fills"), image_refs),
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


def walk_and_extract(root: dict) -> ExtractionResult:
    section = {
        "id": root.get("id"),
        "name": root.get("name"),
        "bbox": extract_bbox(root),
    }

    text_nodes: list[dict] = []
    frame_nodes: list[dict] = []
    interactions: list[dict] = []
    image_refs: set[str] = set()

    def walk(node: dict) -> None:
        if not isinstance(node, dict):
            return

        interactions.extend(extract_url_interactions(node))

        node_type = node.get("type")
        if node_type == "TEXT":
            text_nodes.append(normalize_text_node(node))
        if node_type == "FRAME":
            frame_nodes.append(normalize_frame_node(node, image_refs))

        children = node.get("children")
        if isinstance(children, list):
            for child in children:
                walk(child)

    walk(root)

    return ExtractionResult(
        section=section,
        text_nodes=text_nodes,
        frame_nodes=frame_nodes,
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
        "textAlignHorizontal",
        "textAlignVertical",
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
    ]
    lines.append(render_table(frame_columns, frame_nodes))
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
    token = require_figma_token()

    root = fetch_node_document(args.file_key, args.node_id, token)
    extracted = walk_and_extract(root)
    images = fetch_images_map(args.file_key, token, extracted.image_refs)

    payload = {
        "schema_version": 1,
        "section": extracted.section,
        "text_nodes": extracted.text_nodes,
        "frame_nodes": extracted.frame_nodes,
        "interactions": extracted.interactions,
        "images": {key: images[key] for key in sorted(images.keys())},
    }

    name = args.name.strip() if isinstance(args.name, str) and args.name.strip() else default_name(args.node_id)
    os.makedirs(args.output, exist_ok=True)
    json_path = os.path.join(args.output, f"{name}_spec.json")
    md_path = os.path.join(args.output, f"{name}_spec.md")

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_markdown(payload, args.node_id))

    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

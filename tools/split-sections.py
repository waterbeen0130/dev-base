#!/usr/bin/env python3
"""Split normalized Figma JSON into per-section files for AI processing.

Usage:
  python3 tools/split-sections.py --input normalized.json --output ./sections/
  cat normalized.json | python3 tools/split-sections.py --output ./sections/
"""

import argparse
import json
import os
import re
import sys


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "section"


def split(data: dict, output_dir: str) -> list[dict]:
    """Split normalized JSON tree into sections. Returns manifest."""
    tree = data["tree"]
    meta = data["meta"]
    root_children = tree.get("children", [])

    sections = []
    # Find actual content (skip root wrappers like 'inner')
    content_nodes = []
    for rc in root_children:
        name = rc.get("name", "").lower()
        children = rc.get("children", [])
        if name in ("inner", "cont", "wrapper") and children:
            content_nodes.extend(children)
        else:
            content_nodes.append(rc)

    os.makedirs(output_dir, exist_ok=True)

    for i, node in enumerate(content_nodes):
        name = node.get("name", f"section_{i}")
        slug = _slug(name)
        filename = f"{i:02d}_{slug}.json"

        section_data = {
            "meta": {
                "section_index": i,
                "section_name": name,
                "profile": meta.get("profile", "basic"),
                "page": meta.get("section_name", "A_main"),
                "total_sections": len(content_nodes),
            },
            "tree": node,
        }

        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(section_data, f, ensure_ascii=False, indent=2)

        # Count nodes recursively
        def count_nodes(n):
            c = 1
            for ch in n.get("children", []):
                c += count_nodes(ch)
            return c

        node_count = count_nodes(node)
        sections.append({
            "index": i,
            "name": name,
            "slug": slug,
            "file": filename,
            "node_count": node_count,
        })
        print(f"  [{i}] {name} ({node_count} nodes) → {filename}", file=sys.stderr)

    # Write manifest
    manifest = {
        "meta": meta,
        "sections": sections,
    }
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n{len(sections)} sections → {output_dir}/", file=sys.stderr)
    return sections


def main():
    parser = argparse.ArgumentParser(description="Split normalized JSON into sections")
    parser.add_argument("--input", help="Input normalized JSON (default: stdin)")
    parser.add_argument("--output", default="./sections", help="Output directory")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    split(data, args.output)


if __name__ == "__main__":
    main()

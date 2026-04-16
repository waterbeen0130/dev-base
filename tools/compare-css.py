#!/usr/bin/env python3
"""
compare-css.py — Figma mapping JSON vs actual CSS comparison tool

Reads figma-extract.py mapping output and compares against actual CSS file.
Reports:
  1. Component patterns (badge, card) requiring parent+child CSS
  2. TEXT nodes inside badge parents that need wrapper styling
  3. FRAME layout value audit (gap, align-items, padding, flex-direction)
  4. TEXT style value audit (font-size, font-weight, color, line-height, letter-spacing, text-align)
  5. CSS cascade conflict warnings

Usage:
  python3 compare-css.py --mapping <mapping.json> --css <common.css> [--scope <selector_prefix>]
"""
import argparse
import json
import re
import sys
from pathlib import Path


def parse_css_file(css_path: str) -> dict[str, dict[str, str]]:
    """Parse CSS file into {selector: {property: value}} dict."""
    content = Path(css_path).read_text(encoding="utf-8")
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    rules: dict[str, dict[str, str]] = {}
    for match in re.finditer(r'([^{}@]+?)\{([^{}]+)\}', content):
        selector = match.group(1).strip()
        if not selector or selector.startswith('@'):
            continue
        props: dict[str, str] = {}
        for prop in match.group(2).strip().split(';'):
            prop = prop.strip()
            if ':' in prop:
                k, v = prop.split(':', 1)
                props[k.strip()] = v.strip()
        if selector in rules:
            rules[selector].update(props)
        else:
            rules[selector] = props
    return rules


def find_cascade_conflicts(css_rules: dict[str, dict[str, str]], scope: str | None = None) -> list[dict]:
    """Detect broad tag selectors that cascade into nested structures."""
    conflicts = []
    descendant_tags = {'p', 'span', 'strong', 'a'}

    for sel, props in css_rules.items():
        if scope and scope not in sel:
            continue
        parts = sel.split()
        if len(parts) < 2:
            continue
        last = parts[-1]
        if last not in descendant_tags:
            continue
        if '>' in sel:
            continue
        conflicts.append({
            "selector": sel,
            "tag": last,
            "properties": list(props.keys()),
            "warning": f"'{sel}' targets <{last}> without '>'. "
                       f"Props [{', '.join(props.keys())}] may cascade into nested <{last}>."
        })

    return conflicts


# layout/visual properties to audit on FRAME nodes
FRAME_AUDIT_PROPS = [
    "display", "flex-direction", "gap", "padding",
    "justify-content", "align-items",
    "background-color", "border-radius", "border",
]

# text style properties to audit on TEXT nodes
TEXT_AUDIT_PROPS = [
    "font-size", "font-weight", "color", "line-height",
    "letter-spacing", "text-align",
]


def compare_mapping_vs_css(mapping: dict, css_rules: dict) -> list[dict]:
    """Compare figma mapping nodes against CSS rules. Returns issue list."""
    issues = []

    # Build parent lookup
    parent_lookup: dict[str, dict] = {}
    for nid, node in mapping.items():
        pid = node.get("parent_id")
        if pid and pid in mapping:
            parent_lookup[nid] = mapping[pid]

    for node_id, node in mapping.items():
        node_type = node.get("type", "")
        node_name = node.get("name", "")
        node_css = node.get("css", {})
        component = node.get("component")
        parent_id = node.get("parent_id")

        if not node_css:
            continue

        # --- Component detection ---

        if component == "badge":
            bg = node_css.get("background-color", "")
            br = node_css.get("border-radius", "")
            pad = node_css.get("padding", "")
            text_children = [
                (cid, c) for cid, c in mapping.items()
                if c.get("parent_id") == node_id and c.get("type") == "TEXT"
            ]
            child_texts = ", ".join(f'"{c["name"][:20]}"' for _, c in text_children)
            issues.append({
                "node_id": node_id,
                "name": node_name,
                "type": "BADGE_CONTAINER",
                "severity": "HIGH",
                "figma_css": {"background": bg, "border-radius": br, "padding": pad},
                "message": f"Badge: bg:{bg}; radius:{br}; padding:{pad}. Children: {child_texts}",
            })

        if node_type == "TEXT" and parent_id:
            parent = parent_lookup.get(node_id)
            if parent and parent.get("component") == "badge":
                parent_bg = parent.get("css", {}).get("background-color", "")
                text_color = node_css.get("color", "")
                issues.append({
                    "node_id": node_id,
                    "name": node_name,
                    "type": "BADGE_TEXT",
                    "severity": "HIGH",
                    "figma_css": node_css,
                    "message": f"'{node_name[:30]}' inside badge (bg:{parent_bg}). Needs wrapper, not just color:{text_color}.",
                })

        if component == "card":
            issues.append({
                "node_id": node_id,
                "name": node_name,
                "type": "CARD_CONTAINER",
                "severity": "INFO",
                "figma_css": {k: v for k, v in node_css.items() if k in ("border-radius", "background-color", "border")},
                "message": f"Card: verify container CSS matches Figma.",
            })

        # --- Layout value audit (FRAME nodes) ---

        if node_type == "FRAME":
            layout_vals = {k: v for k, v in node_css.items() if k in FRAME_AUDIT_PROPS and v}
            if layout_vals:
                issues.append({
                    "node_id": node_id,
                    "name": node_name,
                    "type": "FRAME_LAYOUT",
                    "severity": "AUDIT",
                    "figma_css": layout_vals,
                    "message": f"Frame '{node_name[:30]}': {'; '.join(f'{k}:{v}' for k,v in layout_vals.items())}",
                })

        # --- Text style audit (TEXT nodes) ---

        if node_type == "TEXT":
            text_vals = {k: v for k, v in node_css.items() if k in TEXT_AUDIT_PROPS and v}
            if text_vals:
                issues.append({
                    "node_id": node_id,
                    "name": node_name,
                    "type": "TEXT_STYLE",
                    "severity": "AUDIT",
                    "figma_css": text_vals,
                    "message": f"Text '{node_name[:30]}': {'; '.join(f'{k}:{v}' for k,v in text_vals.items())}",
                })

    return issues


def print_report(issues: list[dict], conflicts: list[dict], verbose: bool = False, out=sys.stdout):
    print("=" * 60, file=out)
    print("FIGMA vs CSS COMPARISON REPORT", file=out)
    print("=" * 60, file=out)

    badge_issues = [i for i in issues if i["type"] in ("BADGE_CONTAINER", "BADGE_TEXT")]
    card_issues = [i for i in issues if i["type"] == "CARD_CONTAINER"]
    frame_audits = [i for i in issues if i["type"] == "FRAME_LAYOUT"]
    text_audits = [i for i in issues if i["type"] == "TEXT_STYLE"]

    if badge_issues:
        print(f"\n## Badge Components ({len(badge_issues)})", file=out)
        print("-" * 40, file=out)
        for i in badge_issues:
            print(f"  [{i['severity']}] {i['node_id']} | {i['name'][:40]}", file=out)
            print(f"    {i['message']}", file=out)
            print(f"    figma: {json.dumps(i['figma_css'], ensure_ascii=False)}", file=out)
            print(file=out)

    if card_issues:
        print(f"\n## Card Components ({len(card_issues)})", file=out)
        print("-" * 40, file=out)
        for i in card_issues:
            print(f"  [{i['severity']}] {i['node_id']} | {i['name'][:40]}", file=out)
            print(f"    {i['message']}", file=out)

    if frame_audits:
        print(f"\n## Frame Layout Audit ({len(frame_audits)})", file=out)
        print("-" * 40, file=out)
        for i in frame_audits:
            print(f"  {i['node_id']} | {i['name'][:30]}", file=out)
            for k, v in i["figma_css"].items():
                print(f"    {k}: {v}", file=out)
            print(file=out)

    if text_audits:
        print(f"\n## Text Style Audit ({len(text_audits)})", file=out)
        print("-" * 40, file=out)
        for i in text_audits:
            print(f"  {i['node_id']} | {i['name'][:30]}", file=out)
            for k, v in i["figma_css"].items():
                print(f"    {k}: {v}", file=out)
            print(file=out)

    if conflicts:
        print(f"\n## Cascade Warnings ({len(conflicts)})", file=out)
        print("-" * 40, file=out)
        for c in conflicts:
            print(f"  [WARN] {c['warning']}", file=out)

    print(f"\n{'=' * 60}", file=out)
    print(f"Summary: {len(badge_issues)} badge, {len(card_issues)} card, "
          f"{len(frame_audits)} frame-layout, {len(text_audits)} text-style, "
          f"{len(conflicts)} cascade", file=out)


def main():
    parser = argparse.ArgumentParser(description="Compare Figma mapping vs CSS")
    parser.add_argument("--mapping", required=True, help="Path to mapping.json")
    parser.add_argument("--css", required=True, help="Path to CSS file")
    parser.add_argument("--scope", default=None, help="Limit cascade check to selectors containing this string")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    css_rules = parse_css_file(args.css)

    issues = compare_mapping_vs_css(mapping, css_rules)
    conflicts = find_cascade_conflicts(css_rules, scope=args.scope)

    if args.json:
        print(json.dumps({"issues": issues, "cascade_warnings": conflicts}, ensure_ascii=False, indent=2))
    else:
        print_report(issues, conflicts)


if __name__ == "__main__":
    main()

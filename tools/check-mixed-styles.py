#!/usr/bin/env python3
"""DOD-003: mixed-style text (character_segments) preservation check.

spec.json text_nodes with has_mixed_styles=true carry per-segment colors. If a
non-base segment color is dropped (the whole run rendered in one color), the
design intent is lost. This flags any non-base segment color that is absent from
both the HTML (inline style) and the CSS (class rule). has_mixed_styles=false is
skipped (single style, no span split needed).

Usage:
    python3 check-mixed-styles.py --spec extracted/sec_spec.json \\
        --html index.html --css css/common.css
Exit: 0 = clean, 1 = violations found.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def _norm_color(value) -> str | None:
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", v)
    if not m:
        return v or None
    hexpart = m.group(1)
    if len(hexpart) == 3:  # expand shorthand for matching
        hexpart = "".join(c * 2 for c in hexpart)
    return "#" + hexpart


def _color_present(color: str, haystack: str) -> bool:
    """Match a color against text allowing #abc and #aabbcc forms."""
    hl = haystack.lower()
    if color in hl:
        return True
    if len(color) == 7:  # #aabbcc → also try #abc when channels are doubled
        r, g, b = color[1:3], color[3:5], color[5:7]
        if r[0] == r[1] and g[0] == g[1] and b[0] == b[1]:
            short = "#" + r[0] + g[0] + b[0]
            if short in hl:
                return True
    return False


def find_mixed_style_violations(spec: dict, html: str, css: str = "") -> list[dict]:
    violations: list[dict] = []
    haystack = (html or "") + "\n" + (css or "")
    for node in spec.get("text_nodes") or []:
        if not isinstance(node, dict) or not node.get("has_mixed_styles"):
            continue
        segments = node.get("character_segments") or []
        base = _norm_color(node.get("color"))
        seg_colors = {c for c in (_norm_color(s.get("color")) for s in segments) if c}
        if len(seg_colors) < 2:
            continue  # not actually multi-color
        for color in seg_colors:
            if color == base:
                continue  # base/inherited color need not be written explicitly
            if not _color_present(color, haystack):
                violations.append({
                    "node": (node.get("characters") or "")[:30],
                    "detail": f"mixed-style 구간 색상 {color} 가 HTML/CSS에 없음 — character_segments 무시(단일색 출력)",
                })
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--html", required=True)
    ap.add_argument("--css", required=True)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    html = Path(args.html).read_text(encoding="utf-8")
    css = Path(args.css).read_text(encoding="utf-8") if Path(args.css).exists() else ""
    violations = find_mixed_style_violations(spec, html, css)
    if violations:
        print(f"✗ {len(violations)} mixed-style violation(s):")
        for v in violations:
            print(f"  [{v['node']}…] {v['detail']}")
        return 1
    print("✓ mixed-style segments preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())

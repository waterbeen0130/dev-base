#!/usr/bin/env python3
"""Convert normalized Figma JSON to HTML + CSS files.

Reads the normalized intermediate JSON (from figma-extract.py) and generates
pixel-accurate HTML + CSS using ALL values from the normalization data.
No shortcuts, no screenshot images — every node becomes real markup.

Usage:
  python3 tools/json-to-html.py --input normalized.json --page index --output ./output/
  echo '<json>' | python3 tools/json-to-html.py --page index --output ./output/
"""

import argparse
import json
import os
import re
import sys
from typing import Any


def _slug(name: str) -> str:
    """Convert node name to CSS-safe class slug."""
    s = re.sub(r"[^a-zA-Z0-9가-힣_]", "_", name.lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "el"


class Converter:
    def __init__(self, page: str, image_map: dict[str, str] | None = None):
        self.page = page
        self.css_lines: list[str] = []
        self.selector_count: dict[str, int] = {}
        self.html_lines: list[str] = []
        self.image_map = image_map or {}  # node_id -> image path

    def _unique_cls(self, name: str) -> str:
        """Generate unique class name with page prefix."""
        base = f"{self.page}_{_slug(name)}"
        count = self.selector_count.get(base, 0)
        self.selector_count[base] = count + 1
        if count == 0:
            return base
        return f"{base}_{count}"

    def _css_props(self, node: dict) -> dict[str, str]:
        """Extract all CSS properties from a normalized node."""
        props: dict[str, str] = {}
        layout = node.get("layout")
        visual = node.get("visual")

        if layout:
            props["display"] = layout.get("display", "flex")
            d = layout.get("direction")
            if d:
                props["flex-direction"] = d
            gap = layout.get("gap")
            if gap and gap != "0":
                props["gap"] = gap
            pad = layout.get("padding")
            if pad and pad != "0":
                props["padding"] = pad
            j = layout.get("justify")
            if j:
                props["justify-content"] = j
            a = layout.get("align")
            if a:
                props["align-items"] = a

        if visual:
            bg = visual.get("background")
            if bg:
                props["background-color"] = bg
            border = visual.get("border")
            if border:
                props["border"] = border
            br = visual.get("borderRadius")
            if br and br != "0":
                props["border-radius"] = br
            opacity = visual.get("opacity")
            if opacity is not None and float(opacity) < 1.0:
                props["opacity"] = str(opacity)
            # width/height for non-layout containers
            w = visual.get("width")
            h = visual.get("height")
            if w and not layout:
                props["width"] = f"{int(w)}px"
            if h and not layout:
                props["height"] = f"{int(h)}px"

        return props

    def _text_css(self, style: dict) -> dict[str, str]:
        """Extract text CSS properties from a segment style."""
        props: dict[str, str] = {}
        ff = style.get("fontFamily")
        if ff:
            props["font-family"] = f"'{ff}', sans-serif"
        fs = style.get("fontSize")
        if fs:
            props["font-size"] = str(fs)
        fw = style.get("fontWeight")
        if fw:
            props["font-weight"] = str(fw)
        lh = style.get("lineHeight")
        if lh is not None:
            props["line-height"] = str(lh)
        ls = style.get("letterSpacing")
        if ls and ls != "0em":
            props["letter-spacing"] = ls
        color = style.get("color")
        if color:
            props["color"] = color
        ta = style.get("textAlign")
        if ta and ta != "left":
            props["text-align"] = ta
        return props

    def _emit_css(self, cls: str, props: dict[str, str]) -> None:
        """Add a CSS rule (one-line format)."""
        if not props:
            return
        parts = [f"{k}:{v}" for k, v in props.items() if v]
        if parts:
            self.css_lines.append(f".{cls}{{{'; '.join(parts)}}}")

    def _is_list_pattern(self, children: list[dict]) -> bool:
        """Detect repeating list pattern in children."""
        if len(children) < 2:
            return False
        types = [c.get("type") for c in children]
        if len(set(types)) != 1:
            return False
        if types[0] not in ("FRAME", "INSTANCE"):
            return False
        child_counts = [len(c.get("children", [])) for c in children]
        if not child_counts:
            return False
        return max(child_counts) - min(child_counts) <= 2

    def _is_divider(self, node: dict) -> bool:
        """Detect divider nodes (thin elements)."""
        visual = node.get("visual")
        if not visual:
            return False
        w = visual.get("width", 999)
        h = visual.get("height", 999)
        return (w is not None and w <= 3) or (h is not None and h <= 3)

    def _is_image_node(self, node: dict) -> bool:
        """Detect nodes that should be images (no text, no children, has background)."""
        if node.get("text"):
            return False
        if node.get("children"):
            return False
        visual = node.get("visual")
        if not visual:
            return False
        ntype = node.get("type", "")
        # VECTOR, ELLIPSE, LINE, RECTANGLE without children are likely decorative
        if ntype in ("VECTOR", "ELLIPSE", "LINE", "BOOLEAN_OPERATION", "STAR", "REGULAR_POLYGON"):
            return True
        return False

    def _render_node(self, node: dict, depth: int = 0) -> None:
        """Recursively render a node to HTML + CSS."""
        indent = "  " * depth
        name = node.get("name", "")
        ntype = node.get("type", "")
        node_id = node.get("id", "")
        text = node.get("text")
        children = node.get("children", [])
        cls = self._unique_cls(name)

        # Check if this node has a downloaded image
        img_path = self.image_map.get(node_id)
        if img_path:
            visual = node.get("visual", {})
            w = visual.get("width")
            h = visual.get("height")
            props = {}
            if w:
                props["width"] = f"{int(w)}px"
                props["max-width"] = "100%"
                props["height"] = "auto"
            self._emit_css(cls, props)
            alt = name or "image"
            self.html_lines.append(f'{indent}<div class="img_area"><img class="{cls}" src="{img_path}" alt="{alt}"></div>')
            return

        # Skip pure decorative vectors (render as empty styled elements)
        if self._is_image_node(node):
            props = self._css_props(node)
            if props.get("background-color"):
                self._emit_css(cls, props)
                self.html_lines.append(f"{indent}<span class=\"{cls}\"></span>")
            return

        # Divider nodes
        if self._is_divider(node):
            visual = node.get("visual", {})
            props = {"display": "block"}
            bg = visual.get("background")
            if bg:
                props["background-color"] = bg
            w = visual.get("width")
            h = visual.get("height")
            if w and w <= 3:
                props["width"] = f"{int(w)}px"
                props["height"] = "100%"
            elif h and h <= 3:
                props["width"] = "100%"
                props["height"] = f"{int(h)}px"
            self._emit_css(cls, props)
            self.html_lines.append(f"{indent}<span class=\"{cls}\"></span>")
            return

        # Text nodes
        if text:
            tag = text.get("tag_hint", "span")
            content = text.get("content", "")
            segments = text.get("segments", [])
            has_newline = text.get("has_newline", False)

            # Build CSS from first segment's style + container visual
            container_props = self._css_props(node)
            if segments:
                text_props = self._text_css(segments[0]["style"])
                container_props.update(text_props)
            # Remove background-color if it's same as text color (Figma text fill)
            if container_props.get("background-color") == container_props.get("color"):
                del container_props["background-color"]
            self._emit_css(cls, container_props)

            # Render text content
            if len(segments) > 1:
                # Multiple segments — render with override spans
                inner_parts = []
                for i, seg in enumerate(segments):
                    seg_text = seg["text"].replace("\n", "<br>")
                    if seg.get("is_override") and i > 0:
                        seg_cls = f"{cls}_s{i}"
                        seg_style = self._text_css(seg["style"])
                        self._emit_css(seg_cls, seg_style)
                        inner_parts.append(f"<span class=\"{seg_cls}\">{seg_text}</span>")
                    else:
                        inner_parts.append(seg_text)
                inner = "".join(inner_parts)
            else:
                inner = content.replace("\n", "<br>")

            self.html_lines.append(f"{indent}<{tag} class=\"{cls}\">{inner}</{tag}>")
            return

        # Container nodes
        container_props = self._css_props(node)

        # Detect list pattern
        is_list = self._is_list_pattern(children)

        if is_list:
            self._emit_css(cls, container_props)
            self.html_lines.append(f"{indent}<ul class=\"{cls}\">")
            for child in children:
                self.html_lines.append(f"{indent}  <li>")
                self._render_node(child, depth + 2)
                self.html_lines.append(f"{indent}  </li>")
            self.html_lines.append(f"{indent}</ul>")
        else:
            self._emit_css(cls, container_props)
            self.html_lines.append(f"{indent}<div class=\"{cls}\">")
            for child in children:
                self._render_node(child, depth + 1)
            self.html_lines.append(f"{indent}</div>")

    def convert(self, data: dict) -> tuple[str, str]:
        """Convert normalized JSON to HTML + CSS strings."""
        meta = data["meta"]
        tree = data["tree"]

        self._render_node(tree, depth=1)

        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta.get('section_name', 'Page')}</title>
<link rel="stylesheet" href="common.css">
</head>
<body class="page_{self.page}">

{chr(10).join(self.html_lines)}

</body>
</html>"""

        # Build CSS (common.md 규칙 자동 적용)
        css_parts = [
            f"/* {meta.get('section_name','')} | profile: {meta.get('profile','basic')} | nodes: {meta.get('total_nodes',0)} */",
            "",
            "/* reset + base rules (common.md) */",
            ":root{--width:1440px; --padding:20px;}",
            "html,body{font-size:clamp(14px, 1.2vw, 16px);}",
            "body{font-family:'Pretendard', sans-serif; overflow-x:hidden; color:#212121; word-break:keep-all;}",
            "ul{list-style:none;}",
            "img{max-width:100%; height:auto; display:block;}",
            "a{text-decoration:none; color:inherit;}",
            ".img_area{overflow:hidden;}",
            ".cont{margin:0 auto; max-width:var(--width); padding:0 var(--padding); width:100%;}",
            "",
            "/* components */",
        ]
        css_parts.extend(self.css_lines)

        css = "\n".join(css_parts)
        return html, css


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert normalized Figma JSON to HTML + CSS")
    parser.add_argument("--input", help="Input normalized JSON file (default: stdin)")
    parser.add_argument("--page", default="index", help="Page name for CSS prefix")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--image-map", help="JSON file mapping node IDs to image paths")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    image_map = {}
    if args.image_map:
        with open(args.image_map, "r", encoding="utf-8") as f:
            image_map = json.load(f)

    conv = Converter(page=args.page, image_map=image_map)
    html, css = conv.convert(data)

    os.makedirs(args.output, exist_ok=True)
    html_path = os.path.join(args.output, f"{args.page}.html")
    css_path = os.path.join(args.output, "common.css")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)

    print(f"Generated: {html_path} ({len(conv.html_lines)} lines)", file=sys.stderr)
    print(f"CSS rules: {len(conv.css_lines)}", file=sys.stderr)

    # Auto-validation
    validator_path = os.path.join(os.path.dirname(__file__), "validate-semantic.py")
    if os.path.exists(validator_path):
        import subprocess
        img_dir = os.path.join(args.output, "img")
        cmd = [sys.executable, validator_path, "--html", html_path, "--css", css_path]
        if os.path.isdir(img_dir):
            cmd.extend(["--img", img_dir])
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout, file=sys.stderr, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        if result.returncode == 2:
            print("❌ CRITICAL 위반 — 수정 필요", file=sys.stderr)
        elif result.returncode == 1:
            print("⚠️  MAJOR 위반 — 수정 권장", file=sys.stderr)


if __name__ == "__main__":
    main()

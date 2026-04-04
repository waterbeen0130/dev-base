#!/usr/bin/env python3
"""Convert normalized Figma JSON to semantic HTML + CSS.

ALL CSS values come directly from the normalized JSON — no guessing, no memorizing.
AI decisions are limited to: tag choice, class naming, selector strategy, list detection.

Usage:
  python3 tools/json-to-html.py --input normalized.json --page main --output ./output/
  echo '<json>' | python3 tools/json-to-html.py --page main --output ./output/
"""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "el"


class SemanticConverter:
    # Generic name → meaningful name mapping
    # Keys with regex: sec_N, section_N patterns
    GENERIC_REMAP = {
        "sec_1": "process",
        "sec_2": "info",
        "sec_3": "apply",
        "sec_4": "community",
        "sec_5": "gallery",
        "sec_6": "partner",
    }

    def __init__(self, page: str, image_map: dict[str, str] | None = None,
                 name_overrides: dict[str, str] | None = None):
        self.page = page
        self.css_rules: dict[str, dict[str, str]] = {}
        self.html_lines: list[str] = []
        self.image_map = image_map or {}
        self.cls_counter: dict[str, int] = {}
        self.name_overrides = name_overrides or {}  # custom node name → class overrides
        self.current_depth = 0

    # ── Class naming ──

    def _remap_name(self, name: str) -> str:
        """Remap generic names (sec_1, section_01) to meaningful names."""
        slug = _slug(name)
        # User overrides first
        if slug in self.name_overrides:
            return self.name_overrides[slug]
        # Built-in generic remap
        if slug in self.GENERIC_REMAP:
            return self.GENERIC_REMAP[slug]
        # sec_N / section_N pattern
        m = re.match(r'^sec(?:tion)?_(\d+)$', slug)
        if m:
            return f"section_{m.group(1)}"  # will still be caught by validator
        return slug

    def _cls(self, name: str, is_common: bool = False) -> str:
        """Generate class. Common areas get no page prefix. Generic names remapped."""
        slug = self._remap_name(_slug(name))
        common_names = {"header", "footer", "gnb", "logo", "copyright",
                        "btn_top", "btn_menu", "btn_close", "total_menu",
                        "cont", "sub_wrap", "sub_visual", "navi", "lnb"}
        # Also match names that START with common keywords
        for cn in list(common_names):
            if slug.startswith(cn + "_") or slug.startswith(cn):
                return slug  # No page prefix for copyright_xxx, footer_xxx etc
        if is_common or slug in common_names:
            base = slug
        else:
            base = f"{self.page}_{slug}"
        count = self.cls_counter.get(base, 0)
        self.cls_counter[base] = count + 1
        return base if count == 0 else f"{base}_{count}"

    # ── CSS extraction (ALL values from JSON, zero guessing) ──

    def _layout_to_css(self, layout: dict | None) -> dict[str, str]:
        if not layout:
            return {}
        p: dict[str, str] = {}
        p["display"] = layout.get("display", "flex")
        d = layout.get("direction")
        if d:
            p["flex-direction"] = d
        gap = layout.get("gap")
        if gap and gap != "0":
            p["gap"] = gap
        pad = layout.get("padding")
        if pad and pad != "0":
            p["padding"] = pad
        j = layout.get("justify")
        if j:
            p["justify-content"] = j
        a = layout.get("align")
        if a:
            p["align-items"] = a
        return p

    def _visual_to_css(self, visual: dict | None, has_layout: bool = False) -> dict[str, str]:
        if not visual:
            return {}
        p: dict[str, str] = {}
        bg = visual.get("background")
        if bg:
            p["background-color"] = bg
        border = visual.get("border")
        if border:
            p["border"] = border
        br = visual.get("borderRadius")
        if br and br != "0":
            p["border-radius"] = br
        opacity = visual.get("opacity")
        if opacity is not None and float(opacity) < 1.0:
            p["opacity"] = str(opacity)
        return p

    def _segment_to_css(self, style: dict) -> dict[str, str]:
        """Extract ALL text CSS from a single segment style. No omission."""
        p: dict[str, str] = {}
        if style.get("fontFamily"):
            p["font-family"] = f"'{style['fontFamily']}', sans-serif"
        if style.get("fontSize"):
            p["font-size"] = str(style["fontSize"])
        if style.get("fontWeight"):
            p["font-weight"] = str(style["fontWeight"])
        if style.get("lineHeight") is not None:
            p["line-height"] = str(style["lineHeight"])
        ls = style.get("letterSpacing")
        if ls and ls != "0em":
            p["letter-spacing"] = ls
        if style.get("color"):
            p["color"] = style["color"]
        ta = style.get("textAlign")
        if ta and ta != "left":
            p["text-align"] = ta
        return p

    def _emit(self, selector: str, props: dict[str, str]) -> None:
        """Add CSS rule, merging into existing if same selector."""
        if not props:
            return
        if selector in self.css_rules:
            self.css_rules[selector].update(props)
        else:
            self.css_rules[selector] = dict(props)

    # ── Detection helpers ──

    def _is_list(self, children: list[dict]) -> bool:
        if len(children) < 2:
            return False
        types = [c.get("type") for c in children]
        if len(set(types)) != 1 or types[0] not in ("FRAME", "INSTANCE"):
            return False
        counts = [len(c.get("children", [])) for c in children]
        return counts and max(counts) - min(counts) <= 2

    def _is_divider(self, node: dict) -> bool:
        v = node.get("visual", {})
        w, h = v.get("width", 999), v.get("height", 999)
        return (w is not None and w <= 3) or (h is not None and h <= 3)

    def _is_decorative(self, node: dict) -> bool:
        """Leaf node without text/children — purely visual."""
        if node.get("text") or node.get("children"):
            return False
        return node.get("type", "") in ("VECTOR", "ELLIPSE", "LINE",
                                         "BOOLEAN_OPERATION", "STAR", "REGULAR_POLYGON")

    def _style_diff(self, base: dict, override: dict) -> dict[str, str]:
        """Return only the CSS properties that differ between two segment styles."""
        diff: dict[str, str] = {}
        for key in ("fontSize", "fontWeight", "fontFamily", "color", "letterSpacing", "lineHeight"):
            base_val = base.get(key)
            over_val = override.get(key)
            if over_val is not None and over_val != base_val:
                css_key = {
                    "fontSize": "font-size", "fontWeight": "font-weight",
                    "fontFamily": "font-family", "color": "color",
                    "letterSpacing": "letter-spacing", "lineHeight": "line-height",
                }.get(key, key)
                if key == "fontFamily":
                    diff[css_key] = f"'{over_val}', sans-serif"
                else:
                    diff[css_key] = str(over_val)
        return diff

    # ── Rendering ──

    def _should_unwrap(self, node: dict) -> bool:
        """Check if this wrapper node should be removed to reduce DOM depth.
        Unwrap if: no layout, no visual styling, single child, not root."""
        if node.get("text"):
            return False
        children = node.get("children", [])
        if len(children) != 1:
            return False
        layout = node.get("layout")
        visual = node.get("visual", {})
        has_styling = (
            layout or
            visual.get("background") or
            visual.get("border") or
            (visual.get("borderRadius") and visual["borderRadius"] != "0")
        )
        return not has_styling

    def _fix_padding(self, props: dict[str, str]) -> dict[str, str]:
        """Convert side padding >= 100px to 0 (rely on max-width + margin:auto instead)."""
        pad = props.get("padding")
        if not pad:
            return props
        parts = pad.replace("px", "").split()
        if len(parts) >= 2:
            try:
                lr = int(float(parts[1]))  # right value
                if lr >= 100:
                    # Keep top/bottom, zero out left/right
                    if len(parts) == 2:
                        props["padding"] = f"{parts[0]}px 0"
                    elif len(parts) == 4:
                        props["padding"] = f"{parts[0]}px 0 {parts[2]}px 0"
            except (ValueError, IndexError):
                pass
        return props

    def _render(self, node: dict, depth: int = 0, parent_cls: str = "") -> None:
        # Unwrap unnecessary wrappers (reduce DOM depth)
        if depth > 0 and self._should_unwrap(node):
            children = node.get("children", [])
            if children:
                self._render(children[0], depth, parent_cls)
            return

        indent = "  " * depth
        name = node.get("name", "")
        node_id = node.get("id", "")
        text = node.get("text")
        children = node.get("children", [])
        layout = node.get("layout")
        visual = node.get("visual")

        # Image map hit
        img_path = self.image_map.get(node_id)
        if img_path:
            cls = self._cls(name)
            v = visual or {}
            w = v.get("width")
            props = {}
            if w:
                props["max-width"] = "100%"
                props["height"] = "auto"
            self._emit(f".{cls}", props)
            self.html_lines.append(f'{indent}<div class="img_area"><img class="{cls}" src="{img_path}" alt="{name}"></div>')
            return

        # Decorative vectors
        if self._is_decorative(node):
            bg = (visual or {}).get("background")
            if bg:
                cls = self._cls(name)
                self._emit(f".{cls}", {"background-color": bg, "display": "block"})
                self.html_lines.append(f"{indent}<span class=\"{cls}\"></span>")
            return

        # Dividers
        if self._is_divider(node):
            cls = self._cls(name)
            v = visual or {}
            props: dict[str, str] = {"display": "block"}
            bg = v.get("background")
            if bg:
                props["background-color"] = bg
            w, h = v.get("width", 999), v.get("height", 999)
            if w and w <= 3:
                props["width"] = f"{int(w)}px"
                props["height"] = "100%"
            elif h and h <= 3:
                props["width"] = "100%"
                props["height"] = f"{int(h)}px"
            self._emit(f".{cls}", props)
            self.html_lines.append(f"{indent}<span class=\"{cls}\"></span>")
            return

        # ── Text nodes ──
        if text:
            cls = self._cls(name)
            tag = text.get("tag_hint", "span")
            segments = text.get("segments", [])

            # Container CSS (layout + visual, but NOT background-color if it equals text color)
            container_css = {}
            container_css.update(self._fix_padding(self._layout_to_css(layout)))
            container_css.update(self._visual_to_css(visual, bool(layout)))
            # Base text style from first segment
            if segments:
                base_style = segments[0]["style"]
                base_css = self._segment_to_css(base_style)
                # Remove bg-color if same as text color (Figma text fill artifact)
                if container_css.get("background-color") == base_css.get("color"):
                    del container_css["background-color"]
                container_css.update(base_css)
            self._emit(f".{cls}", container_css)

            # Render content with override spans
            if len(segments) > 1:
                base_style = segments[0]["style"]
                parts = []
                for i, seg in enumerate(segments):
                    seg_text = seg["text"].replace("\n", "<br>")
                    if i == 0:
                        parts.append(seg_text)
                    else:
                        diff = self._style_diff(base_style, seg["style"])
                        if diff:
                            seg_cls = f"{cls}_s{i}"
                            self._emit(f".{seg_cls}", diff)
                            parts.append(f'<span class="{seg_cls}">{seg_text}</span>')
                        else:
                            parts.append(seg_text)
                inner = "".join(parts)
            else:
                inner = text.get("content", "").replace("\n", "<br>")

            self.html_lines.append(f"{indent}<{tag} class=\"{cls}\">{inner}</{tag}>")
            return

        # ── Container nodes ──
        cls = self._cls(name)
        container_css = {}
        container_css.update(self._fix_padding(self._layout_to_css(layout)))
        container_css.update(self._visual_to_css(visual, bool(layout)))
        self._emit(f".{cls}", container_css)

        is_list = self._is_list(children)
        tag_open = f'<ul class="{cls}">' if is_list else f'<div class="{cls}">'
        tag_close = "</ul>" if is_list else "</div>"

        self.html_lines.append(f"{indent}{tag_open}")
        for child in children:
            if is_list:
                self.html_lines.append(f"{indent}  <li>")
                self._render(child, depth + 2, cls)
                self.html_lines.append(f"{indent}  </li>")
            else:
                self._render(child, depth + 1, cls)
        self.html_lines.append(f"{indent}{tag_close}")

    # ── Output ──

    def convert(self, data: dict) -> tuple[str, str, str]:
        """Returns (html, common.css, reset.css)."""
        meta = data["meta"]
        self._render(data["tree"], depth=1)

        # HTML (no page_ class on body — rule: body 태그에 프리픽스 불필요)
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta.get('section_name', 'Page')}</title>
<link rel="stylesheet" href="reset.css">
<link rel="stylesheet" href="common.css">
</head>
<body>

{chr(10).join(self.html_lines)}

</body>
</html>"""

        # CSS — :root variables each on own line
        css_parts = [
            f"/* {meta.get('section_name','')} | profile: {meta.get('profile','basic')} | nodes: {meta.get('total_nodes',0)} */",
            "",
            ":root{",
            "--width:1440px;",
            "--padding:20px;",
            "}",
            ".cont{margin:0 auto; max-width:var(--width); padding:0 var(--padding); width:100%;}",
            ".img_area{overflow:hidden;}",
            "",
        ]
        # Emit all CSS rules (deduplicated, one-line format)
        for selector, props in self.css_rules.items():
            parts = [f"{k}:{v}" for k, v in props.items() if v]
            if parts:
                css_parts.append(f"{selector}{{{'; '.join(parts)}}}")

        css = "\n".join(css_parts)

        # reset.css (separate file — basic project rule)
        reset = """@charset "UTF-8";
html,body{font-size:clamp(14px, 1.2vw, 16px);}
body{font-family:'Pretendard', sans-serif; overflow-x:hidden; color:#212121; word-break:keep-all; margin:0; padding:0;}
*{margin:0; padding:0; box-sizing:border-box;}
ul{list-style:none;}
ol{list-style:none;}
img{max-width:100%; height:auto; display:block; border:0;}
a{text-decoration:none; color:inherit;}
button{cursor:pointer; border:none; background:none;}
input,textarea,select{font-family:inherit; font-size:inherit;}
table{border-collapse:collapse; border-spacing:0;}
address{font-style:normal;}"""

        return html, css, reset


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert normalized Figma JSON to semantic HTML + CSS")
    parser.add_argument("--input", help="Input normalized JSON file (default: stdin)")
    parser.add_argument("--page", default="main", help="Page name for CSS prefix (default: main)")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--image-map", help="JSON file mapping node IDs to image paths")
    parser.add_argument("--name-map", help="JSON file mapping generic node names to meaningful names (e.g. {\"sec_1\":\"process\"})")
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

    name_overrides = {}
    if args.name_map:
        with open(args.name_map, "r", encoding="utf-8") as f:
            name_overrides = json.load(f)

    conv = SemanticConverter(page=args.page, image_map=image_map, name_overrides=name_overrides)
    html, css, reset = conv.convert(data)

    os.makedirs(args.output, exist_ok=True)
    html_path = os.path.join(args.output, f"index.html")
    css_path = os.path.join(args.output, "common.css")
    reset_path = os.path.join(args.output, "reset.css")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)
    with open(reset_path, "w", encoding="utf-8") as f:
        f.write(reset)

    print(f"Generated: {html_path} ({len(conv.html_lines)} lines)", file=sys.stderr)
    print(f"CSS rules: {len(conv.css_rules)} (deduplicated)", file=sys.stderr)
    print(f"Reset: {reset_path}", file=sys.stderr)

    # Auto-validation
    validator_path = os.path.join(os.path.dirname(__file__), "validate-semantic.py")
    if os.path.exists(validator_path):
        img_dir = os.path.join(args.output, "img")
        cmd = [sys.executable, validator_path, "--html", html_path, "--css", css_path]
        if os.path.isdir(img_dir):
            cmd.extend(["--img", img_dir])
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout, file=sys.stderr, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")


if __name__ == "__main__":
    main()

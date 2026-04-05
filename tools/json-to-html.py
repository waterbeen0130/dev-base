#!/usr/bin/env python3
"""Convert normalized Figma JSON to semantic HTML + CSS.

ALL CSS values come directly from the normalized JSON — no guessing, no memorizing.
AI decisions are limited to: tag choice, class naming, selector strategy, list detection.

Usage:
  python3 tools/json-to-html.py --input normalized.json --page main --output ./output/
  echo '<json>' | python3 tools/json-to-html.py --page main --output ./output/
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def _slug(name: str) -> str:
    # Keep Korean characters for readable class names, transliterate later
    s = re.sub(r"[^a-zA-Z0-9가-힣_]", "_", name.lower())
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return "el"
    # If purely Korean, transliterate common words
    KR_MAP = {
        "공지사항": "notice", "자주묻는질문": "faq", "로고": "logo",
        "메뉴": "menu", "헤더": "header", "푸터": "footer",
        "검색": "search", "버튼": "btn", "목록": "list",
        "제목": "title", "내용": "content", "설명": "desc",
        "이미지": "img", "아이콘": "icon", "배경": "bg",
        "구름": "cloud", "산": "mountain", "나무": "tree",
        "의림지": "urimji",
    }
    for kr, en in KR_MAP.items():
        s = s.replace(kr, en)
    # If still has Korean, use a generic slug
    if re.search(r"[가-힣]", s):
        # Extract any English parts
        en_parts = re.findall(r"[a-z0-9_]+", s)
        return "_".join(en_parts) if en_parts else "el"
    return s


class SemanticConverter:
    # Generic name → meaningful name mapping
    GENERIC_REMAP = {
        "sec_1": "process",
        "sec_2": "info",
        "sec_3": "apply",
        "sec_4": "community",
        "sec_5": "gallery",
        "sec_6": "partner",
        # Child name prefixes that reference parent section numbers
        "s1_tit": "process_tit",
        "s2_tit": "info_tit",
        "s3_tit": "apply_tit",
        "s4_tit": "community_tit",
        "s1_list": "process_list",
        "s2_list": "info_list",
        "s3_list": "apply_list",
        "s4_list": "community_list",
    }
    GENERIC_NAME_PATTERN = re.compile(
        r"^(el|txt|btn|list|item|box|wrap|frame|group|element|tit|tab|b|img|icon|bg|top|bottom|left|right|center|info|sub|main|sec|block|area|row|col|cell|card|tag|label|desc|num|date|page|line|bar|dot|circle|arrow|link|menu|nav|panel|slot|zone|layer|cover|mask|clip_path_group)_?\d*$"
    )
    GENERIC_PARENT_STOPWORDS = {
        "cont", "inner", "wrapper", "wrap", "box", "group", "frame",
        "list", "item", "el", "txt", "btn", "tit", "sub", "top", "bottom",
        "left", "right", "center", "bg", "img", "main",
    }
    GENERIC_ROLE_MAP = {
        "el": "item",
        "element": "item",
        "frame": "item",
        "group": "item",
        "box": "item",
        "wrap": "item",
    }
    IMAGE_CONTEXT_NAMES = {
        "graphic", "image", "img", "icon", "vector", "photo", "picture",
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
        """Remap generic names (sec_1, section_01, s4_tit) to meaningful names."""
        slug = _slug(name)
        # User overrides first
        if slug in self.name_overrides:
            return self.name_overrides[slug]
        # Built-in generic remap (exact match)
        if slug in self.GENERIC_REMAP:
            return self.GENERIC_REMAP[slug]
        # sec_N / section_N pattern
        m = re.match(r'^sec(?:tion)?_(\d+)$', slug)
        if m:
            num = m.group(1)
            return self.GENERIC_REMAP.get(f"sec_{num}", slug)
        # s{N}_{role} pattern (child referencing parent section number)
        m = re.match(r'^s(\d+)_(.+)$', slug)
        if m:
            num, role = m.group(1), m.group(2)
            parent_name = self.GENERIC_REMAP.get(f"sec_{num}")
            if parent_name:
                return f"{parent_name}_{role}"
        # Frame NNN, Group NNN, el NNN patterns → generic, just use role
        m = re.match(r'^(?:frame|group|el|element|clip_path_group)_?\d*$', slug)
        if m:
            return slug  # keep as-is, will show as MINOR in validator
        return slug

    def _is_generic_slug(self, slug: str) -> bool:
        return bool(self.GENERIC_NAME_PATTERN.match(slug))

    def _parent_context_slug(self, parent_cls: str) -> str:
        """Extract a meaningful parent context token from parent class name."""
        if not parent_cls:
            return ""
        parent = parent_cls
        page_prefix = f"{self.page}_"
        if parent.startswith(page_prefix):
            parent = parent[len(page_prefix):]
        parent = re.sub(r"_\d+$", "", parent)
        tokens = [t for t in parent.split("_") if t]
        for token in reversed(tokens):
            if token in self.GENERIC_PARENT_STOPWORDS:
                continue
            if self._is_generic_slug(token):
                continue
            return token
        return ""

    def _generic_role_slug(self, slug: str) -> str:
        """Normalize generic child role names to a stable semantic token."""
        role = re.sub(r"_?\d+$", "", slug)
        return self.GENERIC_ROLE_MAP.get(role, role or "item")

    def _contextual_slug(self, name: str, parent_cls: str = "") -> str:
        """Resolve class slug with parent context for generic child names."""
        slug = self._remap_name(_slug(name))
        if not self._is_generic_slug(slug):
            return slug
        parent_context = self._parent_context_slug(parent_cls)
        if not parent_context or self._is_generic_slug(parent_context):
            return slug
        role = self._generic_role_slug(slug)
        return f"{parent_context}_{role}"

    # Long/meaningless image name patterns to simplify
    NOISY_IMAGE_PREFIXES = {"gettyimages", "unsplash", "shutterstock", "stock", "mask_group", "clip_path_group"}

    def _contextual_image_slug(self, name: str, parent_cls: str = "") -> tuple[str, bool]:
        """Build image slug with parent context for duplicate-prone names."""
        slug = self._remap_name(_slug(name))
        parent_context = self._parent_context_slug(parent_cls)
        base_slug = re.sub(r"_\d+$", "", slug)
        # Simplify noisy stock photo / mask group names
        for prefix in self.NOISY_IMAGE_PREFIXES:
            if slug.startswith(prefix):
                if parent_context:
                    return f"{parent_context}_bg", True
                return "bg", True
        should_contextualize = bool(parent_context) and (
            self._is_generic_slug(slug) or base_slug in self.IMAGE_CONTEXT_NAMES
        )
        if should_contextualize:
            return f"{parent_context}_{base_slug}", True
        return slug, False

    def _cls(self, name: str, is_common: bool = False, parent_cls: str = "",
             reuse: bool = False) -> str:
        """Generate class. Common areas get no page prefix. Generic names remapped.
        reuse=True: return same class without incrementing counter (for list siblings)."""
        slug = self._contextual_slug(name, parent_cls)
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
        if reuse:
            return base
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
        if gap and gap != "0" and gap != "0px":
            p["gap"] = gap
        pad = layout.get("padding")
        if pad and pad != "0":
            # Clean up 0px → 0, then check if all-zero
            clean = re.sub(r'\b0px\b', '0', pad).strip()
            parts = clean.split()
            if any(v != "0" for v in parts):
                p["padding"] = clean
        j = layout.get("justify")
        if j and j != "flex-start":  # flex-start is default
            p["justify-content"] = j
        a = layout.get("align")
        if a and a not in ("stretch", "flex-start"):  # stretch/flex-start are defaults
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

    # Default font declared in reset.css — skip to avoid redundancy
    DEFAULT_FONTS = {"pretendard"}

    def _segment_to_css(self, style: dict) -> dict[str, str]:
        """Extract ALL text CSS from a single segment style. No omission."""
        p: dict[str, str] = {}
        ff = style.get("fontFamily")
        if ff and ff.lower() not in self.DEFAULT_FONTS:
            p["font-family"] = f"'{ff}', sans-serif"
        if style.get("fontSize"):
            p["font-size"] = str(style["fontSize"])
        fw = style.get("fontWeight")
        if fw and str(fw) != "400":  # 400 is default, skip
            p["font-weight"] = str(fw)
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

    def _is_list(self, children: list[dict], parent_name: str = "") -> bool:
        """Detect repeating list pattern — 3+ similar children (strict)."""
        if len(children) < 3:
            return False
        # Layout wrapper names are never lists
        wrapper_names = {"inner", "cont", "wrap", "wrapper", "title", "top", "bottom",
                         "info", "txt", "bg_img", "frame"}
        if _slug(parent_name) in wrapper_names:
            return False
        types = set(c.get("type") for c in children)
        # Allow mix of FRAME/INSTANCE/GROUP — all are container types
        if not types.issubset({"FRAME", "INSTANCE", "GROUP"}):
            return False
        counts = [len(c.get("children", [])) for c in children]
        if not counts or max(counts) - min(counts) > 2:
            return False
        # Children should have similar names (e.g. list_item, card, frame_322)
        names = [c.get("name", "") for c in children]
        # If children have diverse names, likely not a list
        base_names = set(_slug(n).rstrip("_0123456789") for n in names)
        if len(base_names) > 2:
            return False
        return True

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

    def _has_text_descendant(self, node: dict) -> bool:
        """Check if any descendant has text content."""
        if node.get("text"):
            return True
        for child in node.get("children", []):
            if self._has_text_descendant(child):
                return True
        return False

    def _should_keep_fixed_width(self, node: dict) -> bool:
        """Keep width behavior for decorative/image/divider nodes."""
        if self._is_decorative(node) or self._is_divider(node):
            return True
        return bool(self.image_map.get(node.get("id", "")))

    def _flex_sizing_css(self, node: dict, siblings: list[dict]) -> dict[str, str]:
        """Convert Figma sizing metadata to flex sizing CSS."""
        sizing = (node.get("layout") or {}).get("sizing", {})
        horizontal = sizing.get("horizontal", "FIXED")
        visual = node.get("visual") or {}
        width = visual.get("width")

        if horizontal == "FILL":
            return {"flex": "1"}
        if horizontal == "HUG":
            return {}
        if horizontal == "FIXED" and width and siblings:
            try:
                total_width = sum(
                    float((s.get("visual") or {}).get("width", 0) or 0)
                    for s in siblings
                )
                width_value = float(width)
            except (TypeError, ValueError):
                return {}
            if total_width > 0:
                pct = round(width_value / total_width * 100, 1)
                pct_str = str(int(pct)) if pct.is_integer() else str(pct)
                return {"flex": f"0 0 {pct_str}%"}
        return {}

    # ── Rendering ──

    def _should_unwrap(self, node: dict) -> bool:
        """Check if this wrapper node should be removed to reduce DOM depth.
        Unwrap if: no meaningful visual styling, single child.
        Layout props (gap/padding) are transferred to child.
        Also unwrap multi-child wrappers that add no visual styling and only
        have layout direction matching the parent (redundant flex container)."""
        if node.get("text"):
            return False
        children = node.get("children", [])
        if len(children) == 0:
            return True  # empty container, will be caught by _is_empty_node too
        if len(children) != 1:
            return False
        layout = node.get("layout")
        visual = node.get("visual", {})
        has_styling = (
            visual.get("background") or
            visual.get("border") or
            (visual.get("borderRadius") and visual["borderRadius"] != "0")
        )
        if has_styling:
            return False
        # Transfer layout props to single child before unwrapping
        if layout:
            child = children[0]
            if not child.get("layout"):
                child["layout"] = {}
            child_layout = child["layout"]
            # Transfer padding if child doesn't have its own
            pad = layout.get("padding", "0")
            if pad != "0" and child_layout.get("padding", "0") == "0":
                child_layout["padding"] = pad
            # Transfer gap
            gap = layout.get("gap", "0")
            if gap != "0" and child_layout.get("gap", "0") == "0":
                child_layout["gap"] = gap
            # Transfer direction
            d = layout.get("direction")
            if d and not child_layout.get("direction"):
                child_layout["direction"] = d
            # Transfer display
            if not child_layout.get("display"):
                child_layout["display"] = layout.get("display", "flex")
        return True

    def _is_vector_group(self, node: dict) -> bool:
        """Detect groups that contain only vectors/rectangles (SVG/icon groups).
        These should be skipped — they need image-map to render properly."""
        if node.get("text"):
            return False
        children = node.get("children", [])
        if not children:
            return False
        vector_count = 0
        text_count = 0
        frame_count = 0
        def count_types(n):
            nonlocal vector_count, text_count, frame_count
            ntype = n.get("type", "")
            if ntype in ("VECTOR", "ELLIPSE", "LINE", "BOOLEAN_OPERATION",
                         "STAR", "REGULAR_POLYGON", "RECTANGLE"):
                vector_count += 1
            elif ntype == "TEXT":
                text_count += 1
            elif ntype in ("FRAME", "INSTANCE", "GROUP"):
                frame_count += 1
            for c in n.get("children", []):
                count_types(c)
        count_types(node)
        # Pure vector/rectangle group with no text = illustration/icon
        if text_count == 0 and vector_count >= 2:
            return True
        # Icon-like: mostly vectors with 1 text label at most
        if vector_count >= 3 and text_count <= 1:
            return True
        return False

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
                    tb = int(float(parts[0]))
                    if len(parts) == 2:
                        props["padding"] = f"{tb}px 0" if tb > 0 else ""
                    elif len(parts) == 4:
                        bt = int(float(parts[2]))
                        if tb == 0 and bt == 0:
                            props.pop("padding", None)
                        else:
                            props["padding"] = f"{tb}px 0 {bt}px 0"
            except (ValueError, IndexError):
                pass
        return props

    def _is_empty_node(self, node: dict) -> bool:
        """Empty node: no text, no children, no image-map hit, not decorative with bg."""
        if node.get("text") or node.get("children"):
            return False
        if self.image_map.get(node.get("id", "")):
            return False
        # Decorative with background is a visual element (dot, divider)
        v = node.get("visual", {})
        if v.get("background"):
            return False
        return True

    def _render(self, node: dict, depth: int = 0, parent_cls: str = "") -> None:
        # Skip empty nodes (common.md: empty div forbidden)
        if depth > 0 and self._is_empty_node(node):
            return

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
        pending_flex_css = dict(node.pop("_flex_sizing_css", {}))

        # Component template hit (footer, header)
        component_name = _slug(name)
        template_dir = Path(__file__).resolve().parent / "component-templates"
        template_path = template_dir / f"{component_name}.py"
        if template_path.exists() and depth <= 2:
            spec = importlib.util.spec_from_file_location(component_name, template_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            html = mod.render(node, self.image_map, self.css_rules)
            for line in html.split("\n"):
                self.html_lines.append(f"{indent}{line}")
            return

        # Image map hit
        img_path = self.image_map.get(node_id)
        if img_path:
            image_slug, used_context = self._contextual_image_slug(name, parent_cls)
            cls = self._cls(image_slug, parent_cls=parent_cls)
            is_bg = any(kw in name.lower() for kw in
                        ("bg_img", "bg", "cover", "gettyimages", "배경"))
            alt_text = image_slug.replace("_", " ") if used_context else name

            if is_bg:
                bg_cls = f"{cls}_bg"
                self._emit(f".{bg_cls}", {
                    "position": "absolute", "top": "0", "left": "0",
                    "width": "100%", "height": "100%", "z-index": "0"
                })
                self._emit(f".{bg_cls} img", {
                    "width": "100%", "height": "100%", "object-fit": "cover"
                })
                self.html_lines.append(
                    f'{indent}<div class="{bg_cls}"><img src="{img_path}" alt="{alt_text}"></div>')
            else:
                props = {"max-width": "100%", "height": "auto"}
                props.update(pending_flex_css)
                self._emit(f".{cls}", props)
                self.html_lines.append(
                    f'{indent}<div class="img_area"><img class="{cls}" src="{img_path}" alt="{alt_text}"></div>')
            return

        # Vector illustration groups (3+ vectors, no text) → skip entirely
        if self._is_vector_group(node):
            return

        # Depth limiter: only flatten truly empty wrappers (no styling at all)
        # Keep all nodes that have layout (gap/padding) or visual styling
        if depth >= 5 and children and not text and not img_path:
            layout_has_value = layout and (
                layout.get("gap", "0") != "0" or
                layout.get("padding", "0") != "0"
            )
            has_visual = visual and (
                visual.get("background") or visual.get("border")
            )
            if not layout_has_value and not has_visual and not self._has_text_descendant(node):
                for child in children:
                    self._render(child, depth, parent_cls)
                return

        # Decorative vectors
        if self._is_decorative(node):
            bg = (visual or {}).get("background")
            if bg:
                cls = self._cls(name, parent_cls=parent_cls)
                self._emit(f".{cls}", {"background-color": bg, "display": "block"})
                self.html_lines.append(f"{indent}<span class=\"{cls}\"></span>")
            return

        # Dividers
        if self._is_divider(node):
            cls = self._cls(name, parent_cls=parent_cls)
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
            tag = text.get("tag_hint", "span")
            segments = text.get("segments", [])
            use_parent_sel = node.pop("_use_parent_selector", False)
            parent_css_cls = node.pop("_parent_css_cls", "")
            selector_suffix = node.pop("_selector_suffix", "")

            # Build CSS properties
            text_css: dict[str, str] = {}
            text_css.update(self._fix_padding(self._layout_to_css(layout)))
            text_css.update(self._visual_to_css(visual, bool(layout)))
            text_css.update(pending_flex_css)
            if segments:
                base_style = segments[0]["style"]
                base_css = self._segment_to_css(base_style)
                if text_css.get("background-color") == base_css.get("color"):
                    del text_css["background-color"]
                text_css.update(base_css)

            if use_parent_sel and parent_css_cls:
                # common.md: use .parent tag selector — no individual class
                css_selector = f".{parent_css_cls} {tag}{selector_suffix}"
                self._emit(css_selector, text_css)
                html_open = f"<{tag}>"
            else:
                text_reuse = node.pop("_reuse_cls", False)
                cls = self._cls(name, parent_cls=parent_cls, reuse=text_reuse)
                self._emit(f".{cls}", text_css)
                html_open = f"<{tag} class=\"{cls}\">"

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
                            if use_parent_sel and parent_css_cls:
                                seg_selector = f".{parent_css_cls} {tag} span:nth-of-type({i})"
                                self._emit(seg_selector, diff)
                                parts.append(f"<span>{seg_text}</span>")
                            else:
                                seg_cls = f"{cls}_s{i}"
                                self._emit(f".{seg_cls}", diff)
                                parts.append(f'<span class="{seg_cls}">{seg_text}</span>')
                        else:
                            parts.append(seg_text)
                inner = "".join(parts)
            else:
                inner = text.get("content", "").replace("\n", "<br>")

            self.html_lines.append(f"{indent}{html_open}{inner}</{tag}>")
            return

        # ── Container nodes ──
        reuse = node.pop("_reuse_cls", False)
        cls = self._cls(name, parent_cls=parent_cls, reuse=reuse)
        container_css = {}
        container_css.update(self._fix_padding(self._layout_to_css(layout)))
        container_css.update(self._visual_to_css(visual, bool(layout)))
        container_css.update(pending_flex_css)

        # Content on top of background
        if node.get("_needs_z_index"):
            container_css["position"] = "relative"
            container_css["z-index"] = "1"

        # Detect sections with bg_img or background image children
        # These need position:relative with bg as absolute overlay
        has_bg_child = any(
            c.get("name", "") in ("bg_img", "cover") or
            (self.image_map.get(c.get("id", "")) and
             any(kw in c.get("name", "").lower() for kw in ("bg", "cover", "gettyimages", "배경")))
            for c in children
        )
        if has_bg_child and depth <= 3:
            container_css["position"] = "relative"
            container_css["overflow"] = "hidden"

        self._emit(f".{cls}", container_css)

        # If this container has bg children, non-bg children need z-index
        if has_bg_child and depth <= 3:
            for child in children:
                child_name = child.get("name", "").lower()
                child_id = child.get("id", "")
                is_child_bg = any(kw in child_name for kw in ("bg_img", "bg", "cover", "gettyimages"))
                is_child_bg = is_child_bg or (self.image_map.get(child_id, "") and
                    any(kw in child_name for kw in ("bg", "cover", "gettyimages")))
                if not is_child_bg and not child.get("text") and child.get("children"):
                    # Mark content wrapper to have position:relative + z-index
                    child_layout = child.get("layout", {})
                    if child_layout or child.get("children"):
                        child["_needs_z_index"] = True

        is_list = self._is_list(children, name)
        if not is_list and children:
            flex_targets = [c for c in children if not self._should_keep_fixed_width(c)]
            if len(flex_targets) >= 2:
                for child in flex_targets:
                    flex_css = self._flex_sizing_css(child, flex_targets)
                    if flex_css:
                        child["_flex_sizing_css"] = flex_css

        # Analyze children tags for parent+tag selector strategy (common.md rule)
        # Priority: 1) unique tag → .parent tag  2) multiple same tag → .parent tag:nth-of-type(N)
        if children:
            text_children = [(i, c) for i, c in enumerate(children) if c.get("text")]
            tag_counts: dict[str, int] = {}
            tag_indices: dict[str, int] = {}  # per-tag occurrence counter
            for _, child in text_children:
                ctag = child["text"].get("tag_hint", "span")
                tag_counts[ctag] = tag_counts.get(ctag, 0) + 1
            for _, child in text_children:
                ctag = child["text"].get("tag_hint", "span")
                count = tag_counts.get(ctag, 0)
                if count == 1:
                    # Unique tag → .parent tag
                    child["_use_parent_selector"] = True
                    child["_parent_css_cls"] = cls
                    child["_selector_suffix"] = ""
                elif count <= 4:
                    # Multiple same tag → .parent tag:first-child / + tag
                    idx = tag_indices.get(ctag, 0)
                    tag_indices[ctag] = idx + 1
                    child["_use_parent_selector"] = True
                    child["_parent_css_cls"] = cls
                    if idx == 0:
                        child["_selector_suffix"] = ":first-of-type"
                    else:
                        child["_selector_suffix"] = f":nth-of-type({idx + 1})"

        # Mark list children (and all descendants) to reuse same class
        if is_list:
            def _mark_reuse(n):
                n["_reuse_cls"] = True
                for c in n.get("children", []):
                    _mark_reuse(c)
            for child in children:
                _mark_reuse(child)

        tag_open = f'<ul class="{cls}">' if is_list else f'<div class="{cls}">'
        tag_close = "</ul>" if is_list else "</div>"

        lines_before = len(self.html_lines)
        self.html_lines.append(f"{indent}{tag_open}")
        for child in children:
            if is_list:
                self.html_lines.append(f"{indent}  <li>")
                li_before = len(self.html_lines)
                self._render(child, depth + 2, cls)
                if len(self.html_lines) == li_before:
                    # Empty li — remove it
                    self.html_lines.pop()  # remove <li>
                else:
                    self.html_lines.append(f"{indent}  </li>")
            else:
                self._render(child, depth + 1, cls)

        # If container has no rendered children, remove it (empty div forbidden)
        if len(self.html_lines) == lines_before + 1:
            self.html_lines.pop()  # remove the opening tag
            # Also remove CSS rule for this empty container
            self.css_rules.pop(f".{cls}", None)
        else:
            self.html_lines.append(f"{indent}{tag_close}")

    # ── Output ──

    def _skip_root_wrappers(self, tree: dict) -> list[dict]:
        """Skip Figma root wrapper frames (A_main > inner) to reduce DOM depth.
        Returns the actual content children to render."""
        children = tree.get("children", [])
        # If root has children like 'inner' + 'quick', flatten one level
        if len(children) <= 3:
            result = []
            for child in children:
                name = child.get("name", "").lower()
                # 'inner' is a common Figma wrapper — unwrap its children
                if name == "inner" and child.get("children"):
                    result.extend(child["children"])
                else:
                    result.append(child)
            return result
        return children

    def _flatten_redundant_wrappers(self, node: dict) -> dict:
        """Pre-process: collapse single-child wrappers with no visual styling.
        Transfers layout props down and removes unnecessary nesting."""
        children = node.get("children", [])
        # Recurse first
        node["children"] = [self._flatten_redundant_wrappers(c) for c in children]
        children = node.get("children", [])

        if len(children) != 1 or node.get("text"):
            return node
        child = children[0]
        # Don't unwrap if this node has visual styling
        v = node.get("visual", {})
        if v.get("background") or v.get("border") or \
           (v.get("borderRadius") and v["borderRadius"] != "0"):
            return node
        # Don't unwrap component templates or image-map hits
        if self.image_map.get(node.get("id", "")):
            return node
        # Transfer layout to child
        layout = node.get("layout")
        if layout:
            if not child.get("layout"):
                child["layout"] = {}
            cl = child["layout"]
            for key in ("padding", "gap", "direction", "display"):
                val = layout.get(key)
                if val and val != "0" and not cl.get(key):
                    cl[key] = val
        # Replace node with child (unwrap)
        return child

    def convert(self, data: dict) -> tuple[str, str, str]:
        """Returns (html, common.css, reset.css)."""
        meta = data["meta"]
        # Skip root wrappers (A_main > inner) to reduce DOM depth
        content_nodes = self._skip_root_wrappers(data["tree"])
        # Pre-process: 1) remove empty nodes, 2) flatten redundant wrappers
        def _prune_empty(node):
            children = node.get("children", [])
            node["children"] = [_prune_empty(c) for c in children
                                if not self._is_empty_node(c)]
            return node
        content_nodes = [_prune_empty(n) for n in content_nodes]
        content_nodes = [self._flatten_redundant_wrappers(n) for n in content_nodes]
        for node in content_nodes:
            self._render(node, depth=1)

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

{chr(10).join(l.replace(chr(0x2028), "").replace(chr(0x2029), "") for l in self.html_lines)}

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

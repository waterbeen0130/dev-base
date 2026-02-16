#!/usr/bin/env python3
import argparse
import copy
import html
import json
import os
import re

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover
    BeautifulSoup = None


STYLE_OVERRIDE_KEYS = (
    "fontFamily",
    "fontPostScriptName",
    "fontStyle",
    "fontWeight",
    "textAutoResize",
    "textAlignHorizontal",
    "textAlignVertical",
    "fontSize",
    "lineHeightPx",
    "lineHeightPercent",
    "lineHeightPercentFontSize",
    "lineHeightUnit",
    "letterSpacing",
    "textDecoration",
    "textCase",
)

INLINE_TEXT_HINTS = (
    "브레인바디",
    "BrainBody",
    "MRI",
    "MRI 검진",
    "비급여",
    "건강보험",
    "그린몰 원스톱",
    "Greenmall",
    "영상의학과",
    "원스톱 토탈케어",
    "원스톱",
    "토탈케어",
)

INLINE_TEXT_EXACT_HINTS = (
    "브레인바디",
    "BrainBody",
    "BrainBody+MRI",
    "BrainBody + MRI",
    "MRI 검진",
    "그린몰 원스톱 토탈케어 시스템",
    "그린몰 원스톱",
    "Greenmall One-Stop Process",
)

BLOCK_TEXT_KEYWORDS = (
    "됩니다",
    "있습니다",
    "합니다",
    "말씀",
    "수 있습니다",
    "필요합니다",
    "확인됩니다",
)

PARAGRAPH_TERMS = (
    "결과",
    "결국",
    "때문",
    "확인됩니다",
    "필요합니다",
    "필요",
    "관리",
    "검사",
)

PARAGRAPH_PATTERN = re.compile(r"[.?!]\Z|습니다$|됩니다$|입니다$|있습니다$|됩니다\.$|필요합니다|확인합니다|판독")

HEADING_LEVEL_FROM_NAME = {
    "heading 1": "h1",
    "heading 2": "h2",
    "heading 3": "h3",
    "heading 4": "h4",
    "heading 5": "h5",
    "heading 6": "h6",
}


def _px(value):
    if value is None:
        return None
    if isinstance(value, (int, float)) and float(value).is_integer():
        return f"{int(value)}px"
    return f"{value}px"


def _rgba_from_fill(fill):
    if not isinstance(fill, dict):
        return None
    if fill.get("type") != "SOLID" or not isinstance(fill.get("color"), dict):
        return None
    color = fill["color"]
    r = int(color.get("r", 0) * 255)
    g = int(color.get("g", 0) * 255)
    b = int(color.get("b", 0) * 255)
    a = round(color.get("a", 1), 2)
    return f"rgba({r}, {g}, {b}, {a})"


def _is_inline_label_text(text):
    normalized = text.strip()
    if not normalized:
        return False
    return any(hint.lower() in normalized.lower() for hint in INLINE_TEXT_HINTS) or any(
        exact in normalized for exact in INLINE_TEXT_EXACT_HINTS
    )


def _infer_text_tag(node_name, parent_name, visible_text, style):
    node_key = (node_name or "").lower()
    parent_key = (parent_name or "").lower()
    visible_key = (visible_text or "").strip().lower()
    font_size = style.get("fontSize")
    font_weight = style.get("fontWeight") or 0

    if _is_inline_label_text(visible_text):
        return "span"

    if visible_key:
        for key, tag in HEADING_LEVEL_FROM_NAME.items():
            if key in visible_key:
                return tag
            if key in parent_key:
                return tag

    if font_size is not None and font_size >= 70:
        return "h1" if font_weight >= 700 else "h2"

    for key, tag in HEADING_LEVEL_FROM_NAME.items():
        if key in node_key:
            return tag
        if key in parent_key:
            return tag

    if font_size is not None:
        if font_size >= 80:
            return "h1"
        if font_size >= 60:
            return "h2"
        if font_size >= 50:
            return "h3"
        if font_size >= 37 and font_weight >= 700:
            return "h4"

    return "span"


def _is_textual_block(text, style):
    font_size = style.get("fontSize") or 0
    line_count = text.count("\n") + 1
    plain = text.replace("\n", "").strip()
    plain_len = len(plain)

    if not plain:
        return False
    if "\n" in text:
        return True
    if line_count > 1:
        return True
    if any(keyword in plain for keyword in INLINE_TEXT_HINTS):
        return False
    if any(keyword in plain for keyword in PARAGRAPH_TERMS):
        return True
    if plain_len <= 45 and font_size <= 55:
        return False
    if plain_len > 95:
        return True
    if font_size >= 55:
        return True
    if line_count == 1 and font_size >= 50 and plain_len >= 40:
        return True
    if any(keyword in plain for keyword in BLOCK_TEXT_KEYWORDS):
        return True
    if PARAGRAPH_PATTERN.search(plain):
        return True
    return False


def _normalize_text_for_semantic(node, node_name, parent_name, style):
    text = (node.get("characters") or "")
    font_size = style.get("fontSize")
    plain = text.replace("\n", "").strip()

    if not plain:
        return "span"
    if "\n" in text:
        return "p"

    inferred = _infer_text_tag(node_name, parent_name, text, style)
    if _is_textual_block(text, style):
        return "p" if inferred == "span" else inferred

    if font_size is not None and font_size >= 28 and len(plain) >= 20:
        return "p" if inferred == "span" else inferred

    if plain in ("브레인바디", "MRI", "브레인바디+MRI", "BrainBody", "MRI 검진"):
        return "span"

    label_like = len(plain) <= 45 and "\n" not in plain
    if not label_like:
        return "p"
    if len(plain) <= 24:
        return "span"
    if len(plain.split()) >= 6:
        return "p"
    if PARAGRAPH_PATTERN.search(plain):
        return "p"
    if re.search(r"[:;,/]", plain):
        return "p"

    return inferred


def _style_to_rule_text(style, fills, *, inline=False):
    declarations = []
    merged_style = copy.deepcopy(style or {})
    merged_fills = copy.deepcopy(fills or [])

    if merged_style.get("fontFamily"):
        value = html.escape(str(merged_style["fontFamily"]))
        declarations.append(("font-family", value))
    if merged_style.get("fontSize") is not None:
        declarations.append(("font-size", _px(merged_style["fontSize"])))
    if merged_style.get("fontWeight") is not None:
        declarations.append(("font-weight", merged_style["fontWeight"]))
    if merged_style.get("letterSpacing") is not None:
        declarations.append(("letter-spacing", f"{merged_style['letterSpacing']}px"))
    if merged_style.get("lineHeightPx") is not None:
        declarations.append(("line-height", _px(merged_style["lineHeightPx"])))
    if merged_fills:
        color = _rgba_from_fill(merged_fills[0])
        if color:
            declarations.append(("color", color))

    if not declarations:
        return ""
    return " ".join(f"{name}: {value}" for name, value in declarations) if not inline else " ".join(
        f"{name}: {value};" for name, value in declarations
    )


def _style_to_inline(style, fills):
    return _style_to_rule_text(style, fills, inline=True)


def _merge_style(base_style, base_fills, prev_style, prev_fills, override_entry):
    if not isinstance(override_entry, dict):
        return copy.deepcopy(base_style or {}), copy.deepcopy(base_fills or [])

    merged_style = copy.deepcopy((prev_style if prev_style else base_style) or {})
    merged_fills = copy.deepcopy(prev_fills or base_fills or [])

    if override_entry.get("style") and isinstance(override_entry.get("style"), dict):
        merged_style.update(copy.deepcopy(override_entry["style"]))

    for key in STYLE_OVERRIDE_KEYS:
        if key in override_entry:
            merged_style[key] = override_entry[key]

    if "fills" in override_entry:
        merged_fills = copy.deepcopy(override_entry.get("fills"))

    return merged_style, merged_fills


def _iter_style_runs(text, style_overrides, style_table):
    if not style_overrides or not style_table:
        yield 0, text
        return
    if len(style_overrides) != len(text):
        for idx, ch in enumerate(text):
            ov = style_overrides[idx] if idx < len(style_overrides) else 0
            yield ov, ch
        return

    start = 0
    current_id = style_overrides[0]
    for idx, oid in enumerate(style_overrides):
        if idx == 0:
            continue
        if oid != current_id:
            run = text[start:idx]
            if run:
                yield current_id, run
            current_id = oid
            start = idx
    tail = text[start:]
    if tail:
        yield current_id, tail


def _escape_with_breaks(value):
    return html.escape(value).replace("\n", "<br>")


def _build_text_html(child):
    text_content = child.get("characters", "")
    base_style = child.get("style", {})
    base_fills = child.get("fills", [])
    style_overrides = child.get("characterStyleOverrides") or []
    style_table = child.get("styleOverrideTable") or {}

    override_ids = [0] + [int(k) for k in style_table.keys()] if style_table else [0]
    if len(style_overrides) != len(text_content) or len(set(override_ids)) <= 1:
        return _escape_with_breaks(text_content)

    pieces = []
    prev_style = None
    prev_fills = None

    for style_id, run in _iter_style_runs(text_content, style_overrides, style_table):
        if style_id == 0:
            run_style = copy.deepcopy(base_style)
            run_fills = copy.deepcopy(base_fills)
        else:
            override_entry = style_table.get(str(style_id), {})
            if override_entry:
                run_style, run_fills = _merge_style(base_style, base_fills, prev_style, prev_fills, override_entry)
            else:
                run_style = copy.deepcopy(base_style)
                run_fills = copy.deepcopy(base_fills)

        if run_style == base_style and run_fills == base_fills:
            pieces.append(_escape_with_breaks(run))
        else:
            inline_style = _style_to_inline(run_style, run_fills)
            if inline_style:
                pieces.append(f'<span style="{inline_style}">{_escape_with_breaks(run)}</span>')
            else:
                pieces.append(_escape_with_breaks(run))

        prev_style = run_style
        prev_fills = run_fills

    return "".join(pieces)


def _extract_node_html(node, parent_name=""):
    node_type = node.get("type")

    if node_type == "TEXT":
        text_html = _build_text_html(node)
        style = node.get("style", {})
        tag_name = _normalize_text_for_semantic(node, node.get("name"), parent_name, style)
        return f'<{tag_name} class="motion_section" data-delay="0.2" data-direction="bottom">{text_html}</{tag_name}>\n'

    if node_type in ("RECTANGLE", "ELLIPSE", "VECTOR"):
        style_attrs = []
        if node.get("fills"):
            for fill in node["fills"]:
                if fill.get("type") == "IMAGE" and fill.get("imageRef"):
                    return (
                        f'<img src="img/placeholder_figma_image.png" alt="{node.get("name", "Figma Image")}" '
                        'class="motion_section" data-delay="0.3" data-direction="right">\n'
                    )
        if node.get("absoluteBoundingBox"):
            box = node["absoluteBoundingBox"]
            style_attrs.append(f"width: {box['width']}px;")
            style_attrs.append(f"height: {box['height']}px;")
        if style_attrs:
            style_str = "; ".join(style_attrs)
            return f'<div class="motion_section" data-delay="0.4" data-direction="left" style="{style_str}"></div>\n'
        return '<div class="motion_section" data-delay="0.4" data-direction="left"></div>\n'

    html_parts = []
    for child in node.get("children", []) or []:
        child_html = _extract_node_html(child, node.get("name", ""))
        if child_html:
            html_parts.append(child_html)
    return "".join(html_parts)


def _resolve_page_node(figma_data):
    page_node = figma_data
    if not page_node.get("children") and isinstance(page_node.get("document"), dict):
        if page_node.get("document", {}).get("children"):
            page_node = page_node["document"]

    if not page_node.get("children") and isinstance(page_node.get("nodes"), dict):
        page_nodes = list(page_node["nodes"].values())
        if page_nodes:
            first_node = page_nodes[0]
            if isinstance(first_node, dict) and isinstance(first_node.get("document"), dict):
                page_node = first_node["document"]

    return page_node


def _insert_into_template(template_html, generated_html_content):
    if BeautifulSoup is None:
        section_pattern = re.compile(
            r"(<section\\s+[^>]*class=['\\\"][^'\\\"]*container[^'\\\"]*['\\\"][^>]*>)([\\s\\S]*?)(</section>)",
            re.IGNORECASE,
        )
        if section_pattern.search(template_html):
            return section_pattern.sub(r"\\1\\n" + generated_html_content + r"\\3", template_html, count=1)

        main_pattern = re.compile(r"(<main[^>]*>)([\\s\\S]*?)(</main>)", re.IGNORECASE)
        if main_pattern.search(template_html):
            return main_pattern.sub(r"\\1\\n" + generated_html_content + r"\\3", template_html, count=1)

        raise RuntimeError(
            "BeautifulSoup(bs4) 없음 + 템플릿에서 교체 가능한 <section class='container'> 또는 <main>을 찾지 못했습니다."
        )

    soup = BeautifulSoup(template_html, "html.parser")
    container_section = soup.find("section", class_="container")
    if container_section:
        container_section.clear()
        container_section.append(BeautifulSoup(generated_html_content, "html.parser"))
        return str(soup)

    main_section = soup.find("main")
    if main_section:
        main_section.clear()
        main_section.append(BeautifulSoup(generated_html_content, "html.parser"))
        return str(soup)

    raise RuntimeError("템플릿 HTML에서 <section class='container'> 또는 <main>을 찾지 못했습니다.")


def generate_html_from_figma(figma_json_path, template_html_path, output_html_path=None):
    with open(figma_json_path, "r", encoding="utf-8") as f:
        figma_data = json.load(f)

    page_node = _resolve_page_node(figma_data)
    if not page_node.get("children"):
        raise RuntimeError("Figma 페이지 노드에 'children'이 없습니다.")

    generated_html_content = "".join(_extract_node_html(child) for child in page_node["children"])
    if not generated_html_content:
        raise RuntimeError("Figma 데이터에서 HTML 콘텐츠를 생성하지 못했습니다.")

    with open(template_html_path, "r", encoding="utf-8") as f:
        template_html = f.read()

    final_html = _insert_into_template(template_html, generated_html_content)

    output_path = output_html_path or template_html_path
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate HTML from Figma JSON with BrainBody-preserving tag rules.")
    parser.add_argument("figma_json_path", help="Figma JSON path (e.g., figma_grinmall_brianbody_260212_page.json)")
    parser.add_argument("template_html_path", help="Template HTML file path to insert content")
    parser.add_argument("-o", "--output", dest="output_html_path", default=None, help="Output HTML path (default: template path)")
    args = parser.parse_args()

    try:
        output_path = generate_html_from_figma(args.figma_json_path, args.template_html_path, args.output_html_path)
    except FileNotFoundError as exc:
        raise SystemExit(f"오류: 파일을 찾을 수 없습니다 - {exc.filename}")
    except json.JSONDecodeError:
        raise SystemExit(f"오류: JSON 파싱 실패 - {args.figma_json_path}")
    except Exception as exc:
        raise SystemExit(f"오류: {exc}")

    print(f"수정된 HTML 파일 저장 완료: {output_path}")


if __name__ == "__main__":
    main()

"""Header component template."""
from typing import Any


def _find_by_name(node: dict, target: str) -> dict | None:
    if node.get("name", "").lower() == target.lower():
        return node
    for c in node.get("children", []):
        found = _find_by_name(c, target)
        if found:
            return found
    return None


def _collect_menu_texts(node: dict) -> list[str]:
    texts = []
    for c in node.get("children", []):
        text = c.get("text")
        if text and text.get("content", "").strip():
            texts.append(text["content"].strip())
        elif c.get("children"):
            texts.extend(_collect_menu_texts(c))
    return texts


def render(node: dict, image_map: dict[str, str], css_rules: dict) -> str:
    layout = node.get("layout", {})
    visual = node.get("visual", {})

    # Logo image from image_map
    logo_path = None
    for nid, path in image_map.items():
        if "logo" in path:
            logo_path = path
            break

    # Menu icon
    ic_menu_path = None
    for nid, path in image_map.items():
        if "ic_menu" in path:
            ic_menu_path = path
            break

    # Menu items
    menu_node = _find_by_name(node, "menu")
    menu_items = _collect_menu_texts(menu_node) if menu_node else []

    # CSS
    bg = visual.get("background", "#fff")
    css_rules[".header"] = {
        "background": bg, "position": "sticky", "top": "0", "z-index": "100"
    }
    css_rules[".header .cont"] = {
        "display": "flex", "justify-content": "space-between",
        "align-items": "center", "height": "100px"
    }
    css_rules[".logo"] = {"flex-shrink": "0"}
    css_rules[".logo img"] = {"height": "50px", "width": "auto"}
    css_rules[".gnb ul"] = {"display": "flex", "gap": "50px", "align-items": "center"}
    css_rules[".gnb li a"] = {
        "font-size": "1.25rem", "font-weight": "700", "color": "#000", "white-space": "nowrap"
    }
    css_rules[".header_btn"] = {"cursor": "pointer"}
    css_rules[".header_btn img"] = {"width": "40px", "height": "40px"}

    lines = []
    lines.append('<header class="header">')
    lines.append('  <div class="cont">')

    # Logo
    if logo_path:
        lines.append(f'    <h1 class="logo"><a href="/"><img src="{logo_path}" alt="logo"></a></h1>')

    # GNB
    if menu_items:
        lines.append('    <nav class="gnb">')
        lines.append('      <ul>')
        for item in menu_items:
            lines.append(f'        <li><a href="#">{item}</a></li>')
        lines.append('      </ul>')
        lines.append('    </nav>')

    # Menu button
    if ic_menu_path:
        lines.append(f'    <div class="header_btn"><img src="{ic_menu_path}" alt="메뉴"></div>')

    lines.append('  </div>')
    lines.append('</header>')

    return "\n".join(lines)

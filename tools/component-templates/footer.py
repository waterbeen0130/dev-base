"""Footer component template.

Extracts text data from normalized JSON footer node and generates
semantic HTML with proper ul>li>a structure.
"""
from typing import Any


def _find_texts(node: dict, path: str = "") -> dict[str, str]:
    """Recursively collect all text content keyed by path."""
    result: dict[str, str] = {}
    name = node.get("name", "")
    if name == "bg_img":
        return result
    text = node.get("text")
    if text:
        result[f"{path}/{name}"] = text.get("content", "")
    for c in node.get("children", []):
        result.update(_find_texts(c, f"{path}/{name}"))
    return result


def _find_by_name(node: dict, target: str) -> dict | None:
    """Find first descendant node with matching name."""
    if node.get("name", "").lower() == target.lower():
        return node
    for c in node.get("children", []):
        found = _find_by_name(c, target)
        if found:
            return found
    return None


def _collect_menu_texts(node: dict) -> list[str]:
    """Collect TEXT node content from a menu container."""
    texts = []
    for c in node.get("children", []):
        text = c.get("text")
        if text and text.get("content", "").strip():
            content = text["content"].strip()
            # Skip separator dots
            if content in ("·", "•", "|", ""):
                continue
            texts.append(content)
        # Recurse into sub-containers
        if not text and c.get("children"):
            for cc in c.get("children", []):
                t = cc.get("text")
                if t and t.get("content", "").strip():
                    texts.append(t["content"].strip())
    return texts


def _extract_footer_css(node: dict) -> dict[str, str]:
    """Extract footer-level CSS from normalized data."""
    layout = node.get("layout", {})
    visual = node.get("visual", {})
    props = {}
    if layout.get("padding"):
        props["padding"] = layout["padding"]
    if visual.get("background"):
        props["background-color"] = visual["background"]
    return props


def render(node: dict, image_map: dict[str, str], css_rules: dict) -> str:
    """Render footer as semantic HTML. Returns HTML string."""

    # Find sub-components
    f_bar = _find_by_name(node, "f_bar")
    f_menu = _find_by_name(node, "f_menu")
    foot_menu = _find_by_name(node, "foot_menu")
    info_node = _find_by_name(node, "info") or _find_by_name(node, "정보")

    # Footer menu items
    menu_items = _collect_menu_texts(f_menu) if f_menu else []

    # Bottom links (개인정보, 이용약관, Top)
    bottom_links = _collect_menu_texts(foot_menu) if foot_menu else []

    # Info texts
    info_texts = []
    if info_node:
        all_texts = _find_texts(info_node)
        info_texts = [v for v in all_texts.values() if v.strip()]

    # Copyright
    copyright_text = ""
    for t in info_texts:
        if "COPYRIGHT" in t.upper():
            copyright_text = t
            info_texts.remove(t)
            break

    # Family Site text
    family_site = ""
    fs_node = _find_by_name(node, "Family Site")
    if fs_node and fs_node.get("text"):
        family_site = fs_node["text"]["content"]

    # SNS icons from image_map
    sns_images = []
    for nid, path in image_map.items():
        if "sns_" in path:
            name = path.replace("img/", "").replace(".png", "")
            sns_images.append((name, path))

    # Footer background
    bg_path = None
    for nid, path in image_map.items():
        if "footer_bg" in path:
            bg_path = path
            break

    # Extract CSS from f_bar
    if f_bar:
        bar_layout = f_bar.get("layout", {})
        bar_visual = f_bar.get("visual", {})
        bar_css = {}
        if bar_layout.get("padding"):
            bar_css["padding"] = bar_layout["padding"]
        if bar_visual.get("background"):
            bar_css["background-color"] = bar_visual["background"]
        if bar_visual.get("borderRadius") and bar_visual["borderRadius"] != "0":
            bar_css["border-radius"] = bar_visual["borderRadius"]
        bar_css["display"] = "flex"
        bar_css["justify-content"] = "space-between"
        bar_css["align-items"] = "center"
        css_rules[".footer_bar"] = bar_css

    # Footer CSS
    css_rules[".footer"] = {"position": "relative", "overflow": "hidden"}
    css_rules[".footer_bg"] = {"position": "absolute", "top": "0", "left": "0",
                                "width": "100%", "height": "100%", "z-index": "0"}
    css_rules[".footer_bg img"] = {"width": "100%", "height": "100%", "object-fit": "cover"}
    css_rules[".footer .cont"] = {"position": "relative", "z-index": "1",
                                   "padding": "50px 0", "display": "flex",
                                   "flex-direction": "column", "gap": "40px"}
    css_rules[".footer_top"] = {"display": "flex", "justify-content": "space-between",
                                 "align-items": "center"}
    css_rules[".footer_sns"] = {"display": "flex", "gap": "10px"}
    css_rules[".footer_sns li a img"] = {"width": "40px", "height": "40px"}
    css_rules[".footer_bar ul"] = {"display": "flex", "gap": "12px"}
    css_rules[".footer_bar li a"] = {"font-size": "0.9375rem", "color": "#fff"}
    css_rules[".f_family"] = {"font-size": "1rem", "color": "#fff",
                               "padding": "5px 30px", "background": "#508830",
                               "border-radius": "4px"}
    css_rules[".footer_links"] = {"display": "flex", "gap": "15px"}
    css_rules[".footer_links li a"] = {"font-size": "0.8125rem", "font-weight": "700",
                                        "color": "#424242"}
    css_rules[".footer address"] = {"font-size": "0.9375rem", "color": "#616161",
                                     "font-style": "normal", "line-height": "1.6"}
    css_rules[".copyright"] = {"font-size": "0.9375rem", "color": "#616161"}

    # Build HTML
    lines = []
    lines.append('<footer class="footer">')

    # Background
    if bg_path:
        lines.append(f'  <div class="footer_bg"><img src="{bg_path}" alt="footer background"></div>')

    lines.append('  <div class="cont">')

    # Top: SNS + Apply button
    if sns_images:
        lines.append('    <div class="footer_top">')
        lines.append('      <ul class="footer_sns">')
        for name, path in sns_images:
            alt = name.replace("sns_", "")
            lines.append(f'        <li><a href="#"><img src="{path}" alt="{alt}"></a></li>')
        lines.append('      </ul>')
        lines.append('    </div>')

    # Green bar with menu
    if menu_items:
        lines.append('    <div class="footer_bar">')
        lines.append('      <nav>')
        lines.append('        <ul>')
        for item in menu_items:
            lines.append(f'          <li><a href="#">{item}</a></li>')
        lines.append('        </ul>')
        lines.append('      </nav>')
        if family_site:
            lines.append(f'      <span class="f_family">{family_site}</span>')
        lines.append('    </div>')

    # Bottom links
    if bottom_links:
        lines.append('    <ul class="footer_links">')
        for link in bottom_links:
            lines.append(f'      <li><a href="#">{link}</a></li>')
        lines.append('    </ul>')

    # Info address
    if info_texts:
        lines.append('    <address>')
        lines.append('<br>'.join(info_texts))
        lines.append('    </address>')

    # Copyright
    if copyright_text:
        lines.append(f'    <span class="copyright">{copyright_text}</span>')

    lines.append('  </div>')
    lines.append('</footer>')

    return "\n".join(lines)

"""Quick menu (floating side buttons) component template."""
from typing import Any


def _find_text(node: dict) -> str:
    """Find first text content in node tree."""
    text = node.get("text")
    if text:
        return text.get("content", "")
    for c in node.get("children", []):
        found = _find_text(c)
        if found:
            return found
    return ""


def render(node: dict, image_map: dict[str, str], css_rules: dict) -> str:
    children = node.get("children", [])

    # CSS
    css_rules[".quick"] = {
        "position": "fixed", "right": "20px", "top": "50%",
        "transform": "translateY(-50%)", "display": "flex",
        "flex-direction": "column", "gap": "8px", "z-index": "100"
    }
    css_rules[".quick li a"] = {
        "display": "flex", "flex-direction": "column",
        "align-items": "center", "gap": "4px", "width": "70px",
        "text-align": "center"
    }
    css_rules[".quick li a span"] = {
        "font-size": "0.75rem", "font-weight": "600", "color": "#424242"
    }

    lines = []
    lines.append('<ul class="quick">')

    for child in children:
        node_id = child.get("id", "")
        name = child.get("name", "")
        label = _find_text(child) or name

        # Find image in image_map
        img_path = image_map.get(node_id)

        lines.append('  <li>')
        lines.append('    <a href="#">')
        if img_path:
            lines.append(f'      <img src="{img_path}" alt="{label}">')
        lines.append(f'      <span>{label}</span>')
        lines.append('    </a>')
        lines.append('  </li>')

    lines.append('</ul>')

    return "\n".join(lines)

#!/usr/bin/env python3
"""Validate generated HTML/CSS against normalized Figma section specs.

Usage:
  python3 tools/figma-validate.py --spec extracted/section_spec.json --html output.html --css output.css
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import types
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


if __name__ not in sys.modules:
    module_proxy = types.ModuleType(__name__)
    module_proxy.__dict__.update(globals())
    sys.modules[__name__] = module_proxy


VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

BOX_SIDES = ("top", "right", "bottom", "left")
FONT_FIELDS = ("font-family", "font-size", "font-weight", "line-height", "color")
INHERITED_PROPERTIES = {"font-family", "font-size", "font-weight", "line-height", "color", "letter-spacing"}


@dataclass
class Violation:
    category: str
    node: str
    expected: str
    actual: str


@dataclass
class DOMElement:
    tag: str
    attrs: dict[str, str]
    parent: DOMElement | None = None
    order: int = 0
    content: list[DOMElement | str] = field(default_factory=list)
    _text_cache: str | None = None

    @property
    def classes(self) -> set[str]:
        value = self.attrs.get("class", "")
        return {token for token in value.split() if token}

    @property
    def depth(self) -> int:
        depth = 0
        current = self.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth

    def add_child(self, child: DOMElement) -> None:
        self.content.append(child)

    def add_text(self, text: str) -> None:
        if text:
            self.content.append(text)

    def text_content(self) -> str:
        if self._text_cache is not None:
            return self._text_cache

        parts: list[str] = []
        for item in self.content:
            if isinstance(item, str):
                parts.append(item)
            elif item.tag == "br":
                parts.append("\n")
            else:
                parts.append(item.text_content())
        self._text_cache = "".join(parts)
        return self._text_cache

    def short_selector(self) -> str:
        tokens: list[str] = []
        current: DOMElement | None = self
        while current is not None and current.tag != "document" and len(tokens) < 4:
            token = current.tag
            if current.attrs.get("id"):
                token += f"#{current.attrs['id']}"
            elif current.classes:
                token += "".join(f".{name}" for name in sorted(current.classes)[:2])
            tokens.append(token)
            current = current.parent
        return " > ".join(reversed(tokens))


class SimpleHTMLDocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.root = DOMElement("document", {}, None, 0)
        self.stack: list[DOMElement] = [self.root]
        self.order = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs, push=tag.lower() not in VOID_TAGS)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs, push=False)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].add_text(data)

    def handle_entityref(self, name: str) -> None:
        self.stack[-1].add_text(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.stack[-1].add_text(unescape(f"&#{name};"))

    def _open(self, tag: str, attrs: list[tuple[str, str | None]], push: bool) -> None:
        self.order += 1
        attr_map = {key.lower(): (value or "") for key, value in attrs}
        element = DOMElement(tag.lower(), attr_map, self.stack[-1], self.order)
        self.stack[-1].add_child(element)
        if push:
            self.stack.append(element)


@dataclass
class CSSRule:
    selectors: list[str]
    declarations: dict[str, str]
    order: int
    pseudo_element: str | None = None


@dataclass
class PropertyValue:
    value: str
    selector: str
    specificity: tuple[int, int, int]
    order: int
    important: bool


@dataclass
class ElementMatch:
    element: DOMElement
    normalized_text: str
    raw_text: str


@dataclass(frozen=True)
class FrameMatchContext:
    depth: int
    area: float | None
    path_hint: str
    blocked_rule_keys: tuple[tuple[int, tuple[str, ...]], ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate HTML/CSS output against normalized Figma section spec")
    parser.add_argument("--spec", required=True, help="Path to section_spec.json")
    parser.add_argument("--html", required=True, help="Path to generated HTML")
    parser.add_argument("--css", required=True, help="Path to generated CSS")
    return parser.parse_args()


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def read_text(path_str: str) -> str:
    path = Path(path_str)
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"File not found: {path}")
    except OSError as exc:
        fail(f"Failed to read file: {path}\n{exc}")
    raise AssertionError("unreachable")


def load_spec(path_str: str) -> dict:
    raw = read_text(path_str)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: {path_str}\n{exc}")
    if not isinstance(payload, dict):
        fail(f"Invalid spec JSON: expected object at root ({path_str})")
    return payload


def normalize_text_for_match(text: str) -> str:
    text = text.replace("\u2028", "\n").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_hex(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value.startswith("#"):
        return None
    digits = value[1:]
    if len(digits) == 3 and re.fullmatch(r"[0-9a-fA-F]{3}", digits):
        digits = "".join(ch * 2 for ch in digits)
    elif len(digits) == 6 and re.fullmatch(r"[0-9a-fA-F]{6}", digits):
        pass
    else:
        return None
    return f"#{digits.lower()}"


def extract_hex_colors(value: str | None) -> list[str]:
    if not isinstance(value, str):
        return []
    colors: list[str] = []
    for match in re.findall(r"#[0-9a-fA-F]{3,6}", value):
        normalized = normalize_hex(match)
        if normalized:
            colors.append(normalized)
    return colors


def top_level_split(text: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    quote = ""
    for char in text:
        if quote:
            buf.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            continue
        if char == "(":
            depth += 1
            buf.append(char)
            continue
        if char == ")":
            depth = max(0, depth - 1)
            buf.append(char)
            continue
        if char == delimiter and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(char)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def split_whitespace_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    buf: list[str] = []
    depth = 0
    quote = ""
    for char in value.strip():
        if quote:
            buf.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            continue
        if char == "(":
            depth += 1
            buf.append(char)
            continue
        if char == ")":
            depth = max(0, depth - 1)
            buf.append(char)
            continue
        if char.isspace() and depth == 0:
            if buf:
                tokens.append("".join(buf).strip())
                buf = []
            continue
        buf.append(char)
    if buf:
        tokens.append("".join(buf).strip())
    return tokens


def expand_box_value(value: str) -> dict[str, str]:
    tokens = split_whitespace_tokens(value)
    if not tokens:
        return {}
    if len(tokens) == 1:
        top = right = bottom = left = tokens[0]
    elif len(tokens) == 2:
        top = bottom = tokens[0]
        right = left = tokens[1]
    elif len(tokens) == 3:
        top = tokens[0]
        right = left = tokens[1]
        bottom = tokens[2]
    else:
        top, right, bottom, left = tokens[:4]
    return {
        "top": top,
        "right": right,
        "bottom": bottom,
        "left": left,
    }


def parse_length_candidates_px(value: str, font_size_px: float | None = None) -> list[float]:
    candidates: list[float] = []
    for raw_number, unit in re.findall(r"(-?\d+(?:\.\d+)?)(px|rem|em|%)?", value):
        number = float(raw_number)
        if unit == "px":
            candidates.append(number)
        elif unit == "rem":
            candidates.append(number * 16.0)
        elif unit == "em":
            base = font_size_px if font_size_px is not None else 16.0
            candidates.append(number * base)
        elif unit == "%":
            if font_size_px is not None:
                candidates.append((number / 100.0) * font_size_px)
        elif number == 0:
            candidates.append(0.0)
    return candidates


def value_matches_px(value: str | None, expected_px: float | int | None, tolerance: float = 0.75) -> bool:
    if value is None or expected_px is None:
        return False
    expected = float(expected_px)
    return any(abs(candidate - expected) <= tolerance for candidate in parse_length_candidates_px(value))


def parse_line_height_ratio(line_height: str | None, font_size: str | None) -> float | None:
    if not line_height:
        return None
    value = line_height.strip().lower()
    if value in {"normal", "inherit", "initial", "unset"}:
        return None
    if re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        return float(value)
    if value.endswith("%"):
        try:
            return float(value[:-1]) / 100.0
        except ValueError:
            return None
    font_candidates = parse_length_candidates_px(font_size or "")
    font_px = font_candidates[0] if font_candidates else None
    line_candidates = parse_length_candidates_px(value, font_px)
    if not line_candidates:
        return None
    if font_px and font_px != 0:
        return line_candidates[0] / font_px
    return None


def render_value(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


def parse_declarations(block: str) -> dict[str, str]:
    declarations: dict[str, str] = {}
    for item in top_level_split(block, ";"):
        if not item:
            continue
        buf: list[str] = []
        depth = 0
        quote = ""
        colon_index: int | None = None
        for index, char in enumerate(item):
            if quote:
                if char == quote:
                    quote = ""
                continue
            if char in {"'", '"'}:
                quote = char
                continue
            if char == "(":
                depth += 1
                continue
            if char == ")":
                depth = max(0, depth - 1)
                continue
            if char == ":" and depth == 0:
                colon_index = index
                break
        if colon_index is None:
            continue
        prop = item[:colon_index].strip().lower()
        value = item[colon_index + 1:].strip()
        if prop:
            declarations[prop] = value
    return declarations


def find_matching_brace(css: str, start_brace: int) -> int:
    depth = 0
    quote = ""
    index = start_brace
    while index < len(css):
        char = css[index]
        if quote:
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return len(css) - 1


def split_selectors(selector_text: str) -> list[str]:
    return [part.strip() for part in top_level_split(selector_text, ",") if part.strip()]


def extract_pseudo_element(selector: str) -> str | None:
    match = re.search(r"::?(before|after)\b", selector, flags=re.I)
    if not match:
        return None
    return match.group(1).lower()


def parse_css_rules(css_text: str) -> list[CSSRule]:
    css = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
    rules: list[CSSRule] = []
    order = 0
    index = 0
    length = len(css)

    while index < length:
        while index < length and css[index].isspace():
            index += 1
        if index >= length:
            break

        if css[index] == "@":
            header_end = index
            quote = ""
            depth = 0
            while header_end < length:
                char = css[header_end]
                if quote:
                    if char == quote:
                        quote = ""
                    header_end += 1
                    continue
                if char in {"'", '"'}:
                    quote = char
                    header_end += 1
                    continue
                if char == "(":
                    depth += 1
                    header_end += 1
                    continue
                if char == ")":
                    depth = max(0, depth - 1)
                    header_end += 1
                    continue
                if depth == 0 and char in "{;":
                    break
                header_end += 1
            if header_end >= length or css[header_end] == ";":
                index = header_end + 1
                continue
            block_end = find_matching_brace(css, header_end)
            inner = css[header_end + 1:block_end]
            rules.extend(parse_css_rules(inner))
            index = block_end + 1
            continue

        selector_end = index
        quote = ""
        depth = 0
        while selector_end < length:
            char = css[selector_end]
            if quote:
                if char == quote:
                    quote = ""
                selector_end += 1
                continue
            if char in {"'", '"'}:
                quote = char
                selector_end += 1
                continue
            if char in {"(", "["}:
                depth += 1
                selector_end += 1
                continue
            if char in {")", "]"}:
                depth = max(0, depth - 1)
                selector_end += 1
                continue
            if depth == 0 and char == "{":
                break
            selector_end += 1
        if selector_end >= length:
            break
        selector_text = css[index:selector_end].strip()
        block_end = find_matching_brace(css, selector_end)
        declarations = parse_declarations(css[selector_end + 1:block_end])
        selectors = split_selectors(selector_text)
        if selectors and declarations:
            order += 1
            grouped_selectors: dict[str | None, list[str]] = {}
            for selector in selectors:
                pseudo_element = extract_pseudo_element(selector)
                grouped_selectors.setdefault(pseudo_element, []).append(selector)
            for pseudo_element, grouped in grouped_selectors.items():
                rules.append(
                    CSSRule(
                        selectors=grouped,
                        declarations=declarations,
                        order=order,
                        pseudo_element=pseudo_element,
                    )
                )
        index = block_end + 1

    return rules


def iter_elements(root: DOMElement) -> Iterable[DOMElement]:
    for item in root.content:
        if isinstance(item, DOMElement):
            yield item
            yield from iter_elements(item)


def strip_pseudos(selector: str) -> str:
    return re.sub(r"::?[a-zA-Z0-9_-]+(?:\([^)]*\))?", "", selector)


def tokenize_selector(selector: str) -> tuple[list[str], list[str]] | None:
    cleaned = strip_pseudos(selector).strip()
    if not cleaned or any(token in cleaned for token in ("+", "~")):
        return None

    simples: list[str] = []
    combinators: list[str] = []
    buf: list[str] = []
    depth = 0
    quote = ""
    pending_descendant = False

    for char in cleaned:
        if quote:
            buf.append(char)
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            continue
        if char == "[":
            depth += 1
            buf.append(char)
            continue
        if char == "]":
            depth = max(0, depth - 1)
            buf.append(char)
            continue
        if depth == 0 and char == ">":
            if buf:
                simples.append("".join(buf).strip())
                buf = []
            if simples and len(combinators) < len(simples):
                combinators.append(">")
            pending_descendant = False
            continue
        if depth == 0 and char.isspace():
            if buf:
                simples.append("".join(buf).strip())
                buf = []
                pending_descendant = True
            continue
        if pending_descendant and simples and len(combinators) < len(simples):
            combinators.append(" ")
        pending_descendant = False
        buf.append(char)

    if buf:
        simples.append("".join(buf).strip())

    if not simples:
        return None
    while len(combinators) > len(simples) - 1:
        combinators.pop()
    while len(combinators) < len(simples) - 1:
        combinators.insert(0, " ")
    return simples, combinators


def parse_simple_selector(simple: str) -> dict[str, object] | None:
    simple = simple.strip()
    if not simple:
        return None
    tag = None
    element_id = None
    classes: set[str] = set()

    for match in re.finditer(r"(#[-_a-zA-Z0-9]+)|(\.[-_a-zA-Z0-9]+)|([a-zA-Z][-_a-zA-Z0-9]*)|(\*)|(\[[^\]]+\])", simple):
        token = match.group(0)
        if token.startswith("#"):
            element_id = token[1:]
        elif token.startswith("."):
            classes.add(token[1:])
        elif token == "*" or token.startswith("["):
            continue
        else:
            tag = token.lower()

    return {"tag": tag, "id": element_id, "classes": classes}


def matches_simple_selector(element: DOMElement, simple: str) -> bool:
    parsed = parse_simple_selector(simple)
    if not parsed:
        return False
    tag = parsed["tag"]
    element_id = parsed["id"]
    classes = parsed["classes"]
    if isinstance(tag, str) and element.tag != tag:
        return False
    if isinstance(element_id, str) and element.attrs.get("id") != element_id:
        return False
    if isinstance(classes, set) and not classes.issubset(element.classes):
        return False
    return True


def matches_selector(element: DOMElement, selector: str) -> bool:
    tokenized = tokenize_selector(selector)
    if tokenized is None:
        return False
    simples, combinators = tokenized
    current: DOMElement | None = element
    if current is None or not matches_simple_selector(current, simples[-1]):
        return False

    for index in range(len(simples) - 2, -1, -1):
        combinator = combinators[index]
        if combinator == ">":
            current = current.parent
            if current is None or current.tag == "document" or not matches_simple_selector(current, simples[index]):
                return False
            continue

        ancestor = current.parent
        while ancestor is not None and ancestor.tag != "document":
            if matches_simple_selector(ancestor, simples[index]):
                current = ancestor
                break
            ancestor = ancestor.parent
        else:
            return False

    return True


def selector_specificity(selector: str) -> tuple[int, int, int]:
    stripped = strip_pseudos(selector)
    id_count = len(re.findall(r"#[a-zA-Z0-9_-]+", stripped))
    class_count = len(re.findall(r"\.[a-zA-Z0-9_-]+", stripped)) + len(re.findall(r"\[[^\]]+\]", stripped))
    tag_count = len(re.findall(r"(?<![#.\w-])[a-zA-Z][a-zA-Z0-9_-]*", stripped))
    return (id_count, class_count, tag_count)


def better_property(new: PropertyValue, old: PropertyValue) -> bool:
    if new.important != old.important:
        return new.important and not old.important
    if new.specificity != old.specificity:
        return new.specificity > old.specificity
    return new.order >= old.order


def expand_font_shorthand(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not value:
        return result

    match = re.search(
        r"(?P<prefix>.*?)(?P<size>-?\d+(?:\.\d+)?(?:px|rem|em|%))(?:\s*/\s*(?P<line>[^ ]+))?\s+(?P<family>.+)$",
        value.strip(),
    )
    if not match:
        return result

    prefix = match.group("prefix")
    size = match.group("size")
    line = match.group("line")
    family = match.group("family").strip()
    weight_match = re.search(r"\b([1-9]00|bold|normal|lighter|bolder)\b", prefix)
    if weight_match:
        result["font-weight"] = weight_match.group(1)
    result["font-size"] = size
    if line:
        result["line-height"] = line
    if family:
        result["font-family"] = family
    return result


def compute_direct_element_properties(element: DOMElement, rules: list[CSSRule]) -> dict[str, PropertyValue]:
    properties: dict[str, PropertyValue] = {}

    for rule in rules:
        if rule.pseudo_element is not None:
            continue
        matched_selectors = [selector for selector in rule.selectors if matches_selector(element, selector)]
        if not matched_selectors:
            continue
        selector = max(matched_selectors, key=selector_specificity)
        specificity = selector_specificity(selector)

        expanded = dict(rule.declarations)
        if "font" in rule.declarations:
            expanded.update(expand_font_shorthand(rule.declarations["font"]))

        for prop, raw_value in expanded.items():
            value = raw_value.strip()
            important = False
            if value.endswith("!important"):
                value = value[:-10].strip()
                important = True
            candidate = PropertyValue(
                value=value,
                selector=selector,
                specificity=specificity,
                order=rule.order,
                important=important,
            )
            current = properties.get(prop)
            if current is None or better_property(candidate, current):
                properties[prop] = candidate

    return properties


def compute_element_properties(element: DOMElement, rules: list[CSSRule]) -> dict[str, PropertyValue]:
    direct_properties = compute_direct_element_properties(element, rules)
    if element.parent is None:
        return direct_properties

    inherited_properties = {
        name: value
        for name, value in compute_element_properties(element.parent, rules).items()
        if name in INHERITED_PROPERTIES
    }
    return {**inherited_properties, **direct_properties}


def resolve_padding(properties: dict[str, PropertyValue]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    shorthand = properties.get("padding")
    if shorthand:
        resolved.update(expand_box_value(shorthand.value))
    for side in BOX_SIDES:
        longhand = properties.get(f"padding-{side}")
        if longhand:
            resolved[side] = longhand.value
    return resolved


def resolve_gap_values(properties: dict[str, PropertyValue]) -> list[str]:
    values: list[str] = []
    if "gap" in properties:
        values.extend(split_whitespace_tokens(properties["gap"].value))
    for prop in ("row-gap", "column-gap"):
        if prop in properties:
            values.append(properties[prop].value)
    return [value for value in values if value]


def resolved_background_colors(properties: dict[str, PropertyValue]) -> list[str]:
    colors: list[str] = []
    if "background-color" in properties:
        colors.extend(extract_hex_colors(properties["background-color"].value))
    if "background" in properties:
        colors.extend(extract_hex_colors(properties["background"].value))
    return colors


def collect_text_candidates(root: DOMElement) -> list[ElementMatch]:
    candidates: list[ElementMatch] = []
    for element in iter_elements(root):
        if element.tag in {"document", "html", "head", "body", "script", "style"}:
            continue
        raw = element.text_content()
        normalized = normalize_text_for_match(raw)
        if normalized:
            candidates.append(ElementMatch(element=element, normalized_text=normalized, raw_text=raw))
    return candidates


def match_text_node(text_value: str, candidates: list[ElementMatch]) -> ElementMatch | None:
    normalized = normalize_text_for_match(text_value)
    if not normalized:
        return None

    ranked: list[tuple[int, int, int, int, ElementMatch]] = []
    for candidate in candidates:
        if normalized not in candidate.normalized_text:
            continue
        exact = 0 if candidate.normalized_text == normalized else 1
        excess = len(candidate.normalized_text) - len(normalized)
        depth_rank = -candidate.element.depth
        ranked.append((exact, excess, depth_rank, candidate.element.order, candidate))

    if not ranked:
        return None
    ranked.sort(key=lambda item: item[:4])
    return ranked[0][4]


def build_special_whitespace_regex(text: str) -> str:
    parts: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        segment = "".join(buffer)
        tokens = re.split(r"\s+", segment.strip())
        if not tokens or tokens == [""]:
            parts.append(r"\s+")
        else:
            parts.append(r"\s+".join(re.escape(token) for token in tokens if token))
        buffer.clear()

    for char in text:
        if char == "\xa0":
            flush()
            parts.append(r"\u00a0")
            continue
        if char in {"\n", "\u2028"}:
            flush()
            parts.append(r"\s*(?:\u2028|\r?\n)\s*")
            continue
        buffer.append(char)
    flush()
    return "".join(parts)


def special_whitespace_preserved(spec_text: str, actual_text: str) -> bool:
    if not any(marker in spec_text for marker in ("\n", "\u2028", "\xa0")):
        return True
    pattern = build_special_whitespace_regex(spec_text)
    if not pattern:
        return True
    return re.search(pattern, actual_text.replace("\u2028", "\n"), flags=re.S) is not None


def describe_node(node: dict) -> str:
    name = node.get("name")
    node_id = node.get("id") or node.get("node_id")
    if name:
        return f"{node_id} ({name})"
    return render_value(node_id)


def add_violation(violations: list[Violation], category: str, node: dict | str, expected, actual) -> None:
    label = describe_node(node) if isinstance(node, dict) else str(node)
    violations.append(
        Violation(
            category=category,
            node=label,
            expected=render_value(expected),
            actual=render_value(actual),
        )
    )


def parse_html_document(html_text: str) -> SimpleHTMLDocumentParser:
    parser = SimpleHTMLDocumentParser()
    parser.feed(html_text)
    parser.close()
    return parser


def link_matches(element: DOMElement, url: str) -> bool:
    return element.tag == "a" and element.attrs.get("href", "").strip() == url and element.attrs.get("target", "").strip().lower() == "_blank"


def selector_depth(selector: str) -> int:
    tokenized = tokenize_selector(selector)
    if tokenized is None:
        return 0
    return len(tokenized[0])


def css_rule_key(rule: CSSRule) -> tuple[int, tuple[str, ...]]:
    return (rule.order, tuple(rule.selectors))


def normalize_bbox(bbox: object) -> dict[str, float] | None:
    if not isinstance(bbox, dict):
        return None
    keys = ("x", "y", "w", "h")
    normalized: dict[str, float] = {}
    for key in keys:
        value = bbox.get(key)
        if not isinstance(value, (int, float)):
            return None
        normalized[key] = float(value)
    return normalized


def bbox_area(bbox: object) -> float | None:
    normalized = normalize_bbox(bbox)
    if not normalized:
        return None
    width = normalized["w"]
    height = normalized["h"]
    if width <= 0 or height <= 0:
        return None
    return width * height


def bbox_contains(outer_bbox: object, inner_bbox: object) -> bool:
    outer = normalize_bbox(outer_bbox)
    inner = normalize_bbox(inner_bbox)
    if not outer or not inner:
        return False
    return (
        outer["x"] <= inner["x"]
        and outer["y"] <= inner["y"]
        and outer["x"] + outer["w"] >= inner["x"] + inner["w"]
        and outer["y"] + outer["h"] >= inner["y"] + inner["h"]
    )


def frame_identifier(frame: dict, fallback_index: int | None = None) -> str:
    node_id = frame.get("id")
    if isinstance(node_id, str) and node_id.strip():
        return node_id.strip()
    if fallback_index is not None:
        return f"frame@{fallback_index}"
    return "frame@unknown"


def infer_parent_lookup(frame_nodes: list[dict]) -> dict[str, str]:
    frame_by_id = {frame_identifier(frame, index): frame for index, frame in enumerate(frame_nodes)}
    parent_lookup: dict[str, str] = {}

    for index, frame in enumerate(frame_nodes):
        node_id = frame_identifier(frame, index)
        parent_id = frame.get("parent_id")
        if isinstance(parent_id, str) and parent_id.strip():
            parent_lookup[node_id] = parent_id.strip()
            continue

        containing_parents: list[tuple[float, str]] = []
        for other_index, other in enumerate(frame_nodes):
            other_id = frame_identifier(other, other_index)
            if other_id == node_id or not bbox_contains(other.get("bbox"), frame.get("bbox")):
                continue
            area = bbox_area(other.get("bbox"))
            if area is None:
                continue
            containing_parents.append((area, other_id))

        if containing_parents:
            containing_parents.sort(key=lambda item: item[0])
            guessed_parent_id = containing_parents[0][1]
            if guessed_parent_id in frame_by_id:
                parent_lookup[node_id] = guessed_parent_id

    return parent_lookup


def frame_parent_chain(frame_id: str, parent_lookup: dict[str, str]) -> list[str]:
    chain: list[str] = []
    seen: set[str] = set()
    current = parent_lookup.get(frame_id)
    while current and current not in seen:
        chain.append(current)
        seen.add(current)
        current = parent_lookup.get(current)
    return chain


def frame_path_hint(frame: dict, parent_lookup: dict[str, str], fallback_index: int | None = None) -> str:
    frame_id = frame_identifier(frame, fallback_index)
    chain = frame_parent_chain(frame_id, parent_lookup)
    if chain:
        return f"frame {frame_id} (parent: {' -> '.join(chain)})"
    return f"frame {frame_id}"


def evaluate_frame_rule(rule: CSSRule, frame: dict) -> tuple[int, list[str]]:
    if rule.pseudo_element is not None:
        return 0, []

    score = 0
    notes: list[str] = []
    properties = {key: PropertyValue(value=value, selector=", ".join(rule.selectors), specificity=(0, 0, 0), order=rule.order, important=False) for key, value in rule.declarations.items()}
    padding = resolve_padding(properties)
    backgrounds = resolved_background_colors(properties)
    gap_values = resolve_gap_values(properties)
    expected_fill = normalize_hex(frame.get("fills"))

    for side in BOX_SIDES:
        expected = frame.get(f"padding{side.capitalize()}")
        if expected not in (None, 0) and value_matches_px(padding.get(side), expected):
            score += 2
            notes.append(f"padding-{side}")

    spacing = frame.get("itemSpacing")
    if spacing not in (None, 0):
        if any(value_matches_px(value, spacing) for value in gap_values):
            score += 2
            notes.append("gap")

    if expected_fill and expected_fill in backgrounds:
        score += 3
        notes.append("fill")

    flex_direction = rule.declarations.get("flex-direction", "").strip().lower()
    layout_mode = str(frame.get("layoutMode") or "").upper()
    if layout_mode == "HORIZONTAL" and flex_direction == "row":
        score += 1
        notes.append("layout")
    if layout_mode == "VERTICAL" and flex_direction == "column":
        score += 1
        notes.append("layout")

    context = frame.get("_match_context")
    if isinstance(context, FrameMatchContext) and score > 0:
        selector_depths = [selector_depth(selector) for selector in rule.selectors]
        selector_depths = [depth for depth in selector_depths if depth > 0]
        if selector_depths:
            target_depth = context.depth + 1
            depth_delta = min(abs(depth - target_depth) for depth in selector_depths)
            if depth_delta == 0:
                score += 3
                notes.append("depth")
                if context.area is not None:
                    score += 1
                    notes.append("bbox")
            elif depth_delta == 1:
                score += 1
                notes.append("depth-near")

    return score, notes


def best_frame_rule(frame: dict, rules: list[CSSRule]) -> tuple[CSSRule | None, list[str]]:
    context = frame.get("_match_context")
    blocked_rule_keys = set(context.blocked_rule_keys) if isinstance(context, FrameMatchContext) else set()
    ranked: list[tuple[int, int, CSSRule, list[str]]] = []
    for rule in rules:
        if css_rule_key(rule) in blocked_rule_keys:
            continue
        score, notes = evaluate_frame_rule(rule, frame)
        if score <= 0:
            continue
        ranked.append((score, rule.order, rule, notes))
    if not ranked:
        if isinstance(context, FrameMatchContext):
            return None, [context.path_hint]
        return None, []
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2], ranked[0][3]


def rule_properties(rule: CSSRule) -> dict[str, PropertyValue]:
    return {key: PropertyValue(value=value, selector=", ".join(rule.selectors), specificity=(0, 0, 0), order=rule.order, important=False) for key, value in rule.declarations.items()}


def validate_text_nodes(
    text_nodes: list[dict],
    candidates: list[ElementMatch],
    css_rules: list[CSSRule],
) -> tuple[list[Violation], list[dict]]:
    violations: list[Violation] = []
    missing_rows: list[dict] = []
    property_cache: dict[int, dict[str, PropertyValue]] = {}

    for node in text_nodes:
        match = match_text_node(node.get("characters", ""), candidates)
        if match is None:
            missing_rows.append(node)
            add_violation(violations, "텍스트 위변조", node, node.get("characters", ""), "HTML 텍스트 미발견")
            continue

        properties = property_cache.get(match.element.order)
        if properties is None:
            properties = compute_element_properties(match.element, css_rules)
            property_cache[match.element.order] = properties

        if not special_whitespace_preserved(node.get("characters", ""), match.raw_text):
            add_violation(
                violations,
                "줄바꿈 보존",
                node,
                node.get("characters", "").replace("\n", r"\n").replace("\u2028", r"\u2028").replace("\xa0", r"\xa0"),
                match.raw_text.replace("\n", r"\n").replace("\xa0", r"\xa0"),
            )

        missing_fields = [field for field in FONT_FIELDS if field not in properties]
        if missing_fields:
            add_violation(
                violations,
                "폰트 5필드 완결성",
                node,
                ", ".join(FONT_FIELDS),
                f"missing: {', '.join(missing_fields)} @ {match.element.short_selector()}",
            )

        expected_ratio = node.get("lineHeightRatio")
        if expected_ratio is not None:
            actual_ratio = parse_line_height_ratio(
                properties.get("line-height").value if properties.get("line-height") else None,
                properties.get("font-size").value if properties.get("font-size") else None,
            )
            if actual_ratio is None or abs(actual_ratio - float(expected_ratio)) > 0.05:
                add_violation(
                    violations,
                    "lineHeight 비율 일치",
                    node,
                    f"{expected_ratio} ±0.05",
                    f"{render_value(actual_ratio)} @ {match.element.short_selector()}",
                )

        expected_color = normalize_hex(node.get("color"))
        actual_color_values = extract_hex_colors(properties.get("color").value if properties.get("color") else None)
        actual_color = actual_color_values[0] if actual_color_values else None
        if expected_color and actual_color != expected_color:
            add_violation(
                violations,
                "fills color hex 일치",
                node,
                expected_color,
                f"{render_value(actual_color)} @ {match.element.short_selector()}",
            )

    return violations, missing_rows


def validate_frame_nodes(frame_nodes: list[dict], css_rules: list[CSSRule]) -> list[Violation]:
    violations: list[Violation] = []
    parent_lookup = infer_parent_lookup(frame_nodes)

    ordered_frames: list[tuple[int, float, int, dict, str, FrameMatchContext]] = []
    for index, frame in enumerate(frame_nodes):
        frame_id = frame_identifier(frame, index)
        area = bbox_area(frame.get("bbox")) or 0.0
        chain = frame_parent_chain(frame_id, parent_lookup)
        context = FrameMatchContext(
            depth=len(chain),
            area=area if area > 0 else None,
            path_hint=frame_path_hint(frame, parent_lookup, index),
        )
        ordered_frames.append((len(chain), -area, index, frame, frame_id, context))

    ordered_frames.sort(key=lambda item: (item[0], item[1], item[2]))
    matched_rule_by_frame_id: dict[str, tuple[int, tuple[str, ...]]] = {}

    for _, _, index, frame, frame_id, context in ordered_frames:
        blocked_rule_keys = tuple(
            matched_rule_by_frame_id[parent_id]
            for parent_id in frame_parent_chain(frame_id, parent_lookup)
            if parent_id in matched_rule_by_frame_id
        )
        contextualized_frame = dict(frame)
        contextualized_frame["_match_context"] = FrameMatchContext(
            depth=context.depth,
            area=context.area,
            path_hint=context.path_hint,
            blocked_rule_keys=blocked_rule_keys,
        )

        best_rule, matched_notes = best_frame_rule(contextualized_frame, css_rules)
        if best_rule is not None:
            matched_rule_by_frame_id[frame_id] = css_rule_key(best_rule)

        match_hint = matched_notes[0] if best_rule is None and matched_notes else None
        rule_label = ", ".join(best_rule.selectors) if best_rule else "미매칭"
        rule_display = f"{rule_label} ({match_hint})" if match_hint else rule_label
        props = rule_properties(best_rule) if best_rule else {}
        padding = resolve_padding(props)
        gap_values = resolve_gap_values(props)
        backgrounds = resolved_background_colors(props)
        expected_fill = normalize_hex(frame.get("fills"))

        if expected_fill:
            if expected_fill not in backgrounds:
                add_violation(
                    violations,
                    "fills color hex 일치",
                    frame,
                    expected_fill,
                    f"{', '.join(backgrounds) if backgrounds else 'background 미발견'} @ {rule_display}",
                )

        meaningful_padding = [side for side in BOX_SIDES if frame.get(f"padding{side.capitalize()}") not in (None, 0)]
        spacing = frame.get("itemSpacing")
        needs_layout_check = bool(meaningful_padding) or spacing not in (None, 0)
        if needs_layout_check:
            missing_bits: list[str] = []
            for side in meaningful_padding:
                expected = frame.get(f"padding{side.capitalize()}")
                if not value_matches_px(padding.get(side), expected):
                    missing_bits.append(f"padding-{side}={expected}")
            if spacing not in (None, 0) and not any(value_matches_px(value, spacing) for value in gap_values):
                missing_bits.append(f"gap={spacing}")
            if missing_bits:
                add_violation(
                    violations,
                    "frame padding/gap 반영",
                    frame,
                    ", ".join(missing_bits),
                    f"{rule_display} ({', '.join(matched_notes) if best_rule else match_hint or 'signature 없음'})",
                )

        clamp_targets: list[tuple[str, float | int]] = []
        for side in BOX_SIDES:
            expected = frame.get(f"padding{side.capitalize()}")
            if isinstance(expected, (int, float)) and expected >= 100:
                clamp_targets.append((f"padding-{side}", expected))
        if isinstance(spacing, (int, float)) and spacing >= 100:
            clamp_targets.append(("gap", spacing))

        for prop_name, expected in clamp_targets:
            actual_value = None
            if prop_name.startswith("padding-"):
                actual_value = padding.get(prop_name.split("-", 1)[1])
            elif prop_name == "gap":
                actual_value = next((value for value in gap_values if value_matches_px(value, expected)), gap_values[0] if gap_values else None)
            if actual_value is None or "clamp(" not in actual_value.lower():
                add_violation(
                    violations,
                    "clamp 적용",
                    frame,
                    f"{prop_name}={expected} requires clamp()",
                    f"{render_value(actual_value)} @ {rule_display}",
                )

        if str(frame.get("layoutMode") or "").upper() == "VERTICAL" and any(prop in props for prop in ("gap", "row-gap", "column-gap")):
            add_violation(
                violations,
                "column flex gap 금지",
                frame,
                "gap 미사용",
                f"{', '.join(f'{prop}={props[prop].value}' for prop in ('gap', 'row-gap', 'column-gap') if prop in props)} @ {rule_display}",
            )

    return violations


def validate_interactions(interactions: list[dict], root: DOMElement) -> list[Violation]:
    violations: list[Violation] = []
    anchors = [element for element in iter_elements(root) if element.tag == "a"]
    for interaction in interactions:
        url = (interaction.get("url") or "").strip()
        if not url:
            add_violation(violations, "interaction URL 일치", interaction, "non-empty URL", "빈 URL")
            continue
        if not any(link_matches(anchor, url) for anchor in anchors):
            add_violation(violations, "interaction URL 일치", interaction, f'<a href="{url}" target="_blank">', "불일치")
    return violations


def print_report(violations: list[Violation], missing_rows: list[dict]) -> None:
    print("카테고리 | 노드 | 기대값 | 실제값")
    if violations:
        for item in violations:
            print(f"{item.category} | {item.node} | {item.expected} | {item.actual}")
    else:
        print("PASS | - | 위반 0건 | -")

    print()
    print("누락된 spec 행")
    if missing_rows:
        print("id | characters")
        for node in missing_rows:
            characters = (node.get("characters") or "").replace("\n", r"\n").replace("\u2028", r"\u2028").replace("\xa0", r"\xa0")
            print(f"{render_value(node.get('id'))} | {characters}")
    else:
        print("없음")


def main() -> int:
    args = parse_args()
    spec = load_spec(args.spec)
    html_text = read_text(args.html)
    css_text = read_text(args.css)

    parser = parse_html_document(html_text)
    css_rules = parse_css_rules(css_text)
    text_candidates = collect_text_candidates(parser.root)

    text_nodes = spec.get("text_nodes")
    frame_nodes = spec.get("frame_nodes")
    interactions = spec.get("interactions")
    if not isinstance(text_nodes, list) or not isinstance(frame_nodes, list) or not isinstance(interactions, list):
        fail("Invalid spec JSON: expected text_nodes/frame_nodes/interactions arrays")

    text_violations, missing_rows = validate_text_nodes(text_nodes, text_candidates, css_rules)
    frame_violations = validate_frame_nodes(frame_nodes, css_rules)
    interaction_violations = validate_interactions(interactions, parser.root)

    violations = text_violations + frame_violations + interaction_violations
    print_report(violations, missing_rows)
    return 1 if violations or missing_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


SPEC_COVERAGE_MIN_TEXT_NODES = 5
SPEC_COVERAGE_MIN_RATIO = 0.3
BORDER_RADIUS_TOLERANCE_PX = 1.0
ALLOWED_BORDER_RADIUS_TOKENS = ("50%", "2em")
_BORDER_RADIUS_PROPERTIES = (
    "border-radius",
    "border-top-left-radius",
    "border-top-right-radius",
    "border-bottom-right-radius",
    "border-bottom-left-radius",
)
_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
_PX_VALUE_RE = re.compile(r"^(-?(?:\d+|\d*\.\d+))px$")
_ZERO_VALUE_RE = re.compile(r"^-?0+(?:\.0+)?$")
VISIBLE_TEXT_TAGS = {
    "p", "span", "a", "li", "strong", "em", "b", "i", "small", "mark",
    "figcaption", "dt", "dd", "label", "button", "td", "th", "blockquote",
    "cite", "summary", "legend", "h1", "h2", "h3", "h4", "h5", "h6",
}
IGNORED_TEXT_TAGS = {"script", "style", "noscript"}


@dataclass
class _VisibleFrame:
    tag: str
    has_text: bool
    is_outermost: bool


@dataclass
class _SelectorPart:
    tag: str | None
    id_value: str | None
    classes: tuple[str, ...]
    combinator: str | None


@dataclass
class _HTMLElement:
    tag: str
    attrs: dict[str, str]
    parent: "_HTMLElement | None"
    children: list["_HTMLElement"]


class VisibleTextBlockCounter(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._visible_stack: list[_VisibleFrame] = []
        self._count = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in IGNORED_TEXT_TAGS:
            self._ignored_depth += 1
        if tag in VISIBLE_TEXT_TAGS:
            self._visible_stack.append(
                _VisibleFrame(
                    tag=tag,
                    has_text=False,
                    is_outermost=not self._visible_stack,
                )
            )

    def handle_endtag(self, tag: str) -> None:
        if tag in VISIBLE_TEXT_TAGS:
            for index in range(len(self._visible_stack) - 1, -1, -1):
                frame = self._visible_stack[index]
                if frame.tag != tag:
                    continue
                closed = self._visible_stack.pop(index)
                if closed.is_outermost and closed.has_text:
                    self._count += 1
                break
        if tag in IGNORED_TEXT_TAGS and self._ignored_depth > 0:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth > 0 or not data.strip():
            return
        for frame in self._visible_stack:
            frame.has_text = True

    @property
    def count(self) -> int:
        return self._count


def count_html_text_blocks_from_source(html_source: str) -> int:
    parser = VisibleTextBlockCounter()
    parser.feed(html_source)
    parser.close()
    return parser.count


def count_html_text_blocks(html_path: Path | None) -> int | None:
    if not html_path or not html_path.is_file():
        return None
    return count_html_text_blocks_from_source(html_path.read_text(encoding="utf-8"))


def count_spec_text_nodes(spec_files: list[Path]) -> int:
    count = 0
    for path in spec_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        nodes = data.get("text_nodes")
        if isinstance(nodes, list):
            count += sum(1 for node in nodes if isinstance(node, dict))
    return count


def build_spec_sha_map(spec_files: list[Path]) -> dict[str, str]:
    spec_shas: dict[str, str] = {}
    for path in spec_files:
        try:
            spec_shas[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception:
            continue
    return spec_shas


def _evaluate_spec_file(spec_path: Path, html_text_blocks: int) -> dict[str, object]:
    spec_text_nodes = count_spec_text_nodes([spec_path])
    effective_min_nodes = min(
        SPEC_COVERAGE_MIN_TEXT_NODES,
        max(html_text_blocks, 1),
    )
    ratio = round(spec_text_nodes / html_text_blocks, 4) if html_text_blocks > 0 else 1.0
    passed = (
        spec_text_nodes >= effective_min_nodes
        and ratio >= SPEC_COVERAGE_MIN_RATIO
    )
    return {
        "spec_text_nodes": spec_text_nodes,
        "html_text_blocks": html_text_blocks,
        "ratio": ratio,
        "threshold_ratio": SPEC_COVERAGE_MIN_RATIO,
        "min_nodes": SPEC_COVERAGE_MIN_TEXT_NODES,
        "effective_min_nodes": effective_min_nodes,
        "passed": passed,
        "target_spec_paths": [str(spec_path)],
    }


def measure_spec_coverage(
    spec_files: list[Path],
    html_text_blocks: int | None,
) -> dict[str, object] | None:
    if html_text_blocks is None:
        return None
    if not spec_files:
        effective_min_nodes = min(
            SPEC_COVERAGE_MIN_TEXT_NODES,
            max(html_text_blocks, 1),
        )
        return {
            "spec_text_nodes": 0,
            "html_text_blocks": html_text_blocks,
            "ratio": 0.0 if html_text_blocks > 0 else 1.0,
            "threshold_ratio": SPEC_COVERAGE_MIN_RATIO,
            "min_nodes": SPEC_COVERAGE_MIN_TEXT_NODES,
            "effective_min_nodes": effective_min_nodes,
            "passed": False,
            "target_spec_paths": [],
        }

    measurements = [_evaluate_spec_file(path, html_text_blocks) for path in spec_files]
    # Pick the worst per-spec verdict so one shell spec cannot be masked by another.
    measurements.sort(
        key=lambda item: (
            bool(item["passed"]),
            float(item["ratio"]),
            int(item["spec_text_nodes"]),
            item["target_spec_paths"][0],
        )
    )
    measurement = dict(measurements[0])
    measurement["evaluated_spec_paths"] = [str(path) for path in spec_files]
    return measurement


def format_spec_coverage_detail(measurement: dict[str, object]) -> str:
    return (
        "spec_text_nodes={spec_text_nodes}, html_text_blocks={html_text_blocks}, "
        "ratio={ratio:.2f}, threshold_ratio={threshold_ratio:.2f}, "
        "min_nodes={min_nodes}, effective_min_nodes={effective_min_nodes}, "
        "target_spec_paths={target_spec_paths}"
    ).format(**measurement)


def _parse_radius_tokens(value: str) -> list[str]:
    text = value.strip().lower()
    if not text:
        return []
    primary = text.split("/", 1)[0].strip()
    if not primary:
        return []
    return [token for token in primary.split() if token]


class _HTMLSelectorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _HTMLElement(tag="__root__", attrs={}, parent=None, children=[])
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _HTMLElement(
            tag=tag.lower(),
            attrs={key.lower(): (value or "") for key, value in attrs},
            parent=self._stack[-1],
            children=[],
        )
        self._stack[-1].children.append(node)
        self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _HTMLElement(
            tag=tag.lower(),
            attrs={key.lower(): (value or "") for key, value in attrs},
            parent=self._stack[-1],
            children=[],
        )
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == lowered:
                del self._stack[index:]
                return


def _iter_html_elements(html_source: str) -> list[_HTMLElement]:
    parser = _HTMLSelectorParser()
    parser.feed(html_source)
    parser.close()
    elements: list[_HTMLElement] = []
    stack = list(reversed(parser.root.children))
    while stack:
        node = stack.pop()
        elements.append(node)
        stack.extend(reversed(node.children))
    return elements


def _parse_simple_selector(selector: str) -> _SelectorPart | None:
    text = selector.strip()
    if not text:
        return None
    if any(token in text for token in ("[", "]", ":", "*", "+", "~")):
        return None
    tag: str | None = None
    id_value: str | None = None
    classes: list[str] = []
    token = ""
    mode = "tag"
    for char in text:
        if char == ".":
            if mode == "tag" and token:
                tag = token.lower()
            elif mode == "id" and token:
                id_value = token
            elif mode == "class" and token:
                classes.append(token)
            token = ""
            mode = "class"
            continue
        if char == "#":
            if mode == "tag" and token:
                tag = token.lower()
            elif mode == "id" and token:
                id_value = token
            elif mode == "class" and token:
                classes.append(token)
            token = ""
            mode = "id"
            continue
        token += char
    if mode == "tag" and token:
        tag = token.lower()
    elif mode == "id" and token:
        id_value = token
    elif mode == "class" and token:
        classes.append(token)
    if not tag and not id_value and not classes:
        return None
    return _SelectorPart(tag=tag, id_value=id_value, classes=tuple(classes), combinator=None)


def _parse_selector_chain(selector: str) -> list[_SelectorPart] | None:
    normalized = selector.replace(">", " > ")
    raw_tokens = [token for token in normalized.split() if token]
    if not raw_tokens:
        return None
    parts: list[_SelectorPart] = []
    combinator: str | None = None
    for token in raw_tokens:
        if token == ">":
            if combinator is not None:
                return None
            combinator = ">"
            continue
        part = _parse_simple_selector(token)
        if part is None:
            return None
        part.combinator = combinator
        parts.append(part)
        combinator = " "
    return parts or None


def _element_has_class(node: _HTMLElement, class_name: str) -> bool:
    classes = node.attrs.get("class", "")
    return class_name in classes.split()


def _element_matches_simple(node: _HTMLElement, part: _SelectorPart) -> bool:
    if part.tag and node.tag != part.tag:
        return False
    if part.id_value and node.attrs.get("id") != part.id_value:
        return False
    return all(_element_has_class(node, class_name) for class_name in part.classes)


def _element_matches_selector(node: _HTMLElement, parts: list[_SelectorPart]) -> bool:
    current: _HTMLElement | None = node
    index = len(parts) - 1
    while index >= 0 and current is not None:
        part = parts[index]
        if not _element_matches_simple(current, part):
            return False
        index -= 1
        if index < 0:
            return True
        next_part = parts[index + 1]
        if next_part.combinator == ">":
            current = current.parent
            continue
        ancestor = current.parent
        target_part = parts[index]
        while ancestor is not None and not _element_matches_simple(ancestor, target_part):
            ancestor = ancestor.parent
        current = ancestor
    return index < 0


def _selector_is_used(selector: str, html_source: str) -> tuple[bool, bool]:
    parts = _parse_selector_chain(selector)
    if parts is None:
        return False, False
    for node in _iter_html_elements(html_source):
        if _element_matches_selector(node, parts):
            return True, True
    return True, False


def _parse_radius_value(token: str) -> float | None:
    lowered = token.strip().lower()
    if lowered in ALLOWED_BORDER_RADIUS_TOKENS:
        return None
    if _ZERO_VALUE_RE.fullmatch(lowered):
        return 0.0
    match = _PX_VALUE_RE.fullmatch(lowered)
    if not match:
        return None
    return float(match.group(1))


def _expand_border_radius(tokens: list[str]) -> list[str] | None:
    if not tokens or len(tokens) > 4:
        return None
    if len(tokens) == 1:
        return tokens * 4
    if len(tokens) == 2:
        return [tokens[0], tokens[1], tokens[0], tokens[1]]
    if len(tokens) == 3:
        return [tokens[0], tokens[1], tokens[2], tokens[1]]
    return tokens[:4]


def _extract_css_radius_declarations(css_source: str, html_source: str | None = None) -> tuple[list[dict[str, object]], list[str]]:
    stripped = _CSS_COMMENT_RE.sub("", css_source)
    declarations: list[dict[str, object]] = []
    unscanned: list[str] = []
    for selector_group, body in _CSS_RULE_RE.findall(stripped):
        selectors = [selector.strip() for selector in selector_group.split(",") if selector.strip()]
        if not selectors:
            continue
        if html_source is None:
            matched_selectors = selectors
        else:
            matched_selectors = []
            for selector in selectors:
                supported, used = _selector_is_used(selector, html_source)
                if not supported or not used:
                    unscanned.append(selector)
                    continue
                matched_selectors.append(selector)
        if not matched_selectors:
            continue
        for declaration in body.split(";"):
            if ":" not in declaration:
                continue
            prop, raw_value = declaration.split(":", 1)
            property_name = prop.strip().lower()
            if property_name not in _BORDER_RADIUS_PROPERTIES:
                continue
            tokens = _parse_radius_tokens(raw_value)
            if property_name == "border-radius":
                expanded = _expand_border_radius(tokens)
            else:
                expanded = tokens[:1]
            if not expanded:
                continue
            if all(_parse_radius_value(token) == 0.0 for token in expanded if token.strip()):
                continue
            declarations.append(
                {
                    "property": property_name,
                    "tokens": expanded,
                    "selectors": matched_selectors[:],
                }
            )
    return declarations, unscanned


def _normalize_radius_number(value: float) -> float | int:
    rounded = round(float(value), 3)
    if rounded.is_integer():
        return int(rounded)
    return rounded


def _match_radius_token(value: str, spec_values: list[float | int]) -> bool:
    lowered = value.strip().lower()
    if lowered in ALLOWED_BORDER_RADIUS_TOKENS:
        return True
    if _ZERO_VALUE_RE.fullmatch(lowered):
        actual = 0.0
    else:
        match = _PX_VALUE_RE.fullmatch(lowered)
        if not match:
            return False
        actual = float(match.group(1))
    return any(abs(float(spec_value) - actual) <= BORDER_RADIUS_TOLERANCE_PX for spec_value in spec_values)


def _declaration_to_corners(property_name: str, tokens: list[str]) -> list[str] | None:
    if property_name == "border-radius":
        return _expand_border_radius(tokens)
    if not tokens:
        return None
    value = tokens[0]
    mapping = {
        "border-top-left-radius": [value, None, None, None],
        "border-top-right-radius": [None, value, None, None],
        "border-bottom-right-radius": [None, None, value, None],
        "border-bottom-left-radius": [None, None, None, value],
    }
    return mapping.get(property_name)


def _corners_match(css_corners: list[str], spec_corners: list[float | int]) -> bool:
    for index, token in enumerate(css_corners):
        if token is None:
            continue
        lowered = token.strip().lower()
        if lowered in ALLOWED_BORDER_RADIUS_TOKENS:
            continue
        actual = _parse_radius_value(lowered)
        if actual is None:
            return False
        if abs(float(spec_corners[index]) - actual) > BORDER_RADIUS_TOLERANCE_PX:
            return False
    return True


def measure_border_radius_check(
    spec_files: list[Path],
    css_source: str,
    html_source: str | None = None,
) -> dict[str, object]:
    css_declarations, unscanned = _extract_css_radius_declarations(css_source, html_source)
    css_values: list[str] = []
    seen_css_values: set[str] = set()
    spec_values: set[float | int] = set()
    spec_corner_sets: set[tuple[float | int, float | int, float | int, float | int]] = set()
    frame_nodes_key_seen = False
    saw_any_frame = False
    radius_field_seen = False

    for path in spec_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "frame_nodes" not in data:
            continue
        frame_nodes_key_seen = True
        frame_nodes = data.get("frame_nodes")
        if not isinstance(frame_nodes, list):
            continue
        for frame in frame_nodes:
            if not isinstance(frame, dict):
                continue
            saw_any_frame = True
            corner_radius = frame.get("cornerRadius")
            rect_radii = frame.get("rectangleCornerRadii")
            measured_radius_present = isinstance(corner_radius, (int, float))
            if isinstance(rect_radii, list):
                normalized_radii: list[float | int] = []
                for value in rect_radii[:4]:
                    if not isinstance(value, (int, float)):
                        normalized_radii = []
                        break
                    normalized_radii.append(_normalize_radius_number(float(value)))
                if len(normalized_radii) == 4:
                    spec_corner_sets.add(tuple(normalized_radii))
                    for radius_value in normalized_radii:
                        if abs(float(radius_value)) > 0.01:
                            spec_values.add(radius_value)
                    measured_radius_present = measured_radius_present or any(
                        abs(float(radius_value)) > 0.01 for radius_value in normalized_radii
                    )
            if "cornerRadius" in frame or "rectangleCornerRadii" in frame:
                radius_field_seen = radius_field_seen or measured_radius_present
            if not isinstance(corner_radius, (int, float)):
                continue
            if abs(float(corner_radius)) <= 0.01:
                continue
            spec_values.add(_normalize_radius_number(float(corner_radius)))
    sorted_spec_values = sorted(spec_values, key=float)
    sorted_corner_sets = sorted(spec_corner_sets, key=lambda corners: tuple(float(value) for value in corners))
    if not frame_nodes_key_seen or (saw_any_frame and not radius_field_seen):
        reason = "legacy spec: frame_nodes or radius fields missing"
        return {
            "status": "skipped",
            "passed": True,
            "reason": reason,
            "spec_radius_set": sorted_spec_values,
            "spec_corner_sets": [list(corners) for corners in sorted_corner_sets],
            "css_radius_values": css_values,
            "violations": [],
            "warnings": [reason],
            "unscanned": unscanned,
            "target_spec_paths": [str(path) for path in spec_files],
        }

    violations: list[str] = []
    warnings: list[str] = []
    for declaration in css_declarations:
        property_name = str(declaration["property"])
        tokens = list(declaration["tokens"])
        corners = _declaration_to_corners(property_name, tokens)
        if corners is None:
            continue
        for token in tokens:
            if token not in seen_css_values:
                seen_css_values.add(token)
                css_values.append(token)
        if property_name == "border-radius" and all(token.strip().lower() in ALLOWED_BORDER_RADIUS_TOKENS for token in tokens):
            continue
        matched = False
        if sorted_corner_sets:
            matched = any(_corners_match(corners, list(spec_corners)) for spec_corners in sorted_corner_sets)
        elif sorted_spec_values:
            matched = all(_match_radius_token(token, sorted_spec_values) for token in tokens if token is not None)
        if matched:
            continue
        violation_token = next((token for token in tokens if token not in ALLOWED_BORDER_RADIUS_TOKENS), tokens[0])
        if violation_token not in violations:
            violations.append(violation_token)

    if not sorted_spec_values and css_values:
        warnings.append("spec has no border radius but CSS declares border-radius values")
    elif sorted_spec_values and not css_values:
        warnings.append("spec has border radius values but CSS declares none")

    if not sorted_spec_values and css_values:
        reason = "unauthorized border-radius declarations"
        status = "failed"
    elif violations:
        reason = "border-radius values outside allowed spec set"
        status = "failed"
    else:
        reason = "border-radius declarations align with spec set"
        status = "passed"

    return {
        "status": status,
        "passed": status != "failed",
        "reason": reason,
        "spec_radius_set": sorted_spec_values,
        "spec_corner_sets": [list(corners) for corners in sorted_corner_sets],
        "css_radius_values": css_values,
        "violations": violations,
        "warnings": warnings,
        "unscanned": unscanned,
        "target_spec_paths": [str(path) for path in spec_files],
    }


def format_border_radius_detail(measurement: dict[str, object]) -> str:
    return (
        "status={status}, reason={reason}, spec_radius_set={spec_radius_set}, "
        "css_radius_values={css_radius_values}, violations={violations}, unscanned={unscanned}"
    ).format(**measurement)

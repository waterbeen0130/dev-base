#!/usr/bin/env python3
"""Validate generated HTML/CSS against normalized Figma section specs.

Usage:
  python3 tools/figma-validate.py --spec extracted/section_spec.json --html output.html --css output.css
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
import types
from collections import Counter
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rules.models import RuleDefinition, load_rules


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
SCHEMA_V1_PATTERN = re.compile(r"^1(?:\.\d+\.\d+)?$")
SCHEMA_V2_PATTERN = re.compile(r"^2(?:\.\d+\.\d+)?$")
POLICY_1_CATEGORY = "[POLICY-1] VERTICAL frame itemSpacing must map to margin-bottom"
V1_CATEGORIES = (
    "텍스트 위변조",
    "텍스트 byte-exact",
    "줄바꿈 보존",
    "폰트 5필드 완결성",
    "lineHeight 비율 일치",
    "fills color hex 일치",
    "frame padding/gap 반영",
    "clamp 적용",
    "column flex gap 금지",
    "interaction URL 일치",
    "asset_manifest 일치",
)
V2_DETAIL_CATEGORIES = (
    "v2.fills.solid.match",
    "v2.fills.gradient.match",
    "v2.fills.image.match",
    "v2.effects.shadow.match",
    "v2.effects.blur.match",
    "v2.opacity.match",
    "v2.blendMode.match",
    "v2.strokes.match",
    "v2.cornerRadii.match",
    "v2.layoutSizing.match",
    "v2.textCase.match",
    "v2.textDecoration.match",
    "v2.componentId.match",
    "v2.assetManifest.exists",
)
V2_CATEGORIES = V1_CATEGORIES + (POLICY_1_CATEGORY,) + V2_DETAIL_CATEGORIES

POLICY_RULE_SUMMARIES = {
    "vertical_frame_itemspacing_uses_margin_bottom": "Figma VERTICAL frame 의 itemSpacing > 0 은 자식 요소의 margin-bottom 으로 변환한다. column flex gap / row-gap 사용 금지.",
    "no_constraints_to_position_absolute_mapping": "Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다.",
    "figma_rules_conflict_uses_meta_marker": "Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지).",
}
POLICY_HANDLER_MAP = {
    "vertical_frame_itemspacing_uses_margin_bottom": "enforce_policy1_vertical_margin_bottom",
    "no_constraints_to_position_absolute_mapping": "enforce_policy2_constraints_extract_only",
    "figma_rules_conflict_uses_meta_marker": "enforce_policy3_rules_conflict_bypass",
}

CRITICAL_CATEGORIES = {
    "텍스트 byte-exact",
    "asset_manifest 일치",
    "텍스트 위변조",
    "fills color hex 일치",
}
MAJOR_CATEGORIES = {
    "frame padding/gap 반영",
    "clamp 적용",
    "lineHeight 비율 일치",
    "column flex gap 금지",
}


@dataclass
class Violation:
    category: str
    node: str
    expected: str
    actual: str


@dataclass(frozen=True)
class SectionValidationResult:
    section_name: str
    schema_branch: str
    violations: list[Violation]
    missing_rows: list[dict]


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


@dataclass(frozen=True)
class RuleHandlerResult:
    rule_id: str
    severity: str
    passed: bool
    skipped: bool = False
    message: str = ""


@dataclass(frozen=True)
class RuleDispatchContext:
    spec: dict[str, Any] | None = None
    spec_path: str | None = None
    text_nodes: list[dict] | None = None
    frame_nodes: list[dict] | None = None
    interactions: list[dict] | None = None
    text_candidates: list[ElementMatch] | None = None
    css_rules: list[CSSRule] | None = None
    root: DOMElement | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate HTML/CSS output against normalized Figma section spec")
    parser.add_argument("--spec", required=False, help="Path to single spec.json")
    parser.add_argument("--spec-dir", required=False, help="Directory containing *_spec.json files")
    parser.add_argument("--html", required=False, help="Path to generated HTML")
    parser.add_argument("--css", required=False, help="Path to generated CSS")
    parser.add_argument("--version-info", action="store_true", help="Print v1/v2 category map and exit")
    args = parser.parse_args()
    if args.spec and args.spec_dir:
        parser.error("--spec and --spec-dir are mutually exclusive")
    if not args.version_info and (not args.spec and not args.spec_dir or not args.html or not args.css):
        parser.error("--spec or --spec-dir, --html, --css are required unless --version-info is used")
    return args


def parse_schema_branch(schema_version: object) -> str:
    if isinstance(schema_version, int):
        if schema_version == 1:
            return "v1"
        if schema_version == 2:
            return "v2"
    if isinstance(schema_version, str):
        text = schema_version.strip()
        if SCHEMA_V1_PATTERN.match(text):
            return "v1"
        if SCHEMA_V2_PATTERN.match(text):
            return "v2"
    return "v1"


def print_version_info() -> None:
    total = len(V1_CATEGORIES) + len(V2_DETAIL_CATEGORIES)
    print(f"category counts: v1={len(V1_CATEGORIES)}, v2={len(V2_DETAIL_CATEGORIES)}, total={total}")
    print("v1 categories:")
    for name in V1_CATEGORIES:
        print(f"- {name}")
    print("v2 categories:")
    for name in V2_CATEGORIES:
        print(f"- {name}")


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


def load_spec_paths(spec_dir: str) -> list[str]:
    paths = sorted(glob.glob(str(Path(spec_dir) / "*_spec.json")))
    if not paths:
        fail(f"No *_spec.json files found in: {spec_dir}")
    return paths


def asset_manifest_path_from_spec(spec_path: str) -> Path:
    spec = Path(spec_path)
    stem = spec.stem
    if stem.endswith("_spec"):
        base = stem[: -len("_spec")]
    else:
        base = stem
    return spec.with_name(f"{base}_asset_manifest.json")


def normalize_vector_path_data(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        if isinstance(item, str):
            normalized.append(item)
    return normalized


def extract_vector_geometry_paths(geometry: object) -> list[str]:
    if not isinstance(geometry, list):
        return []
    extracted: list[str] = []
    for item in geometry:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if isinstance(path, str):
            extracted.append(path)
    return extracted


def vector_node_path_content(node: dict) -> str:
    fill_paths = normalize_vector_path_data(node.get("fillGeometryPathData"))
    stroke_paths = normalize_vector_path_data(node.get("strokeGeometryPathData"))
    if not fill_paths:
        fill_paths = extract_vector_geometry_paths(node.get("fillGeometry"))
    if not stroke_paths:
        stroke_paths = extract_vector_geometry_paths(node.get("strokeGeometry"))
    return "\n".join(fill_paths + stroke_paths)


def spec_node_identifier(node: dict, prefix: str, index: int) -> str:
    node_id = node.get("id")
    if isinstance(node_id, str) and node_id.strip():
        return node_id.strip()
    return f"{prefix}@{index}"


def expected_asset_manifest_entries(spec: dict) -> list[dict[str, str]]:
    expected: list[dict[str, str]] = []
    image_seen: set[str] = set()
    vector_seen: set[str] = set()

    frame_nodes = spec.get("frame_nodes")
    if isinstance(frame_nodes, list):
        for index, frame in enumerate(frame_nodes):
            if not isinstance(frame, dict):
                continue
            frame_id = spec_node_identifier(frame, "frame", index)
            fills = frame.get("fills_v2")
            if not isinstance(fills, list):
                continue
            for fill in fills:
                if not isinstance(fill, dict):
                    continue
                if fill.get("type") != "IMAGE":
                    continue
                image_ref = fill.get("imageRef")
                if not isinstance(image_ref, str) or not image_ref or image_ref in image_seen:
                    continue
                image_seen.add(image_ref)
                expected.append(
                    {
                        "ref": image_ref,
                        "kind": "image",
                        "hash": image_ref,
                        "spec_node_id": frame_id,
                    }
                )

    vector_nodes = spec.get("vector_nodes")
    if isinstance(vector_nodes, list):
        for index, vector_node in enumerate(vector_nodes):
            if not isinstance(vector_node, dict):
                continue
            vector_id = spec_node_identifier(vector_node, "vector", index)
            if vector_id in vector_seen:
                continue
            vector_seen.add(vector_id)
            expected.append(
                {
                    "ref": vector_id,
                    "kind": "vector",
                    "hash": hashlib.sha256(vector_node_path_content(vector_node).encode("utf-8")).hexdigest(),
                    "spec_node_id": vector_id,
                }
            )

    expected.sort(key=lambda item: (item["kind"], item["ref"], item["spec_node_id"], item["hash"]))
    return expected


def validate_asset_manifest(spec: dict, spec_path: str) -> list[Violation]:
    violations: list[Violation] = []
    expected_entries = expected_asset_manifest_entries(spec)
    if not expected_entries:
        return violations

    manifest_path = asset_manifest_path_from_spec(spec_path)
    if not manifest_path.exists():
        add_violation(
            violations,
            "v2.assetManifest.exists",
            str(manifest_path),
            f"manifest exists with {len(expected_entries)} asset entries",
            "missing file",
        )
        return violations

    try:
        manifest_raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        add_violation(
            violations,
            "v2.assetManifest.exists",
            str(manifest_path),
            "valid manifest JSON",
            f"invalid JSON: {exc}",
        )
        return violations

    if isinstance(manifest_raw, dict):
        manifest_assets = manifest_raw.get("assets")
    else:
        manifest_assets = manifest_raw
    if not isinstance(manifest_assets, list):
        add_violation(
            violations,
            "v2.assetManifest.exists",
            str(manifest_path),
            "assets list",
            f"invalid assets payload type: {type(manifest_assets).__name__}",
        )
        return violations

    manifest_index: dict[tuple[str, str], dict[str, str]] = {}
    duplicate_keys: set[tuple[str, str]] = set()
    for item in manifest_assets:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        ref = item.get("ref")
        hash_value = item.get("hash")
        spec_node_id = item.get("spec_node_id")
        if not all(isinstance(value, str) and value for value in (kind, ref, hash_value, spec_node_id)):
            continue
        local_path = item.get("local_path")
        asset_format = item.get("format")
        key = (kind, ref)
        if key in manifest_index:
            duplicate_keys.add(key)
        else:
            manifest_item = {
                "kind": kind,
                "ref": ref,
                "hash": hash_value,
                "spec_node_id": spec_node_id,
            }
            if isinstance(local_path, str) and local_path:
                manifest_item["local_path"] = local_path
            if isinstance(asset_format, str) and asset_format:
                manifest_item["format"] = asset_format
            manifest_index[key] = manifest_item

    for duplicate_kind, duplicate_ref in sorted(duplicate_keys):
        add_violation(
            violations,
            "v2.assetManifest.exists",
            f"{duplicate_kind}:{duplicate_ref}",
            "single manifest entry per asset ref",
            "duplicate manifest entries",
        )

    for expected in expected_entries:
        key = (expected["kind"], expected["ref"])
        actual = manifest_index.get(key)
        if actual is None:
            add_violation(
                violations,
                "v2.assetManifest.exists",
                f"{expected['kind']}:{expected['ref']}",
                json.dumps(expected, ensure_ascii=False, sort_keys=True),
                "missing entry",
            )
            continue
        if "local_path" in actual:
            valid_hash = re.fullmatch(r"[0-9a-fA-F]{64}", actual["hash"]) is not None
            valid_format = actual.get("format") in {"svg", "png"}
            matches_expected_identity = actual["spec_node_id"] == expected["spec_node_id"]
            if not (matches_expected_identity and valid_hash and valid_format):
                add_violation(
                    violations,
                    "v2.assetManifest.exists",
                    f"{expected['kind']}:{expected['ref']}",
                    "downloaded asset entry with matching spec_node_id, 64-char hash, and svg/png format",
                    json.dumps(actual, ensure_ascii=False, sort_keys=True),
                )
            continue
        if actual["hash"] != expected["hash"] or actual["spec_node_id"] != expected["spec_node_id"]:
            add_violation(
                violations,
                "v2.assetManifest.exists",
                f"{expected['kind']}:{expected['ref']}",
                json.dumps(expected, ensure_ascii=False, sort_keys=True),
                json.dumps(actual, ensure_ascii=False, sort_keys=True),
            )

    return violations


def validate_text_byte_exact(spec: dict, html: str) -> list[Violation]:
    violations: list[Violation] = []
    text_nodes = spec.get("text_nodes")
    if not isinstance(text_nodes, list):
        return violations

    for node in text_nodes:
        if not isinstance(node, dict):
            continue
        chars = node.get("characters", "")
        if not isinstance(chars, str) or not chars:
            continue
        if chars not in html:
            add_violation(
                violations,
                "텍스트 byte-exact",
                node,
                repr(chars),
                "HTML 에 byte-exact 미발견",
            )
    return violations


def _manifest_path_for_section(spec: dict, spec_dir: Path | None, spec_path: str | None = None) -> Path | None:
    section = spec.get("section")
    section_name = ""
    if isinstance(section, dict):
        raw_name = section.get("name")
        if isinstance(raw_name, str):
            section_name = raw_name.strip().lower()
    if spec_dir is not None and section_name:
        candidates = list(spec_dir.glob(f"{section_name}_asset_manifest.json"))
        if candidates:
            return candidates[0]
    if spec_path is not None:
        fallback = asset_manifest_path_from_spec(spec_path)
        if fallback.exists():
            return fallback
    return None


def _manifest_image_refs(manifest: object) -> set[str]:
    if isinstance(manifest, dict):
        assets = manifest.get("assets")
    else:
        assets = manifest
    if not isinstance(assets, list):
        return set()

    refs: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        kind = asset.get("kind")
        if isinstance(kind, str) and kind and kind != "image":
            continue
        ref = asset.get("image_ref")
        if not isinstance(ref, str) or not ref:
            ref = asset.get("ref")
        if isinstance(ref, str) and ref:
            refs.add(ref)
    return refs


def _manifest_html_asset_refs(manifest: object) -> set[str]:
    if isinstance(manifest, dict):
        assets = manifest.get("assets")
    else:
        assets = manifest
    if not isinstance(assets, list):
        return set()

    refs: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        local_path = asset.get("local_path")
        if isinstance(local_path, str) and local_path:
            stem = Path(urlsplit(local_path).path).stem
            if stem:
                refs.add(stem)
            continue

        kind = asset.get("kind")
        if isinstance(kind, str) and kind and kind != "image":
            continue
        ref = asset.get("image_ref")
        if not isinstance(ref, str) or not ref:
            ref = asset.get("ref")
        if isinstance(ref, str) and ref:
            refs.add(ref)
    return refs


def _html_img_basenames(html: str) -> set[str]:
    srcs = re.findall(r"<img\b[^>]*\bsrc\s*=\s*['\"]([^'\"]+)['\"]", html, flags=re.I)
    basenames: set[str] = set()
    for src in srcs:
        path = urlsplit(src).path
        stem = Path(path).stem
        if stem:
            basenames.add(stem)
    return basenames


def _asset_ref_matches_basename(ref: str, basename: str) -> bool:
    return ref in basename or basename in ref


def validate_asset_manifest_consistency(
    spec: dict,
    html: str,
    spec_dir: Path | None,
    spec_path: str | None = None,
) -> list[Violation]:
    manifest_path = _manifest_path_for_section(spec, spec_dir, spec_path)
    if manifest_path is None or not manifest_path.exists():
        return []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []

    manifest_refs = _manifest_html_asset_refs(manifest)
    html_basenames = _html_img_basenames(html)
    if not html_basenames:
        return []
    violations: list[Violation] = []

    for ref in sorted(manifest_refs):
        if not any(_asset_ref_matches_basename(ref, basename) for basename in html_basenames):
            add_violation(
                violations,
                "asset_manifest 일치",
                ref,
                "HTML에 존재해야 함",
                "HTML에 미발견",
            )

    for basename in sorted(html_basenames):
        if not any(_asset_ref_matches_basename(ref, basename) for ref in manifest_refs):
            add_violation(
                violations,
                "asset_manifest 일치",
                basename,
                "asset_manifest 등록 필요 (Figma 원본)",
                "통이미지 의심 (manifest 미등록)",
            )

    return violations


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


def parse_numeric_value(value: str | None) -> float | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return None
    return float(text)


def normalize_blend_mode_value(value: object) -> str:
    if not isinstance(value, str):
        return "PASS_THROUGH"
    text = value.strip()
    if not text:
        return "PASS_THROUGH"
    return text.upper()


def normalize_css_blend_mode(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip().lower().replace("_", "-")
    return token or None


def blend_mode_matches(expected: object, actual: str | None) -> bool:
    expected_mode = normalize_blend_mode_value(expected)
    actual_mode = normalize_css_blend_mode(actual)
    if expected_mode in {"PASS_THROUGH", "NORMAL"}:
        if actual_mode is None:
            return True
        return actual_mode == "normal"
    return actual_mode == expected_mode.lower().replace("_", "-")


def opacity_matches(expected: object, actual: str | None, tolerance: float = 0.01) -> bool:
    if not isinstance(expected, (int, float)):
        return True
    expected_value = float(expected)
    actual_value = parse_numeric_value(actual)
    if actual_value is None:
        return abs(expected_value - 1.0) <= tolerance
    return abs(actual_value - expected_value) <= tolerance


def shadow_components(value: str | None) -> tuple[float, float, float] | None:
    if not isinstance(value, str):
        return None
    lowered = value.strip().lower()
    if not lowered or lowered == "none":
        return None
    candidates = parse_length_candidates_px(value)
    if len(candidates) < 3:
        return None
    return (candidates[0], candidates[1], candidates[2])


def blur_radius(value: str | None) -> float | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"blur\(([^)]+)\)", value, flags=re.I)
    if not match:
        return None
    candidates = parse_length_candidates_px(match.group(1).strip())
    if not candidates:
        return None
    return candidates[0]


BORDER_STYLE_KEYWORDS = {
    "none",
    "hidden",
    "dotted",
    "dashed",
    "solid",
    "double",
    "groove",
    "ridge",
    "inset",
    "outset",
}


def collect_border_width_candidates(properties: dict[str, PropertyValue]) -> list[float]:
    widths: list[float] = []
    for prop in ("border-width", "border-top-width", "border-right-width", "border-bottom-width", "border-left-width"):
        value = properties.get(prop)
        if value:
            widths.extend(parse_length_candidates_px(value.value))

    for prop in ("border", "border-top", "border-right", "border-bottom", "border-left"):
        value = properties.get(prop)
        if value:
            widths.extend(parse_length_candidates_px(value.value))

    return widths


def collect_border_colors(properties: dict[str, PropertyValue]) -> list[str]:
    colors: list[str] = []
    for prop in ("border-color", "border-top-color", "border-right-color", "border-bottom-color", "border-left-color"):
        value = properties.get(prop)
        if value:
            colors.extend(extract_hex_colors(value.value))

    for prop in ("border", "border-top", "border-right", "border-bottom", "border-left"):
        value = properties.get(prop)
        if value:
            colors.extend(extract_hex_colors(value.value))

    deduped: list[str] = []
    seen: set[str] = set()
    for color in colors:
        if color in seen:
            continue
        seen.add(color)
        deduped.append(color)
    return deduped


def collect_border_styles(properties: dict[str, PropertyValue]) -> set[str]:
    styles: set[str] = set()
    for prop in ("border-style", "border-top-style", "border-right-style", "border-bottom-style", "border-left-style"):
        value = properties.get(prop)
        if value:
            for token in split_whitespace_tokens(value.value.lower()):
                if token in BORDER_STYLE_KEYWORDS:
                    styles.add(token)

    for prop in ("border", "border-top", "border-right", "border-bottom", "border-left"):
        value = properties.get(prop)
        if value:
            for token in split_whitespace_tokens(value.value.lower()):
                if token in BORDER_STYLE_KEYWORDS:
                    styles.add(token)
    return styles


def border_visible(properties: dict[str, PropertyValue]) -> bool:
    styles = collect_border_styles(properties)
    if not styles:
        # border shorthand with width/color but no style token can still render as default solid.
        return bool(collect_border_width_candidates(properties) or collect_border_colors(properties))
    return any(style not in {"none", "hidden"} for style in styles)


def border_uses_gradient(properties: dict[str, PropertyValue]) -> bool:
    for prop in ("border-image", "border-image-source", "border"):
        value = properties.get(prop)
        if value and "gradient(" in value.value.lower():
            return True
    return False


def parse_border_radius_tokens(value: str | None) -> list[str] | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    primary = text.split("/", 1)[0].strip()
    tokens = split_whitespace_tokens(primary)
    if not tokens:
        return None
    if len(tokens) == 1:
        return [tokens[0], tokens[0], tokens[0], tokens[0]]
    if len(tokens) == 2:
        return [tokens[0], tokens[1], tokens[0], tokens[1]]
    if len(tokens) == 3:
        return [tokens[0], tokens[1], tokens[2], tokens[1]]
    return tokens[:4]


def resolve_corner_radii_values(properties: dict[str, PropertyValue]) -> list[str | None]:
    resolved: list[str | None] = [None, None, None, None]
    shorthand = properties.get("border-radius")
    if shorthand:
        parsed = parse_border_radius_tokens(shorthand.value)
        if parsed:
            resolved = parsed

    longhand_map = {
        "border-top-left-radius": 0,
        "border-top-right-radius": 1,
        "border-bottom-right-radius": 2,
        "border-bottom-left-radius": 3,
    }
    for prop, index in longhand_map.items():
        value = properties.get(prop)
        if value:
            parsed = parse_border_radius_tokens(value.value)
            if parsed:
                resolved[index] = parsed[0]
    return resolved


def corner_radii_match(expected: object, properties: dict[str, PropertyValue]) -> bool:
    if not isinstance(expected, list) or len(expected) < 4:
        return True
    expected_values: list[float] = []
    for value in expected[:4]:
        if not isinstance(value, (int, float)):
            return True
        expected_values.append(float(value))

    actual_values = resolve_corner_radii_values(properties)
    if all(abs(value) <= 0.01 for value in expected_values):
        return all(item is None or value_matches_px(item, 0) for item in actual_values)

    for index, expected_value in enumerate(expected_values):
        actual = actual_values[index]
        if actual is None or not value_matches_px(actual, expected_value):
            return False
    return True


def parse_flex_grow(properties: dict[str, PropertyValue]) -> float | None:
    flex_grow = properties.get("flex-grow")
    if flex_grow:
        parsed = parse_numeric_value(flex_grow.value)
        if parsed is not None:
            return parsed

    flex = properties.get("flex")
    if flex:
        tokens = split_whitespace_tokens(flex.value)
        if tokens:
            parsed = parse_numeric_value(tokens[0])
            if parsed is not None:
                return parsed
    return None


def is_auto_or_fit_content(value: str | None) -> bool:
    if value is None:
        return True
    lowered = value.strip().lower()
    return lowered in {"auto", "fit-content", "max-content", "min-content", "content"}


def is_fill_sizing(value: str | None, properties: dict[str, PropertyValue]) -> bool:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"100%", "stretch", "fill-available", "-webkit-fill-available"}:
            return True
    flex_grow = parse_flex_grow(properties)
    return flex_grow is not None and flex_grow >= 1.0


def is_explicit_fixed_sizing(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.strip().lower()
    if lowered in {"auto", "fit-content", "max-content", "min-content", "100%"}:
        return False
    if parse_length_candidates_px(lowered):
        return True
    return bool(re.search(r"\d", lowered) and any(token in lowered for token in ("calc(", "clamp(", "min(", "max(")))


def layout_sizing_axis_match(expected: object, value: str | None, properties: dict[str, PropertyValue]) -> bool:
    if not isinstance(expected, str):
        return True
    normalized = expected.strip().upper()
    if normalized == "HUG":
        return is_auto_or_fit_content(value)
    if normalized == "FILL":
        return is_fill_sizing(value, properties)
    if normalized == "FIXED":
        return is_explicit_fixed_sizing(value)
    return True


def layout_align_matches(expected: object, properties: dict[str, PropertyValue]) -> bool:
    if not isinstance(expected, str):
        return True
    normalized = expected.strip().upper()
    if normalized == "INHERIT":
        return True
    value = properties.get("align-self")
    actual = value.value.strip().lower() if value else ""
    if normalized == "STRETCH":
        return actual == "stretch"
    if normalized == "MIN":
        return actual in {"flex-start", "start"}
    if normalized == "MAX":
        return actual in {"flex-end", "end"}
    if normalized == "CENTER":
        return actual == "center"
    return True


def layout_sizing_matches(frame: dict, properties: dict[str, PropertyValue]) -> bool:
    has_layout_keys = any(
        key in frame for key in ("layoutSizingHorizontal", "layoutSizingVertical", "layoutGrow", "layoutAlign")
    )
    if not has_layout_keys:
        return True

    width_prop = properties.get("width")
    height_prop = properties.get("height")
    width_value = width_prop.value if width_prop else None
    height_value = height_prop.value if height_prop else None

    horizontal_ok = layout_sizing_axis_match(frame.get("layoutSizingHorizontal"), width_value, properties)
    vertical_ok = layout_sizing_axis_match(frame.get("layoutSizingVertical"), height_value, properties)
    align_ok = layout_align_matches(frame.get("layoutAlign"), properties)

    grow_expected = frame.get("layoutGrow")
    grow_ok = True
    if isinstance(grow_expected, (int, float)) and float(grow_expected) > 0:
        grow_actual = parse_flex_grow(properties)
        grow_ok = grow_actual is not None and grow_actual >= float(grow_expected) - 0.05

    return horizontal_ok and vertical_ok and align_ok and grow_ok


def text_case_expected_transform(text_case: object) -> str | None:
    if not isinstance(text_case, str):
        return None
    normalized = text_case.strip().upper()
    mapping = {
        "ORIGINAL": "none",
        "UPPER": "uppercase",
        "LOWER": "lowercase",
        "TITLE": "capitalize",
        "SMALL_CAPS": "none",
        "SMALL_CAPS_FORCED": "none",
    }
    return mapping.get(normalized)


def text_case_matches(text_case: object, css_text_transform: str | None) -> bool:
    expected = text_case_expected_transform(text_case)
    if expected is None:
        return True
    if css_text_transform is None:
        return expected == "none"
    actual = css_text_transform.strip().lower()
    if expected == "none":
        return actual in {"none", "initial", "unset", "inherit"}
    return actual == expected


def collect_text_decoration_tokens(css_text_decoration: str | None, css_text_decoration_line: str | None) -> set[str]:
    tokens: set[str] = set()
    for value in (css_text_decoration, css_text_decoration_line):
        if not isinstance(value, str):
            continue
        for token in re.findall(r"[a-z-]+", value.lower()):
            tokens.add(token)
    return tokens


def text_decoration_matches(expected: object, css_text_decoration: str | None, css_text_decoration_line: str | None) -> bool:
    if not isinstance(expected, str):
        return True
    expected_norm = expected.strip().upper()
    tokens = collect_text_decoration_tokens(css_text_decoration, css_text_decoration_line)
    if expected_norm == "NONE":
        if not tokens:
            return True
        return "underline" not in tokens and "line-through" not in tokens
    if expected_norm == "UNDERLINE":
        return "underline" in tokens
    if expected_norm == "STRIKETHROUGH":
        return "line-through" in tokens
    return True


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


def v2_fills_list(frame: dict) -> list[dict]:
    fills = frame.get("fills_v2")
    if isinstance(fills, list):
        return [item for item in fills if isinstance(item, dict)]
    return []


def gradient_colors_match(fill: dict, properties: dict[str, PropertyValue]) -> bool:
    fill_type = str(fill.get("type") or "")
    expected_keyword = "linear-gradient(" if fill_type == "GRADIENT_LINEAR" else "radial-gradient("
    gradient_sources: list[str] = []
    for prop in ("background", "background-image"):
        prop_value = properties.get(prop)
        if prop_value:
            gradient_sources.append(prop_value.value.lower())
    if not any(expected_keyword in source for source in gradient_sources):
        return False

    expected_colors: list[str] = []
    stops = fill.get("gradientStops")
    if isinstance(stops, list):
        for stop in stops:
            if not isinstance(stop, dict):
                continue
            color = normalize_hex(stop.get("color"))
            if color:
                expected_colors.append(color)
    if not expected_colors:
        return False

    actual_colors = set()
    for source in gradient_sources:
        actual_colors.update(extract_hex_colors(source))
    return all(color in actual_colors for color in expected_colors)


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


def match_text_node(
    text_value: str,
    candidates: list[ElementMatch],
    spec_ratio: float | None = None,
    css_rules: list[CSSRule] | None = None,
) -> ElementMatch | None:
    normalized = normalize_text_for_match(text_value)
    if not normalized:
        return None

    ranked: list[tuple[int, int, int, int, int, ElementMatch]] = []
    for candidate in candidates:
        if normalized not in candidate.normalized_text:
            continue
        exact = 0 if candidate.normalized_text == normalized else 1
        excess = len(candidate.normalized_text) - len(normalized)
        ratio_penalty = 2
        if spec_ratio is not None and css_rules is not None:
            try:
                props = compute_element_properties(candidate.element, css_rules)
                actual_ratio = parse_line_height_ratio(
                    props.get("line-height").value if props.get("line-height") else None,
                    props.get("font-size").value if props.get("font-size") else None,
                )
                if actual_ratio is not None and abs(actual_ratio - spec_ratio) <= 0.05:
                    ratio_penalty = 0
                elif actual_ratio is not None:
                    ratio_penalty = 1
            except Exception:
                pass
        depth_rank = -candidate.element.depth
        ranked.append((exact, ratio_penalty, excess, depth_rank, candidate.element.order, candidate))

    if not ranked:
        return None
    ranked.sort(key=lambda item: item[:5])
    return ranked[0][5]


def build_special_whitespace_regex(text: str) -> str:
    parts: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        segment = "".join(buffer)
        # Preserve leading/trailing whitespace as optional \s* so regex allows
        # original space characters that precede/follow non-space tokens.
        leading = r"\s*" if segment and segment[0].isspace() else ""
        trailing = r"\s*" if segment and segment[-1].isspace() else ""
        tokens = re.split(r"\s+", segment.strip())
        if not tokens or tokens == [""]:
            parts.append(r"\s+")
        else:
            parts.append(leading + r"\s+".join(re.escape(token) for token in tokens if token) + trailing)
        buffer.clear()

    for char in text:
        if char in {"\n", "\u2028"}:
            flush()
            parts.append(r"\s*(?:\u2028|\r?\n)\s*")
            continue
        buffer.append(char)
    flush()
    return "".join(parts)


def special_whitespace_preserved(spec_text: str, actual_text: str) -> bool:
    if not any(marker in spec_text for marker in ("\n", "\u2028")):
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


def rules_conflict_payload(node: dict) -> tuple[str, str, str] | None:
    conflict = node.get("rules_conflict")
    if not isinstance(conflict, dict):
        return None
    rule_id = conflict.get("rule_id")
    figma_value = conflict.get("figma_value")
    applied_value = conflict.get("applied_value")
    if not isinstance(rule_id, str) or not rule_id.strip():
        return None
    return (
        rule_id.strip(),
        str(figma_value) if figma_value is not None else "",
        str(applied_value) if applied_value is not None else "",
    )


def log_rules_conflict_once(node: dict, rule_id: str, figma_value: str, applied_value: str, seen: set[tuple[str, str]]) -> None:
    node_id = str(node.get("id") or node.get("node_id") or "-")
    marker = (node_id, rule_id)
    if marker in seen:
        return
    seen.add(marker)
    print(
        f"[RULES-CONFLICT] node {node_id} bypassed rule {rule_id} "
        f"(figma: {figma_value} \u2192 applied: {applied_value})"
    )


def should_bypass_rule(node: dict, rule_id: str, seen: set[tuple[str, str]]) -> bool:
    payload = rules_conflict_payload(node)
    if payload is None:
        return False
    conflict_rule_id, figma_value, applied_value = payload
    if conflict_rule_id != rule_id:
        return False
    log_rules_conflict_once(node, conflict_rule_id, figma_value, applied_value, seen)
    return True


def selector_scope_prefixes(rule: CSSRule | None) -> list[str]:
    if rule is None:
        return []
    prefixes: list[str] = []
    for selector in rule.selectors:
        base = strip_pseudos(selector).strip()
        if base:
            prefixes.append(base)
    return prefixes


def has_margin_bottom_mapping(
    frame_rule: CSSRule | None,
    css_rules: list[CSSRule],
    spacing: float | int,
    frame_properties: dict[str, PropertyValue],
) -> bool:
    if value_matches_px(frame_properties.get("margin-bottom").value if frame_properties.get("margin-bottom") else None, spacing):
        return True

    prefixes = selector_scope_prefixes(frame_rule)
    if not prefixes:
        return False

    for css_rule in css_rules:
        if css_rule.pseudo_element is not None:
            continue
        margin_bottom = css_rule.declarations.get("margin-bottom")
        if not value_matches_px(margin_bottom, spacing):
            continue
        for selector in css_rule.selectors:
            normalized = strip_pseudos(selector).strip()
            for prefix in prefixes:
                if (
                    normalized == prefix
                    or normalized.startswith(prefix + " ")
                    or normalized.startswith(prefix + ">")
                ):
                    return True
    return False


def enforce_policy1_vertical_margin_bottom(
    frame: dict,
    props: dict[str, PropertyValue],
    best_rule: CSSRule | None,
    css_rules: list[CSSRule],
    rule_display: str,
    violations: list[Violation],
    rules_conflict_seen: set[tuple[str, str]],
) -> None:
    spacing = frame.get("itemSpacing")
    if not isinstance(spacing, (int, float)) or spacing <= 0:
        return
    if str(frame.get("layoutMode") or "").upper() != "VERTICAL":
        return
    if should_bypass_rule(frame, "vertical_frame_itemspacing_uses_margin_bottom", rules_conflict_seen):
        return

    gap_props = [prop for prop in ("gap", "row-gap", "column-gap") if prop in props]
    if gap_props:
        add_violation(
            violations,
            POLICY_1_CATEGORY,
            frame,
            f"margin-bottom:{render_value(spacing)}px and no gap/row-gap/column-gap",
            f"{', '.join(f'{prop}={props[prop].value}' for prop in gap_props)} @ {rule_display}",
        )
        return

    if not has_margin_bottom_mapping(best_rule, css_rules, spacing, props):
        add_violation(
            violations,
            POLICY_1_CATEGORY,
            frame,
            f"margin-bottom:{render_value(spacing)}px",
            f"margin-bottom 미발견 @ {rule_display}",
        )


def enforce_policy2_constraints_extract_only(frame: dict) -> bool:
    _ = frame
    return True


def enforce_policy3_rules_conflict_bypass(node: dict, rule_id: str, seen: set[tuple[str, str]]) -> bool:
    return should_bypass_rule(node, rule_id, seen)


def _rule_severity(rule: RuleDefinition) -> str:
    severity = rule.severity
    return severity.value if hasattr(severity, "value") else str(severity)


def _rule_handler_name(rule: RuleDefinition) -> str:
    return rule.custom_handler or rule.id


def _stub_handler(rule: RuleDefinition, _context: RuleDispatchContext | None = None) -> RuleHandlerResult:
    handler_name = _rule_handler_name(rule)
    return RuleHandlerResult(
        rule_id=rule.id,
        severity="warning",
        passed=False,
        skipped=False,
        message=f"[STUB-PASS BLOCKED] handler {handler_name} not implemented — treating as MAJOR FAIL",
    )


def _figma_policy_handler(rule: RuleDefinition, _context: RuleDispatchContext | None = None) -> RuleHandlerResult:
    return RuleHandlerResult(
        rule_id=rule.id,
        severity=_rule_severity(rule),
        passed=True,
        skipped=True,
        message="validated_by_figma_validate_runtime",
    )


PYDANTIC_POLICY_HANDLERS: dict[str, Callable[[RuleDefinition, RuleDispatchContext | None], RuleHandlerResult]] = {
    "vertical_frame_itemspacing_uses_margin_bottom": _figma_policy_handler,
    "no_constraints_to_position_absolute_mapping": _figma_policy_handler,
    "figma_rules_conflict_uses_meta_marker": _figma_policy_handler,
}


def build_rule_handler_registry(
    rules: Iterable[RuleDefinition] | None = None,
) -> dict[str, Callable[[RuleDefinition, RuleDispatchContext | None], RuleHandlerResult]]:
    source_rules = list(rules) if rules is not None else load_rules()
    registry = {rule.id: _stub_handler for rule in source_rules}
    registry.update(PYDANTIC_POLICY_HANDLERS)
    return registry


RULE_HANDLER_REGISTRY = build_rule_handler_registry()


def dispatch_rule_handler(rule: RuleDefinition, context: RuleDispatchContext | None = None) -> RuleHandlerResult:
    handler = RULE_HANDLER_REGISTRY.get(rule.id, _stub_handler)
    return handler(rule, context)


def validate_text_nodes(
    text_nodes: list[dict],
    candidates: list[ElementMatch],
    css_rules: list[CSSRule],
    schema_branch: str = "v1",
) -> tuple[list[Violation], list[dict]]:
    violations: list[Violation] = []
    missing_rows: list[dict] = []
    property_cache: dict[int, dict[str, PropertyValue]] = {}
    used_orders: set[int] = set()

    for node in text_nodes:
        spec_ratio = node.get("lineHeightRatio")
        try:
            spec_ratio = float(spec_ratio) if spec_ratio is not None else None
        except (TypeError, ValueError):
            spec_ratio = None
        available = [c for c in candidates if c.element.order not in used_orders]
        match = match_text_node(node.get("characters", ""), available, spec_ratio, css_rules)
        if match is None:
            match = match_text_node(node.get("characters", ""), candidates, spec_ratio, css_rules)
        if match is not None:
            used_orders.add(match.element.order)
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

        if schema_branch == "v2":
            opacity_prop = properties.get("opacity")
            opacity_value = opacity_prop.value if opacity_prop else None
            if not opacity_matches(node.get("opacity"), opacity_value):
                add_violation(
                    violations,
                    "v2.opacity.match",
                    node,
                    render_value(node.get("opacity")),
                    f"{render_value(opacity_value)} @ {match.element.short_selector()}",
                )

            blend_prop = properties.get("mix-blend-mode")
            blend_value = blend_prop.value if blend_prop else None
            if not blend_mode_matches(node.get("blendMode"), blend_value):
                add_violation(
                    violations,
                    "v2.blendMode.match",
                    node,
                    render_value(node.get("blendMode")),
                    f"{render_value(blend_value)} @ {match.element.short_selector()}",
                )

            transform_prop = properties.get("text-transform")
            transform_value = transform_prop.value if transform_prop else None
            if not text_case_matches(node.get("textCase"), transform_value):
                add_violation(
                    violations,
                    "v2.textCase.match",
                    node,
                    render_value(node.get("textCase")),
                    f"{render_value(transform_value)} @ {match.element.short_selector()}",
                )

            decoration_prop = properties.get("text-decoration")
            decoration_line_prop = properties.get("text-decoration-line")
            decoration_value = decoration_prop.value if decoration_prop else None
            decoration_line_value = decoration_line_prop.value if decoration_line_prop else None
            if not text_decoration_matches(node.get("textDecoration"), decoration_value, decoration_line_value):
                add_violation(
                    violations,
                    "v2.textDecoration.match",
                    node,
                    render_value(node.get("textDecoration")),
                    (
                        f"text-decoration={render_value(decoration_value)}, "
                        f"text-decoration-line={render_value(decoration_line_value)} @ {match.element.short_selector()}"
                    ),
                )

            effects = node.get("effects")
            if isinstance(effects, list):
                for effect in effects:
                    if not isinstance(effect, dict):
                        continue
                    effect_type = effect.get("type")
                    if effect_type == "DROP_SHADOW":
                        shadow_value = None
                        if properties.get("text-shadow"):
                            shadow_value = properties["text-shadow"].value
                        elif properties.get("box-shadow"):
                            shadow_value = properties["box-shadow"].value
                        expected_offset = effect.get("offset") if isinstance(effect.get("offset"), dict) else {}
                        expected_x = expected_offset.get("x") if isinstance(expected_offset, dict) else None
                        expected_y = expected_offset.get("y") if isinstance(expected_offset, dict) else None
                        expected_radius = effect.get("radius")
                        parsed = shadow_components(shadow_value)
                        if (
                            parsed is None
                            or not isinstance(expected_x, (int, float))
                            or not isinstance(expected_y, (int, float))
                            or not isinstance(expected_radius, (int, float))
                            or abs(parsed[0] - float(expected_x)) > 1.0
                            or abs(parsed[1] - float(expected_y)) > 1.0
                            or abs(parsed[2] - float(expected_radius)) > 1.0
                        ):
                            add_violation(
                                violations,
                                "v2.effects.shadow.match",
                                node,
                                f"x={render_value(expected_x)}, y={render_value(expected_y)}, blur={render_value(expected_radius)}",
                                f"{render_value(shadow_value)} @ {match.element.short_selector()}",
                            )
                    elif effect_type == "LAYER_BLUR":
                        filter_value = properties.get("filter").value if properties.get("filter") else None
                        radius_value = blur_radius(filter_value)
                        expected_radius = effect.get("radius")
                        if not isinstance(expected_radius, (int, float)) or radius_value is None or abs(radius_value - float(expected_radius)) > 1.0:
                            add_violation(
                                violations,
                                "v2.effects.blur.match",
                                node,
                                f"filter: blur({render_value(expected_radius)}px)",
                                f"{render_value(filter_value)} @ {match.element.short_selector()}",
                            )
                    elif effect_type == "BACKGROUND_BLUR":
                        filter_value = properties.get("backdrop-filter").value if properties.get("backdrop-filter") else None
                        radius_value = blur_radius(filter_value)
                        expected_radius = effect.get("radius")
                        if not isinstance(expected_radius, (int, float)) or radius_value is None or abs(radius_value - float(expected_radius)) > 1.0:
                            add_violation(
                                violations,
                                "v2.effects.blur.match",
                                node,
                                f"backdrop-filter: blur({render_value(expected_radius)}px)",
                                f"{render_value(filter_value)} @ {match.element.short_selector()}",
                            )

    return violations, missing_rows


def validate_frame_nodes(frame_nodes: list[dict], css_rules: list[CSSRule], schema_branch: str = "v1") -> list[Violation]:
    violations: list[Violation] = []
    rules_conflict_seen: set[tuple[str, str]] = set()
    parent_lookup = infer_parent_lookup(frame_nodes)
    component_rule_signatures: dict[str, list[tuple[str, str]]] = {}

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
        if schema_branch == "v2":
            component_id = frame.get("componentId")
            if isinstance(component_id, str) and component_id.strip():
                signature = "UNMATCHED"
                if best_rule is not None:
                    signature = ",".join(best_rule.selectors)
                component_rule_signatures.setdefault(component_id.strip(), []).append((frame_id, signature))

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
            # VERTICAL frames use child margin-bottom mapping in policy-1 — skip gap check here,
            # and enforce no gap/row-gap/column-gap separately below.
            if spacing not in (None, 0) and str(frame.get("layoutMode") or "").upper() != "VERTICAL" and not any(value_matches_px(value, spacing) for value in gap_values):
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
        # Skip gap clamp for VERTICAL frames (policy-1: no gap on column flex, use margin-bottom)
        if isinstance(spacing, (int, float)) and spacing >= 100 and str(frame.get("layoutMode") or "").upper() != "VERTICAL":
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

        matched_flex_dir = ""
        if "flex-direction" in props:
            matched_flex_dir = str(props["flex-direction"].value).strip().lower()
        if str(frame.get("layoutMode") or "").upper() == "VERTICAL" and matched_flex_dir == "column" and any(prop in props for prop in ("gap", "row-gap", "column-gap")):
            if not enforce_policy3_rules_conflict_bypass(frame, "no_column_flex_gap", rules_conflict_seen):
                add_violation(
                    violations,
                    "column flex gap 금지",
                    frame,
                    "gap 미사용",
                    f"{', '.join(f'{prop}={props[prop].value}' for prop in ('gap', 'row-gap', 'column-gap') if prop in props)} @ {rule_display}",
                )

        if schema_branch == "v2" and str(frame.get("layoutMode") or "").upper() == "VERTICAL":
            enforce_policy2_constraints_extract_only(frame)
            enforce_policy1_vertical_margin_bottom(
                frame=frame,
                props=props,
                best_rule=best_rule,
                css_rules=css_rules,
                rule_display=rule_display,
                violations=violations,
                rules_conflict_seen=rules_conflict_seen,
            )

        if schema_branch == "v2":
            for fill in v2_fills_list(frame):
                fill_type = fill.get("type")
                if fill_type == "SOLID":
                    expected_color_v2 = normalize_hex(fill.get("color"))
                    if expected_color_v2 and expected_color_v2 not in backgrounds:
                        add_violation(
                            violations,
                            "v2.fills.solid.match",
                            frame,
                            expected_color_v2,
                            f"{', '.join(backgrounds) if backgrounds else 'background-color/background 미발견'} @ {rule_display}",
                        )
                elif fill_type in {"GRADIENT_LINEAR", "GRADIENT_RADIAL"}:
                    if not gradient_colors_match(fill, props):
                        add_violation(
                            violations,
                            "v2.fills.gradient.match",
                            frame,
                            f"{fill_type} stops in CSS gradient",
                            f"{rule_display} ({', '.join(matched_notes) if matched_notes else 'gradient 불일치'})",
                        )
                elif fill_type == "IMAGE":
                    background_value = props.get("background").value if props.get("background") else ""
                    background_image_value = props.get("background-image").value if props.get("background-image") else ""
                    joined = f"{background_value} {background_image_value}".lower()
                    if "url(" not in joined:
                        add_violation(
                            violations,
                            "v2.fills.image.match",
                            frame,
                            "background-image: url(...)",
                            f"{rule_display} (url() 미발견)",
                        )

            frame_effects = frame.get("effects")
            if isinstance(frame_effects, list):
                for effect in frame_effects:
                    if not isinstance(effect, dict):
                        continue
                    effect_type = effect.get("type")
                    if effect_type == "DROP_SHADOW":
                        shadow_value = props.get("box-shadow").value if props.get("box-shadow") else None
                        parsed = shadow_components(shadow_value)
                        offset = effect.get("offset") if isinstance(effect.get("offset"), dict) else {}
                        expected_x = offset.get("x") if isinstance(offset, dict) else None
                        expected_y = offset.get("y") if isinstance(offset, dict) else None
                        expected_radius = effect.get("radius")
                        if (
                            parsed is None
                            or not isinstance(expected_x, (int, float))
                            or not isinstance(expected_y, (int, float))
                            or not isinstance(expected_radius, (int, float))
                            or abs(parsed[0] - float(expected_x)) > 1.0
                            or abs(parsed[1] - float(expected_y)) > 1.0
                            or abs(parsed[2] - float(expected_radius)) > 1.0
                        ):
                            node_id = render_value(frame.get("id"))
                            add_violation(
                                violations,
                                "v2.effects.shadow.match",
                                frame,
                                f"[V2-EFFECTS] node {node_id} expected box-shadow for DROP_SHADOW",
                                f"{render_value(shadow_value)} @ {rule_display}",
                            )
                    elif effect_type == "LAYER_BLUR":
                        filter_value = props.get("filter").value if props.get("filter") else None
                        expected_radius = effect.get("radius")
                        actual_radius = blur_radius(filter_value)
                        if not isinstance(expected_radius, (int, float)) or actual_radius is None or abs(actual_radius - float(expected_radius)) > 1.0:
                            add_violation(
                                violations,
                                "v2.effects.blur.match",
                                frame,
                                f"filter: blur({render_value(expected_radius)}px)",
                                f"{render_value(filter_value)} @ {rule_display}",
                            )
                    elif effect_type == "BACKGROUND_BLUR":
                        filter_value = props.get("backdrop-filter").value if props.get("backdrop-filter") else None
                        expected_radius = effect.get("radius")
                        actual_radius = blur_radius(filter_value)
                        if not isinstance(expected_radius, (int, float)) or actual_radius is None or abs(actual_radius - float(expected_radius)) > 1.0:
                            add_violation(
                                violations,
                                "v2.effects.blur.match",
                                frame,
                                f"backdrop-filter: blur({render_value(expected_radius)}px)",
                                f"{render_value(filter_value)} @ {rule_display}",
                            )

            opacity_prop = props.get("opacity")
            opacity_value = opacity_prop.value if opacity_prop else None
            if not opacity_matches(frame.get("opacity"), opacity_value):
                add_violation(
                    violations,
                    "v2.opacity.match",
                    frame,
                    render_value(frame.get("opacity")),
                    f"{render_value(opacity_value)} @ {rule_display}",
                )

            blend_prop = props.get("mix-blend-mode")
            blend_value = blend_prop.value if blend_prop else None
            if not blend_mode_matches(frame.get("blendMode"), blend_value):
                add_violation(
                    violations,
                    "v2.blendMode.match",
                    frame,
                    render_value(frame.get("blendMode")),
                    f"{render_value(blend_value)} @ {rule_display}",
                )

            strokes = frame.get("strokes")
            first_stroke = None
            if isinstance(strokes, list):
                for stroke in strokes:
                    if isinstance(stroke, dict):
                        first_stroke = stroke
                        break
            if isinstance(first_stroke, dict):
                stroke_type = first_stroke.get("type")
                expected_weight = frame.get("strokeWeight")
                expected_color = normalize_hex(first_stroke.get("color"))
                border_widths = collect_border_width_candidates(props)
                border_colors = collect_border_colors(props)
                type_ok = border_visible(props)
                if stroke_type in {"GRADIENT_LINEAR", "GRADIENT_RADIAL"}:
                    type_ok = border_uses_gradient(props)
                weight_ok = isinstance(expected_weight, (int, float)) and any(
                    abs(width - float(expected_weight)) <= 0.75 for width in border_widths
                )
                color_ok = True
                if stroke_type == "SOLID" and expected_color:
                    color_ok = expected_color in border_colors
                if not (type_ok and weight_ok and color_ok):
                    add_violation(
                        violations,
                        "v2.strokes.match",
                        frame,
                        (
                            f"type={render_value(stroke_type)}, "
                            f"color={render_value(expected_color)}, "
                            f"weight={render_value(expected_weight)}"
                        ),
                        (
                            f"styles={','.join(sorted(collect_border_styles(props))) or '-'}, "
                            f"colors={','.join(border_colors) or '-'}, "
                            f"widths={','.join(render_value(width) for width in border_widths) or '-'} @ {rule_display}"
                        ),
                    )

            expected_corners = frame.get("rectangleCornerRadii")
            if not corner_radii_match(expected_corners, props):
                add_violation(
                    violations,
                    "v2.cornerRadii.match",
                    frame,
                    render_value(expected_corners),
                    f"{render_value(resolve_corner_radii_values(props))} @ {rule_display}",
                )

            if not layout_sizing_matches(frame, props):
                add_violation(
                    violations,
                    "v2.layoutSizing.match",
                    frame,
                    (
                        f"H={render_value(frame.get('layoutSizingHorizontal'))}, "
                        f"V={render_value(frame.get('layoutSizingVertical'))}, "
                        f"grow={render_value(frame.get('layoutGrow'))}, "
                        f"align={render_value(frame.get('layoutAlign'))}"
                    ),
                    (
                        f"width={render_value(props.get('width').value if props.get('width') else None)}, "
                        f"height={render_value(props.get('height').value if props.get('height') else None)}, "
                        f"flex={render_value(props.get('flex').value if props.get('flex') else None)}, "
                        f"flex-grow={render_value(props.get('flex-grow').value if props.get('flex-grow') else None)}, "
                        f"align-self={render_value(props.get('align-self').value if props.get('align-self') else None)} @ {rule_display}"
                    ),
                )

    if schema_branch == "v2":
        for component_id, instances in component_rule_signatures.items():
            if len(instances) < 2:
                continue
            signatures = {signature for _, signature in instances}
            if len(signatures) <= 1:
                continue
            frame_ids = ", ".join(frame_id for frame_id, _ in instances)
            add_violation(
                violations,
                "v2.componentId.match",
                frame_ids,
                f"single selector/template signature for componentId={component_id}",
                "; ".join(f"{frame_id}=>{signature}" for frame_id, signature in instances),
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


def run_v2_categories(
    *,
    spec: dict,
    spec_path: str,
    spec_dir: Path | None,
    html_text: str,
    text_nodes: list[dict],
    frame_nodes: list[dict],
    interactions: list[dict],
    text_candidates: list[ElementMatch],
    css_rules: list[CSSRule],
    root: DOMElement,
) -> tuple[list[Violation], list[dict]]:
    text_violations, missing_rows = validate_text_nodes(
        text_nodes,
        text_candidates,
        css_rules,
        schema_branch="v2",
    )
    frame_violations = validate_frame_nodes(frame_nodes, css_rules, schema_branch="v2")
    interaction_violations = validate_interactions(interactions, root)
    asset_manifest_violations = validate_asset_manifest(spec, spec_path)
    text_byte_exact_violations = validate_text_byte_exact(spec, html_text)
    asset_consistency_violations = validate_asset_manifest_consistency(spec, html_text, spec_dir, spec_path)
    violations = (
        text_byte_exact_violations
        + text_violations
        + frame_violations
        + interaction_violations
        + asset_manifest_violations
        + asset_consistency_violations
    )
    return violations, missing_rows


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


def section_name_from_spec(spec: dict, spec_path: str) -> str:
    section = spec.get("section")
    if isinstance(section, dict):
        name = section.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip().lower()
    stem = Path(spec_path).stem
    if stem.endswith("_spec"):
        stem = stem[: -len("_spec")]
    return stem.lower()


def validate_spec_payload(
    *,
    spec: dict,
    spec_path: str,
    spec_dir: Path | None,
    html_text: str,
    parser: SimpleHTMLDocumentParser,
    css_rules: list[CSSRule],
    text_candidates: list[ElementMatch],
) -> SectionValidationResult:
    schema_branch = parse_schema_branch(spec.get("schema_version"))
    text_nodes = spec.get("text_nodes")
    frame_nodes = spec.get("frame_nodes")
    interactions = spec.get("interactions")
    if not isinstance(text_nodes, list) or not isinstance(frame_nodes, list) or not isinstance(interactions, list):
        fail("Invalid spec JSON: expected text_nodes/frame_nodes/interactions arrays")

    if schema_branch == "v2":
        violations, missing_rows = run_v2_categories(
            spec=spec,
            spec_path=spec_path,
            spec_dir=spec_dir,
            html_text=html_text,
            text_nodes=text_nodes,
            frame_nodes=frame_nodes,
            interactions=interactions,
            text_candidates=text_candidates,
            css_rules=css_rules,
            root=parser.root,
        )
    else:
        text_violations, missing_rows = validate_text_nodes(
            text_nodes,
            text_candidates,
            css_rules,
            schema_branch=schema_branch,
        )
        frame_violations = validate_frame_nodes(frame_nodes, css_rules, schema_branch=schema_branch)
        interaction_violations = validate_interactions(interactions, parser.root)
        text_byte_exact_violations = validate_text_byte_exact(spec, html_text)
        asset_consistency_violations = validate_asset_manifest_consistency(spec, html_text, spec_dir, spec_path)
        violations = (
            text_byte_exact_violations
            + text_violations
            + frame_violations
            + interaction_violations
            + asset_consistency_violations
        )

    return SectionValidationResult(
        section_name=section_name_from_spec(spec, spec_path),
        schema_branch=schema_branch,
        violations=violations,
        missing_rows=missing_rows,
    )


def violation_severity(category: str) -> str:
    if category in CRITICAL_CATEGORIES:
        return "CRITICAL"
    if category in MAJOR_CATEGORIES:
        return "MAJOR"
    return "MINOR"


def violation_category_counts(violations: list[Violation]) -> Counter[str]:
    return Counter(item.category for item in violations)


def violation_severity_counts(violations: list[Violation]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in violations:
        counts[violation_severity(item.category)] += 1
    return counts


def print_section_category_summary(violations: list[Violation]) -> None:
    print()
    print("위반 카테고리 | 건수")
    counts = violation_category_counts(violations)
    if not counts:
        print("없음 | 0")
        return
    for category in sorted(counts):
        print(f"{category} | {counts[category]}")


def print_spec_dir_report(results: list[SectionValidationResult]) -> None:
    for index, result in enumerate(results):
        if index:
            print()
        print(f"=== [{result.section_name}] ===")
        print_report(result.violations, result.missing_rows)
        print_section_category_summary(result.violations)

    print()
    print("=== 총계 ===")
    print("섹션 | CRITICAL | MAJOR | MINOR | 합계")
    overall: Counter[str] = Counter()
    for result in results:
        counts = violation_severity_counts(result.violations)
        overall.update(counts)
        total = sum(counts.values())
        print(
            f"{result.section_name} | {counts['CRITICAL']} | {counts['MAJOR']} | "
            f"{counts['MINOR']} | {total}"
        )
    print(
        f"전체 | {overall['CRITICAL']} | {overall['MAJOR']} | "
        f"{overall['MINOR']} | {sum(overall.values())}"
    )


def main() -> int:
    args = parse_args()
    if args.version_info:
        print_version_info()
        return 0

    assert args.html is not None
    assert args.css is not None

    html_text = read_text(args.html)
    css_text = read_text(args.css)
    parser = parse_html_document(html_text)
    css_rules = parse_css_rules(css_text)
    text_candidates = collect_text_candidates(parser.root)

    if args.spec_dir:
        spec_paths = load_spec_paths(args.spec_dir)
        results: list[SectionValidationResult] = []
        for spec_path in spec_paths:
            spec = load_spec(spec_path)
            result = validate_spec_payload(
                spec=spec,
                spec_path=spec_path,
                spec_dir=Path(args.spec_dir),
                html_text=html_text,
                parser=parser,
                css_rules=css_rules,
                text_candidates=text_candidates,
            )
            if result.schema_branch == "v1":
                print(f"[WARN] {result.section_name}: schema_version=1 (legacy)", file=sys.stderr)
            results.append(result)
        print_spec_dir_report(results)
        return 1 if any(result.schema_branch != "v1" and (result.violations or result.missing_rows) for result in results) else 0

    assert args.spec is not None
    spec = load_spec(args.spec)
    result = validate_spec_payload(
        spec=spec,
        spec_path=args.spec,
        spec_dir=Path(args.spec).parent,
        html_text=html_text,
        parser=parser,
        css_rules=css_rules,
        text_candidates=text_candidates,
    )
    if result.schema_branch == "v1":
        print("[WARN] schema_version=1 (legacy)", file=sys.stderr)
    print_report(result.violations, result.missing_rows)
    if result.schema_branch == "v1":
        return 0
    return 1 if result.violations or result.missing_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())

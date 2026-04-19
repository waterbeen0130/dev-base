from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"
EXTRACTED_DIR = ROOT / "extracted"
TARGET_SPECS = ("section_03_spec.json", "section_04_spec.json")

REQ031_TEXT_KEYS = {
    "characterStyleOverrides",
    "styleOverrideTable",
    "textCase",
    "textDecoration",
    "paragraphSpacing",
    "paragraphIndent",
}
REQ031_FRAME_KEYS = {
    "strokes",
    "strokeWeight",
    "strokeAlign",
    "rectangleCornerRadii",
    "layoutSizingHorizontal",
    "layoutSizingVertical",
    "layoutGrow",
    "layoutAlign",
}

# Some checked-in fixtures may not carry all earlier REQ-030 defaults yet.
LEGACY_V2_TEXT_COMPAT_KEYS = {"effects", "opacity", "blendMode"}
LEGACY_V2_FRAME_COMPAT_KEYS = {"fills_v2", "effects", "opacity", "blendMode"}
REQ032_FRAME_COMPAT_KEYS = {"componentId", "componentSetId"}
NORMALIZATION_ALLOWED_KEYS = (
    REQ031_TEXT_KEYS
    | REQ031_FRAME_KEYS
    | LEGACY_V2_TEXT_COMPAT_KEYS
    | LEGACY_V2_FRAME_COMPAT_KEYS
    | REQ032_FRAME_COMPAT_KEYS
)


def _load_module():
    module_name = "figma_section_spec_req031_add_only"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _assert_existing_keys_preserved(before: object, after: object, *, path: str = "") -> None:
    if isinstance(before, dict):
        assert isinstance(after, dict), f"type mismatch at {path or '<root>'}"
        for key, value in before.items():
            assert key in after, f"missing key at {path or '<root>'}: {key}"
            if key in NORMALIZATION_ALLOWED_KEYS:
                continue
            next_path = f"{path}.{key}" if path else key
            _assert_existing_keys_preserved(value, after[key], path=next_path)
        return
    if isinstance(before, list):
        assert isinstance(after, list), f"type mismatch at {path or '<root>'}"
        assert len(before) == len(after), f"length mismatch at {path or '<root>'}"
        for idx, (before_item, after_item) in enumerate(zip(before, after)):
            next_path = f"{path}[{idx}]" if path else f"[{idx}]"
            _assert_existing_keys_preserved(before_item, after_item, path=next_path)
        return
    assert before == after, f"value mismatch at {path or '<root>'}: {before!r} != {after!r}"


def _collect_added_node_keys(before_nodes: list[dict], after_nodes: list[dict]) -> set[str]:
    added: set[str] = set()
    for before, after in zip(before_nodes, after_nodes):
        if not isinstance(before, dict) or not isinstance(after, dict):
            continue
        added.update(set(after.keys()) - set(before.keys()))
    return added


def test_req031_add_only_preserves_existing_values_and_adds_only_req031_axes() -> None:
    module = _load_module()

    for name in TARGET_SPECS:
        before = json.loads((EXTRACTED_DIR / name).read_text(encoding="utf-8"))
        transformed = module.ensure_v2_payload_shape(copy.deepcopy(before))

        assert transformed["schema_version"] == "2.0.0"
        _assert_existing_keys_preserved(before, transformed)

        before_text_nodes = before.get("text_nodes", [])
        after_text_nodes = transformed.get("text_nodes", [])
        before_frame_nodes = before.get("frame_nodes", [])
        after_frame_nodes = transformed.get("frame_nodes", [])

        assert len(before_text_nodes) == len(after_text_nodes)
        assert len(before_frame_nodes) == len(after_frame_nodes)

        added_text_keys = _collect_added_node_keys(before_text_nodes, after_text_nodes)
        added_frame_keys = _collect_added_node_keys(before_frame_nodes, after_frame_nodes)

        allowed_text_keys = REQ031_TEXT_KEYS | LEGACY_V2_TEXT_COMPAT_KEYS
        allowed_frame_keys = REQ031_FRAME_KEYS | LEGACY_V2_FRAME_COMPAT_KEYS | REQ032_FRAME_COMPAT_KEYS

        assert added_text_keys <= allowed_text_keys
        assert added_frame_keys <= allowed_frame_keys

        for text_node in after_text_nodes:
            assert REQ031_TEXT_KEYS <= set(text_node.keys())

        for frame_node in after_frame_nodes:
            assert REQ031_FRAME_KEYS <= set(frame_node.keys())

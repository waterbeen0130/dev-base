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

REQ030_TEXT_KEYS = {"effects", "opacity", "blendMode"}
REQ030_FRAME_KEYS = {"fills_v2", "effects", "opacity", "blendMode"}
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
REQ032_FRAME_KEYS = {"componentId", "componentSetId"}
REQ032_VECTOR_KEYS = {"viewBox", "fillGeometryPathData", "strokeGeometryPathData"}

NORMALIZATION_ALLOWED_KEYS = (
    REQ030_TEXT_KEYS
    | REQ030_FRAME_KEYS
    | REQ031_TEXT_KEYS
    | REQ031_FRAME_KEYS
    | REQ032_FRAME_KEYS
    | REQ032_VECTOR_KEYS
)


def _load_module():
    module_name = "figma_section_spec_req032_add_only"
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


def test_req032_add_only_preserves_existing_v2_keys_and_adds_only_req032_axes() -> None:
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
        before_vector_nodes = before.get("vector_nodes", [])
        after_vector_nodes = transformed.get("vector_nodes", [])

        assert len(before_text_nodes) == len(after_text_nodes)
        assert len(before_frame_nodes) == len(after_frame_nodes)
        assert len(before_vector_nodes) == len(after_vector_nodes)

        added_text_keys = _collect_added_node_keys(before_text_nodes, after_text_nodes)
        added_frame_keys = _collect_added_node_keys(before_frame_nodes, after_frame_nodes)
        added_vector_keys = _collect_added_node_keys(before_vector_nodes, after_vector_nodes)

        assert added_text_keys <= REQ030_TEXT_KEYS | {"styleOverrideTable"}
        assert added_frame_keys <= REQ030_FRAME_KEYS | REQ031_FRAME_KEYS | REQ032_FRAME_KEYS
        assert added_vector_keys <= REQ032_VECTOR_KEYS

        for frame_node in after_frame_nodes:
            assert REQ032_FRAME_KEYS <= set(frame_node.keys())

        for vector_node in after_vector_nodes:
            assert REQ032_VECTOR_KEYS <= set(vector_node.keys())

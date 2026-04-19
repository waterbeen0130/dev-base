from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "extracted" / "section_03_spec.json"
BACKUP_SPEC_PATH = ROOT / "extracted.v1.backup" / "section_03_spec.json"
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"

REQUIRED_FRAME_KEYS = {
    "fills_v2",
    "effects",
    "opacity",
    "blendMode",
    "strokes",
    "rectangleCornerRadii",
    "layoutSizingHorizontal",
    "layoutSizingVertical",
    "layoutGrow",
    "layoutAlign",
    "componentId",
    "componentSetId",
}
REQUIRED_VECTOR_KEYS = {"viewBox", "fillGeometryPathData"}


def _load_figma_section_spec_module():
    spec = importlib.util.spec_from_file_location("figma_section_spec_phase_a_progress", FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_phase_a_schema_version_and_keys_are_available() -> None:
    payload = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == "2.0.0"

    module = _load_figma_section_spec_module()
    normalized = module.ensure_v2_payload_shape(copy.deepcopy(payload))

    frame_nodes = normalized.get("frame_nodes")
    assert isinstance(frame_nodes, list) and frame_nodes, "frame_nodes must be a non-empty list"
    for frame_node in frame_nodes:
        assert REQUIRED_FRAME_KEYS <= set(frame_node.keys())

    vector_nodes = normalized.get("vector_nodes")
    if isinstance(vector_nodes, list) and vector_nodes:
        for vector_node in vector_nodes:
            assert REQUIRED_VECTOR_KEYS <= set(vector_node.keys())
    else:
        # section_03 fixture currently has no vector nodes; ensure the v2 schema contract still exposes these keys.
        assert REQUIRED_VECTOR_KEYS <= set(module.V2_VECTOR_NODE_NULL_KEYS)


def test_phase_a_backup_schema_version_is_preserved() -> None:
    backup_payload = json.loads(BACKUP_SPEC_PATH.read_text(encoding="utf-8"))
    assert backup_payload.get("schema_version") == 1

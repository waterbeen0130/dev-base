from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC_PATH = ROOT / "tools" / "figma-section-spec.py"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "figma_node_sample.json"


def _load_figma_section_spec_module():
    module_name = "figma_section_spec"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _normalized_payload_bytes(module, figma_root_node: dict) -> bytes:
    extracted = module.walk_and_extract(figma_root_node)
    payload = {
        "schema_version": module.SCHEMA_VERSION_V2,
        "section": extracted.section,
        "text_nodes": extracted.text_nodes,
        "frame_nodes": extracted.frame_nodes,
        "vector_nodes": extracted.vector_nodes,
        "interactions": extracted.interactions,
        "images": {},
    }
    payload = module.ensure_v2_payload_shape(payload)
    payload = module.preprocess_payload(payload)
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def test_normalization_is_byte_exact_deterministic_across_100_runs() -> None:
    module = _load_figma_section_spec_module()
    fixture_node = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    digests: set[str] = set()
    snapshots: list[bytes] = []

    for _ in range(100):
        payload_bytes = _normalized_payload_bytes(module, copy.deepcopy(fixture_node))
        snapshots.append(payload_bytes)
        digests.add(hashlib.md5(payload_bytes).hexdigest())  # noqa: S324 - deterministic fingerprint only

    assert len(digests) == 1
    assert all(snapshot == snapshots[0] for snapshot in snapshots)

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req032_manifest_determinism"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _manifest_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def test_asset_manifest_is_byte_exact_deterministic_for_same_input() -> None:
    module = _load_module()
    payload = {
        "frame_nodes": [
            {
                "id": "f-2",
                "fills_v2": [
                    {"type": "IMAGE", "imageRef": "img-z"},
                    {"type": "IMAGE", "imageRef": "img-a"},
                ],
            },
            {
                "id": "f-1",
                "fills_v2": [
                    {"type": "IMAGE", "imageRef": "img-a"},
                ],
            },
        ],
        "vector_nodes": [
            {
                "id": "v-2",
                "fillGeometryPathData": ["M3 3L4 4Z"],
                "strokeGeometryPathData": [],
            },
            {
                "id": "v-1",
                "fillGeometryPathData": ["M0 0L1 1Z"],
                "strokeGeometryPathData": ["M1 1L2 2Z"],
            },
        ],
    }

    manifest_1 = module.build_asset_manifest(payload)
    manifest_2 = module.build_asset_manifest(payload)

    bytes_1 = _manifest_bytes(manifest_1)
    bytes_2 = _manifest_bytes(manifest_2)

    assert manifest_1 == manifest_2
    assert bytes_1 == bytes_2

    digest_1 = hashlib.sha256(bytes_1).hexdigest()
    digest_2 = hashlib.sha256(bytes_2).hexdigest()
    assert digest_1 == digest_2

    assert manifest_1["assets"] == sorted(
        manifest_1["assets"],
        key=lambda item: (item["kind"], item["ref"], item["spec_node_id"], item["hash"]),
    )

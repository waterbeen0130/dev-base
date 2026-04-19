from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req032_asset_manifest"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_asset_manifest_collects_image_and_vector_assets_deterministically() -> None:
    module = _load_module()
    payload = {
        "frame_nodes": [
            {
                "id": "1:2",
                "fills_v2": [{"type": "IMAGE", "imageRef": "img_same"}, {"type": "IMAGE", "imageRef": "img_same"}],
            },
            {"id": "1:3", "fills_v2": [{"type": "IMAGE", "imageRef": "img_other"}]},
        ],
        "vector_nodes": [
            {
                "id": "1:10",
                "fillGeometryPathData": ["M0 0L10 10Z"],
                "strokeGeometryPathData": ["M2 2L3 3Z"],
            }
        ],
    }

    manifest_1 = module.build_asset_manifest(payload)
    manifest_2 = module.build_asset_manifest(payload)

    assert manifest_1 == manifest_2

    assets = manifest_1["assets"]
    image_assets = [item for item in assets if item["kind"] == "image"]
    vector_assets = [item for item in assets if item["kind"] == "vector"]

    assert len(image_assets) == 2
    assert {item["ref"] for item in image_assets} == {"img_same", "img_other"}
    assert {item["hash"] for item in image_assets} == {"img_same", "img_other"}

    assert len(vector_assets) == 1
    expected_vector_hash = hashlib.sha256("M0 0L10 10Z\nM2 2L3 3Z".encode("utf-8")).hexdigest()
    assert vector_assets[0]["ref"] == "1:10"
    assert vector_assets[0]["spec_node_id"] == "1:10"
    assert vector_assets[0]["hash"] == expected_vector_hash

    serialized = json.dumps(manifest_1, ensure_ascii=False, sort_keys=True, indent=2)
    assert serialized == json.dumps(manifest_2, ensure_ascii=False, sort_keys=True, indent=2)


def test_emit_asset_manifest_is_enabled_by_default_and_can_be_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    source_spec = tmp_path / "source_spec.json"
    source_payload = {
        "schema_version": "2.0.0",
        "section": {"id": "1:1", "name": "S", "bbox": {"x": 0, "y": 0, "w": 100, "h": 100}},
        "text_nodes": [],
        "frame_nodes": [{"id": "1:2", "fills_v2": [{"type": "IMAGE", "imageRef": "img_hash"}]}],
        "vector_nodes": [{"id": "1:3", "fillGeometryPathData": ["M0 0L1 1Z"], "strokeGeometryPathData": []}],
        "interactions": [],
        "images": {},
    }
    source_spec.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    output_default = tmp_path / "out-default"
    monkeypatch.setattr(
        sys,
        "argv",
        ["figma-section-spec.py", "--from-spec", str(source_spec), "--output", str(output_default), "--name", "section_03"],
    )
    assert module.main() == 0
    assert (output_default / "section_03_asset_manifest.json").exists()

    output_disabled = tmp_path / "out-disabled"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "figma-section-spec.py",
            "--from-spec",
            str(source_spec),
            "--output",
            str(output_disabled),
            "--name",
            "section_03",
            "--no-emit-asset-manifest",
        ],
    )
    assert module.main() == 0
    assert not (output_disabled / "section_03_asset_manifest.json").exists()

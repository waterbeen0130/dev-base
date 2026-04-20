from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"
EXTRACTED_DIR = ROOT / "extracted"
TARGET_SPECS = ("section_03_spec.json", "section_04_spec.json")


def _load_module():
    module_name = "figma_section_spec_req037_add_only"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _baseline_payload(module, raw_payload: dict) -> dict:
    payload = copy.deepcopy(raw_payload)
    payload["schema_version"] = module.SCHEMA_VERSION_V2
    if not isinstance(payload.get("vector_nodes"), list):
        payload["vector_nodes"] = []
    if not isinstance(payload.get("interactions"), list):
        payload["interactions"] = []
    images = payload.get("images")
    payload["images"] = {key: images[key] for key in sorted(images.keys())} if isinstance(images, dict) else {}
    payload = module.ensure_v2_payload_shape(payload)
    payload = module.preprocess_payload(payload)
    return payload


def _json_bytes(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def test_req037_from_spec_generation_adds_only_component_groups(tmp_path: Path) -> None:
    module = _load_module()

    for spec_name in TARGET_SPECS:
        source_path = EXTRACTED_DIR / spec_name
        raw_payload = json.loads(source_path.read_text(encoding="utf-8"))
        expected_payload = _baseline_payload(module, raw_payload)

        result = subprocess.run(
            [
                sys.executable,
                str(FIGMA_SECTION_SPEC),
                "--from-spec",
                str(source_path),
                "--output",
                str(tmp_path),
                "--name",
                source_path.stem.removesuffix("_spec"),
                "--no-emit-asset-manifest",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

        generated_path = tmp_path / spec_name
        generated_payload = json.loads(generated_path.read_text(encoding="utf-8"))
        assert list(generated_payload.keys())[-1] == "component_groups"
        assert generated_payload["component_groups"] == []

        generated_without_component_groups = copy.deepcopy(generated_payload)
        generated_without_component_groups.pop("component_groups")
        assert _json_bytes(generated_without_component_groups) == _json_bytes(expected_payload)

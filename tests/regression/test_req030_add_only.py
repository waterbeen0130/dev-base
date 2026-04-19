from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"
BACKUP_DIR = ROOT / "extracted.v1.backup"
TARGET_SPECS = ("section_03_spec.json", "section_04_spec.json")


def _load_module():
    module_name = "figma_section_spec_req030_add_only"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _assert_existing_keys_preserved(before: object, after: object, *, path: str = "") -> None:
    if isinstance(before, dict):
        assert isinstance(after, dict)
        for key, value in before.items():
            if key == "schema_version":
                continue
            assert key in after
            next_path = f"{path}.{key}" if path else key
            _assert_existing_keys_preserved(value, after[key], path=next_path)
        return
    if isinstance(before, list):
        assert isinstance(after, list)
        assert len(before) == len(after)
        for before_item, after_item in zip(before, after):
            _assert_existing_keys_preserved(before_item, after_item, path=path)
        return
    assert before == after


def test_req030_add_only_preserves_v1_fields_while_adding_v2_keys() -> None:
    module = _load_module()

    for name in TARGET_SPECS:
        before = json.loads((BACKUP_DIR / name).read_text(encoding="utf-8"))
        transformed = module.ensure_v2_payload_shape(copy.deepcopy(before))

        assert transformed["schema_version"] == "2.0.0"
        _assert_existing_keys_preserved(before, transformed)

        first_frame = transformed["frame_nodes"][0]
        assert "fills_v2" in first_frame
        assert "effects" in first_frame
        assert "blendMode" in first_frame

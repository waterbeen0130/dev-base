from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def _load_figma_validate_module():
    spec = importlib.util.spec_from_file_location("figma_validate_asset_fidelity", FIGMA_VALIDATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_manifest(spec_dir: Path, section_name: str, refs: list[str]) -> None:
    payload = {"assets": [{"image_ref": ref} for ref in refs]}
    (spec_dir / f"{section_name}_asset_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_missing_image_detected(tmp_path: Path) -> None:
    module = _load_figma_validate_module()
    _write_manifest(tmp_path, "hero", ["hero_img_1", "hero_img_2", "hero_img_3", "hero_img_4", "hero_img_5"])
    spec = {"section": {"name": "hero"}}
    html = """
    <img src="./assets/hero_img_1.png">
    <img src="./assets/hero_img_2.png">
    <img src="./assets/hero_img_3.png">
    <img src="./assets/hero_img_4.png">
    """

    violations = module.validate_asset_manifest_consistency(spec, html, tmp_path)

    assert len(violations) == 1
    assert violations[0].category == "asset_manifest 일치"
    assert violations[0].node == "hero_img_5"
    assert violations[0].actual == "HTML에 미발견"


def test_phantom_image_detected(tmp_path: Path) -> None:
    module = _load_figma_validate_module()
    _write_manifest(tmp_path, "hero", ["hero_img_1"])
    spec = {"section": {"name": "hero"}}
    html = """
    <img src="./assets/hero_img_1.png">
    <img src="./assets/ai_composite.png">
    """

    violations = module.validate_asset_manifest_consistency(spec, html, tmp_path)

    assert len(violations) == 1
    assert violations[0].category == "asset_manifest 일치"
    assert violations[0].node == "ai_composite"
    assert violations[0].actual == "통이미지 의심 (manifest 미등록)"

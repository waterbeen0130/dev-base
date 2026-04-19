#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

python3 - <<'PY'
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

root = Path.cwd()
module_path = root / "tools" / "figma-validate.py"
spec = importlib.util.spec_from_file_location("figma_validate_v2_router_test", module_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

required_categories = set(module.V2_DETAIL_CATEGORIES)
assert required_categories, "V2 detail categories are empty"
assert hasattr(module, "run_v2_categories"), "run_v2_categories() is required"

text_cats = {
    "v2.opacity.match",
    "v2.blendMode.match",
    "v2.textCase.match",
    "v2.textDecoration.match",
    "v2.effects.shadow.match",
    "v2.effects.blur.match",
}
frame_cats = {
    "v2.fills.solid.match",
    "v2.fills.gradient.match",
    "v2.fills.image.match",
    "v2.strokes.match",
    "v2.cornerRadii.match",
    "v2.layoutSizing.match",
    "v2.componentId.match",
}
asset_cat = {"v2.assetManifest.exists"}

call_order: list[str] = []


def _violation(category: str) -> object:
    return module.Violation(category=category, node="node", expected="expected", actual="actual")


def fake_text_nodes(text_nodes, text_candidates, css_rules, schema_branch="v1"):
    call_order.append("text")
    assert schema_branch == "v2"
    return [_violation(category) for category in sorted(text_cats)], []


def fake_frame_nodes(frame_nodes, css_rules, schema_branch="v1"):
    call_order.append("frame")
    assert schema_branch == "v2"
    return [_violation(category) for category in sorted(frame_cats)]


def fake_interactions(interactions, root):
    call_order.append("interactions")
    return []


def fake_asset_manifest(spec_payload, spec_path):
    call_order.append("asset")
    return [_violation("v2.assetManifest.exists")]


module.validate_text_nodes = fake_text_nodes
module.validate_frame_nodes = fake_frame_nodes
module.validate_interactions = fake_interactions
module.validate_asset_manifest = fake_asset_manifest

dom_root = module.DOMElement("document", {}, None, 0)
violations, missing_rows = module.run_v2_categories(
    spec={"schema_version": "2.0.0"},
    spec_path="dummy_spec.json",
    text_nodes=[],
    frame_nodes=[],
    interactions=[],
    text_candidates=[],
    css_rules=[],
    root=dom_root,
)

assert missing_rows == []
assert call_order == ["text", "frame", "interactions", "asset"], call_order
seen_categories = {violation.category for violation in violations}
assert required_categories.issubset(seen_categories), f"missing routed categories: {sorted(required_categories - seen_categories)}"
print("[PASS] run_v2_categories routes all 14 v2 categories via single entrypoint")
PY

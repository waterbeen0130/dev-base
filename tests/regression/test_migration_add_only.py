from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTRACTED_DIR = ROOT / "extracted"
BACKUP_DIR = ROOT / "extracted.v1.backup"
TARGET_SPECS = ("section_03_spec.json", "section_04_spec.json")

V2_TEXT_NODE_KEYS = (
    "characterStyleOverrides",
    "textCase",
    "textDecoration",
    "paragraphSpacing",
    "paragraphIndent",
    "rules_conflict",
    "_extra",
)
V2_FRAME_NODE_KEYS = (
    "fills_v2",
    "effects",
    "strokes",
    "strokeWeight",
    "strokeAlign",
    "layoutSizingHorizontal",
    "layoutSizingVertical",
    "layoutGrow",
    "layoutAlign",
    "constraints",
    "rules_conflict",
    "_extra",
)
V2_VECTOR_NODE_KEYS = ("rules_conflict", "_extra")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _strip_v2_additions(payload: dict) -> dict:
    copy_payload = json.loads(json.dumps(payload, ensure_ascii=False))
    copy_payload.pop("schema_version", None)
    copy_payload.pop("_extra", None)

    section = copy_payload.get("section")
    if isinstance(section, dict):
        section.pop("_extra", None)

    for node in copy_payload.get("text_nodes", []):
        if isinstance(node, dict):
            for key in V2_TEXT_NODE_KEYS:
                node.pop(key, None)

    for node in copy_payload.get("frame_nodes", []):
        if isinstance(node, dict):
            for key in V2_FRAME_NODE_KEYS:
                node.pop(key, None)

    for node in copy_payload.get("vector_nodes", []):
        if isinstance(node, dict):
            for key in V2_VECTOR_NODE_KEYS:
                node.pop(key, None)

    return copy_payload


def _strip_v1_schema_version(payload: dict) -> dict:
    copy_payload = json.loads(json.dumps(payload, ensure_ascii=False))
    copy_payload.pop("schema_version", None)
    return copy_payload


def test_migration_add_only_hash_matches_backup_for_section_specs() -> None:
    for name in TARGET_SPECS:
        before_payload = _load_json(BACKUP_DIR / name)
        after_payload = _load_json(EXTRACTED_DIR / name)

        before_stripped = _strip_v1_schema_version(before_payload)
        after_stripped = _strip_v2_additions(after_payload)

        assert _canonical_sha256(before_stripped) == _canonical_sha256(after_stripped)


def test_regression_checklist_korean_text_preserved() -> None:
    before_payload = _load_json(BACKUP_DIR / "section_04_spec.json")
    after_payload = _load_json(EXTRACTED_DIR / "section_04_spec.json")

    before_text = before_payload["text_nodes"][0]["characters"]
    after_text = after_payload["text_nodes"][0]["characters"]

    assert before_text == after_text
    assert any("가" <= ch <= "힣" for ch in after_text)


def test_regression_checklist_frame_fill_preserved() -> None:
    before_payload = _load_json(BACKUP_DIR / "section_04_spec.json")
    after_payload = _load_json(EXTRACTED_DIR / "section_04_spec.json")

    assert before_payload["frame_nodes"][0]["fills"] == after_payload["frame_nodes"][0]["fills"]


def test_regression_checklist_padding_integers_preserved() -> None:
    before_payload = _load_json(BACKUP_DIR / "section_04_spec.json")
    after_payload = _load_json(EXTRACTED_DIR / "section_04_spec.json")

    for key in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft"):
        assert isinstance(after_payload["frame_nodes"][0][key], int)
        assert before_payload["frame_nodes"][0][key] == after_payload["frame_nodes"][0][key]

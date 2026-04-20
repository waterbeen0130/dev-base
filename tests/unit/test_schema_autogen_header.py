from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATION_SCHEMA = ROOT / "rules" / "validation_schema.json"


def test_validation_schema_has_auto_generated_comment() -> None:
    payload = json.loads(VALIDATION_SCHEMA.read_text(encoding="utf-8"))

    assert "AUTO-GENERATED FROM rules/models.py" in payload.get("$comment", "")

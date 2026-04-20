from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATION_SCHEMA = ROOT / "rules" / "validation_schema.json"


def _load_schema() -> dict:
    return json.loads(VALIDATION_SCHEMA.read_text(encoding="utf-8"))


def test_python_module_regenerates_validation_schema_with_same_rule_ids() -> None:
    before = _load_schema()

    result = subprocess.run(
        [sys.executable, "-m", "rules.models"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, "\n".join(part for part in (result.stdout, result.stderr) if part)

    after = _load_schema()
    ids_before = {rule["id"] for rule in before.get("rules", [])}
    ids_after = {rule["id"] for rule in after.get("rules", [])}

    assert ids_before == ids_after


def test_python_module_preserves_type_and_severity_enums() -> None:
    before = _load_schema()

    result = subprocess.run(
        [sys.executable, "-m", "rules.models"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, "\n".join(part for part in (result.stdout, result.stderr) if part)

    after = _load_schema()
    types_before = {rule["type"] for rule in before.get("rules", [])}
    types_after = {rule["type"] for rule in after.get("rules", [])}
    severities_before = {rule["severity"] for rule in before.get("rules", [])}
    severities_after = {rule["severity"] for rule in after.get("rules", [])}

    assert types_before == types_after
    assert severities_before == severities_after

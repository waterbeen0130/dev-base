from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATION_SCHEMA = ROOT / "rules" / "validation_schema.json"
REQ_035_TAG_PATTERNS = {
    "REQ-035": re.compile(r"\[REQ-035(?:/\d+)?\]"),
}


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_req035_phase_b_commits_are_present_in_git_log() -> None:
    result = _run(["git", "log", "--oneline", "--decorate", "--all"])
    combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    assert result.returncode == 0, combined

    log_lines = result.stdout.splitlines()
    for req_name, pattern in REQ_035_TAG_PATTERNS.items():
        assert any(pattern.search(line) for line in log_lines), f"missing commit subject tag: {req_name}"


def test_rules_models_module_regenerates_committed_validation_schema() -> None:
    original_schema = VALIDATION_SCHEMA.read_bytes()

    try:
        result = _run([sys.executable, "-m", "rules.models"])
        combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        assert result.returncode == 0, combined

        regenerated_schema = VALIDATION_SCHEMA.read_bytes()
        payload = json.loads(regenerated_schema.decode("utf-8"))
        assert payload.get("$comment") == "AUTO-GENERATED FROM rules/models.py \u2014 DO NOT EDIT"
        assert regenerated_schema == original_schema
    finally:
        if VALIDATION_SCHEMA.read_bytes() != original_schema:
            VALIDATION_SCHEMA.write_bytes(original_schema)


def test_all_rules_drift_check_converges_for_phase_b() -> None:
    result = _run([sys.executable, "tools/check-rules-drift.py", "--all"])
    combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()

    assert result.returncode == 0, combined
    assert "63/63 rules in sync" in combined

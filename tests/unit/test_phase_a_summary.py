from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQ_TAG_PATTERNS = {
    "REQ-029": re.compile(r"\[REQ-029(?:/\d+)?\]"),
    "REQ-030": re.compile(r"\[REQ-030(?:/\d+)?\]"),
    "REQ-031": re.compile(r"\[REQ-031(?:/\d+)?\]"),
    "REQ-032": re.compile(r"\[REQ-032(?:/\d+)?\]"),
    "REQ-033": re.compile(r"\[REQ-033(?:/\d+)?\]"),
    "REQ-034": re.compile(r"\[REQ-034(?:/\d+)?\]"),
}


def test_phase_a_req_commits_are_present_in_git_log() -> None:
    result = subprocess.run(
        ["git", "log", "--oneline", "--decorate", "--all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    assert result.returncode == 0, combined

    log_lines = result.stdout.splitlines()
    for req_name, pattern in REQ_TAG_PATTERNS.items():
        assert any(pattern.search(line) for line in log_lines), f"missing commit subject tag: {req_name}"

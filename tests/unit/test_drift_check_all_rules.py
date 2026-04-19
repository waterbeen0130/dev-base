from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DRIFT_CHECKER = ROOT / "tools" / "check-rules-drift.py"


def test_check_rules_drift_all_rules_mode() -> None:
    result = subprocess.run(
        [sys.executable, str(DRIFT_CHECKER), "--all-rules"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    assert result.returncode == 0, combined
    assert re.search(r"\[OK\]\s+\d+/\d+\s+rules in sync", combined), combined

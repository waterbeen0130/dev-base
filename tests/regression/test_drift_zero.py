from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DRIFT_CHECKER = ROOT / "tools" / "check-rules-drift.py"


def test_check_rules_drift_all_reports_65_rules_in_sync() -> None:
    result = subprocess.run(
        [sys.executable, str(DRIFT_CHECKER), "--all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    assert result.returncode == 0, combined
    assert "65/65 rules in sync" in combined

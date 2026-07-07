from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def test_figma_validate_version_info_preserves_category_counts() -> None:
    result = subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--version-info"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    assert result.returncode == 0, combined
    assert "category counts: v1=12, v2=14, total=26" in combined

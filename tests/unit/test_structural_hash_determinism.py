from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRUCTURAL_DIFF = ROOT / "tools" / "structural-diff.py"


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("PYTEST_"):
            env.pop(key)
    return env


def test_structural_hash_is_deterministic_for_same_html() -> None:
    hashes: set[str] = set()

    for _ in range(10):
        result = subprocess.run(
            [
                sys.executable,
                str(STRUCTURAL_DIFF),
                "--html",
                str(ROOT / "landing" / "index.html"),
                "--css",
                str(ROOT / "landing" / "css" / "common.css"),
                "--dump-hash",
            ],
            cwd=ROOT,
            env=_clean_env(),
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        hashes.add(result.stdout.strip())

    assert len(hashes) == 1
    assert len(next(iter(hashes))) == 64

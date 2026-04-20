from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRUCTURAL_DIFF = ROOT / "tools" / "structural-diff.py"


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("PYTEST_"):
            env.pop(key)
    return env


def test_structural_drift_reports_tag_mismatch(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    html_path = tmp_path / "index.html"

    spec_path.write_text(
        json.dumps({"frame_nodes": [{"children": [{"children": []}]}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    html_path.write_text("<!doctype html><html><body><div><section></section></div></body></html>", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(STRUCTURAL_DIFF),
            "--spec",
            str(spec_path),
            "--html",
            str(html_path),
        ],
        cwd=ROOT,
        env=_clean_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "STRUCTURE_DRIFT" in result.stdout
    assert "tag expected 'div', actual 'section'" in result.stdout

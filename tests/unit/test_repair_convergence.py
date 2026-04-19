from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPAIR_SCRIPT = ROOT / "tools" / "repair-from-violations.py"


def test_repair_stops_early_when_violation_count_no_longer_changes(tmp_path: Path) -> None:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    violations_path = tmp_path / "violations.json"

    html_path.write_text("<html><body><h1>Title</h1></body></html>\n", encoding="utf-8")
    css_path.write_text("h1{color:#111;}\n", encoding="utf-8")
    violations_path.write_text(
        json.dumps(
            {
                "violations": [
                    {
                        "rule_id": "semantic.text_exists",
                        "file": "landing/index.html",
                        "line": 1,
                        "expected": "node exists",
                        "actual": "node missing",
                        "fix_strategy": "manual",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(REPAIR_SCRIPT),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--violations",
            str(violations_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    combined = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    assert proc.returncode == 1, combined
    assert "[repair] convergence-stop" in combined

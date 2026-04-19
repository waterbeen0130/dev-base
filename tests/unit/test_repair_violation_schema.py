from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
REPAIR_SCRIPT = ROOT / "tools" / "repair-from-violations.py"


@pytest.mark.parametrize(
    ("violation_payload", "missing_key"),
    [
        ({"file": "landing/css/common.css", "line": 10}, "rule_id"),
        ({"rule_id": "no_inline_style", "line": 10}, "file"),
    ],
)
def test_repair_rejects_violations_missing_required_fields(
    tmp_path: Path,
    violation_payload: dict[str, object],
    missing_key: str,
) -> None:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    violations_path = tmp_path / "violations.json"

    html_path.write_text("<html><body><h1>Title</h1></body></html>\n", encoding="utf-8")
    css_path.write_text("h1{color:#111;}\n", encoding="utf-8")
    violations_path.write_text(json.dumps({"violations": [violation_payload]}, ensure_ascii=False), encoding="utf-8")

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
    assert proc.returncode != 0, combined
    assert f"missing required field: {missing_key}" in combined

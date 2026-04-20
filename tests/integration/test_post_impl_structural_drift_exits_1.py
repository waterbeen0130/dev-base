from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"


def test_post_impl_structural_drift_exits_1(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"

    spec_path.write_text(
        json.dumps(
            {
                "structural_tree": {
                    "tag": "body",
                    "classes": [],
                    "path": "0",
                    "children": [
                        {
                            "tag": "div",
                            "classes": [],
                            "path": "0/0",
                            "children": [
                                {
                                    "tag": "div",
                                    "classes": [],
                                    "path": "0/0/0",
                                    "children": [],
                                }
                            ],
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    html_path.write_text(
        "<!doctype html><html><body><div><section></section></div></body></html>",
        encoding="utf-8",
    )
    css_path.write_text("", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(POST_IMPL_VERIFY),
            "--spec",
            str(spec_path),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--profile",
            "basic",
            "--no-figma",
            "--no-repair",
            "--structural-diff",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "[STRUCTURAL] DRIFT" in result.stdout

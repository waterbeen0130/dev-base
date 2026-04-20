from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"


def test_post_impl_structural_diff_reports_structural_line(tmp_path: Path) -> None:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    shutil.copyfile(ROOT / "landing" / "index.html", html_path)
    shutil.copyfile(ROOT / "landing" / "css" / "common.css", css_path)

    result = subprocess.run(
        [
            sys.executable,
            str(POST_IMPL_VERIFY),
            "--spec",
            "extracted/section_03_spec.json",
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--profile",
            "landing",
            "--structural-diff",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode in {0, 1}
    assert "[STRUCTURAL]" in result.stdout

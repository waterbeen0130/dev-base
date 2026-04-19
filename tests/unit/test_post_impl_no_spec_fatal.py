from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"


def test_post_impl_requires_spec_when_figma_validation_is_enabled(tmp_path: Path) -> None:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    html_path.write_text("<html><body><p>ok</p></body></html>\n", encoding="utf-8")
    css_path.write_text("p{color:#111;}\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(POST_IMPL_VERIFY),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--no-repair",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    combined = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    assert proc.returncode == 1, combined
    assert "[FATAL] --spec is required" in combined

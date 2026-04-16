import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = ROOT / "tools" / "validate-semantic.py"


def test_validate_semantic_fix_flag_applies_repair(tmp_path):
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"

    html_path.write_text("<html><body><div class=\"card\">x</div></body></html>\n", encoding="utf-8")
    css_path.write_text(
        textwrap.dedent(
            """
            .card {
              border-radius: 999px;
              color: rgb(0, 0, 0);
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(VALIDATE_SCRIPT),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--profile",
            "basic",
            "--fix",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    combined = proc.stdout + "\n" + proc.stderr
    assert "[auto-fix]" in combined

    css_after = css_path.read_text(encoding="utf-8")
    assert "999px" not in css_after
    assert "rgb(" not in css_after.lower()

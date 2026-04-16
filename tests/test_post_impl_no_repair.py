import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"
FIXTURE_HTML = ROOT / "tests" / "fixtures" / "dirty.html"
FIXTURE_CSS = ROOT / "tests" / "fixtures" / "dirty.css"


def test_post_impl_no_repair_flag_keeps_legacy_behavior(tmp_path):
    spec_path = tmp_path / "spec.json"
    html_path = tmp_path / "dirty.html"
    css_path = tmp_path / "dirty.css"

    spec_path.write_text(
        json.dumps({"text_nodes": [], "frame_nodes": [], "interactions": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    shutil.copyfile(FIXTURE_HTML, html_path)
    shutil.copyfile(FIXTURE_CSS, css_path)

    proc = subprocess.run(
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
            "--no-repair",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    combined = proc.stdout + "\n" + proc.stderr
    assert "[auto-repair]" not in combined

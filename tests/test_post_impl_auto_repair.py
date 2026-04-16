import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"
FIXTURE_HTML = ROOT / "tests" / "fixtures" / "dirty.html"
FIXTURE_CSS = ROOT / "tests" / "fixtures" / "dirty.css"


def _write_spec(path: Path) -> None:
    path.write_text(
        json.dumps({"text_nodes": [], "frame_nodes": [], "interactions": []}, ensure_ascii=False),
        encoding="utf-8",
    )


def _run_verify(spec_path: Path, html_path: Path, css_path: Path, no_repair: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [
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
    ]
    if no_repair:
        cmd.append("--no-repair")
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def _semantic_blocking_score(output: str) -> int:
    matched = re.search(r"validate-semantic: .*\(critical=(\d+), major=(\d+), minor=(\d+),", output)
    assert matched, output
    return int(matched.group(1)) + int(matched.group(2))


def test_post_impl_auto_repair_reduces_semantic_counts(tmp_path):
    spec_path = tmp_path / "spec.json"
    _write_spec(spec_path)

    auto_html = tmp_path / "auto.html"
    auto_css = tmp_path / "auto.css"
    no_html = tmp_path / "no.html"
    no_css = tmp_path / "no.css"
    shutil.copyfile(FIXTURE_HTML, auto_html)
    shutil.copyfile(FIXTURE_CSS, auto_css)
    shutil.copyfile(FIXTURE_HTML, no_html)
    shutil.copyfile(FIXTURE_CSS, no_css)

    no_proc = _run_verify(spec_path, no_html, no_css, no_repair=True)
    auto_proc = _run_verify(spec_path, auto_html, auto_css, no_repair=False)

    combined_output = auto_proc.stdout + "\n" + auto_proc.stderr
    assert "[auto-repair]" in combined_output

    fixed_match = re.search(r"\[auto-repair\]\s+(\d+)\s+violations fixed", combined_output)
    assert fixed_match, combined_output
    assert int(fixed_match.group(1)) >= 1

    auto_score = _semantic_blocking_score(auto_proc.stdout)
    no_score = _semantic_blocking_score(no_proc.stdout)
    assert auto_score <= no_score

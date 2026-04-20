from __future__ import annotations

import importlib.util
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


def _load_structural_diff_module():
    spec = importlib.util.spec_from_file_location("structural_diff_match", STRUCTURAL_DIFF)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_structural_match_for_landing_self_comparison(tmp_path: Path) -> None:
    matching_html = tmp_path / "matching.html"
    matching_spec = tmp_path / "matching_spec.json"
    matching_html.write_text("<!doctype html><html><body><div><div></div></div></body></html>", encoding="utf-8")
    matching_spec.write_text(
        json.dumps({"frame_nodes": [{"children": [{"children": []}]}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    matching_result = subprocess.run(
        [
            sys.executable,
            str(STRUCTURAL_DIFF),
            "--spec",
            str(matching_spec),
            "--html",
            str(matching_html),
        ],
        cwd=ROOT,
        env=_clean_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert matching_result.returncode == 0, matching_result.stderr
    assert "STRUCTURAL MATCH" in matching_result.stdout

    module = _load_structural_diff_module()
    html_path = ROOT / "landing" / "index.html"
    css_path = ROOT / "landing" / "css" / "common.css"
    spec_path = tmp_path / "landing_structural_spec.json"
    spec_path.write_text(
        json.dumps({"structural_tree": module.render_dom_tree(html_path, css_path)}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(STRUCTURAL_DIFF),
            "--spec",
            str(spec_path),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
        ],
        cwd=ROOT,
        env=_clean_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "STRUCTURAL MATCH" in result.stdout

"""DOD-011: output boundary recognition.

Raw extraction leftovers (extracted/ dir, or HTML still full of Figma node-name
classes) must not be mistaken for the final deliverable. The checker flags such
artifacts so they are not validated/delivered as the published output.
"""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECK_PATH = ROOT / "tools" / "check-output-boundary.py"

spec = importlib.util.spec_from_file_location("check_output_boundary", CHECK_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_clean_deliverable_passes(tmp_path):
    (tmp_path / "index.html").write_text(
        "<html><body><div class='main_intro'></div></body></html>", encoding="utf-8"
    )
    assert mod.find_boundary_violations(tmp_path) == []


def test_extracted_dir_in_deliverable_is_flagged(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "extracted").mkdir()
    (tmp_path / "extracted" / "main_base.html").write_text("<div class='main_f0'></div>", encoding="utf-8")
    violations = mod.find_boundary_violations(tmp_path)
    assert any("extracted" in v["detail"] for v in violations)


def test_raw_node_name_dump_html_is_flagged(tmp_path):
    # An HTML file dominated by Figma node-name classes = raw extraction leftover.
    body = "".join(f"<div class='main_f{i}'></div>" for i in range(12))
    (tmp_path / "page.html").write_text(f"<html><body>{body}</body></html>", encoding="utf-8")
    violations = mod.find_boundary_violations(tmp_path)
    assert any("page.html" in v["file"] for v in violations)

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def _write_spec(spec_dir: Path, section_name: str, node_id: str, characters: str) -> None:
    payload = {
        "schema_version": "2.0.0",
        "section": {"id": node_id, "name": section_name, "bbox": {"x": 0, "y": 0, "w": 100, "h": 100}},
        "text_nodes": [
            {
                "id": node_id,
                "name": f"{section_name} text",
                "characters": characters,
                "lineHeightRatio": 1.2,
                "color": "#111111",
            }
        ],
        "frame_nodes": [],
        "vector_nodes": [],
        "interactions": [],
        "images": {},
    }
    (spec_dir / f"{section_name}_spec.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_spec_dir_runs_all_section_specs(tmp_path: Path) -> None:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    _write_spec(spec_dir, "hero", "hero-node", "Hero headline")
    _write_spec(spec_dir, "adventure", "adventure-node", "Adventure copy")

    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    html_path.write_text(
        """
        <html><body>
          <section><p class="hero_text">Changed hero</p></section>
          <section><p class="adventure_text">Changed adventure</p></section>
        </body></html>
        """,
        encoding="utf-8",
    )
    css_path.write_text(
        """
        .hero_text, .adventure_text {
          font-family: Arial;
          font-size: 16px;
          font-weight: 400;
          line-height: 1.2;
          color: #111111;
        }
        """,
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(FIGMA_VALIDATE),
            "--spec-dir",
            str(spec_dir),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = proc.stdout + proc.stderr
    assert proc.returncode == 1
    assert "=== [hero] ===" in output
    assert "=== [adventure] ===" in output
    assert "=== 총계 ===" in output
    assert "hero-node" in output
    assert "adventure-node" in output

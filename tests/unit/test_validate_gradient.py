from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def _run_validator(tmp_path: Path, spec_payload: dict, css_text: str) -> subprocess.CompletedProcess[str]:
    spec_path = tmp_path / "spec.json"
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    spec_path.write_text(json.dumps(spec_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text("<html><body><div class='card'></div></body></html>\n", encoding="utf-8")
    css_path.write_text(css_text.strip() + "\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--spec", str(spec_path), "--html", str(html_path), "--css", str(css_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_v2_gradient_fill_category_passes_when_css_gradient_contains_stop_colors(tmp_path: Path) -> None:
    spec_payload = {
        "schema_version": "2.0.0",
        "section": {"id": "1:1", "name": "S", "bbox": {"x": 0, "y": 0, "w": 100, "h": 100}},
        "text_nodes": [],
        "frame_nodes": [
            {
                "id": "1:2",
                "name": "card",
                "bbox": {"x": 0, "y": 0, "w": 100, "h": 100},
                "layoutMode": "HORIZONTAL",
                "paddingTop": None,
                "paddingRight": None,
                "paddingBottom": None,
                "paddingLeft": None,
                "itemSpacing": None,
                "primaryAxisAlignItems": None,
                "counterAxisAlignItems": None,
                "fills": "#aabbcc",
                "fills_v2": [
                    {
                        "type": "GRADIENT_LINEAR",
                        "opacity": 1.0,
                        "gradientStops": [
                            {"position": 0.0, "color": "#aabbcc"},
                            {"position": 1.0, "color": "#ddeeff"},
                        ],
                        "gradientHandlePositions": [
                            {"x": 0.0, "y": 0.0},
                            {"x": 1.0, "y": 0.0},
                            {"x": 0.0, "y": 1.0},
                        ],
                    }
                ],
                "effects": [],
                "opacity": 1.0,
                "blendMode": "PASS_THROUGH",
            }
        ],
        "vector_nodes": [],
        "interactions": [],
        "images": {},
    }
    proc = _run_validator(
        tmp_path,
        spec_payload,
        """
        .card { display: flex; flex-direction: row; background: linear-gradient(180deg, #aabbcc, #ddeeff); }
        """,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr

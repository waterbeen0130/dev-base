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
    html_path.write_text("<html><body><div class='hero'></div></body></html>\n", encoding="utf-8")
    css_path.write_text(css_text.strip() + "\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--spec", str(spec_path), "--html", str(html_path), "--css", str(css_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_v2_image_fill_category_passes_when_css_has_background_image_url(tmp_path: Path) -> None:
    spec_payload = {
        "schema_version": "2.0.0",
        "section": {"id": "1:1", "name": "S", "bbox": {"x": 0, "y": 0, "w": 100, "h": 100}},
        "text_nodes": [],
        "frame_nodes": [
            {
                "id": "1:2",
                "name": "hero",
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
                        "type": "IMAGE",
                        "imageRef": "image_hash",
                        "scaleMode": "FILL",
                        "imageTransform": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                        "opacity": 1.0,
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
        .hero {
          display: flex;
          flex-direction: row;
          background: #aabbcc;
          background-image: url('https://example.com/hero.png');
        }
        """,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr

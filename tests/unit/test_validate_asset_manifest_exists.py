from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def test_v2_asset_manifest_missing_fails_validation(tmp_path: Path) -> None:
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
                "fills_v2": [{"type": "IMAGE", "imageRef": "img_hash"}],
                "effects": [],
                "opacity": 1.0,
                "blendMode": "PASS_THROUGH",
            }
        ],
        "vector_nodes": [],
        "interactions": [],
        "images": {},
    }

    spec_path = tmp_path / "section_99_spec.json"
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    spec_path.write_text(json.dumps(spec_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text("<html><body><div class='hero'></div></body></html>\n", encoding="utf-8")
    css_path.write_text(
        ".hero{display:flex;flex-direction:row;background:#aabbcc;background-image:url('https://example.com/a.png');}\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--spec", str(spec_path), "--html", str(html_path), "--css", str(css_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    output = proc.stdout + proc.stderr
    assert proc.returncode == 1
    assert "v2.assetManifest.exists" in output

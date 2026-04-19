from __future__ import annotations

import json
import subprocess
import sys
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def _run_validator(tmp_path: Path, spec_payload: dict, css_text: str) -> subprocess.CompletedProcess[str]:
    spec_path = tmp_path / "spec.json"
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    manifest_path = tmp_path / "spec_asset_manifest.json"
    spec_path.write_text(json.dumps(spec_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text("<html><body><div class='hero'></div></body></html>\n", encoding="utf-8")
    css_path.write_text(css_text.strip() + "\n", encoding="utf-8")
    assets: list[dict[str, str]] = []
    image_seen: set[str] = set()
    for frame in spec_payload.get("frame_nodes", []):
        if not isinstance(frame, dict):
            continue
        node_id = frame.get("id") if isinstance(frame.get("id"), str) and frame.get("id") else "frame"
        fills = frame.get("fills_v2")
        if not isinstance(fills, list):
            continue
        for fill in fills:
            if not isinstance(fill, dict) or fill.get("type") != "IMAGE":
                continue
            image_ref = fill.get("imageRef")
            if not isinstance(image_ref, str) or not image_ref or image_ref in image_seen:
                continue
            image_seen.add(image_ref)
            assets.append({"ref": image_ref, "kind": "image", "hash": image_ref, "spec_node_id": node_id})
    for vector in spec_payload.get("vector_nodes", []):
        if not isinstance(vector, dict):
            continue
        node_id = vector.get("id") if isinstance(vector.get("id"), str) and vector.get("id") else "vector"
        paths: list[str] = []
        for path in vector.get("fillGeometryPathData", []):
            if isinstance(path, str):
                paths.append(path)
        for path in vector.get("strokeGeometryPathData", []):
            if isinstance(path, str):
                paths.append(path)
        assets.append(
            {
                "ref": node_id,
                "kind": "vector",
                "hash": hashlib.sha256("\n".join(paths).encode("utf-8")).hexdigest(),
                "spec_node_id": node_id,
            }
        )
    manifest_path.write_text(json.dumps({"assets": assets}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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

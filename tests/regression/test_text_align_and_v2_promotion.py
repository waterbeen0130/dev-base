"""Regression: text-align verification + selective promotion of v2 frame checks.

Covers the gaps found when border-radius / text-align / color were not gated:
  - text-align 일치: new check, inheritance-aware, LEFT (default) ignored.
  - v2.cornerRadii.match / v2.fills.solid.match: promoted to gating in pm-verify,
    but demoted to noise on unmatched ("미매칭") frames.

All values are measured against a correctly-paired schema_v2 spec so a clean
output produces zero false-positives and a wrong output is caught.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"
PM_VERIFY = ROOT / "tools" / "pm-verify.py"

# import pm-verify as a module (hyphenated filename)
_spec = importlib.util.spec_from_file_location("pm_verify", PM_VERIFY)
pm_verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pm_verify)


def _spec_json() -> dict:
    return {
        "schema_version": "2.0.0",
        "text_nodes": [
            {
                "id": "1:10", "name": "title", "characters": "안녕하세요",
                "fontFamily": "Noto Sans KR", "fontSize": 32, "fontWeight": 700,
                "lineHeightPx": 48, "lineHeightRatio": 1.5, "letterSpacing": -0.025,
                "color": "#090944", "textAlignHorizontal": "CENTER", "textAlignVertical": "TOP",
            }
        ],
        "frame_nodes": [
            {
                "id": "1:1", "name": "box", "bbox": {"x": 0, "y": 0, "w": 1920, "h": 600},
                "layoutMode": "VERTICAL", "paddingTop": 80, "paddingRight": 40,
                "paddingBottom": 80, "paddingLeft": 40, "itemSpacing": 0,
                "primaryAxisAlignItems": "CENTER", "counterAxisAlignItems": "CENTER",
                "fills": "#f5f5f5", "fills_v2": [{"type": "SOLID", "color": "#f5f5f5", "opacity": 1.0}],
                "rectangleCornerRadii": [24, 24, 24, 24], "cornerRadius": 24,
            }
        ],
        "interactions": [],
    }


HTML = (
    "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
    "<link rel=\"stylesheet\" href=\"common.css\"></head>"
    "<body><section class=\"box\"><h2 class=\"title\">안녕하세요</h2></section></body></html>"
)

TITLE_FONT = (
    '.box .title { font-family: "Noto Sans KR"; font-size: 32px; font-weight: 700; '
    "line-height: 1.5; color: #090944; letter-spacing: -0.025em; }"
)


def _run_figma_validate(tmp_path: Path, css: str) -> str:
    (tmp_path / "section_spec.json").write_text(json.dumps(_spec_json(), ensure_ascii=False), encoding="utf-8")
    (tmp_path / "index.html").write_text(HTML, encoding="utf-8")
    (tmp_path / "common.css").write_text(css, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--spec-dir", str(tmp_path),
         "--html", str(tmp_path / "index.html"), "--css", str(tmp_path / "common.css")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    return result.stdout + result.stderr


# ---- text-align ----

def test_text_align_inherited_from_parent_passes(tmp_path):
    css = (".box { display: flex; flex-direction: column; padding: 80px 40px; "
           "background: #f5f5f5; border-radius: 24px; text-align: center; }\n" + TITLE_FONT)
    assert "text-align 일치" not in _run_figma_validate(tmp_path, css)


def test_text_align_missing_is_flagged(tmp_path):
    css = (".box { display: flex; flex-direction: column; padding: 80px 40px; "
           "background: #f5f5f5; border-radius: 24px; }\n" + TITLE_FONT)
    assert "text-align 일치" in _run_figma_validate(tmp_path, css)


def test_text_align_left_default_not_flagged(tmp_path):
    # spec LEFT must never produce a violation even when CSS omits text-align
    spec = _spec_json()
    spec["text_nodes"][0]["textAlignHorizontal"] = "LEFT"
    (tmp_path / "section_spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "index.html").write_text(HTML, encoding="utf-8")
    css = (".box { display: flex; flex-direction: column; padding: 80px 40px; "
           "background: #f5f5f5; border-radius: 24px; }\n" + TITLE_FONT)
    (tmp_path / "common.css").write_text(css, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--spec-dir", str(tmp_path),
         "--html", str(tmp_path / "index.html"), "--css", str(tmp_path / "common.css")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert "text-align 일치" not in (result.stdout + result.stderr)


# ---- border-radius (v2.cornerRadii.match) ----

def test_corner_radii_correct_passes(tmp_path):
    css = (".box { display: flex; flex-direction: column; padding: 80px 40px; "
           "background: #f5f5f5; border-radius: 24px; text-align: center; }\n" + TITLE_FONT)
    assert "v2.cornerRadii.match" not in _run_figma_validate(tmp_path, css)


def test_corner_radii_wrong_is_flagged(tmp_path):
    css = (".box { display: flex; flex-direction: column; padding: 80px 40px; "
           "background: #f5f5f5; border-radius: 8px; text-align: center; }\n" + TITLE_FONT)
    assert "v2.cornerRadii.match" in _run_figma_validate(tmp_path, css)


# ---- pm-verify selective promotion / 미매칭 demotion ----

def test_pm_verify_gates_corner_radii_and_fills():
    out = (
        "v2.cornerRadii.match | 1:1 (box) | [24, 24, 24, 24] | ['8px'] @ .box\n"
        "v2.fills.solid.match | 1:1 (box) | #f5f5f5 | #ffffff @ .box\n"
        "text-align 일치 | 1:10 (title) | center | - @ .box .title\n"
    )
    trusted, _ = pm_verify.parse_figma_validate(out)
    cats = " ".join(trusted)
    assert "v2.cornerRadii.match" in cats
    assert "v2.fills.solid.match" in cats
    assert "text-align 일치" in cats


def test_pm_verify_demotes_unmatched_frame():
    out = "v2.cornerRadii.match | 1:1 (box) | [24] | - @ 미매칭 (frame 1:1)\n"
    trusted, noisy = pm_verify.parse_figma_validate(out)
    assert not trusted, "unmatched-frame radius must not gate"
    assert any("unmatched-frame" in n for n in noisy)

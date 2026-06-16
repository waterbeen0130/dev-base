"""DOD-003: mixed-style text (character_segments) must not collapse to one style.

When spec text_node has has_mixed_styles=true with >1 distinct segment color,
each non-base segment color must appear in the HTML/CSS. Dropping it (rendering
the whole run as a single color) is a violation. has_mixed_styles=false → skip.
"""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECK_PATH = ROOT / "tools" / "check-mixed-styles.py"

spec = importlib.util.spec_from_file_location("check_mixed_styles", CHECK_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _spec(mixed=True):
    return {
        "text_nodes": [{
            "characters": "고객 여러분과 사회의 믿음에 보답하는 파트너",
            "color": "#212121",
            "has_mixed_styles": mixed,
            "character_segments": [
                {"text": "고객 여러분과 ", "color": "#212121"},
                {"text": "사회의 믿음에 보답하는 파트너", "color": "#438eca"},
            ],
        }]
    }


def test_dropped_segment_color_is_flagged():
    html = "<p>고객 여러분과 사회의 믿음에 보답하는 파트너</p>"  # single color, #438eca dropped
    violations = mod.find_mixed_style_violations(_spec(mixed=True), html, "")
    assert violations
    assert any("#438eca" in v["detail"] for v in violations)


def test_segment_color_present_passes():
    html = '<p>고객 여러분과 <span style="color:#438eca">사회의 믿음에 보답하는 파트너</span></p>'
    violations = mod.find_mixed_style_violations(_spec(mixed=True), html, "")
    assert violations == []


def test_segment_color_via_css_class_passes():
    html = '<p>고객 여러분과 <span class="point">사회의 믿음에 보답하는 파트너</span></p>'
    css = ".point{color:#438eca}"
    violations = mod.find_mixed_style_violations(_spec(mixed=True), html, css)
    assert violations == []


def test_not_mixed_is_skipped():
    html = "<p>고객 여러분과 사회의 믿음에 보답하는 파트너</p>"
    violations = mod.find_mixed_style_violations(_spec(mixed=False), html, "")
    assert violations == []

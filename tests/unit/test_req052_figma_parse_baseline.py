from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PM_VERIFY = ROOT / "tools" / "pm-verify.py"


def _load_pm_verify_module():
    spec = importlib.util.spec_from_file_location("pm_verify_req052", PM_VERIFY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parse_figma_validate_linebreak_enforced_without_br_or_block_boundary():
    pm_verify = _load_pm_verify_module()
    html = "<section><p>Alpha Beta</p></section>"
    output = "줄바꿈 보존 | 1:10 (copy) | 'Alpha\\nBeta' | 'Alpha Beta' @ .copy"

    trusted, noisy = pm_verify.parse_figma_validate(output, html)

    # T02 changes intent on purpose: linebreak-preservation violations must stay
    # trusted unless the HTML represents the same newline count with <br> or
    # equivalent block boundaries.
    assert trusted == [output]
    assert noisy == []


def test_parse_figma_validate_linebreak_passes_with_matching_br_count():
    pm_verify = _load_pm_verify_module()
    html = "<section><p>Alpha<br>Beta<br>Gamma</p></section>"
    output = "줄바꿈 보존 | 1:10 (copy) | 'Alpha\\nBeta\\nGamma' | 'Alpha Beta Gamma' @ .copy"

    trusted, noisy = pm_verify.parse_figma_validate(output, html)

    assert trusted == []
    assert noisy == [f"[linebreak-match] {output}"]


def test_parse_figma_validate_linebreak_passes_with_block_boundaries():
    pm_verify = _load_pm_verify_module()
    html = "<section><p>Alpha</p><p>Beta</p><p>Gamma</p></section>"
    output = "줄바꿈 보존 | 1:10 (copy) | 'Alpha\\nBeta\\nGamma' | 'Alpha Beta Gamma' @ .copy"

    trusted, noisy = pm_verify.parse_figma_validate(output, html)

    # Multiple block elements carrying the same text sequence count as one
    # preserved line break per boundary.
    assert trusted == []
    assert noisy == [f"[linebreak-match] {output}"]


def test_parse_figma_validate_linebreak_enforced_when_block_count_is_short():
    pm_verify = _load_pm_verify_module()
    html = "<section><p>Alpha</p><p>Beta Gamma</p></section>"
    output = "줄바꿈 보존 | 1:10 (copy) | 'Alpha\\nBeta\\nGamma' | 'Alpha Beta Gamma' @ .copy"

    trusted, noisy = pm_verify.parse_figma_validate(output, html)

    assert trusted == [output]
    assert noisy == []


def test_parse_figma_validate_linebreak_scopes_duplicate_text_to_reported_selector():
    pm_verify = _load_pm_verify_module()
    html = "<section><p class='copy'>Alpha Beta</p><p class='other'>Alpha<br>Beta</p></section>"
    output = "줄바꿈 보존 | 1:10 (copy) | 'Alpha\\nBeta' | 'Alpha Beta' @ .copy"

    trusted, noisy = pm_verify.parse_figma_validate(output, html)

    assert trusted == [output]
    assert noisy == []


def test_parse_figma_validate_linebreak_passes_with_nested_block_open_boundary():
    pm_verify = _load_pm_verify_module()
    html = "<section><div>Alpha<p>Beta</p></div></section>"
    output = "줄바꿈 보존 | 1:10 (copy) | 'Alpha\\nBeta' | 'Alpha Beta' @ div"

    trusted, noisy = pm_verify.parse_figma_validate(output, html)

    assert trusted == []
    assert noisy == [f"[linebreak-match] {output}"]


def test_parse_figma_validate_softmatch_scope_and_trusted_routing():
    pm_verify = _load_pm_verify_module()
    html = "<section><p>Hello World</p></section>"
    output = "\n".join(
        [
            "텍스트 byte-exact | 1:10 (copy) | 'Hello\\nWorld' | 'Hello World' @ .copy",
            "텍스트 byte-exact | 1:11 (copy) | 'Exact phrase' | 'Different phrase' @ .copy",
            "fills color hex 일치 | 1:2 (hero) | #111111 | #111111 @ .hero > span",
            "v2.opacity.match | 1:1 (box) | 1 | 0.8 @ .box",
        ]
    )

    trusted, noisy = pm_verify.parse_figma_validate(output, html)

    assert trusted == ["텍스트 byte-exact | 1:11 (copy) | 'Exact phrase' | 'Different phrase' @ .copy"]
    assert noisy == [
        "[span-inherit] fills color hex 일치 | 1:2 (hero) | #111111 | #111111 @ .hero > span",
        "v2.opacity.match | 1:1 (box) | 1 | 0.8 @ .box",
        "[soft-match] 텍스트 byte-exact | 1:10 (copy) | 'Hello\\nWorld' | 'Hello World' @ .copy",
    ]


def test_parse_figma_validate_linebreak_pass_handles_nbsp_and_unicode_separator():
    pm_verify = _load_pm_verify_module()
    html = "<section><p>Alpha&nbsp;<br>Beta\u2028<br>Gamma</p></section>"
    output = "줄바꿈 보존 | 1:10 (copy) | 'Alpha\\xa0\\nBeta\\u2028\\nGamma' | 'Alpha Beta Gamma' @ .copy"

    trusted, noisy = pm_verify.parse_figma_validate(output, html)

    assert trusted == []
    assert noisy == [f"[linebreak-match] {output}"]


def test_parse_figma_validate_figma_parse_baseline_corner_radii_match_and_unmatched_frame():
    pm_verify = _load_pm_verify_module()
    output = "\n".join(
        [
            "v2.cornerRadii.match | 1:1 (box) | [24] | ['8px'] @ .box",
            "v2.cornerRadii.match | 1:1 (box) | [24] | - @ 미매칭 (frame 1:1)",
        ]
    )

    trusted, noisy = pm_verify.parse_figma_validate(output)

    # Baseline lock for T03: matched radius violations gate, unmatched frames are
    # downgraded because the frame-to-selector pairing is heuristic today.
    assert trusted == ["v2.cornerRadii.match | 1:1 (box) | [24] | ['8px'] @ .box"]
    assert noisy == ["[unmatched-frame] v2.cornerRadii.match | 1:1 (box) | [24] | - @ 미매칭 (frame 1:1)"]

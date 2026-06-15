"""DOD-008: trust/noise reclassification lock.

After re-judging every suppressed (NOISY) category, the decision is: all current
suppressions are false-positive-driven and justified, and the genuine risks behind
them (broken images, excessive nesting) are already covered by NON-suppressed
checks (broken-link check, max_dom_depth). So nothing is restored.

This test LOCKS that re-judged decision: if the suppression sets drift, it fails,
forcing a conscious re-judgment + doc update instead of silent suppression creep.
See objective/details/trust-noise-reclassification.md (재판정 결과).
"""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PM_VERIFY = ROOT / "tools" / "pm-verify.py"

spec = importlib.util.spec_from_file_location("pm_verify", PM_VERIFY)
pm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)

# Re-judged JUSTIFIED suppressions (DOD-008). Changing suppression requires
# updating this set AND the rationale doc.
EXPECTED_NOISY_SEMANTIC = {
    "vertical_frame_margin_bottom",
    "inner_wrapper_limit",
    "line_height_tidy_ratio",
    "reset_duplicate",
}
EXPECTED_NOISY_FIGMA = {
    "frame padding/gap 반영",
    "clamp 적용",
    "column flex gap 금지",
    "[POLICY-1] VERTICAL frame itemSpacing must map to margin-bottom",
    "asset_manifest 일치",
    "v2.layoutSizing.match",
    "v2.opacity.match",
    "v2.cornerRadii.match",
    "v2.strokes.match",
    "v2.fills.solid.match",
    "v2.effects.match",
    "v2.textCase.match",
}


def test_noisy_semantic_matches_rejudged_decision():
    assert pm.NOISY_SEMANTIC_RULES == EXPECTED_NOISY_SEMANTIC


def test_noisy_figma_matches_rejudged_decision():
    assert pm.NOISY_FIGMA_CATEGORIES == EXPECTED_NOISY_FIGMA


def test_broken_link_risk_is_not_suppressed():
    # asset_manifest suppression is justified ONLY because broken links are checked
    # separately and reported (not suppressed). Guard that the check still exists.
    assert hasattr(pm, "check_broken_links")

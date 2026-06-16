"""Guards for the rule-catalog cleanup (audit quick-cleanup bundle).

- Every custom rule must resolve to a real handler (no silent stub-fail).
- _stub_handler must fail-closed at the rule's own severity (not downgrade).
- Coverage preserved after removing duplicate rules (no_forbidden_class still
  catches generic names; no_raw_calc now also covers vw).
"""
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic_cleanup", SCRIPT_PATH)
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


def _rules():
    return yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["rules"]


def test_every_custom_rule_has_a_real_handler():
    """No custom rule may silently route to _stub_handler (typo / missing handler)."""
    handlers = vs.CUSTOM_HANDLERS
    missing = []
    for r in _rules():
        v = r.get("validation", {})
        if v.get("type") != "custom":
            continue
        name = v.get("custom_handler") or r["id"]
        if name not in handlers:
            missing.append((r["id"], name))
    assert not missing, f"custom rules with no handler (would stub-fail): {missing}"


def test_stub_handler_fails_closed_as_critical():
    # even an info-declared rule with a missing handler fails-closed at error(CRITICAL)
    rule = {"id": "fake", "severity": "info", "validation": {"custom_handler": "nope"}}
    res = vs._stub_handler(rule, None)
    assert res.passed is False
    assert res.severity == "error"  # always CRITICAL, never downgraded


def test_removed_rules_are_gone():
    ids = {r["id"] for r in _rules()}
    for gone in ("font_size_base", "no_media_indent", "no_raw_vw",
                 "p_tag_misuse", "generic_class_name"):
        assert gone not in ids


def _results(tmp_path, *, html="", css=""):
    h = tmp_path / "index.html"; h.write_text(html or "<html><body></body></html>", encoding="utf-8")
    c = tmp_path / "common.css"; c.write_text(css or "body{margin:0}", encoding="utf-8")
    out = vs.run_validation(rules_path=str(RULES_PATH), html_path=str(h),
                            css_path=str(c), profile="landing")
    return {r.rule_id: r for r in out}


def test_forbidden_class_still_catches_generic_name(tmp_path):
    # generic_class_name removed → no_forbidden_class must still catch sec_1
    r = _results(tmp_path, html='<html><body><div class="sec_1"></div></body></html>')
    assert "no_forbidden_class" in r
    assert r["no_forbidden_class"].passed is False


def test_no_raw_calc_now_covers_vw(tmp_path):
    # no_raw_vw removed → no_raw_calc must still flag standalone vw
    r = _results(tmp_path, css=".x{width:50vw;}")
    assert r["no_raw_calc"].passed is False

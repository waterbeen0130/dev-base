"""Follow-up: omx_usage_detection — code-extraction provenance via ledger.

The code-extraction steps (structure/values) must record a known AI provider
(omx default, or codex/claude/gemini). Unknown/missing provenance is flagged so
an untracked external agent's output is not trusted blindly (CLAUDE.md: 외주 AI
자가보고 신뢰 금지, OMX 기본).
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK_PATH = ROOT / "tools" / "check-extraction-provenance.py"

spec = importlib.util.spec_from_file_location("check_extraction_provenance", CHECK_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _ledger(struct_provider, values_provider):
    return {"steps": [
        {"step": "extract", "provider": "figma-section-spec"},
        {"step": "structure", "provider": struct_provider},
        {"step": "values", "provider": values_provider},
        {"step": "verify", "provider": "pm-verify"},
    ]}


def test_known_provider_ok():
    ok, reason = mod.check_provenance(_ledger("omx", "omx"))
    assert ok is True, reason


def test_unknown_provider_flagged():
    ok, reason = mod.check_provenance(_ledger("some-external-bot", "omx"))
    assert ok is False
    assert "structure" in reason


def test_missing_provider_flagged():
    ledger = {"steps": [{"step": "structure"}, {"step": "values", "provider": "omx"}]}
    ok, reason = mod.check_provenance(ledger)
    assert ok is False


def test_other_known_agents_ok():
    for p in ("codex", "claude", "gemini"):
        ok, reason = mod.check_provenance(_ledger(p, p))
        assert ok is True, f"{p}: {reason}"

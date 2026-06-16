#!/usr/bin/env python3
"""Follow-up (omx_usage_detection): code-extraction provenance check.

The code-extraction steps (structure = Pass1, values = Pass2) in the workflow
ledger must record a KNOWN AI provider. OMX is the default; codex/claude/gemini
are the other sanctioned managed agents. Unknown or missing provenance is
flagged so an untracked external agent's output is not trusted blindly
(CLAUDE.md: 외주 AI 자가보고 신뢰 금지).

Usage:
    python3 check-extraction-provenance.py --ledger .gran-maestro/workflow-ledger.json
Exit: 0 = ok, 1 = unknown/missing provenance.
"""

import argparse
import json
import sys
from pathlib import Path

KNOWN_EXTRACTION_PROVIDERS = {"omx", "codex", "claude", "gemini"}
EXTRACTION_STEPS = {"structure", "values"}


def check_provenance(ledger: dict):
    """Return (ok: bool, reason: str)."""
    violations = []
    for entry in ledger.get("steps") or []:
        if not isinstance(entry, dict) or entry.get("step") not in EXTRACTION_STEPS:
            continue
        provider = entry.get("provider")
        if not provider:
            violations.append(f"{entry.get('step')}: provider 미기록")
        elif provider not in KNOWN_EXTRACTION_PROVIDERS:
            violations.append(f"{entry.get('step')}: 미상 provider '{provider}' (허용: {sorted(KNOWN_EXTRACTION_PROVIDERS)})")
    if violations:
        return False, "unverified_provenance: " + "; ".join(violations)
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--ledger", required=True)
    args = ap.parse_args()
    path = Path(args.ledger)
    if not path.exists():
        print(f"BLOCK: no_ledger: 워크플로우 원장 없음 ({path}) — 추출 주체 증명 불가")
        return 1
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"BLOCK: invalid_ledger: 원장 파싱 실패 ({exc})")
        return 1
    ok, reason = check_provenance(ledger)
    print(("ALLOW" if ok else "BLOCK") + f": {reason}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

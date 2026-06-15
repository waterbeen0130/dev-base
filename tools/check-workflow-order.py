#!/usr/bin/env python3
"""Follow-up (workflow_order_enforced): screenshot-first 2-pass order check.

Validates a workflow ledger (.gran-maestro/workflow-ledger.json) so the
conversion followed: extract -> structure (Pass1, screenshot) -> values
(Pass2, spec) -> verify. The decisive guarantee is that `values` happens AFTER
`structure`; applying spec values before building semantic structure is the
node-name transliteration failure mode this whole effort targets.

Ledger format:
    {"section": "...", "steps": [{"step": "extract", "provider": "...", "ts": "..."}, ...]}

Usage:
    python3 check-workflow-order.py --ledger .gran-maestro/workflow-ledger.json
Exit: 0 = ok, 1 = order violation.
"""

import argparse
import json
import sys
from pathlib import Path

REQUIRED_ORDER = ["extract", "structure", "values", "verify"]


def validate_order(ledger: dict):
    """Return (ok: bool, reason: str)."""
    steps = [s.get("step") for s in (ledger.get("steps") or []) if isinstance(s, dict)]
    # first-occurrence index of each required step
    first = {}
    for idx, step in enumerate(steps):
        if step in REQUIRED_ORDER and step not in first:
            first[step] = idx

    missing = [s for s in REQUIRED_ORDER if s not in first]
    if missing:
        return False, f"missing_step: 워크플로우 단계 누락 {missing}"

    # required steps must appear in REQUIRED_ORDER sequence
    prev_idx = -1
    prev_step = None
    for step in REQUIRED_ORDER:
        if first[step] <= prev_idx:
            return False, f"out_of_order: '{step}' 가 '{prev_step}' 보다 먼저 나옴 (screenshot-first 위반: values는 structure 이후)"
        prev_idx = first[step]
        prev_step = step
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--ledger", required=True)
    args = ap.parse_args()
    path = Path(args.ledger)
    if not path.exists():
        print(f"BLOCK: no_ledger: 워크플로우 원장 없음 ({path}) — 2패스 순서 증명 불가")
        return 1
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"BLOCK: invalid_ledger: 원장 파싱 실패 ({exc})")
        return 1
    ok, reason = validate_order(ledger)
    print(("ALLOW" if ok else "BLOCK") + f": {reason}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

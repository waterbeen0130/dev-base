#!/usr/bin/env python3
"""Workflow ledger writer (AGI-004 #4).

Canonical, atomic writer for `.gran-maestro/workflow-ledger.json` so the
screenshot-first 2-pass conversion records its steps as it runs, instead of the
ledger being hand-edited (error-prone). The recorded ledger is what
check-workflow-order.py / check-extraction-provenance.py (and the accept gate)
validate.

Ledger format (single section per file, as defined in rules/INSTRUCTIONS.md):
    {"section": "main_visual", "steps": [
        {"step": "extract",   "provider": "figma-section-spec", "ts": "..."},
        {"step": "structure", "provider": "omx", "ts": "..."},
        {"step": "values",    "provider": "omx", "ts": "..."},
        {"step": "verify",    "provider": "pm-verify", "ts": "..."}]}

`extract` starts a fresh section workflow (resets the ledger); the other steps
append to the current section. This keeps the file faithful to the format the
checkers read (a flat top-level `steps`). Multi-section aggregation is a
documented follow-up — the accept gate validates the most-recently-worked
section.

Usage:
    python3 workflow-ledger.py init   --section main_visual
    python3 workflow-ledger.py append --step extract   --provider figma-section-spec --section main_visual
    python3 workflow-ledger.py append --step structure --provider omx
    python3 workflow-ledger.py append --step values    --provider omx
    python3 workflow-ledger.py append --step verify    --provider pm-verify
    python3 workflow-ledger.py show

Exit: 0 = ok, 1 = usage/validation error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_STEPS = ("extract", "structure", "values", "verify", "visual-compare")
DEFAULT_LEDGER_REL = Path(".gran-maestro") / "workflow-ledger.json"


def find_project_root() -> Path:
    candidate = Path.cwd()
    while candidate != candidate.parent:
        if (candidate / ".gran-maestro").is_dir():
            return candidate
        candidate = candidate.parent
    return Path.cwd()


def default_ledger_path() -> Path:
    return find_project_root() / DEFAULT_LEDGER_REL


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_ledger(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    data.setdefault("steps", [])
    return data


def init_ledger(path: Path, section: str) -> dict:
    ledger = {"section": section, "steps": []}
    _atomic_write(path, ledger)
    return ledger


def append_step(path: Path, step: str, provider: str, section: str | None = None,
                ts: str | None = None) -> dict:
    """Append a step. `extract` starts a fresh section ledger.

    Raises ValueError on invalid step, or when starting a non-extract step with
    no existing ledger and no section to anchor to.
    """
    if step not in VALID_STEPS:
        raise ValueError(f"invalid step '{step}' (allowed: {', '.join(VALID_STEPS)})")

    ledger = load_ledger(path)

    if step == "extract":
        # extract begins a new section's workflow → reset.
        sec = section or (ledger or {}).get("section")
        if not sec:
            raise ValueError("extract requires --section (no existing ledger to inherit from)")
        ledger = {"section": sec, "steps": []}
    else:
        if ledger is None:
            if not section:
                raise ValueError(
                    f"no ledger at {path}; run `init`/`append --step extract` first, "
                    f"or pass --section"
                )
            ledger = {"section": section, "steps": []}
        elif section and section != ledger.get("section"):
            raise ValueError(
                f"section mismatch: ledger tracks '{ledger.get('section')}' but got "
                f"'{section}' (run `append --step extract --section {section}` to start it)"
            )

    ledger["steps"].append({
        "step": step,
        "provider": provider,
        "ts": ts or _now_iso(),
    })
    _atomic_write(path, ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser(description="Workflow ledger writer")
    parser.add_argument("--ledger", help="Ledger path (default: <root>/.gran-maestro/workflow-ledger.json)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create a fresh ledger for a section")
    p_init.add_argument("--section", required=True)

    p_app = sub.add_parser("append", help="Append a step")
    p_app.add_argument("--step", required=True, choices=VALID_STEPS)
    p_app.add_argument("--provider", required=True)
    p_app.add_argument("--section", help="Section name (required for first step / new section)")
    p_app.add_argument("--ts", help="ISO8601 timestamp override (default: now UTC)")

    sub.add_parser("show", help="Print the current ledger")

    args = parser.parse_args()
    path = Path(args.ledger) if args.ledger else default_ledger_path()

    if args.cmd == "init":
        ledger = init_ledger(path, args.section)
        print(f"[ledger] init section='{args.section}' → {path}")
        return 0

    if args.cmd == "append":
        try:
            ledger = append_step(path, args.step, args.provider, args.section, args.ts)
        except ValueError as exc:
            print(f"[ledger] ERROR: {exc}", file=sys.stderr)
            return 1
        steps = " → ".join(s["step"] for s in ledger["steps"])
        print(f"[ledger] +{args.step} (provider={args.provider}) section='{ledger['section']}' [{steps}]")
        return 0

    if args.cmd == "show":
        ledger = load_ledger(path)
        if ledger is None:
            print(f"[ledger] none at {path}")
            return 0
        print(json.dumps(ledger, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())

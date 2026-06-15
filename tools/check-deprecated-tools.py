#!/usr/bin/env python3
"""DOD-004: deprecated / forbidden tool usage detection.

Flags (a) resurrection of deprecated tool files under tools/, and (b) actual
invocations of deprecated tools or the `--converge` auto-retry flag inside
scripts (.py/.sh). Prohibition *mentions* in docs (.md) are intentionally NOT
scanned, so listing the forbidden names in rules/CLAUDE docs is fine.

Usage:
    python3 check-deprecated-tools.py [--root .]
Exit: 0 = clean, 1 = violations found.
"""

import argparse
import re
import sys
from pathlib import Path

# Forbidden auto-generation / auto-repair / retired pipeline tools (CLAUDE.md / INSTRUCTIONS.md).
DEPRECATED_TOOLS = (
    "generate.py", "json-to-html.py", "repair-from-violations.py", "structural-diff.py",
    "compare-css.py", "check-rules-drift.py", "build-prompts.py", "brief-checksum.py",
    "run-pipeline.py", "split-sections.py", "assemble.py", "migrate-spec-v1-to-v2.py",
    "post-impl-verify.py",
)
FORBIDDEN_FLAG = "--converge"

# Directories that legitimately reference the names (prohibition lists, history, fixtures).
EXCLUDE_DIRS = {".git", ".gran-maestro", "node_modules", "__pycache__", "rules", "tests"}
SCRIPT_SUFFIXES = {".py", ".sh"}


def find_violations(root) -> list[dict]:
    root = Path(root)
    self_name = Path(__file__).name
    violations: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name == self_name:
            continue

        # (a) resurrected deprecated tool file under any tools/ dir
        if path.suffix == ".py" and path.name in DEPRECATED_TOOLS and "tools" in path.parts:
            violations.append({"file": str(path), "detail": f"deprecated tool file resurrected: {path.name}"})
            continue

        # (b) invocation / forbidden flag inside scripts only (docs are skipped)
        if path.suffix not in SCRIPT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue  # comment, not an invocation
            if FORBIDDEN_FLAG in line:
                violations.append({"file": f"{path}:{lineno}", "detail": f"forbidden flag {FORBIDDEN_FLAG}"})
            for tool in DEPRECATED_TOOLS:
                if tool in line and re.search(r"(python3?\s|subprocess|os\.system|exec|run\(|\./|import)", line):
                    violations.append({"file": f"{path}:{lineno}", "detail": f"deprecated tool invocation: {tool}"})
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    violations = find_violations(args.root)
    if violations:
        print(f"✗ {len(violations)} deprecated-tool violation(s):")
        for v in violations:
            print(f"  [{v['file']}] {v['detail']}")
        return 1
    print("✓ no deprecated tool usage")
    return 0


if __name__ == "__main__":
    sys.exit(main())

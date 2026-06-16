#!/usr/bin/env python3
"""DOD-011: output boundary recognition.

Raw extraction leftovers must not be mistaken for the published deliverable.
This flags:
  (a) a raw-extraction directory (extracted/) sitting inside the deliverable, and
  (b) HTML files dominated by Figma node-name classes (main_f0, main_v53 ...),
      which indicate an un-refactored raw extraction dump.

Usage:
    python3 check-output-boundary.py [--deliverable .]
Exit: 0 = clean, 1 = boundary violations found.
"""

import argparse
import re
import sys
from pathlib import Path

RAW_DIRS = {"extracted"}
NODE_NAME_RE = re.compile(r"\b[a-z]+_[fvt][0-9]+\b")
# An HTML with this many distinct node-name classes is treated as a raw dump.
RAW_NODE_NAME_THRESHOLD = 8
EXCLUDE_DIRS = {".git", ".gran-maestro", "node_modules", "__pycache__"}


def find_boundary_violations(deliverable) -> list[dict]:
    root = Path(deliverable)
    violations: list[dict] = []

    # (a) raw extraction directory inside the deliverable
    for raw in RAW_DIRS:
        raw_dir = root / raw
        if raw_dir.is_dir():
            violations.append({
                "file": str(raw_dir),
                "detail": f"raw 추출 디렉토리 '{raw}/' 가 산출물 안에 있음 — 최종물과 분리/제거 필요",
            })

    # (b) HTML files that are raw node-name dumps
    for html in root.rglob("*.html"):
        if any(part in EXCLUDE_DIRS for part in html.parts):
            continue
        try:
            text = html.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        distinct = set(NODE_NAME_RE.findall(text))
        if len(distinct) >= RAW_NODE_NAME_THRESHOLD:
            violations.append({
                "file": str(html),
                "detail": f"Figma 노드명 클래스 {len(distinct)}종 — raw 추출 잔재로 보임 (시맨틱 마크업으로 재작업 필요)",
            })
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--deliverable", default=".")
    args = ap.parse_args()
    violations = find_boundary_violations(args.deliverable)
    if violations:
        print(f"✗ {len(violations)} output-boundary violation(s):")
        for v in violations:
            print(f"  [{v['file']}] {v['detail']}")
        return 1
    print("✓ output boundary clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

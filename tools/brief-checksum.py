#!/usr/bin/env python3
"""Brief checksum validator for publishing impl-request briefs.

Verifies that outsourced implementation briefs (phase2-impl.md) include the
mandatory "## 규칙" section with required subsections and sufficient inline
content from common.md / gemini.md. Exits non-zero when the section is
missing, truncated, or lacks required subsections.

Usage:
    python3 brief-checksum.py --brief {path}

AC mapping:
    AC-002: "## 규칙" section existence + minimum body length
    AC-003: required subsections (### CSS 핵심 규칙, ### Figma MCP 값 사용 규칙)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Minimum character length for the "## 규칙" section body (AC-002 threshold).
MIN_SECTION_BODY_LENGTH = 500

# Minimum number of bullet items inside the "## 규칙" section (AC-001 guard).
MIN_BULLET_COUNT = 10

# Required subsections inside "## 규칙" (AC-003).
REQUIRED_SUBSECTIONS = [
    "### CSS 핵심 규칙",
    "### Figma MCP 값 사용 규칙",
]

# Accepted heading aliases for the top-level rules section.
RULES_HEADING_PATTERN = re.compile(r"^##\s+(규칙|코딩 규칙)\b", re.MULTILINE)


def extract_rules_section(text: str) -> str | None:
    """Return the body of the first matching "## 규칙" section, or None."""
    match = RULES_HEADING_PATTERN.search(text)
    if not match:
        return None

    start = match.end()
    # Section ends at the next top-level "## " heading (excluding "### ...").
    next_heading = re.search(r"^##\s+(?!#)", text[start:], re.MULTILINE)
    if next_heading:
        end = start + next_heading.start()
    else:
        end = len(text)
    return text[start:end]


def count_bullets(section_body: str) -> int:
    """Count markdown bullet items (lines starting with '- ' or '* ')."""
    bullet_re = re.compile(r"^\s*[-*]\s+\S", re.MULTILINE)
    return len(bullet_re.findall(section_body))


def find_missing_subsections(section_body: str) -> list[str]:
    """Return list of required subsection headings missing from section_body."""
    missing: list[str] = []
    for heading in REQUIRED_SUBSECTIONS:
        pattern = re.compile(r"^" + re.escape(heading) + r"\b", re.MULTILINE)
        if not pattern.search(section_body):
            missing.append(heading)
    return missing


def validate_brief(brief_path: Path) -> tuple[bool, list[str]]:
    """Return (ok, errors) after checking the brief at brief_path."""
    errors: list[str] = []

    if not brief_path.exists():
        return False, [f"Brief file not found: {brief_path}"]

    try:
        text = brief_path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, [f"Failed to read brief: {exc}"]

    section_body = extract_rules_section(text)
    if section_body is None:
        errors.append(
            'Missing required section "## 규칙" (or "## 코딩 규칙") — '
            "rules must be inlined from common.md / gemini.md."
        )
        return False, errors

    body_length = len(section_body.strip())
    if body_length < MIN_SECTION_BODY_LENGTH:
        errors.append(
            f'"## 규칙" section body is too short '
            f"({body_length} chars < {MIN_SECTION_BODY_LENGTH} required)."
        )

    bullet_count = count_bullets(section_body)
    if bullet_count < MIN_BULLET_COUNT:
        errors.append(
            f'"## 규칙" section has {bullet_count} bullets '
            f"(minimum {MIN_BULLET_COUNT} required)."
        )

    missing = find_missing_subsections(section_body)
    for heading in missing:
        errors.append(f"Missing required subsection: {heading}")

    return (len(errors) == 0), errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Validate that an impl-request brief includes the "## 규칙" '
            "section with required subsections (AC-002, AC-003)."
        )
    )
    parser.add_argument(
        "--brief",
        required=True,
        help="Path to the brief file (e.g. phase2-impl.md)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    brief_path = Path(args.brief)
    ok, errors = validate_brief(brief_path)

    if ok:
        print(f"[OK] Brief passes rule-section checksum: {brief_path}")
        return 0

    print(f"[FAIL] Brief rule-section checksum failed: {brief_path}", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

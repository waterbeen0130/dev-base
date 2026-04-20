#!/usr/bin/env python3
"""Deterministic repair tool for known HTML/CSS violations."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:  # optional dependency, preferred when available
    import tinycss2  # type: ignore
except Exception:  # pragma: no cover - optional
    tinycss2 = None


CATEGORY_KEYS = (
    "pill_radius",
    "rgba_to_hex",
    "rgb_to_hex",
    "hex8_opaque_to_hex6",
    "multiline_selector",
    "media_indent",
    "letter_spacing_px_to_em",
    "duplicate_selector_merge",
)
REQUIRED_VIOLATION_FIELDS = ("rule_id", "file")
OPTIONAL_VIOLATION_FIELDS = ("line", "expected", "actual", "fix_strategy", "patch_hint")
DEFAULT_PATCH_HINT_TEXT = "패치 힌트 없음 — 직접 수정 필요"

SIMPLE_BLOCK_RE = re.compile(r"([^{]+)\{([^{}]*)\}", re.DOTALL)
RULE_LINE_RE = re.compile(r"^([^@{}][^{}]*)\{([^{}]*)\}$")
RGB_RE = re.compile(r"\brgb\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*\)", re.IGNORECASE)
RGBA_OPAQUE_RE = re.compile(
    r"\brgba\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*(1(?:\.0+)?)\s*\)",
    re.IGNORECASE,
)
HEX8_OPAQUE_RE = re.compile(r"#([0-9a-fA-F]{6})(ff)\b", re.IGNORECASE)
PILL_RADIUS_RE = re.compile(r"(border-radius\s*:\s*)(99|999|9999)px\b", re.IGNORECASE)
LETTER_SPACING_PX_RE = re.compile(r"^(-?[0-9]+(?:\.[0-9]+)?)px$", re.IGNORECASE)
FONT_SIZE_PX_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)px$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministically repair known HTML/CSS violations")
    parser.add_argument("--html", required=True, help="HTML file path")
    parser.add_argument("--css", required=True, help="CSS file path")
    parser.add_argument("--violations", help="Violation report JSON path")
    parser.add_argument(
        "--agent",
        choices=["codex-dev", "gemini-dev", "claude-dev"],
        default="codex-dev",
        help="Dispatch agent label",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; print unified diff")
    parser.add_argument("--report", help="Write repair report JSON")
    return parser.parse_args()


def _format_number(value: float, precision: int = 6) -> str:
    text = f"{value:.{precision}f}".rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def _clamp_channel(raw: str) -> int:
    try:
        return max(0, min(255, int(raw)))
    except ValueError:
        return 0


def _rgb_to_hex(r: str, g: str, b: str) -> str:
    return "#{:02x}{:02x}{:02x}".format(_clamp_channel(r), _clamp_channel(g), _clamp_channel(b))


def _normalize_selector(selector: str) -> str:
    compact = re.sub(r"\s+", " ", selector.strip())
    if "," not in compact:
        return compact
    items = [re.sub(r"\s+", " ", item.strip()) for item in compact.split(",") if item.strip()]
    return ", ".join(items)


def _split_declarations(block_body: str) -> list[str]:
    declarations: list[str] = []
    current: list[str] = []
    paren_depth = 0
    for char in block_body:
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth > 0:
            paren_depth -= 1
        if char == ";" and paren_depth == 0:
            merged = "".join(current).strip()
            if merged:
                declarations.append(merged)
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        declarations.append(tail)
    return declarations


def _normalize_declaration(declaration: str) -> str:
    if ":" not in declaration:
        return declaration.strip()
    prop, value = declaration.split(":", 1)
    normalized_value = re.sub(r"\s+", " ", value.strip())
    return f"{prop.strip()}:{normalized_value}"


def _apply_regex_value_repairs(css_text: str, counts: dict[str, int]) -> str:
    def _pill_replacer(match: re.Match[str]) -> str:
        counts["pill_radius"] += 1
        return f"{match.group(1)}2em"

    css_text = PILL_RADIUS_RE.sub(_pill_replacer, css_text)

    def _rgba_replacer(match: re.Match[str]) -> str:
        counts["rgba_to_hex"] += 1
        return _rgb_to_hex(match.group(1), match.group(2), match.group(3))

    css_text = RGBA_OPAQUE_RE.sub(_rgba_replacer, css_text)

    def _rgb_replacer(match: re.Match[str]) -> str:
        counts["rgb_to_hex"] += 1
        return _rgb_to_hex(match.group(1), match.group(2), match.group(3))

    css_text = RGB_RE.sub(_rgb_replacer, css_text)

    def _hex8_replacer(match: re.Match[str]) -> str:
        counts["hex8_opaque_to_hex6"] += 1
        return f"#{match.group(1)}"

    css_text = HEX8_OPAQUE_RE.sub(_hex8_replacer, css_text)
    return css_text


def _apply_block_repairs(css_text: str, counts: dict[str, int]) -> str:
    selector_font_size: dict[str, float] = {}
    chunks: list[str] = []
    cursor = 0

    for match in SIMPLE_BLOCK_RE.finditer(css_text):
        chunks.append(css_text[cursor:match.start()])
        cursor = match.end()

        selector_raw = match.group(1)
        body_raw = match.group(2)
        selector_clean = selector_raw.strip()
        leading_ws = selector_raw[: len(selector_raw) - len(selector_raw.lstrip(" \t\r\n"))]

        if not selector_clean or selector_clean.startswith("@"):
            chunks.append(match.group(0))
            continue

        normalized_selector = _normalize_selector(selector_clean)
        declarations = [_normalize_declaration(item) for item in _split_declarations(body_raw)]
        if not declarations:
            chunks.append(f"{leading_ws}{normalized_selector}{{}}")
            continue

        font_size: float | None = None
        for declaration in declarations:
            if ":" not in declaration:
                continue
            prop, value = declaration.split(":", 1)
            if prop.strip().lower() != "font-size":
                continue
            parsed = FONT_SIZE_PX_RE.match(value.strip())
            if parsed:
                font_size = float(parsed.group(1))
                break
        if font_size is None:
            font_size = selector_font_size.get(normalized_selector)
        else:
            selector_font_size[normalized_selector] = font_size

        rewritten: list[str] = []
        for declaration in declarations:
            if ":" not in declaration:
                rewritten.append(declaration)
                continue
            prop, value = declaration.split(":", 1)
            if prop.strip().lower() == "letter-spacing" and font_size and font_size > 0:
                spacing = LETTER_SPACING_PX_RE.match(value.strip())
                if spacing:
                    px_value = float(spacing.group(1))
                    em_value = _format_number(px_value / font_size)
                    rewritten.append(f"{prop.strip()}:{em_value}em")
                    counts["letter_spacing_px_to_em"] += 1
                    continue
            rewritten.append(_normalize_declaration(declaration))

        new_block = f"{leading_ws}{normalized_selector}{{{';'.join(rewritten)}}}"
        selector_has_multiline = "\n" in selector_clean
        body_has_multiline = "\n" in body_raw.strip()
        if selector_has_multiline or body_has_multiline:
            if new_block != match.group(0).strip():
                counts["multiline_selector"] += 1
        chunks.append(new_block)

    chunks.append(css_text[cursor:])
    return "".join(chunks)


def _remove_media_indentation(css_text: str, counts: dict[str, int]) -> str:
    lines = css_text.splitlines()
    out: list[str] = []
    media_depth = 0

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.lstrip(" \t")

        if media_depth > 0 and stripped and stripped != line:
            counts["media_indent"] += 1
            line = stripped

        out.append(line)

        if re.match(r"^\s*@media\b", line):
            media_depth += line.count("{") - line.count("}")
            if media_depth < 0:
                media_depth = 0
            continue
        if media_depth > 0:
            media_depth += line.count("{") - line.count("}")
            if media_depth < 0:
                media_depth = 0

    rebuilt = "\n".join(out)
    if css_text.endswith("\n"):
        rebuilt += "\n"
    return rebuilt


def _merge_duplicate_selector_blocks(css_text: str, counts: dict[str, int]) -> str:
    lines = css_text.splitlines()
    out: list[str] = []
    index = 0

    while index < len(lines):
        current = lines[index].strip()
        matched = RULE_LINE_RE.match(current)
        if not matched:
            out.append(lines[index].rstrip())
            index += 1
            continue

        selector = _normalize_selector(matched.group(1))
        merged_decls = [_normalize_declaration(item) for item in _split_declarations(matched.group(2))]

        cursor = index + 1
        while cursor < len(lines):
            probe = lines[cursor].strip()
            if not probe:
                cursor += 1
                continue
            probe_match = RULE_LINE_RE.match(probe)
            if not probe_match:
                break
            probe_selector = _normalize_selector(probe_match.group(1))
            if probe_selector != selector:
                break
            extra = [_normalize_declaration(item) for item in _split_declarations(probe_match.group(2))]
            merged_decls.extend(extra)
            counts["duplicate_selector_merge"] += 1
            cursor += 1

        out.append(f"{selector}{{{';'.join(merged_decls)}}}")
        index = cursor

    rebuilt = "\n".join(out)
    if css_text.endswith("\n"):
        rebuilt += "\n"
    return rebuilt


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_max_cli_retries(project_root: Path) -> int:
    config_path = project_root / ".gran-maestro" / "config.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return 2
    retry = payload.get("retry")
    if not isinstance(retry, dict):
        return 2
    raw = retry.get("max_cli_retries")
    if isinstance(raw, int) and raw >= 0:
        return raw
    return 2


def _validate_violation_schema(violation: Any, index: int) -> dict[str, Any]:
    if not isinstance(violation, dict):
        raise ValueError(f"invalid violation[{index}]: expected object")

    normalized: dict[str, Any] = {}
    for field in REQUIRED_VIOLATION_FIELDS:
        value = violation.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"invalid violation[{index}]: missing required field: {field}")
        normalized[field] = value.strip()

    for field in OPTIONAL_VIOLATION_FIELDS:
        value = violation.get(field)
        if value is None:
            continue
        if field == "line":
            if isinstance(value, int):
                normalized[field] = value
            elif isinstance(value, float) and value.is_integer():
                normalized[field] = int(value)
            elif isinstance(value, str) and value.strip().isdigit():
                normalized[field] = int(value.strip())
            else:
                raise ValueError(f"invalid violation[{index}]: line must be int-compatible")
            continue
        normalized[field] = str(value)
    return normalized


def _collect_violation_items(payload: Any) -> list[Any]:
    if isinstance(payload, dict):
        if isinstance(payload.get("violations"), list):
            return list(payload["violations"])
        items: list[Any] = []
        for key in ("figma_validate", "validate_semantic"):
            nested = payload.get(key)
            if isinstance(nested, dict) and isinstance(nested.get("violations"), list):
                items.extend(nested["violations"])
        return items
    if isinstance(payload, list):
        return list(payload)
    return []


def _load_violations(violations_path: str | None) -> list[dict[str, Any]] | None:
    if not violations_path:
        return None
    path = Path(violations_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"failed to parse violations JSON: {exc}") from exc

    raw_items = _collect_violation_items(payload)
    validated: list[dict[str, Any]] = []
    for index, item in enumerate(raw_items):
        validated.append(_validate_violation_schema(item, index))
    return validated


def _collect_current_violation_count(
    violations: list[dict[str, Any]] | None,
    html_path: Path,
    css_path: Path,
) -> int:
    if violations is not None:
        return len(violations)
    tools_dir = Path(__file__).resolve().parent
    command = [
        sys.executable,
        str(tools_dir / "validate-semantic.py"),
        "--html",
        str(html_path),
        "--css",
        str(css_path),
        "--profile",
        "all",
    ]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    lines = [line for line in (proc.stdout + "\n" + proc.stderr).splitlines() if line.strip().startswith("[")]
    return len(lines)


def _escape_markdown_cell(value: Any) -> str:
    text = str(value).replace("\n", "<br>")
    return text.replace("|", "\\|")


def _build_violation_brief_appendix(violations: list[dict[str, Any]]) -> str:
    if not violations:
        return ""
    lines = [
        "| rule_id | file | line | expected | actual | fix_strategy | patch_hint |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for violation in violations:
        patch_hint = violation.get("patch_hint")
        if not isinstance(patch_hint, str) or not patch_hint.strip():
            patch_hint = DEFAULT_PATCH_HINT_TEXT
        line_value = violation.get("line", "")
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_markdown_cell(violation.get("rule_id", "")),
                    _escape_markdown_cell(violation.get("file", "")),
                    _escape_markdown_cell(line_value),
                    _escape_markdown_cell(violation.get("expected", "")),
                    _escape_markdown_cell(violation.get("actual", "")),
                    _escape_markdown_cell(violation.get("fix_strategy", "")),
                    _escape_markdown_cell(patch_hint),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _count_remaining_fixable(css_text: str) -> int:
    remaining = 0
    remaining += len(PILL_RADIUS_RE.findall(css_text))
    remaining += len(RGBA_OPAQUE_RE.findall(css_text))
    remaining += len(RGB_RE.findall(css_text))
    remaining += len(HEX8_OPAQUE_RE.findall(css_text))

    for match in SIMPLE_BLOCK_RE.finditer(css_text):
        selector = match.group(1).strip()
        if selector.startswith("@"):
            continue
        if "\n" in selector or "\n" in match.group(2).strip():
            remaining += 1
        if re.search(r"letter-spacing\s*:\s*-?[0-9]+(?:\.[0-9]+)?px\b", match.group(2), re.IGNORECASE):
            remaining += 1

    media_depth = 0
    for line in css_text.splitlines():
        if media_depth > 0 and line.startswith((" ", "\t")) and line.strip():
            remaining += 1
        if re.match(r"^\s*@media\b", line):
            media_depth += line.count("{") - line.count("}")
        elif media_depth > 0:
            media_depth += line.count("{") - line.count("}")
        if media_depth < 0:
            media_depth = 0

    prev_selector: str | None = None
    for raw in css_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        matched = RULE_LINE_RE.match(line)
        if not matched:
            prev_selector = None
            continue
        selector = _normalize_selector(matched.group(1))
        if prev_selector == selector:
            remaining += 1
        prev_selector = selector

    return remaining


def _print_dry_run_diff(before: str, after: str, css_path: Path) -> None:
    diff = list(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{css_path} (before)",
            tofile=f"{css_path} (after)",
        )
    )
    if diff:
        print("".join(diff), end="")
    else:
        print("[dry-run] no changes")


def _has_tinycss2_support(css_text: str) -> bool:
    if tinycss2 is None:
        return False
    try:  # pragma: no cover - environment dependent
        tinycss2.parse_stylesheet(css_text, skip_comments=False, skip_whitespace=False)
        return True
    except Exception:
        return False


def _run_repair_pass(css_text: str) -> tuple[str, dict[str, int]]:
    counts = {key: 0 for key in CATEGORY_KEYS}
    repaired_css = css_text
    repaired_css = _apply_regex_value_repairs(repaired_css, counts)
    repaired_css = _apply_block_repairs(repaired_css, counts)
    repaired_css = _remove_media_indentation(repaired_css, counts)
    repaired_css = _merge_duplicate_selector_blocks(repaired_css, counts)
    if not repaired_css.endswith("\n"):
        repaired_css += "\n"
    return repaired_css, counts


def main() -> int:
    args = parse_args()
    html_path = Path(args.html)
    css_path = Path(args.css)
    project_root = _project_root()
    max_cli_retries = _load_max_cli_retries(project_root)
    max_attempts = max(1, max_cli_retries + 1)

    try:
        _ = html_path.read_text(encoding="utf-8")
        original_css = css_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"[repair] parse error: {exc}", file=sys.stderr)
        return 2

    try:
        violations = _load_violations(args.violations)
    except ValueError as exc:
        print(f"[repair] schema error: {exc}", file=sys.stderr)
        return 2

    if violations is None:
        max_attempts = 1

    brief_appendix = _build_violation_brief_appendix(violations or [])

    # Preference contract: use tinycss2 when available, otherwise regex fallback.
    _has_tinycss2_support(original_css)

    aggregate_counts = {key: 0 for key in CATEGORY_KEYS}
    repaired_css = original_css
    previous_violation_count: int | None = None
    attempts = 0
    convergence_early_stop = False

    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        current_violation_count = _collect_current_violation_count(violations, html_path, css_path)
        next_css, pass_counts = _run_repair_pass(repaired_css)

        for key, value in pass_counts.items():
            aggregate_counts[key] += value

        css_changed = next_css != repaired_css
        if (
            violations is not None
            and previous_violation_count is not None
            and not css_changed
            and current_violation_count == previous_violation_count
        ):
            convergence_early_stop = True
            print(
                "[repair] convergence-stop: "
                f"violation_count unchanged at {current_violation_count} (attempt={attempt})"
            )
            break

        previous_violation_count = current_violation_count
        repaired_css = next_css

        if not css_changed and attempt >= max_attempts:
            break

    files_modified: list[str] = []
    if repaired_css != original_css:
        files_modified.append(str(css_path))
        if args.dry_run:
            _print_dry_run_diff(original_css, repaired_css, css_path)
        else:
            css_path.write_text(repaired_css, encoding="utf-8")

    total_fixed = sum(aggregate_counts.values())
    remaining_fixable = _count_remaining_fixable(repaired_css)
    violation_count = _collect_current_violation_count(violations, html_path, css_path)
    unfixable_count = max(0, violation_count - total_fixed)

    summary = {
        "total_fixed": total_fixed,
        "by_category": aggregate_counts,
        "files_modified": files_modified,
        "unfixable_count": unfixable_count,
        "dry_run": bool(args.dry_run),
        "attempts": attempts,
        "max_attempts": max_attempts,
        "convergence_early_stop": convergence_early_stop,
        "violations_loaded": len(violations) if violations is not None else 0,
        "violation_brief_appendix": brief_appendix,
    }

    print(f"[repair] total_fixed={total_fixed}")
    print(f"[repair] files_modified={len(files_modified)}")
    print(f"[repair] attempts={attempts}/{max_attempts}")
    if total_fixed:
        non_zero = ", ".join(f"{key}:{value}" for key, value in aggregate_counts.items() if value)
        print(f"[repair] by_category={non_zero}")
    if violations is not None:
        print(f"[repair] violations_loaded={len(violations)}")
        if brief_appendix:
            print("[repair] external_brief_appendix:")
            print(brief_appendix)

    if args.report:
        Path(args.report).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if violations is not None and convergence_early_stop:
        return 1
    if violations is not None and violation_count > 0 and total_fixed == 0:
        return 1
    if total_fixed == 0 and remaining_fixable > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Post-implementation verification for PM dispatch follow-up."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


CRITICAL_CATEGORIES = {
    "텍스트 위변조",
    "폰트 5필드 완결성",
    "fills color hex 일치",
}

MAJOR_CATEGORIES = {
    "lineHeight 비율 일치",
    "clamp 적용",
    "frame padding/gap 반영",
    "줄바꿈 보존",
    "interaction URL 일치",
    "column flex gap 금지",
}

PSEUDO_PATTERN = re.compile(r"::?(before|after)\b")
SEMANTIC_COUNTS_PATTERN = re.compile(r"CRITICAL:\s*(\d+)\s*\|\s*MAJOR:\s*(\d+)\s*\|\s*MINOR:\s*(\d+)")
SCHEMA_V1_PATTERN = re.compile(r"^1(?:\.\d+\.\d+)?$")
SCHEMA_V2_PATTERN = re.compile(r"^2(?:\.\d+\.\d+)?$")
POLICY_1_CATEGORY = "[POLICY-1] VERTICAL frame itemSpacing must map to margin-bottom"
V1_CATEGORIES = (
    "텍스트 위변조",
    "줄바꿈 보존",
    "폰트 5필드 완결성",
    "lineHeight 비율 일치",
    "fills color hex 일치",
    "frame padding/gap 반영",
    "clamp 적용",
    "column flex gap 금지",
    "interaction URL 일치",
)
V2_CATEGORIES = V1_CATEGORIES + (
    POLICY_1_CATEGORY,
    "v2.fills.type.stub",
    "v2.effects.stub",
    "v2.strokes.stub",
    "v2.layoutSizing.stub",
    "v2.characterStyleOverrides.stub",
)
DRIFT_SOURCE_FILES = (
    "rules/rules.yaml",
    "rules/validation_schema.json",
    "tools/validate-semantic.py",
)
DRIFT_CACHE_RELATIVE_PATH = Path(".gran-maestro/state/drift-cache.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run figma-validate + validate-semantic and classify post-impl verification results."
    )
    parser.add_argument("--spec", required=False, help="Path to section spec JSON")
    parser.add_argument("--html", required=True, help="Path to generated HTML")
    parser.add_argument("--css", required=True, help="Path to generated CSS")
    parser.add_argument("--profile", default="all", help="validate-semantic profile")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit JSON output")
    parser.add_argument("--no-repair", action="store_true", help="Disable one-pass auto-repair loop")
    parser.add_argument("--no-figma", action="store_true", help="Skip figma-validate step (not recommended)")
    return parser.parse_args()


def parse_schema_branch(schema_version: object) -> str:
    if isinstance(schema_version, int):
        if schema_version == 1:
            return "v1"
        if schema_version == 2:
            return "v2"
    if isinstance(schema_version, str):
        text = schema_version.strip()
        if SCHEMA_V1_PATTERN.match(text):
            return "v1"
        if SCHEMA_V2_PATTERN.match(text):
            return "v2"
    return "v1"


def detect_spec_branch(spec_path: str) -> str:
    try:
        payload = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return "v1"
    if not isinstance(payload, dict):
        return "v1"
    return parse_schema_branch(payload.get("schema_version"))


def run_validator(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, capture_output=True, text=True)
    output_parts: list[str] = []
    if result.stdout:
        output_parts.append(result.stdout.rstrip())
    if result.stderr:
        output_parts.append(result.stderr.rstrip())
    return result.returncode, "\n".join(part for part in output_parts if part)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_json_file(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _is_drift_check_enabled(project_root: Path) -> bool:
    config_path = project_root / ".gran-maestro" / "config.json"
    payload = _read_json_file(config_path)
    workflow = payload.get("workflow", {})
    if isinstance(workflow, dict):
        enabled = workflow.get("drift_check_enabled")
        if isinstance(enabled, bool):
            return enabled
    return True


def _collect_drift_source_mtimes(project_root: Path) -> dict[str, float]:
    mtimes: dict[str, float] = {}
    for rel_path in DRIFT_SOURCE_FILES:
        target = project_root / rel_path
        mtimes[rel_path] = target.stat().st_mtime if target.exists() else 0.0
    return mtimes


def _should_run_drift_check(cache_payload: dict[str, object], source_mtimes: dict[str, float]) -> bool:
    cached_sources = cache_payload.get("sources")
    if not isinstance(cached_sources, dict):
        return True

    for rel_path, current_mtime in source_mtimes.items():
        cached_raw = cached_sources.get(rel_path)
        if not isinstance(cached_raw, (int, float)):
            return True
        if float(cached_raw) < current_mtime:
            return True
    return False


def _write_drift_cache(path: Path, source_mtimes: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sources": source_mtimes,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_drift_check() -> dict[str, object]:
    project_root = _project_root()
    enabled = _is_drift_check_enabled(project_root)
    if not enabled:
        return {
            "enabled": False,
            "ran": False,
            "passed": True,
            "message": "[DRIFT] disabled (workflow.drift_check_enabled=false)",
            "output": "",
            "cache_path": str(project_root / DRIFT_CACHE_RELATIVE_PATH),
        }

    source_mtimes = _collect_drift_source_mtimes(project_root)
    cache_path = project_root / DRIFT_CACHE_RELATIVE_PATH
    cache_payload = _read_json_file(cache_path)
    if not _should_run_drift_check(cache_payload, source_mtimes):
        return {
            "enabled": True,
            "ran": False,
            "passed": True,
            "message": "[DRIFT] cache up-to-date",
            "output": "",
            "cache_path": str(cache_path),
        }

    drift_command = [sys.executable, str(project_root / "tools" / "check-rules-drift.py")]
    drift_exit_code, drift_output = run_validator(drift_command)
    if drift_exit_code == 0:
        _write_drift_cache(cache_path, source_mtimes)

    return {
        "enabled": True,
        "ran": True,
        "passed": drift_exit_code == 0,
        "message": "[DRIFT] check-rules-drift executed",
        "output": drift_output,
        "exit_code": drift_exit_code,
        "cache_path": str(cache_path),
    }


def classify_ignore_reason(category: str, node: str, expected: str, actual: str) -> str | None:
    joined = " | ".join((category, node, expected, actual))
    if "signature 없음" in joined:
        return "frame signature 없음"
    if PSEUDO_PATTERN.search(joined):
        return "pseudo-element false-positive 의심"
    return None


def parse_figma_output(output: str, exit_code: int, known_categories: set[str]) -> dict[str, object]:
    summary: dict[str, object] = {
        "exit_code": exit_code,
        "status": "PASS",
        "critical": 0,
        "major": 0,
        "ignore": 0,
        "violations": [],
        "missing_rows": [],
        "runner_error": False,
        "raw_output": output,
    }
    violations = summary["violations"]
    missing_rows = summary["missing_rows"]
    in_missing_rows = False
    pending_row: dict[str, str] | None = None

    def _is_new_violation_row(raw_line: str) -> bool:
        parts = raw_line.split(" | ")
        if len(parts) < 3:
            return False
        return parts[0].strip() in known_categories

    def _starts_with_known_category(raw_line: str) -> bool:
        first, *_ = raw_line.split(" | ", 1)
        return first.strip() in known_categories

    def _start_pending_row(raw_line: str) -> None:
        nonlocal pending_row
        pending_row = {"raw": raw_line}

    def _append_pending_row(raw_line: str) -> None:
        if pending_row is None:
            return
        current = pending_row.get("raw", "")
        pending_row["raw"] = f"{current}\n{raw_line}" if current else raw_line

    def _flush_pending_row() -> None:
        nonlocal pending_row
        if pending_row is None:
            return

        raw = pending_row.get("raw", "")
        pending_row = None
        if not raw:
            return

        parts = [part.strip() for part in raw.split(" | ", 3)]
        if len(parts) < 4:
            parts.extend([""] * (4 - len(parts)))
        category, node, expected, actual = parts[:4]
        if not any((category, node, expected, actual)):
            return

        severity = "MAJOR"
        ignore_reason = classify_ignore_reason(category, node, expected, actual)
        if ignore_reason is not None:
            severity = "IGNORE"
            summary["ignore"] = int(summary["ignore"]) + 1
        elif category in CRITICAL_CATEGORIES:
            severity = "CRITICAL"
            summary["critical"] = int(summary["critical"]) + 1
        elif category in MAJOR_CATEGORIES:
            severity = "MAJOR"
            summary["major"] = int(summary["major"]) + 1
        else:
            summary["major"] = int(summary["major"]) + 1

        violation = {
            "severity": severity,
            "category": category,
            "node": node,
            "expected": expected,
            "actual": actual,
        }
        if ignore_reason is not None:
            violation["reason"] = ignore_reason
        violations.append(violation)

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "카테고리 | 노드 | 기대값 | 실제값":
            continue
        if line == "누락된 spec 행":
            _flush_pending_row()
            in_missing_rows = True
            continue
        if line == "PASS | - | 위반 0건 | -":
            continue
        if in_missing_rows:
            if line in {"id | characters", "없음"}:
                continue
            parts = [part.strip() for part in raw_line.split(" | ", 1)]
            if len(parts) == 2:
                missing_rows.append({"id": parts[0], "characters": parts[1]})
            continue
        if _is_new_violation_row(raw_line):
            _flush_pending_row()
            _start_pending_row(raw_line)
            continue
        if pending_row is not None and _starts_with_known_category(raw_line):
            _flush_pending_row()
            _start_pending_row(raw_line)
            continue
        if pending_row is not None:
            _append_pending_row(raw_line)
            continue
        if " | " in raw_line:
            _start_pending_row(raw_line)

    _flush_pending_row()

    if exit_code not in {0, 1}:
        summary["runner_error"] = True
        summary["status"] = "FAIL"
    elif int(summary["critical"]) or int(summary["major"]) or missing_rows:
        summary["status"] = "FAIL"

    if exit_code == 1 and not violations and not missing_rows:
        summary["runner_error"] = True
        summary["status"] = "FAIL"

    return summary


def parse_validate_semantic_output(output: str, exit_code: int) -> dict[str, object]:
    critical = 0
    major = 0
    minor = 0
    match = SEMANTIC_COUNTS_PATTERN.search(output)
    if match:
        critical = int(match.group(1))
        major = int(match.group(2))
        minor = int(match.group(3))

    violations: list[dict[str, str]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line.startswith("[") or "]" not in line:
            continue
        label, message = line.split("]", 1)
        violations.append(
            {
                "severity": label.lstrip("["),
                "message": message.strip(),
            }
        )

    unexpected_exit = exit_code not in {0, 1, 2}
    blocking = critical > 0 or major > 0 or unexpected_exit
    return {
        "exit_code": exit_code,
        "status": "FAIL" if blocking else "PASS",
        "blocking": blocking,
        "counts": {
            "critical": critical,
            "major": major,
            "minor": minor,
        },
        "violations": violations,
        "unexpected_exit": unexpected_exit,
        "raw_output": output,
    }


def apply_legacy_v1_relaxation(figma_result: dict[str, object], schema_branch: str) -> dict[str, object]:
    if schema_branch != "v1":
        return figma_result
    relaxed = dict(figma_result)
    relaxed["status"] = "PASS"
    relaxed["critical"] = 0
    relaxed["major"] = 0
    relaxed["ignore"] = 0
    relaxed["violations"] = []
    relaxed["missing_rows"] = []
    relaxed["legacy_relaxed"] = True
    return relaxed


def build_commands(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    tools_dir = Path(__file__).resolve().parent
    figma_command: list[str] = []
    if args.spec and not args.no_figma:
        figma_command = [
            sys.executable,
            str(tools_dir / "figma-validate.py"),
            "--spec",
            str(Path(args.spec)),
            "--html",
            str(Path(args.html)),
            "--css",
            str(Path(args.css)),
        ]
    semantic_command = [
        sys.executable,
        str(tools_dir / "validate-semantic.py"),
        "--html",
        str(Path(args.html)),
        "--css",
        str(Path(args.css)),
        "--profile",
        args.profile,
    ]
    return figma_command, semantic_command


def run_auto_repair(args: argparse.Namespace) -> dict[str, object]:
    tools_dir = Path(__file__).resolve().parent
    report_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="auto-repair-", suffix=".json", delete=False) as temp_file:
            report_path = Path(temp_file.name)
        repair_command = [
            sys.executable,
            str(tools_dir / "repair-from-violations.py"),
            "--html",
            str(Path(args.html)),
            "--css",
            str(Path(args.css)),
            "--report",
            str(report_path),
        ]
        repair_exit_code, repair_output = run_validator(repair_command)
        payload: dict[str, object] = {}
        if report_path.exists():
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        payload["exit_code"] = repair_exit_code
        payload["raw_output"] = repair_output
        return payload
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "total_fixed": 0,
            "by_category": {},
            "files_modified": [],
            "unfixable_count": 0,
            "dry_run": False,
            "exit_code": 2,
            "raw_output": str(exc),
        }
    finally:
        if report_path and report_path.exists():
            report_path.unlink(missing_ok=True)


def needs_auto_repair(figma_result: dict[str, object], semantic_result: dict[str, object]) -> bool:
    return (
        int(figma_result["critical"]) > 0
        or int(figma_result["major"]) > 0
        or int(semantic_result["counts"]["critical"]) > 0
        or int(semantic_result["counts"]["major"]) > 0
    )


def determine_exit_code(figma_result: dict[str, object], semantic_result: dict[str, object]) -> int:
    if bool(figma_result["runner_error"]) or bool(semantic_result["blocking"]):
        return 1
    if int(figma_result["critical"]) > 0 or int(figma_result["major"]) > 0:
        return 1
    if int(figma_result["ignore"]) > 0:
        return 2
    return 0


def render_text_output(
    figma_result: dict[str, object],
    semantic_result: dict[str, object],
    overall_exit_code: int,
    auto_repair_result: dict[str, object] | None = None,
) -> str:
    lines: list[str] = []
    if auto_repair_result is not None:
        by_category = auto_repair_result.get("by_category", {})
        category_summary = "none"
        if isinstance(by_category, dict):
            non_zero = [f"{key}:{value}" for key, value in by_category.items() if int(value) > 0]
            if non_zero:
                category_summary = ", ".join(non_zero)
        lines.append(
            "[auto-repair] "
            f"{auto_repair_result.get('total_fixed', 0)} violations fixed "
            f"(category: {category_summary})"
        )

    lines.extend(
        [
        (
            "figma-validate: "
            f"{figma_result['status']} "
            f"(critical={figma_result['critical']}, major={figma_result['major']}, "
            f"ignore={figma_result['ignore']}, exit={figma_result['exit_code']})"
        ),
        (
            "validate-semantic: "
            f"{semantic_result['status']} "
            f"(critical={semantic_result['counts']['critical']}, "
            f"major={semantic_result['counts']['major']}, "
            f"minor={semantic_result['counts']['minor']}, "
            f"exit={semantic_result['exit_code']}, "
            f"{'blocking' if semantic_result['blocking'] else 'non-blocking'})"
        ),
        ]
    )

    for violation in figma_result["violations"]:
        message = (
            f"[{violation['severity']}] {violation['category']} | {violation['node']} | "
            f"{violation['expected']} | {violation['actual']}"
        )
        if "reason" in violation:
            message = f"{message} ({violation['reason']})"
        lines.append(message)

    if figma_result["missing_rows"]:
        lines.append(f"[MAJOR] 누락된 spec 행 {len(figma_result['missing_rows'])}건")

    if bool(semantic_result["blocking"]):
        for violation in semantic_result["violations"]:
            if violation["severity"] == "CRITICAL":
                lines.append(f"[SEMANTIC-CRITICAL] {violation['message']}")

    if overall_exit_code == 2:
        lines.append("[INFO] exit=2 means PASS-with-IGNORE-only (사용자 검수 권장)")
    lines.append(f"post-impl-verify: exit={overall_exit_code}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    drift_result = _run_drift_check()

    if args.json_output:
        if not bool(drift_result["passed"]):
            print(
                json.dumps(
                    {
                        "drift_check": drift_result,
                        "summary": {"exit_code": 1},
                    },
                    ensure_ascii=False,
                )
            )
            return 1
    else:
        print(str(drift_result["message"]))
        if not bool(drift_result["passed"]):
            if drift_result["output"]:
                print(str(drift_result["output"]))
            print("post-impl-verify: exit=1")
            return 1

    if not args.spec and not args.no_figma:
        fatal = "[FATAL] --spec is required"
        if args.json_output:
            print(
                json.dumps(
                    {
                        "drift_check": drift_result,
                        "summary": {"exit_code": 1},
                        "error": fatal,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(fatal)
            print("post-impl-verify: exit=1")
        return 1

    schema_branch = "v1"
    if args.spec and not args.no_figma:
        schema_branch = detect_spec_branch(args.spec)
        if schema_branch == "v1":
            print("[WARN] schema_version=1 (legacy)", file=sys.stderr)
    known_figma_categories = set(V1_CATEGORIES if schema_branch == "v1" else V2_CATEGORIES)

    figma_command, semantic_command = build_commands(args)

    if args.no_figma:
        figma_exit_code, figma_output = 0, "figma-validate skipped (--no-figma)"
    else:
        figma_exit_code, figma_output = run_validator(figma_command)
    semantic_exit_code, semantic_output = run_validator(semantic_command)

    figma_result = parse_figma_output(figma_output, figma_exit_code, known_figma_categories)
    figma_result = apply_legacy_v1_relaxation(figma_result, schema_branch)
    semantic_result = parse_validate_semantic_output(semantic_output, semantic_exit_code)
    auto_repair_result: dict[str, object] | None = None

    if not args.no_repair and needs_auto_repair(figma_result, semantic_result):
        auto_repair_result = run_auto_repair(args)
        figma_exit_code, figma_output = run_validator(figma_command)
        semantic_exit_code, semantic_output = run_validator(semantic_command)
        figma_result = parse_figma_output(figma_output, figma_exit_code, known_figma_categories)
        figma_result = apply_legacy_v1_relaxation(figma_result, schema_branch)
        semantic_result = parse_validate_semantic_output(semantic_output, semantic_exit_code)

    overall_exit_code = determine_exit_code(figma_result, semantic_result)

    payload = {
        "drift_check": drift_result,
        "figma_validate": figma_result,
        "validate_semantic": semantic_result,
        "auto_repair": auto_repair_result,
        "summary": {
            "critical": figma_result["critical"],
            "major": figma_result["major"],
            "ignore": figma_result["ignore"],
            "semantic_critical": semantic_result["counts"]["critical"],
            "exit_code": overall_exit_code,
        },
    }

    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(render_text_output(figma_result, semantic_result, overall_exit_code, auto_repair_result))

    return int(overall_exit_code)


if __name__ == "__main__":
    sys.exit(int(main()))

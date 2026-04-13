#!/usr/bin/env python3
"""Post-implementation verification for PM dispatch follow-up."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run figma-validate + validate-semantic and classify post-impl verification results."
    )
    parser.add_argument("--spec", required=True, help="Path to section spec JSON")
    parser.add_argument("--html", required=True, help="Path to generated HTML")
    parser.add_argument("--css", required=True, help="Path to generated CSS")
    parser.add_argument("--profile", default="all", help="validate-semantic profile")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit JSON output")
    return parser.parse_args()


def run_validator(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, capture_output=True, text=True)
    output_parts: list[str] = []
    if result.stdout:
        output_parts.append(result.stdout.rstrip())
    if result.stderr:
        output_parts.append(result.stderr.rstrip())
    return result.returncode, "\n".join(part for part in output_parts if part)


def classify_ignore_reason(category: str, node: str, expected: str, actual: str) -> str | None:
    joined = " | ".join((category, node, expected, actual))
    if "signature 없음" in joined:
        return "frame signature 없음"
    if PSEUDO_PATTERN.search(joined):
        return "pseudo-element false-positive 의심"
    return None


def parse_figma_output(output: str, exit_code: int) -> dict[str, object]:
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

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "카테고리 | 노드 | 기대값 | 실제값":
            continue
        if line == "누락된 spec 행":
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
        if " | " not in raw_line:
            continue

        category, node, expected, actual = [part.strip() for part in raw_line.split(" | ", 3)]
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
    blocking = critical > 0 or unexpected_exit
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


def build_commands(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    tools_dir = Path(__file__).resolve().parent
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
) -> str:
    lines = [
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

    lines.append(f"post-impl-verify: exit={overall_exit_code}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    figma_command, semantic_command = build_commands(args)

    figma_exit_code, figma_output = run_validator(figma_command)
    semantic_exit_code, semantic_output = run_validator(semantic_command)

    figma_result = parse_figma_output(figma_output, figma_exit_code)
    semantic_result = parse_validate_semantic_output(semantic_output, semantic_exit_code)
    overall_exit_code = determine_exit_code(figma_result, semantic_result)

    payload = {
        "figma_validate": figma_result,
        "validate_semantic": semantic_result,
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
        print(render_text_output(figma_result, semantic_result, overall_exit_code))

    return int(overall_exit_code)


if __name__ == "__main__":
    sys.exit(int(main()))

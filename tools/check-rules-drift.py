#!/usr/bin/env python3
"""Check rule drift across rules.yaml, validation_schema.json, and validate-semantic handlers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import yaml


EXPECTED_SUMMARIES = {
    "vertical_frame_itemspacing_uses_margin_bottom": "Figma VERTICAL frame 의 itemSpacing > 0 은 자식 요소의 margin-bottom 으로 변환한다. column flex gap / row-gap 사용 금지.",
    "no_constraints_to_position_absolute_mapping": "Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다.",
    "figma_rules_conflict_uses_meta_marker": "Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지).",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate drift across rule sources.")
    parser.add_argument("--policy-ids", nargs="+", help="Legacy policy-only mode (REQ-029 compatibility)")
    parser.add_argument("--all-rules", action="store_true", help="Check all rule IDs across 3 sources")
    parser.add_argument("--rules-yaml", default="rules/rules.yaml")
    parser.add_argument("--validation-schema", default="rules/validation_schema.json")
    parser.add_argument(
        "--semantic-validator",
        default="tools/validate-semantic.py",
        help="Path to validate-semantic.py for handler/type coverage checks",
    )
    parser.add_argument(
        "--validator",
        default="tools/figma-validate.py",
        help="Path to figma-validate.py for legacy --policy-ids mode",
    )
    args = parser.parse_args()
    if not args.policy_ids and not args.all_rules:
        args.all_rules = True
    return args


def load_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def load_rules_yaml(path: str) -> list[dict]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    rules = payload.get("rules", []) if isinstance(payload, dict) else []
    return [rule for rule in rules if isinstance(rule, dict)]


def load_validation_schema(path: str) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rules = payload.get("rules", []) if isinstance(payload, dict) else []
    return [rule for rule in rules if isinstance(rule, dict)]


def _rule_map_by_id(rules: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for rule in rules:
        rule_id = str(rule.get("id", "")).strip()
        if not rule_id:
            continue
        result[rule_id] = rule
    return result


def _parse_validator_keys(text: str, mapping_name: str) -> set[str]:
    block = re.search(rf"{mapping_name}\s*=\s*\{{(.*?)\n\}}", text, flags=re.S)
    if not block:
        return set()
    return {key for key in re.findall(r'"([^"]+)"\s*:', block.group(1))}


def _parse_validate_semantic_capabilities(path: str) -> tuple[set[str], set[str]]:
    text = load_text(path)
    custom_handlers = _parse_validator_keys(text, "CUSTOM_HANDLERS: Dict\\[str, Callable\\]")
    enum_validators = _parse_validator_keys(text, "ENUM_VALIDATORS: Dict\\[str, Callable\\]")
    if not custom_handlers:
        # fallback for small formatting differences
        custom_handlers = _parse_validator_keys(text, "CUSTOM_HANDLERS")
    if not enum_validators:
        enum_validators = _parse_validator_keys(text, "ENUM_VALIDATORS")
    return custom_handlers, enum_validators


def _policy_rule_entry(rules: list[dict], rule_id: str) -> tuple[str, str] | None:
    for rule in rules:
        if rule.get("id") != rule_id:
            continue
        validation = rule.get("validation", {}) if isinstance(rule.get("validation"), dict) else {}
        return str(rule.get("description", "")), str(validation.get("custom_handler", ""))
    return None


def _schema_rule_entry(rules: list[dict], rule_id: str) -> tuple[str, str] | None:
    for rule in rules:
        if rule.get("id") != rule_id:
            continue
        return str(rule.get("description", "")), str(rule.get("custom_handler", ""))
    return None


def _validator_policy_maps(text: str) -> tuple[dict[str, str], dict[str, str]]:
    summaries: dict[str, str] = {}
    handlers: dict[str, str] = {}
    summary_block = re.search(r"POLICY_RULE_SUMMARIES\s*=\s*\{(.*?)\n\}", text, flags=re.S)
    if summary_block:
        for key, value in re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', summary_block.group(1)):
            summaries[key] = value
    handler_block = re.search(r"POLICY_HANDLER_MAP\s*=\s*\{(.*?)\n\}", text, flags=re.S)
    if handler_block:
        for key, value in re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', handler_block.group(1)):
            handlers[key] = value
    return summaries, handlers


def _handler_exists(text: str, handler_name: str) -> bool:
    return re.search(rf"^def\s+{re.escape(handler_name)}\s*\(", text, flags=re.M) is not None


def run_policy_mode(args: argparse.Namespace) -> int:
    rules_yaml = load_rules_yaml(args.rules_yaml)
    schema_rules = load_validation_schema(args.validation_schema)
    validator_text = load_text(args.validator)
    validator_summaries, validator_handlers = _validator_policy_maps(validator_text)

    failures: list[str] = []
    for rule_id in args.policy_ids or []:
        expected_summary = EXPECTED_SUMMARIES.get(rule_id)
        if expected_summary is None:
            failures.append(f"{rule_id}: no expected summary registered in checker")
            continue

        rules_entry = _policy_rule_entry(rules_yaml, rule_id)
        if rules_entry is None:
            failures.append(f"{rule_id}: missing in rules.yaml")
            continue
        rules_summary, rules_handler = rules_entry

        schema_entry = _schema_rule_entry(schema_rules, rule_id)
        if schema_entry is None:
            failures.append(f"{rule_id}: missing in validation_schema.json")
            continue
        schema_summary, schema_handler = schema_entry

        validator_summary = validator_summaries.get(rule_id)
        validator_handler = validator_handlers.get(rule_id)

        if rules_summary != expected_summary:
            failures.append(f"{rule_id}: rules.yaml summary mismatch")
        if schema_summary != expected_summary:
            failures.append(f"{rule_id}: validation_schema.json summary mismatch")
        if validator_summary != expected_summary:
            failures.append(f"{rule_id}: figma-validate POLICY_RULE_SUMMARIES mismatch")

        if not rules_handler:
            failures.append(f"{rule_id}: rules.yaml custom_handler missing")
        if not schema_handler:
            failures.append(f"{rule_id}: validation_schema.json custom_handler missing")
        if not validator_handler:
            failures.append(f"{rule_id}: figma-validate POLICY_HANDLER_MAP missing")

        if rules_handler and schema_handler and rules_handler != schema_handler:
            failures.append(f"{rule_id}: handler mismatch rules.yaml vs validation_schema.json")
        if rules_handler and validator_handler and rules_handler != validator_handler:
            failures.append(f"{rule_id}: handler mismatch rules.yaml vs figma-validate")
        if validator_handler and not _handler_exists(validator_text, validator_handler):
            failures.append(f"{rule_id}: handler function not found in figma-validate ({validator_handler})")

    if failures:
        for item in failures:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1

    for rule_id in args.policy_ids or []:
        print(f"[OK] {rule_id}")
    return 0


def run_all_rules_mode(args: argparse.Namespace) -> int:
    rules_yaml = load_rules_yaml(args.rules_yaml)
    schema_rules = load_validation_schema(args.validation_schema)
    custom_handlers, enum_validators = _parse_validate_semantic_capabilities(args.semantic_validator)

    rules_by_id = _rule_map_by_id(rules_yaml)
    schema_by_id = _rule_map_by_id(schema_rules)
    all_rule_ids = sorted(set(rules_by_id) | set(schema_by_id))

    drifts: list[str] = []
    for rule_id in all_rule_ids:
        in_rules = rule_id in rules_by_id
        in_schema = rule_id in schema_by_id
        if not in_rules:
            drifts.append(f"{rule_id}: missing in rules.yaml")
            continue
        if not in_schema:
            drifts.append(f"{rule_id}: missing in validation_schema.json")
            continue

        rules_rule = rules_by_id[rule_id]
        schema_rule = schema_by_id[rule_id]
        rules_validation = rules_rule.get("validation", {}) if isinstance(rules_rule.get("validation"), dict) else {}
        rules_type = str(rules_validation.get("type", "")).strip()
        schema_type = str(schema_rule.get("type", "")).strip()

        if rules_type != schema_type:
            drifts.append(f"{rule_id}: validation type mismatch rules.yaml({rules_type}) vs validation_schema.json({schema_type})")
            continue

        if rules_type == "custom":
            rules_handler = str(rules_validation.get("custom_handler", "")).strip()
            schema_handler = str(schema_rule.get("custom_handler", "")).strip()
            if not rules_handler:
                drifts.append(f"{rule_id}: missing in rules.yaml custom_handler")
                continue
            if not schema_handler:
                drifts.append(f"{rule_id}: missing in validation_schema.json custom_handler")
                continue
            if rules_handler != schema_handler:
                drifts.append(f"{rule_id}: handler mismatch rules.yaml({rules_handler}) vs validation_schema.json({schema_handler})")
                continue
            if rules_handler not in custom_handlers:
                drifts.append(f"{rule_id}: missing in validate-semantic.py handler map ({rules_handler})")
                continue
        else:
            if rules_type not in enum_validators:
                drifts.append(f"{rule_id}: missing in validate-semantic.py enum validators ({rules_type})")

    if drifts:
        for item in drifts:
            print(f"[DRIFT] {item}")
        return 1

    total = len(all_rule_ids)
    print(f"[OK] {total}/{total} rules in sync")
    return 0


def main() -> int:
    args = parse_args()
    if args.all_rules:
        return run_all_rules_mode(args)
    if args.policy_ids:
        return run_policy_mode(args)
    print("[DRIFT] no mode selected", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check policy rule drift across rules.yaml, validation_schema.json, and figma-validate handlers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


EXPECTED_SUMMARIES = {
    "vertical_frame_itemspacing_uses_margin_bottom": "Figma VERTICAL frame 의 itemSpacing > 0 은 자식 요소의 margin-bottom 으로 변환한다. column flex gap / row-gap 사용 금지.",
    "no_constraints_to_position_absolute_mapping": "Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다.",
    "figma_rules_conflict_uses_meta_marker": "Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지).",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate policy drift across rule sources.")
    parser.add_argument("--policy-ids", nargs="+", required=True, help="Policy IDs to verify")
    parser.add_argument("--rules-yaml", default="rules/rules.yaml")
    parser.add_argument("--validation-schema", default="rules/validation_schema.json")
    parser.add_argument("--validator", default="tools/figma-validate.py")
    return parser.parse_args()


def load_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def rules_yaml_entry(text: str, rule_id: str) -> tuple[str, str] | None:
    lines = text.splitlines()
    start_index = None
    id_pattern = re.compile(rf"^\s*-\s*id:\s*{re.escape(rule_id)}\s*$")
    for index, line in enumerate(lines):
        if id_pattern.match(line.strip()):
            start_index = index
            break
        if id_pattern.match(line):
            start_index = index
            break
    if start_index is None:
        return None
    end_index = len(lines)
    next_rule_pattern = re.compile(r"^\s*-\s*id:\s*[a-zA-Z0-9_]+\s*$")
    for index in range(start_index + 1, len(lines)):
        if next_rule_pattern.match(lines[index]):
            end_index = index
            break
    block = "\n".join(lines[start_index:end_index])
    desc_match = re.search(r'^\s*description:\s*"(.*)"\s*$', block, flags=re.M)
    handler_match = re.search(r"^\s*custom_handler:\s*([a-zA-Z0-9_]+)\s*$", block, flags=re.M)
    description = desc_match.group(1) if desc_match else ""
    handler = handler_match.group(1) if handler_match else ""
    return description, handler


def validation_schema_entry(path: str, rule_id: str) -> tuple[str, str] | None:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        return None
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if rule.get("id") != rule_id:
            continue
        description = str(rule.get("description", ""))
        handler = str(rule.get("custom_handler", ""))
        return description, handler
    return None


def validator_policy_maps(text: str) -> tuple[dict[str, str], dict[str, str]]:
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


def handler_exists(text: str, handler_name: str) -> bool:
    return re.search(rf"^def\s+{re.escape(handler_name)}\s*\(", text, flags=re.M) is not None


def main() -> int:
    args = parse_args()
    rules_yaml_text = load_text(args.rules_yaml)
    validator_text = load_text(args.validator)
    validator_summaries, validator_handlers = validator_policy_maps(validator_text)

    failures: list[str] = []
    for rule_id in args.policy_ids:
        expected_summary = EXPECTED_SUMMARIES.get(rule_id)
        if expected_summary is None:
            failures.append(f"{rule_id}: no expected summary registered in checker")
            continue

        rules_entry = rules_yaml_entry(rules_yaml_text, rule_id)
        if rules_entry is None:
            failures.append(f"{rule_id}: missing in rules.yaml")
            continue
        rules_summary, rules_handler = rules_entry

        schema_entry = validation_schema_entry(args.validation_schema, rule_id)
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
        if validator_handler and not handler_exists(validator_text, validator_handler):
            failures.append(f"{rule_id}: handler function not found in figma-validate ({validator_handler})")

    if failures:
        for item in failures:
            print(f"[FAIL] {item}", file=sys.stderr)
        return 1

    for rule_id in args.policy_ids:
        print(f"[OK] {rule_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check rule drift across Pydantic rules, generated schema, and figma handlers."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rules.models import RuleDefinition, generate_schema, load_rules


EXPECTED_SUMMARIES = {
    "vertical_frame_itemspacing_uses_margin_bottom": "Figma VERTICAL frame 의 itemSpacing > 0 은 자식 요소의 margin-bottom 으로 변환한다. column flex gap / row-gap 사용 금지.",
    "no_constraints_to_position_absolute_mapping": "Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다.",
    "figma_rules_conflict_uses_meta_marker": "Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지).",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate drift across rule sources.")
    parser.add_argument("--policy-ids", nargs="+", help="Legacy policy-only mode (REQ-029 compatibility)")
    parser.add_argument(
        "--all",
        "--all-rules",
        dest="all_rules",
        action="store_true",
        help="Check all rule IDs across 3 sources",
    )
    parser.add_argument("--rules-yaml", default="rules/rules.yaml")
    parser.add_argument("--validation-schema", default="rules/validation_schema.json")
    parser.add_argument(
        "--semantic-validator",
        default="tools/validate-semantic.py",
        help="Accepted for REQ-033 compatibility; all-rule drift now uses figma-validate.py",
    )
    parser.add_argument(
        "--validator",
        default="tools/figma-validate.py",
        help="Path to figma-validate.py for handler registry checks",
    )
    args = parser.parse_args()
    if not args.policy_ids and not args.all_rules:
        args.all_rules = True
    return args


def load_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _read_yaml(path: str) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: YAML root must be a mapping")
    return payload


def _read_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: JSON root must be a mapping")
    return payload


def load_rules_yaml(path: str) -> list[dict[str, Any]]:
    payload = _read_yaml(path)
    rules = payload.get("rules", [])
    return [rule for rule in rules if isinstance(rule, dict)] if isinstance(rules, list) else []


def load_validation_schema(path: str) -> list[dict[str, Any]]:
    payload = _read_json(path)
    rules = payload.get("rules", [])
    return [rule for rule in rules if isinstance(rule, dict)] if isinstance(rules, list) else []


def _rule_map_by_id(rules: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for rule in rules:
        rule_id = str(rule.get("id", "")).strip()
        if rule_id:
            result[rule_id] = rule
    return result


def _pydantic_rule_map(rules: list[RuleDefinition]) -> dict[str, RuleDefinition]:
    return {rule.id: rule for rule in rules}


def _canonical_hash(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _rule_dump(rule: RuleDefinition) -> dict[str, Any]:
    return rule.model_dump(mode="json", by_alias=True, exclude_none=True)


def _flatten_yaml_rule(raw_rule: dict[str, Any]) -> dict[str, Any]:
    validation = raw_rule.get("validation")
    validation_map = validation if isinstance(validation, dict) else {}
    flattened = {
        "applies_to": raw_rule.get("applies_to"),
        "category": raw_rule.get("category"),
        "description": raw_rule.get("description"),
        "id": raw_rule.get("id"),
        "severity": raw_rule.get("severity"),
        "target": validation_map.get("target"),
        "type": validation_map.get("type"),
        "pattern": validation_map.get("pattern"),
        "custom_handler": validation_map.get("custom_handler"),
        "selector": validation_map.get("selector"),
        "priority": raw_rule.get("priority"),
        "rationale": raw_rule.get("rationale"),
        "examples": raw_rule.get("examples"),
    }
    canonical = {key: value for key, value in flattened.items() if value is not None}
    if "selector" not in canonical:
        custom_handler = canonical.get("custom_handler")
        validation_type = canonical.get("type")
        if custom_handler:
            canonical["selector"] = f"custom:{custom_handler}"
        elif validation_type and "pattern" not in canonical:
            canonical["selector"] = f"type:{validation_type}"
    return canonical


def _canonical_rule_list_hash(rule_map: dict[str, dict[str, Any]]) -> str:
    return _canonical_hash([rule_map[rule_id] for rule_id in sorted(rule_map)])


def _parse_validator_keys(text: str, mapping_name: str) -> set[str]:
    block = re.search(rf"{mapping_name}\s*=\s*\{{(.*?)\n\}}", text, flags=re.S)
    if not block:
        return set()
    return {key for key in re.findall(r'"([^"]+)"\s*:', block.group(1))}


def _policy_rule_entry(rules: list[dict[str, Any]], rule_id: str) -> tuple[str, str] | None:
    for rule in rules:
        if rule.get("id") != rule_id:
            continue
        validation = rule.get("validation", {}) if isinstance(rule.get("validation"), dict) else {}
        return str(rule.get("description", "")), str(validation.get("custom_handler", ""))
    return None


def _schema_rule_entry(rules: list[dict[str, Any]], rule_id: str) -> tuple[str, str] | None:
    for rule in rules:
        if rule.get("id") == rule_id:
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


def _load_figma_validate_module(path: str) -> ModuleType:
    module_path = Path(path)
    spec = importlib.util.spec_from_file_location("figma_validate_drift_check", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load figma validator module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _figma_handler_registry(path: str) -> dict[str, Any]:
    module = _load_figma_validate_module(path)
    registry = getattr(module, "RULE_HANDLER_REGISTRY", None)
    if not isinstance(registry, dict):
        raise RuntimeError("figma-validate.py does not expose RULE_HANDLER_REGISTRY")
    return dict(registry)


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
    try:
        pydantic_by_id = _pydantic_rule_map(load_rules())
        yaml_by_id = {
            rule_id: _flatten_yaml_rule(rule)
            for rule_id, rule in _rule_map_by_id(load_rules_yaml(args.rules_yaml)).items()
        }
        schema_payload = _read_json(args.validation_schema)
        schema_by_id = _rule_map_by_id(load_validation_schema(args.validation_schema))
        generated_schema = generate_schema()
        figma_handlers = _figma_handler_registry(args.validator)
    except Exception as exc:  # noqa: BLE001
        print(f"[DRIFT] failed to load rule sources: {exc}")
        return 1

    pydantic_canonical = {rule_id: _rule_dump(rule) for rule_id, rule in pydantic_by_id.items()}
    generated_rules_by_id = _rule_map_by_id(generated_schema.get("rules", []))
    figma_handler_ids = {str(rule_id) for rule_id in figma_handlers}

    drifts: list[str] = []
    all_rule_ids = sorted(set(pydantic_by_id) | set(yaml_by_id) | set(schema_by_id) | figma_handler_ids)
    layers = (
        ("Pydantic SSOT", set(pydantic_by_id)),
        ("rules.yaml", set(yaml_by_id)),
        ("validation_schema.json", set(schema_by_id)),
        ("figma-validate handler registry", figma_handler_ids),
    )

    for rule_id in all_rule_ids:
        missing_layers = [name for name, ids in layers if rule_id not in ids]
        if missing_layers:
            drifts.append(f"{rule_id}: missing in {', '.join(missing_layers)}")

    for rule_id in sorted(pydantic_by_id):
        expected = pydantic_canonical[rule_id]
        yaml_rule = yaml_by_id.get(rule_id)
        schema_rule = schema_by_id.get(rule_id)
        generated_rule = generated_rules_by_id.get(rule_id)

        if yaml_rule is not None and _canonical_hash(yaml_rule) != _canonical_hash(expected):
            drifts.append(
                f"{rule_id}: rules.yaml normalized hash mismatch "
                f"rules.yaml({_canonical_hash(yaml_rule)[:12]}) vs Pydantic({_canonical_hash(expected)[:12]})"
            )
        if schema_rule is not None and _canonical_hash(schema_rule) != _canonical_hash(expected):
            drifts.append(
                f"{rule_id}: validation_schema.json rule hash mismatch "
                f"schema({_canonical_hash(schema_rule)[:12]}) vs Pydantic({_canonical_hash(expected)[:12]})"
            )
        if (
            generated_rule is not None
            and schema_rule is not None
            and _canonical_hash(generated_rule) != _canonical_hash(schema_rule)
        ):
            drifts.append(
                f"{rule_id}: generated schema rule hash mismatch "
                f"generated({_canonical_hash(generated_rule)[:12]}) vs file({_canonical_hash(schema_rule)[:12]})"
            )

    if _canonical_hash(schema_payload) != _canonical_hash(generated_schema):
        drifts.append(
            "validation_schema.json: file hash mismatch "
            f"generated({_canonical_hash(generated_schema)[:12]}) vs file({_canonical_hash(schema_payload)[:12]})"
        )

    non_callables = sorted(rule_id for rule_id, handler in figma_handlers.items() if not callable(handler))
    for rule_id in non_callables:
        drifts.append(f"{rule_id}: figma-validate handler registry entry is not callable")

    if drifts:
        for item in drifts:
            print(f"[DRIFT] {item}")
        print(
            "[DRIFT] source hashes "
            f"rules.yaml={_canonical_rule_list_hash(yaml_by_id)[:12]} "
            f"validation_schema.json={_canonical_rule_list_hash(schema_by_id)[:12]} "
            f"generated_schema={_canonical_hash(generated_schema)[:12]}"
        )
        return 1

    total = len(pydantic_by_id)
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

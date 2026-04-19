from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SEMANTIC = ROOT / "tools" / "validate-semantic.py"
RULES_YAML = ROOT / "rules" / "rules.yaml"
VALIDATION_SCHEMA = ROOT / "rules" / "validation_schema.json"


def _load_validate_semantic_module():
    spec = importlib.util.spec_from_file_location("validate_semantic_req033_clarity", VALIDATE_SEMANTIC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _find_rule_in_yaml(rule_id: str) -> dict:
    payload = yaml.safe_load(RULES_YAML.read_text(encoding="utf-8"))
    rules = payload.get("rules", []) if isinstance(payload, dict) else []
    for rule in rules:
        if isinstance(rule, dict) and rule.get("id") == rule_id:
            return rule
    raise AssertionError(f"rule not found in rules.yaml: {rule_id}")


def _find_rule_in_schema(rule_id: str) -> dict:
    payload = json.loads(VALIDATION_SCHEMA.read_text(encoding="utf-8"))
    rules = payload.get("rules", []) if isinstance(payload, dict) else []
    for rule in rules:
        if isinstance(rule, dict) and rule.get("id") == rule_id:
            return rule
    raise AssertionError(f"rule not found in validation_schema.json: {rule_id}")


def _run_meaningful_page_name(module, tmp_path: Path, *, filename: str, html_body: str):
    html_path = tmp_path / filename
    css_path = tmp_path / "common.css"

    html_path.write_text(
        f"<!doctype html><html><head><meta charset='utf-8'><title>T</title></head><body>{html_body}</body></html>\n",
        encoding="utf-8",
    )
    css_path.write_text(".root { display: block; }\n", encoding="utf-8")

    results = module.run_validation(
        str(RULES_YAML),
        str(html_path),
        str(css_path),
        profile="all",
    )

    for result in results:
        if result.rule_id == "meaningful_page_name":
            return result
    raise AssertionError("meaningful_page_name result missing")


def test_meaningful_page_name_description_mentions_filename_and_body() -> None:
    yaml_rule = _find_rule_in_yaml("meaningful_page_name")
    schema_rule = _find_rule_in_schema("meaningful_page_name")

    for rule in (yaml_rule, schema_rule):
        description = str(rule.get("description", ""))
        assert "파일명" in description
        assert "본문" in description
        assert "page_1" in description
        assert "sub_01" in description


def test_meaningful_page_name_fails_for_mechanical_filename_and_body(tmp_path: Path) -> None:
    module = _load_validate_semantic_module()

    filename_fail = _run_meaningful_page_name(
        module,
        tmp_path,
        filename="page_1.html",
        html_body="<main class='greeting products'>Hello</main>",
    )
    assert filename_fail.passed is False
    assert "forbidden pattern matched in filename" in filename_fail.message

    body_fail = _run_meaningful_page_name(
        module,
        tmp_path,
        filename="greeting.html",
        html_body="<main class='sub_01'>Hello</main>",
    )
    assert body_fail.passed is False
    assert "forbidden pattern matched" in body_fail.message


def test_meaningful_page_name_passes_for_meaningful_english_names(tmp_path: Path) -> None:
    module = _load_validate_semantic_module()

    result = _run_meaningful_page_name(
        module,
        tmp_path,
        filename="greeting.html",
        html_body="<main class='greeting products'>Hello products page</main>",
    )

    assert result.passed is True

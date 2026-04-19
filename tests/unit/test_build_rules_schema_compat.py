from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD_RULES_PATH = ROOT / "tools" / "build-rules.py"


def _load_build_rules_module():
    spec = importlib.util.spec_from_file_location("build_rules", BUILD_RULES_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_normalize_schema_version_accepts_integer() -> None:
    build_rules = _load_build_rules_module()
    assert build_rules.normalize_schema_version(1) == 1


def test_normalize_schema_version_accepts_semver_string() -> None:
    build_rules = _load_build_rules_module()
    assert build_rules.normalize_schema_version("2.0.0") == "2.0.0"


def test_build_validation_schema_keeps_integer_schema_version() -> None:
    build_rules = _load_build_rules_module()
    rendered = build_rules.build_validation_schema({"schema_version": 1}, [])
    payload = json.loads(rendered)
    assert payload["version"] == 1


def test_build_validation_schema_keeps_string_schema_version() -> None:
    build_rules = _load_build_rules_module()
    rendered = build_rules.build_validation_schema({"schema_version": "2.0.0"}, [])
    payload = json.loads(rendered)
    assert payload["version"] == "2.0.0"

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from types import UnionType
from typing import Any, get_args, get_origin, get_type_hints

import yaml

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator
except ModuleNotFoundError:
    _MISSING = object()

    class ValidationInfo:
        def __init__(self, context: dict[str, Any] | None = None) -> None:
            self.context = context

    class _FallbackField:
        def __init__(self, default: Any = _MISSING, *, alias: str | None = None) -> None:
            self.default = default
            self.alias = alias

    def Field(default: Any = _MISSING, *, alias: str | None = None) -> _FallbackField:
        return _FallbackField(default, alias=alias)

    def ConfigDict(**kwargs: Any) -> dict[str, Any]:
        return dict(kwargs)

    def field_validator(*_fields: str, **_kwargs: Any) -> Callable[[Any], Any]:
        def decorate(func: Any) -> Any:
            return func

        return decorate

    def model_validator(**_kwargs: Any) -> Callable[[Any], Any]:
        def decorate(func: Any) -> Any:
            return func

        return decorate

    def _coerce_value(hint: Any, value: Any) -> Any:
        if value is None:
            return None

        origin = get_origin(hint)
        args = get_args(hint)
        if origin is list and args:
            return [_coerce_value(args[0], item) for item in value]
        if origin is dict and len(args) == 2:
            return {
                _coerce_value(args[0], key): _coerce_value(args[1], item)
                for key, item in value.items()
            }
        if origin in {UnionType, type(None)} or str(origin) == "typing.Union":
            for option in args:
                if option is type(None):
                    continue
                try:
                    return _coerce_value(option, value)
                except Exception:
                    continue
            return value
        if isinstance(hint, UnionType):
            for option in args:
                if option is type(None):
                    continue
                try:
                    return _coerce_value(option, value)
                except Exception:
                    continue
            return value
        if isinstance(hint, type) and issubclass(hint, Enum):
            return value if isinstance(value, hint) else hint(value)
        if isinstance(hint, type) and issubclass(hint, BaseModel) and isinstance(value, dict):
            return hint(**value)
        return value

    def _dump_value(value: Any, *, by_alias: bool, exclude_none: bool) -> Any:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json", by_alias=by_alias, exclude_none=exclude_none)
        if isinstance(value, list):
            return [_dump_value(item, by_alias=by_alias, exclude_none=exclude_none) for item in value]
        if isinstance(value, dict):
            return {
                key: _dump_value(item, by_alias=by_alias, exclude_none=exclude_none)
                for key, item in value.items()
                if item is not None or not exclude_none
            }
        return value

    class BaseModel:
        def __init__(self, **data: Any) -> None:
            context = data.pop("_context", None)
            hints = get_type_hints(type(self))
            for name, hint in hints.items():
                field = type(self).__dict__.get(name, _MISSING)
                alias = field.alias if isinstance(field, _FallbackField) else None
                default = field.default if isinstance(field, _FallbackField) else field
                has_value = name in data or (alias is not None and alias in data)
                if has_value:
                    raw_value = data[name] if name in data else data[alias]
                elif default is not _MISSING:
                    raw_value = default
                else:
                    raise ValueError(f"missing required field: {name}")
                setattr(self, name, _coerce_value(hint, raw_value))

            fallback_validate = getattr(self, "_fallback_validate", None)
            if fallback_validate is not None:
                fallback_validate(context)

        @classmethod
        def model_validate(cls, data: dict[str, Any], context: dict[str, Any] | None = None) -> Any:
            return cls(_context=context, **data)

        @classmethod
        def model_json_schema(cls, *, by_alias: bool = True, **_kwargs: Any) -> dict[str, Any]:
            properties: dict[str, Any] = {}
            required: list[str] = []
            for name in get_type_hints(cls):
                field = cls.__dict__.get(name, _MISSING)
                alias = field.alias if isinstance(field, _FallbackField) else None
                key = alias if by_alias and alias else name
                properties[key] = {}
                default = field.default if isinstance(field, _FallbackField) else field
                if default is _MISSING:
                    required.append(key)
            return {
                "title": cls.__name__,
                "type": "object",
                "properties": properties,
                "required": required,
            }

        def model_dump(
            self,
            *,
            mode: str = "python",
            by_alias: bool = False,
            exclude_none: bool = False,
        ) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for name in get_type_hints(type(self)):
                value = getattr(self, name)
                if value is None and exclude_none:
                    continue
                field = type(self).__dict__.get(name, _MISSING)
                alias = field.alias if isinstance(field, _FallbackField) else None
                key = alias if by_alias and alias else name
                result[key] = _dump_value(value, by_alias=by_alias, exclude_none=exclude_none)
            return result


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_PATH = ROOT / "rules" / "rules.yaml"
DEFAULT_SCHEMA_PATH = ROOT / "rules" / "validation_schema.json"
EXPECTED_RULE_COUNT = 65
AUTO_GENERATED_COMMENT = "AUTO-GENERATED FROM rules/models.py — DO NOT EDIT"


class ValidationType(str, Enum):
    REGEX_MUST_NOT_MATCH = "regex_must_not_match"
    REGEX_MUST_MATCH = "regex_must_match"
    REGEX_SHOULD_MATCH = "regex_should_match"
    AST_SELECTOR_COUNT = "ast_selector_count"
    VALUE_EQUALS_MAPPING = "value_equals_mapping"
    HTML_TAG_REQUIRED = "html_tag_required"
    FORBIDDEN_SUBSTRING = "forbidden_substring"
    REQUIRED_SUBSTRING = "required_substring"
    NAMING_PATTERN = "naming_pattern"
    NUMERIC_RANGE = "numeric_range"
    CUSTOM = "custom"


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEPRECATED = "deprecated"


class Profile(str, Enum):
    COMMON = "common"
    BASIC = "basic"
    LANDING = "landing"
    FIGMA = "figma"
    ENHANCEMENT = "enhancement"


class ValidationTarget(str, Enum):
    CSS = "css"
    HTML = "html"
    SPEC = "spec"
    JSON = "json"
    TEXT = "text"


class CategoryDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str | None = None

    def _fallback_validate(self, _context: dict[str, Any] | None = None) -> None:
        self.id = self.id_must_not_be_empty(self.id)

    @field_validator("id")
    @classmethod
    def id_must_not_be_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("category id must not be empty")
        return value


class RuleDefinition(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    profiles: list[Profile] = Field(alias="applies_to")
    category: str
    message: str = Field(alias="description")
    id: str
    severity: Severity
    target: ValidationTarget
    type: ValidationType
    pattern: str | None = None
    custom_handler: str | None = None
    selector: str | None = None
    priority: int | None = None
    rationale: str | None = None
    examples: dict[str, str] | None = None

    def _fallback_validate(self, context: dict[str, Any] | None = None) -> None:
        info = ValidationInfo(context)
        self.id = self.required_text_must_not_be_empty(self.id)
        self.category = self.required_text_must_not_be_empty(self.category)
        self.message = self.required_text_must_not_be_empty(self.message)
        self.category = self.category_must_exist_in_yaml(self.category, info)
        self.profiles = self.profiles_must_not_be_empty(self.profiles)
        self.validate_handler_contract()

    @field_validator("id", "category", "message", mode="before")
    @classmethod
    def required_text_must_not_be_empty(cls, value: Any) -> Any:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("required text field must not be empty")
        return value.strip()

    @field_validator("category")
    @classmethod
    def category_must_exist_in_yaml(cls, value: str, info: ValidationInfo) -> str:
        categories = None
        if isinstance(info.context, dict):
            categories = info.context.get("categories")
        if categories and value not in categories:
            raise ValueError(f"unknown category: {value}")
        return value

    @field_validator("profiles")
    @classmethod
    def profiles_must_not_be_empty(cls, value: list[Profile]) -> list[Profile]:
        if not value:
            raise ValueError("applies_to must include at least one profile")
        return value

    @model_validator(mode="after")
    def validate_handler_contract(self) -> RuleDefinition:
        if self.type is ValidationType.CUSTOM and not self.custom_handler:
            raise ValueError("custom validation rule requires custom_handler")
        if self.type is not ValidationType.CUSTOM and self.custom_handler:
            raise ValueError("custom_handler is only valid for custom validation rules")
        if self.selector is None and self.custom_handler:
            self.selector = f"custom:{self.custom_handler}"
        if self.selector is None and self.pattern is None:
            self.selector = f"type:{self.type.value}"
        return self


class ValidationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    schema_version: int | str = Field(alias="version")
    validation_types: list[ValidationType]
    profiles: list[Profile]
    severities: list[Severity]
    categories: list[CategoryDefinition]
    rules: list[RuleDefinition]

    def _fallback_validate(self, _context: dict[str, Any] | None = None) -> None:
        self.rule_ids_must_be_unique(self.rules)

    @field_validator("rules")
    @classmethod
    def rule_ids_must_be_unique(cls, value: list[RuleDefinition]) -> list[RuleDefinition]:
        ids = [rule.id for rule in value]
        duplicates = sorted({rule_id for rule_id in ids if ids.count(rule_id) > 1})
        if duplicates:
            raise ValueError(f"duplicate rule ids: {', '.join(duplicates)}")
        return value


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"rules.yaml not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("rules.yaml root must be a mapping")
    return payload


def _required_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"rules.yaml must define a non-empty {key} list")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key}[{index}] must be a non-empty string")
        result.append(item.strip())
    return result


def _category_definitions(payload: dict[str, Any]) -> list[CategoryDefinition]:
    return [CategoryDefinition(id=category) for category in _required_string_list(payload, "categories")]


def _flatten_rule(raw_rule: dict[str, Any], index: int) -> dict[str, Any]:
    validation = raw_rule.get("validation")
    if not isinstance(validation, dict):
        raise ValueError(f"rules[{index}].validation must be a mapping")

    flattened: dict[str, Any] = {
        "id": raw_rule.get("id"),
        "description": raw_rule.get("description"),
        "severity": raw_rule.get("severity"),
        "priority": raw_rule.get("priority"),
        "applies_to": raw_rule.get("applies_to"),
        "category": raw_rule.get("category"),
        "rationale": raw_rule.get("rationale"),
        "examples": raw_rule.get("examples"),
        "target": validation.get("target"),
        "type": validation.get("type"),
        "pattern": validation.get("pattern"),
        "custom_handler": validation.get("custom_handler"),
        "selector": validation.get("selector"),
    }
    return {key: value for key, value in flattened.items() if value is not None}


def _load_rule_models(payload: dict[str, Any]) -> list[RuleDefinition]:
    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list):
        raise ValueError("rules.yaml must define a rules list")

    categories = {category.id for category in _category_definitions(payload)}
    rules: list[RuleDefinition] = []
    for index, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, dict):
            raise ValueError(f"rules[{index}] must be a mapping")
        data = _flatten_rule(raw_rule, index)
        rules.append(RuleDefinition.model_validate(data, context={"categories": categories}))

    if len(rules) != EXPECTED_RULE_COUNT:
        raise ValueError(f"expected {EXPECTED_RULE_COUNT} rules, got {len(rules)}")
    return rules


def load_rules() -> list[RuleDefinition]:
    payload = _read_yaml(DEFAULT_RULES_PATH)
    return _load_rule_models(payload)


def _build_validation_schema(payload: dict[str, Any]) -> ValidationSchema:
    return ValidationSchema(
        version=payload.get("schema_version", 1),
        validation_types=_required_string_list(payload, "validation_types"),
        profiles=_required_string_list(payload, "profiles"),
        severities=_required_string_list(payload, "severities"),
        categories=_category_definitions(payload),
        rules=_load_rule_models(payload),
    )


def generate_schema() -> dict[str, Any]:
    payload = _read_yaml(DEFAULT_RULES_PATH)
    schema_model = _build_validation_schema(payload)
    schema_data = schema_model.model_dump(mode="json", by_alias=True, exclude_none=True)
    return {
        "$comment": AUTO_GENERATED_COMMENT,
        **schema_data,
        "model_json_schema": ValidationSchema.model_json_schema(by_alias=True),
    }


def write_schema(output_path: str | os.PathLike[str] = DEFAULT_SCHEMA_PATH) -> None:
    target = Path(output_path)
    schema = generate_schema()
    rendered = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=False) + "\n"

    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fp:
            fp.write(rendered)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    write_schema(DEFAULT_SCHEMA_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

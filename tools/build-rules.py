#!/usr/bin/env python3
"""Generate rule artifacts from rules/rules.yaml."""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import yaml


AUTO_HEADER = """<!-- AUTO-GENERATED FROM rules/rules.yaml. DO NOT EDIT MANUALLY.
     Run: python3 tools/build-rules.py
-->
"""

PROFILE_RULES_BEGIN = "# BEGIN AUTO-GEN PROFILE_RULES (rules/rules.yaml → tools/build-rules.py)"
PROFILE_RULES_END = "# END AUTO-GEN PROFILE_RULES"

CATEGORY_LABELS = {
    "css.layout": "CSS 레이아웃",
    "css.color": "CSS 색상",
    "css.format": "CSS 포맷",
    "css.units": "CSS 단위",
    "css.naming": "CSS 네이밍",
    "css.variables": "CSS 변수",
    "css.selector": "CSS 선택자",
    "css.typography": "CSS 타이포그래피",
    "css.border": "CSS 테두리",
    "css.spacing": "CSS 간격",
    "html.structure": "HTML 구조",
    "html.semantic": "HTML 시맨틱",
    "html.naming": "HTML 네이밍",
    "html.image": "HTML 이미지",
    "html.text": "HTML 텍스트",
    "accessibility": "접근성",
    "figma.mapping": "Figma 매핑",
    "figma.fidelity": "Figma 충실도",
    "process": "프로세스",
    "enhancement.workflow": "개선 워크플로우",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build rules artifacts from rules.yaml")
    parser.add_argument("--input", default="rules/rules.yaml", help="Input YAML file path")
    parser.add_argument("--output-dir", default="rules/", help="Output directory for markdown/json files")
    parser.add_argument("--check", action="store_true", help="Compare generated contents only (do not write)")
    parser.add_argument(
        "--profile",
        choices=["basic", "landing", "all"],
        default="all",
        help="Generate profile-specific markdown targets",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fp:
            fp.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def load_rules_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"input not found: {path}")
    with path.open("r", encoding="utf-8") as fp:
        payload = yaml.safe_load(fp) or {}
    if not isinstance(payload, dict):
        raise ValueError("rules.yaml root must be mapping")
    return payload


def normalize_rules(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw_rules = data.get("rules")
    if not isinstance(raw_rules, list):
        raise ValueError("rules.yaml must contain a 'rules' array")

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rules):
        if not isinstance(raw, dict):
            raise ValueError(f"rules[{index}] must be object")

        rule = dict(raw)
        if not rule.get("id"):
            raise ValueError(f"rules[{index}] missing id")

        applies_to = rule.get("applies_to") or []
        if not isinstance(applies_to, list):
            raise ValueError(f"rules[{index}].applies_to must be array")
        rule["applies_to"] = [str(item) for item in applies_to]

        validation = rule.get("validation") or {}
        if not isinstance(validation, dict):
            raise ValueError(f"rules[{index}].validation must be object")
        rule["validation"] = validation
        normalized.append(rule)

    return normalized


def is_deprecated(rule: dict[str, Any]) -> bool:
    return str(rule.get("severity", "")).lower() == "deprecated"


def is_common_core_rule(rule: dict[str, Any]) -> bool:
    applies_to = set(rule.get("applies_to", []))
    return {"common", "basic", "landing"}.issubset(applies_to)


def category_order_map(payload: dict[str, Any]) -> dict[str, int]:
    categories = payload.get("categories")
    if not isinstance(categories, list):
        return {}
    result: dict[str, int] = {}
    for idx, category in enumerate(categories):
        result[str(category)] = idx
    return result


def sort_rules(rules: list[dict[str, Any]], order_map: dict[str, int]) -> list[dict[str, Any]]:
    def key(rule: dict[str, Any]) -> tuple[int, str, str]:
        category = str(rule.get("category", "misc"))
        rank = order_map.get(category, 10_000)
        return rank, category, str(rule.get("id", ""))

    return sorted(rules, key=key)


def group_by_category(rules: list[dict[str, Any]], order_map: dict[str, int]) -> list[tuple[str, list[dict[str, Any]]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for rule in rules:
        category = str(rule.get("category", "misc"))
        grouped.setdefault(category, []).append(rule)

    categories = sorted(grouped.keys(), key=lambda c: (order_map.get(c, 10_000), c))
    return [(category, sort_rules(grouped[category], order_map)) for category in categories]


def category_title(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace(".", " / "))


def markdown_lang_for_rule(rule: dict[str, Any]) -> str:
    target = str((rule.get("validation") or {}).get("target", "text")).lower()
    if target in {"css", "html", "json", "python", "js"}:
        return target
    return "text"


def escape_md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_rule_detail(rule: dict[str, Any]) -> str:
    lines: list[str] = []
    rule_id = str(rule.get("id", ""))
    severity = str(rule.get("severity", "unknown")).lower()
    description = str(rule.get("description", "")).strip()
    validation = rule.get("validation") or {}
    examples = rule.get("examples") or {}
    rationale = str(rule.get("rationale", "")).strip()
    lang = markdown_lang_for_rule(rule)

    lines.append(f"### {rule_id} ({severity})")
    lines.append("")
    if description:
        lines.append(description)
        lines.append("")

    bad_example = examples.get("bad") if isinstance(examples, dict) else None
    good_example = examples.get("good") if isinstance(examples, dict) else None

    if bad_example:
        lines.append("**나쁜 예**:")
        lines.append(f"```{lang}")
        lines.append(str(bad_example).rstrip("\n"))
        lines.append("```")
    if good_example:
        lines.append("**좋은 예**:")
        lines.append(f"```{lang}")
        lines.append(str(good_example).rstrip("\n"))
        lines.append("```")

    if rationale:
        lines.append(f"**근거**: {rationale}")

    if "custom_handler" in validation and not rationale:
        handler = str(validation.get("custom_handler", "")).strip()
        if handler:
            lines.append(f"**검증 핸들러**: `{handler}`")

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def render_markdown_document(
    *,
    title: str,
    subtitle_lines: list[str],
    rules: list[dict[str, Any]],
    order_map: dict[str, int],
) -> str:
    lines: list[str] = [AUTO_HEADER.rstrip(), "", f"# {title}", ""]
    for subtitle in subtitle_lines:
        lines.append(f"> {subtitle}")
    lines.append("")

    grouped = group_by_category(rules, order_map)
    if not grouped:
        lines.append("생성할 규칙이 없습니다.")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    for category, category_rules in grouped:
        lines.append(f"## {category_title(category)}")
        lines.append("")
        lines.append("| Rule ID | Severity | Description |")
        lines.append("| --- | --- | --- |")
        for rule in category_rules:
            rule_id = str(rule.get("id", ""))
            severity = str(rule.get("severity", "unknown")).lower()
            description = escape_md_cell(str(rule.get("description", "")))
            lines.append(f"| `{rule_id}` | `{severity}` | {description} |")
        lines.append("")

        for rule in category_rules:
            lines.append(render_rule_detail(rule).rstrip())

    return "\n".join(lines).rstrip() + "\n"


def select_markdown_rules(
    all_rules: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    common_rules: list[dict[str, Any]] = []
    basic_rules: list[dict[str, Any]] = []
    landing_rules: list[dict[str, Any]] = []

    for rule in all_rules:
        applies = set(rule.get("applies_to", []))
        if is_common_core_rule(rule):
            common_rules.append(rule)
            continue
        if "basic" in applies:
            basic_rules.append(rule)
        if "landing" in applies:
            landing_rules.append(rule)

    return common_rules, basic_rules, landing_rules


def validation_rule_item(rule: dict[str, Any]) -> dict[str, Any]:
    validation = rule.get("validation") or {}
    item: dict[str, Any] = {
        "id": str(rule.get("id", "")),
        "severity": str(rule.get("severity", "")),
        "target": str(validation.get("target", rule.get("target", "")) or ""),
        "type": str(validation.get("type", "")),
    }

    if rule.get("description"):
        item["description"] = str(rule.get("description"))
    if rule.get("category"):
        item["category"] = str(rule.get("category"))
    if rule.get("applies_to"):
        item["applies_to"] = list(rule["applies_to"])
    if rule.get("rationale"):
        item["rationale"] = str(rule.get("rationale"))

    for key, value in validation.items():
        if key in {"target", "type"}:
            continue
        if key in {"pattern", "selector"}:
            item[key] = value
            continue
        item[key] = value

    if "pattern" not in item and "selector" not in item:
        if "custom_handler" in validation:
            item["selector"] = f"custom:{validation['custom_handler']}"
        else:
            item["selector"] = f"type:{item['type']}"

    return item


def normalize_schema_version(value: Any) -> int | str:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return 1


def build_validation_schema(payload: dict[str, Any], rules: list[dict[str, Any]]) -> str:
    schema = {
        "version": normalize_schema_version(payload.get("schema_version", 1)),
        "rules": [validation_rule_item(rule) for rule in rules],
    }
    return json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def profile_rule_descriptions(
    all_rules: list[dict[str, Any]],
    profile: str,
    order_map: dict[str, int],
) -> list[str]:
    selected = [rule for rule in all_rules if profile in set(rule.get("applies_to", []))]
    selected = sort_rules(selected, order_map)
    deduped: list[str] = []
    seen: set[str] = set()
    for rule in selected:
        description = str(rule.get("description", "")).strip()
        if not description or description in seen:
            continue
        deduped.append(description)
        seen.add(description)
    return deduped


def render_profile_rules_block(profile_rules: dict[str, list[str]]) -> str:
    lines: list[str] = [PROFILE_RULES_BEGIN, "PROFILE_RULES = {"]
    for profile in ("basic", "landing"):
        descriptions = profile_rules.get(profile, [])
        lines.append(f'    "{profile}": [')
        for description in descriptions:
            lines.append(f"        {json.dumps(description, ensure_ascii=False)},")
        lines.append("    ],")
    lines.append("}")
    lines.append(PROFILE_RULES_END)
    lines.append("")
    return "\n".join(lines)


def find_profile_rules_node(source: str) -> ast.AST | None:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PROFILE_RULES":
                    return node
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "PROFILE_RULES":
                return node
    return None


def diff_text(path: Path, expected: str) -> str:
    current = read_text(path)
    if current == expected:
        return ""
    return "".join(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def write_or_check(outputs: dict[Path, str], check_only: bool) -> int:
    has_diff = False
    for path, content in outputs.items():
        current = read_text(path)
        if current == content:
            continue
        has_diff = True
        if check_only:
            print(diff_text(path, content), end="")
        else:
            write_text_atomic(path, content)
            print(f"updated: {path}")

    if check_only:
        return 1 if has_diff else 0
    return 0


def build_outputs(args: argparse.Namespace) -> dict[Path, str]:
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    payload = load_rules_yaml(input_path)
    all_rules = [rule for rule in normalize_rules(payload) if not is_deprecated(rule)]
    order_map = category_order_map(payload)
    sorted_rules = sort_rules(all_rules, order_map)

    common_rules, basic_rules, landing_rules = select_markdown_rules(sorted_rules)
    outputs: dict[Path, str] = {}

    common_md = render_markdown_document(
        title="공통 규칙",
        subtitle_lines=[
            "이 파일은 `rules/rules.yaml`에서 자동 생성됩니다.",
            "직접 편집하지 마세요. 규칙 변경은 `rules.yaml`을 수정하고 빌드를 재실행하세요.",
        ],
        rules=common_rules,
        order_map=order_map,
    )
    outputs[output_dir / "common.md"] = common_md

    if args.profile in {"all", "basic"}:
        basic_md = render_markdown_document(
            title="Basic 추가 규칙",
            subtitle_lines=[
                "이 파일은 `rules/rules.yaml`에서 자동 생성됩니다.",
                "공통 규칙은 `common.md`를 참고하세요.",
            ],
            rules=basic_rules,
            order_map=order_map,
        )
        outputs[output_dir / "basic.md"] = basic_md

    if args.profile in {"all", "landing"}:
        landing_md = render_markdown_document(
            title="Landing 추가 규칙",
            subtitle_lines=[
                "이 파일은 `rules/rules.yaml`에서 자동 생성됩니다.",
                "공통 규칙은 `common.md`를 참고하세요.",
            ],
            rules=landing_rules,
            order_map=order_map,
        )
        outputs[output_dir / "landing.md"] = landing_md

    outputs[output_dir / "validation_schema.json"] = build_validation_schema(payload, sorted_rules)
    return outputs


def main() -> int:
    args = parse_args()
    outputs = build_outputs(args)
    return write_or_check(outputs, check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())

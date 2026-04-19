from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE_PATH = ROOT / "tools" / "figma-validate.py"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "req029" / "policy3_rules_conflict_node.json"


def _load_figma_validate_module():
    spec = importlib.util.spec_from_file_location("figma_validate", FIGMA_VALIDATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_policy3_rules_conflict_meta_bypasses_rule_and_logs_once(capsys) -> None:
    figma_validate = _load_figma_validate_module()
    node = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    seen: set[tuple[str, str]] = set()

    bypassed = figma_validate.enforce_policy3_rules_conflict_bypass(node, "no_color_grid", seen)
    assert bypassed is True

    first_log = capsys.readouterr().out
    assert "[RULES-CONFLICT]" in first_log
    assert "no_color_grid" in first_log
    assert "rgb-grid" in first_log
    assert "flexbox" in first_log

    bypassed_again = figma_validate.enforce_policy3_rules_conflict_bypass(node, "no_color_grid", seen)
    assert bypassed_again is True
    assert capsys.readouterr().out == ""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DRIFT_CHECKER = ROOT / "tools" / "check-rules-drift.py"


def _load_drift_checker_module():
    spec = importlib.util.spec_from_file_location("check_rules_drift_injection", DRIFT_CHECKER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_check_rules_drift_detects_pydantic_rule_removal(monkeypatch, capsys) -> None:
    module = _load_drift_checker_module()
    original_rules = module.load_rules()
    removed_rule = original_rules[0]

    monkeypatch.setattr(module, "load_rules", lambda: original_rules[1:])

    args = argparse.Namespace(
        rules_yaml=str(ROOT / "rules" / "rules.yaml"),
        validation_schema=str(ROOT / "rules" / "validation_schema.json"),
        validator=str(ROOT / "tools" / "figma-validate.py"),
    )

    exit_code = module.run_all_rules_mode(args)
    output = "\n".join(capsys.readouterr())

    assert exit_code == 1
    assert removed_rule.id in output
    assert "missing in Pydantic SSOT" in output


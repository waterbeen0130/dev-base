import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "rules" / "rules.yaml"
VALIDATE_SEMANTIC = ROOT / "tools" / "validate-semantic.py"
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def _load_rules() -> list[dict]:
    return yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["rules"]


# REQ-024 introduced a slimming target (<=65). Later REQs (037/038/040/041/047/048)
# added rules intentionally, so the exact ceiling moved. The authoritative count now
# lives in rules.models.EXPECTED_RULE_COUNT; this test keeps a bloat tripwire that
# stays in sync with that authoritative count instead of a stale magic number.
def test_rules_count_matches_authoritative_count():
    from rules.models import EXPECTED_RULE_COUNT

    rules = _load_rules()
    assert len(rules) == EXPECTED_RULE_COUNT


def test_duplicate_rule_pairs_are_collapsed():
    ids = [rule["id"] for rule in _load_rules()]
    target_ids = {"flexbox_layout", "no_css_grid", "forbidden_tag", "no_figure_figcaption"}
    count = sum(1 for rule_id in ids if rule_id in target_ids)
    assert count <= 2


def test_validate_semantic_help_smoke():
    proc = subprocess.run(
        [sys.executable, str(VALIDATE_SEMANTIC), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "usage:" in proc.stdout.lower()


def test_figma_validate_help_smoke():
    proc = subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "usage:" in proc.stdout.lower()

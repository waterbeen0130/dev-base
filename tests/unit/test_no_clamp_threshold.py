from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "tools" / "validate-semantic.py"


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_semantic", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_no_clamp_under_100_flags_50px() -> None:
    module = _load_validator_module()
    css = ".box{padding:clamp(50px,10vw,120px);}"

    violations = module.check_clamp_under_100("", css)

    assert len(violations) == 1
    assert violations[0].rule == "no-clamp-under-100"


def test_no_clamp_under_100_allows_100px_or_more() -> None:
    module = _load_validator_module()
    css = "\n".join(
        [
            ".box{padding:clamp(100px,10vw,180px);}",
            ".card{margin:clamp(120px,12vw,220px);}",
        ]
    )

    violations = module.check_clamp_under_100("", css)

    assert violations == []

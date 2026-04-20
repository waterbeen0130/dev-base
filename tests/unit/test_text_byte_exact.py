from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"


def _load_figma_validate_module():
    spec = importlib.util.spec_from_file_location("figma_validate_text_byte_exact", FIGMA_VALIDATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_nbsp_missing_is_detected() -> None:
    module = _load_figma_validate_module()
    spec = {"text_nodes": [{"id": "n1", "characters": "운영시간\xa0 10:00"}]}
    html = "<div>운영시간 10:00</div>"

    violations = module.validate_text_byte_exact(spec, html)

    assert len(violations) == 1
    assert violations[0].category == "텍스트 byte-exact"

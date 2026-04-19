from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req031_character_overrides"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_character_style_overrides_and_table_are_preserved() -> None:
    module = _load_module()
    node = {
        "id": "1:40",
        "name": "한글 텍스트",
        "type": "TEXT",
        "characters": "안녕",
        "fills": [{"type": "SOLID", "color": {"r": 0.0, "g": 0.0, "b": 0.0}}],
        "style": {
            "fontFamily": "Pretendard",
            "fontSize": 16,
            "fontWeight": 400,
            "lineHeightPx": 24,
            "letterSpacing": 0,
        },
        "characterStyleOverrides": [0, 1],
        "styleOverrideTable": {
            "1": {
                "style": {"fontWeight": 700},
                "fills": [{"type": "SOLID", "color": {"r": 1.0, "g": 0.0, "b": 0.0}}],
            }
        },
    }

    normalized = module.normalize_text_node(node)

    assert normalized["characterStyleOverrides"] == [0, 1]
    assert normalized["styleOverrideTable"] == {
        "1": {
            "style": {"fontWeight": 700},
            "fills": [{"type": "SOLID", "color": {"r": 1.0, "g": 0.0, "b": 0.0}}],
        }
    }

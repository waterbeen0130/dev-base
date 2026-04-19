from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_SECTION_SPEC = ROOT / "tools" / "figma-section-spec.py"


def _load_module():
    module_name = "figma_section_spec_req032_vector_paths"
    spec = importlib.util.spec_from_file_location(module_name, FIGMA_SECTION_SPEC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_vector_geometry_paths_are_preserved_without_transformation() -> None:
    module = _load_module()
    node = {
        "id": "10:20",
        "name": "Icon",
        "type": "VECTOR",
        "size": {"width": 24, "height": 12},
        "fillGeometry": [{"path": "M0 0L10 10Z"}, {"path": "M1 1L2 2Z"}],
        "strokeGeometry": [{"path": "M3 3L4 4Z"}],
    }

    normalized = module.normalize_vector_node(node)

    assert normalized["viewBox"] == {"width": 24, "height": 12}
    assert normalized["fillGeometryPathData"] == ["M0 0L10 10Z", "M1 1L2 2Z"]
    assert normalized["strokeGeometryPathData"] == ["M3 3L4 4Z"]

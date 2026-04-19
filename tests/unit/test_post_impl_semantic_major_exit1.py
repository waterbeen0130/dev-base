from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"

_SPEC = importlib.util.spec_from_file_location("post_impl_verify_semantic_major", POST_IMPL_VERIFY)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)


def test_semantic_major_is_blocking_and_forces_exit_1() -> None:
    semantic = _MODULE.parse_validate_semantic_output(
        "CRITICAL: 0 | MAJOR: 1 | MINOR: 0",
        exit_code=0,
    )
    figma = {
        "runner_error": False,
        "critical": 0,
        "major": 0,
        "ignore": 0,
    }

    assert semantic["counts"]["major"] == 1
    assert semantic["blocking"] is True
    assert _MODULE.determine_exit_code(figma, semantic) == 1

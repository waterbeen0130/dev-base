from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"

_SPEC = importlib.util.spec_from_file_location("post_impl_verify_converge_max_iter", POST_IMPL_VERIFY)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)


def test_converge_max_iterations_warns_and_returns_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(max_iterations=2, convergence_mode="zero-violations", dispatch_agent="codex-dev")
    dispatch_calls: list[tuple[str, str]] = []

    def validate_stub() -> dict[str, int]:
        return {"critical": 1, "major": 0, "minor": 0, "total": 1}

    def dispatch_stub(violations_json: str, dispatch_agent: str) -> None:
        dispatch_calls.append((violations_json, dispatch_agent))

    exit_code = _MODULE.run_convergence_loop(args, validate_stub, dispatch_stub)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert len(dispatch_calls) == 1
    assert "[WARN] 수렴 미달성: iter=2 remaining=1" in captured.err

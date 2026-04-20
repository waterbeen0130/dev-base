from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"

_SPEC = importlib.util.spec_from_file_location("post_impl_verify_converge_no_change", POST_IMPL_VERIFY)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)


def test_converge_no_change_mode_stops_when_total_is_unchanged(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(max_iterations=5, convergence_mode="no-change", dispatch_agent="codex-dev")
    results = iter(
        [
            {"critical": 0, "major": 2, "minor": 0, "total": 2},
            {"critical": 0, "major": 2, "minor": 0, "total": 2},
        ]
    )
    dispatch_calls: list[tuple[str, str]] = []

    def validate_stub() -> dict[str, int]:
        return next(results)

    def dispatch_stub(violations_json: str, dispatch_agent: str) -> None:
        dispatch_calls.append((violations_json, dispatch_agent))

    exit_code = _MODULE.run_convergence_loop(args, validate_stub, dispatch_stub)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert len(dispatch_calls) == 1
    assert dispatch_calls[0][1] == "codex-dev"
    assert "[CONVERGED] iter=2 no-change (total=2)" in captured.out

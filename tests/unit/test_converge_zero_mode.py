from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"

_SPEC = importlib.util.spec_from_file_location("post_impl_verify_converge_zero", POST_IMPL_VERIFY)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)


def test_converge_zero_mode_stops_on_first_zero_iteration(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(max_iterations=3, convergence_mode="zero-violations", dispatch_agent="codex-dev")
    dispatch_calls: list[tuple[str, str]] = []

    def validate_stub() -> dict[str, int]:
        return {"critical": 0, "major": 0, "minor": 0, "total": 0}

    def dispatch_stub(violations_json: str, dispatch_agent: str) -> None:
        dispatch_calls.append((violations_json, dispatch_agent))

    exit_code = _MODULE.run_convergence_loop(args, validate_stub, dispatch_stub)

    captured = capsys.readouterr()
    history = json.loads(Path(".gran-maestro/state/converge-history.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert dispatch_calls == []
    assert "[CONVERGED] iter=1 zero-violations" in captured.out
    assert len(history) == 1
    assert history[0]["iter"] == 1
    assert history[0]["total"] == 0
    assert history[0]["critical"] == 0
    assert history[0]["major"] == 0
    assert history[0]["minor"] == 0
    assert isinstance(history[0]["duration_s"], float)

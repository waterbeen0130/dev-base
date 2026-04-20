from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POST_IMPL_VERIFY = ROOT / "tools" / "post-impl-verify.py"

_SPEC = importlib.util.spec_from_file_location("post_impl_verify_converge_history", POST_IMPL_VERIFY)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)


def test_converge_history_log_records_iteration_counts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(max_iterations=3, convergence_mode="zero-violations", dispatch_agent="codex-dev")
    results = iter(
        [
            {"critical": 1, "major": 1, "minor": 1, "total": 3},
            {"critical": 0, "major": 0, "minor": 0, "total": 0},
        ]
    )
    dispatched_paths: list[str] = []

    def validate_stub() -> dict[str, int]:
        return next(results)

    def dispatch_stub(violations_json: str, dispatch_agent: str) -> None:
        dispatched_paths.append(violations_json)

    exit_code = _MODULE.run_convergence_loop(args, validate_stub, dispatch_stub)

    history_path = Path(".gran-maestro/state/converge-history.json")
    history = json.loads(history_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert dispatched_paths == [".gran-maestro/state/iter-1-violations.json"]
    assert history_path.exists()
    assert history[0]["iter"] == 1
    assert history[0]["critical"] == 1
    assert history[0]["major"] == 1
    assert history[0]["minor"] == 1
    assert history[0]["total"] == 3
    assert history[1]["iter"] == 2
    assert history[1]["total"] == 0
    assert all(isinstance(entry["duration_s"], float) for entry in history)

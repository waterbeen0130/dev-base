#!/usr/bin/env python3
"""Verification execution evidence gate (DOD-006).

Blocks completion/delivery unless a fresh pm-verify report proves verification
actually ran AND passed on the CURRENT deliverable. The report is matched to the
current files by sha256, so a report from before a later edit ("self-report
without re-running") is treated as stale and blocks.

Usage:
    python3 verify-evidence-gate.py --html index.html --css css/common.css \\
        --report .gran-maestro/pm-verify-report.json
Exit: 0 = ALLOW, 1 = BLOCK.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_spec_shas(report: dict, spec_paths: list[Path]) -> tuple[bool, str]:
    spec_coverage = report.get("spec_coverage")
    if not isinstance(spec_coverage, dict):
        return True, "ok"
    report_shas = spec_coverage.get("spec_shas")
    if report_shas is None:
        return True, "ok"
    if not isinstance(report_shas, dict):
        return False, "invalid_evidence: spec_shas 형식이 잘못되었습니다"
    for spec_path in spec_paths:
        if not spec_path.exists():
            return False, f"missing_spec_file: spec 파일이 없습니다 ({spec_path})"
        report_sha = report_shas.get(str(spec_path))
        if report_sha is None:
            return False, f"stale_spec_evidence: spec_shas 에 현재 spec가 없습니다 ({spec_path})"
        if _sha256(spec_path) != report_sha:
            return False, f"stale_spec_evidence: spec 가 검증 후 변경됨 — 재검증이 필요합니다 ({spec_path})"
    return True, "ok"


def check_evidence(html_path, css_path, report_path, spec_paths=None):
    """Return (ok: bool, reason: str). ok=False means delivery must be blocked."""
    html_path, css_path, report_path = Path(html_path), Path(css_path), Path(report_path)
    spec_paths = [Path(path) for path in (spec_paths or [])]
    if not report_path.exists():
        return False, "no_evidence: pm-verify 리포트 없음 — 검증이 실행되지 않았습니다"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report is untrusted input
        return False, f"invalid_evidence: 리포트 파싱 실패 ({exc})"
    if not report.get("passed"):
        return False, f"verification_failed: 리포트가 미통과 상태입니다 (exit_code={report.get('exit_code')})"
    for label, path, key in (
        ("html", html_path, "html_sha256"),
        ("css", css_path, "css_sha256"),
    ):
        if not path.exists():
            return False, f"missing_file: {label} 파일이 없습니다 ({path})"
        if _sha256(path) != report.get(key):
            return False, f"stale_evidence: {label} 가 검증 후 변경됨 — 재검증이 필요합니다"
    spec_ok, spec_reason = _check_spec_shas(report, spec_paths)
    if not spec_ok:
        return False, spec_reason
    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--html", required=True)
    parser.add_argument("--css", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--spec", action="append", default=[])
    args = parser.parse_args()

    ok, reason = check_evidence(args.html, args.css, args.report, spec_paths=args.spec)
    print(("ALLOW" if ok else "BLOCK") + f": {reason}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

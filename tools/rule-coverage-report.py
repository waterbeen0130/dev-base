#!/usr/bin/env python3
"""DOD-005: rule coverage gap report.

Measures the closure of machine-checkable (A/B-grade) rule gaps identified in the
AGI-004 investigation, and lists remaining gaps with reasons. C-grade items
(meaning/visual judgement, agent honesty) are out of scope for mechanical checks.

Usage:
    python3 rule-coverage-report.py [--root .] [--json]
"""

import argparse
import json
import sys
from pathlib import Path

# AGI-004 investigation gap list (machine-checkable A/B + out-of-scope C), with
# resolution status as of this milestone. "closed" items map to a real
# rule/handler/tool now present in the repo.
GAP_MANIFEST = [
    {"id": "no_figma_nodeid_class", "grade": "B", "status": "closed", "by": "rules.yaml:no_figma_nodeid_class"},
    {"id": "common_area_child_scope", "grade": "B", "status": "closed", "by": "validate-semantic:check_common_area_child_scope"},
    {"id": "global_class_standalone", "grade": "A", "status": "closed", "by": "validate-semantic:check_global_class_standalone"},
    {"id": "character_segments_respected", "grade": "B", "status": "closed", "by": "tools/check-mixed-styles.py"},
    {"id": "no_deprecated_tools", "grade": "A", "status": "closed", "by": "tools/check-deprecated-tools.py"},
    {"id": "converge_flag_forbidden", "grade": "A", "status": "closed", "by": "tools/check-deprecated-tools.py"},
    {"id": "verify_execution_evidence", "grade": "A", "status": "closed", "by": "tools/verify-evidence-gate.py + pm-verify --emit-report"},
    {"id": "output_boundary", "grade": "B", "status": "closed", "by": "tools/check-output-boundary.py"},
    {"id": "no_guess_prefix", "grade": "A", "status": "open", "reason": "site_/g_/common_ 추측 prefix 전용 규칙 미구현 (no_forbidden_class가 sec_/box만 커버)"},
    {"id": "workflow_order_enforced", "grade": "B", "status": "open", "reason": "7-step/2패스 순서는 INSTRUCTIONS.md에 문서화됐으나 실행 로그 기반 강제는 미구현"},
    {"id": "omx_usage_detection", "grade": "A", "status": "open", "reason": "추출 에이전트 종류(OMX vs 외부) 식별 미구현 — 환경 신호 필요"},
    {"id": "korean_comment_ban", "grade": "A", "status": "open", "reason": "한국어 코드 주석 금지 grep 규칙 미구현 (후순위)"},
    {"id": "false_report_ban", "grade": "C", "status": "out_of_scope", "reason": "에이전트 보고 정직성 — 기계 검증 불가 (DOD-006 게이트로 간접 방어)"},
    {"id": "visual_reference_priority", "grade": "C", "status": "out_of_scope", "reason": "시각 판단 — 자동화 불가"},
    {"id": "no_unrequested_improvement", "grade": "C", "status": "out_of_scope", "reason": "의도 차이 판단 — 기계 검증 불가"},
]


def _load_rule_count(root: Path) -> int:
    try:
        import yaml
        data = yaml.safe_load((root / "rules" / "rules.yaml").read_text(encoding="utf-8"))
        return len(data.get("rules", []))
    except Exception:
        return 0


def build_report(root) -> dict:
    root = Path(root)
    ab = [g for g in GAP_MANIFEST if g["grade"] in ("A", "B")]
    closed = [g for g in ab if g["status"] == "closed"]
    out_of_scope = [g for g in GAP_MANIFEST if g["status"] == "out_of_scope"]
    ab_total = len(ab)
    ab_closed = len(closed)
    return {
        "encoded_rule_count": _load_rule_count(root),
        "ab_gaps_total": ab_total,
        "ab_gaps_closed": ab_closed,
        "ab_coverage_ratio": round(ab_closed / ab_total, 3) if ab_total else 0.0,
        "out_of_scope_count": len(out_of_scope),
        "gaps": GAP_MANIFEST,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rep = build_report(args.root)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0
    print("=" * 60)
    print("Rule Coverage Report (AGI-004 DOD-005)")
    print("=" * 60)
    print(f"rules.yaml 규칙 수: {rep['encoded_rule_count']}")
    print(f"A/B급 갭: {rep['ab_gaps_closed']}/{rep['ab_gaps_total']} 해소 (coverage {rep['ab_coverage_ratio']:.0%})")
    print(f"out-of-scope(C급): {rep['out_of_scope_count']}")
    print("\n[해소됨]")
    for g in rep["gaps"]:
        if g["status"] == "closed":
            print(f"  ✓ {g['id']} → {g['by']}")
    print("\n[잔여 — 기계검증 가능하나 미구현]")
    for g in rep["gaps"]:
        if g["status"] == "open":
            print(f"  · {g['id']} ({g['grade']}): {g['reason']}")
    print("\n[범위 외 — 기계검증 불가]")
    for g in rep["gaps"]:
        if g["status"] == "out_of_scope":
            print(f"  - {g['id']}: {g['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

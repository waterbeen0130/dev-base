# Implementation Request — REQ-041 / Task 01

**Request**: REQ-041 (post-impl-verify 수렴 루프 정식 통합)
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-041-T01`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-041/tasks/01/spec.md`

**실측 배경**: 목포플레이파크에서 수동 dispatch 5회로 348 → 0 수렴 확인. 이를 post-impl-verify 에 자동화.

## 구현 상세

### 1. `tools/post-impl-verify.py` 신규 인자

```python
parser.add_argument("--converge", action="store_true",
  help="Auto-repair loop: re-dispatch until convergence")
parser.add_argument("--max-iterations", type=int, default=5)
parser.add_argument("--convergence-mode",
  choices=["zero-violations", "no-change", "n-iterations"],
  default="zero-violations")
parser.add_argument("--dispatch-agent", default="codex-dev",
  choices=["codex-dev", "gemini-dev", "claude-dev"])

# --converge 와 --no-repair 는 배타
if args.converge and args.no_repair:
    parser.error("--converge is incompatible with --no-repair")
```

### 2. 수렴 루프 핵심 로직

```python
def run_convergence_loop(args, validate_fn, dispatch_fn):
    history = []
    prev_total = None
    for i in range(1, args.max_iterations + 1):
        t0 = time.time()
        result = validate_fn()
        duration = time.time() - t0

        violations = {
            "iter": i,
            "critical": result["critical"],
            "major": result["major"],
            "minor": result["minor"],
            "total": result["total"],
            "duration_s": round(duration, 2)
        }
        history.append(violations)

        print(f"[ITER {i}] CRITICAL={result['critical']} MAJOR={result['major']} MINOR={result['minor']} TOTAL={result['total']}")

        # 종료 조건 체크
        if args.convergence_mode == "zero-violations" and result["total"] == 0:
            print(f"[CONVERGED] iter={i} zero-violations")
            break
        if args.convergence_mode == "no-change" and prev_total == result["total"]:
            print(f"[CONVERGED] iter={i} no-change (total={result['total']})")
            break
        if i == args.max_iterations:
            if result["total"] > 0:
                print(f"[WARN] 수렴 미달성: iter={args.max_iterations} remaining={result['total']}", file=sys.stderr)
            break

        # 위반 JSON 생성 후 codex dispatch
        violations_json = write_violations_json(result, f".gran-maestro/state/iter-{i}-violations.json")
        dispatch_fn(violations_json, args.dispatch_agent)

        prev_total = result["total"]

    # history 저장
    history_path = Path(".gran-maestro/state/converge-history.json")
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n")

    # exit code
    if history[-1]["total"] == 0:
        return 0
    return 1
```

### 3. dispatch_fn 구현

기존 `tools/repair-from-violations.py` 재사용. CLI 호출:
```bash
python3 tools/repair-from-violations.py --violations {json_path} --agent {codex-dev|gemini-dev|claude-dev}
```

### 4. 신규 테스트 4종 (tests/unit/)

- `test_converge_zero_mode.py`: zero-violations 모드 1 iter 에 0 도달
- `test_converge_no_change_mode.py`: no-change 모드 수렴 감지
- `test_converge_max_iter.py`: max-iterations 한도 도달 시 WARN + exit 1
- `test_converge_history_log.py`: `.gran-maestro/state/converge-history.json` 기록 확인

validate_fn / dispatch_fn 은 monkeypatch 로 stub 처리 (실제 codex 호출 불필요).

### 5. 검증 명령

```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-041-T01

# 신규 테스트 4개
pytest tests/unit/test_converge_*.py -v

# 전체 회귀
pytest tests/ -q 2>&1 | tail -5
# 기대: 144 + 4 신규 = 148 passed / 0 failed

# CLI sanity
python3 tools/post-impl-verify.py --help 2>&1 | grep -E "converge|max-iter|convergence-mode|dispatch-agent"
```

### 6. git 커밋 금지 — PM 직접 커밋.

## 규칙

- 기존 post-impl-verify 동작 완전 유지 (`--converge` 없을 때)
- `--converge` + `--no-repair` argparse error
- `repair-from-violations.py` 재사용 (새 dispatch 함수 작성 금지)
- 기존 144 passed 회귀 없음
- 코드 주석은 영어만

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-041-T01`

## [MANDATORY] 응답에 반드시 포함

1. `tools/post-impl-verify.py` 변경 diff 요약
2. 4개 신규 테스트 파일명 + 통과 확인
3. 전체 pytest 결과 (last 5 lines)

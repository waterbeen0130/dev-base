# Spec — REQ-041 / Task 01: post-impl-verify 수렴 루프 정식 통합

**Assigned Agent**: `[config: codex-dev] codex-dev`

## §0 Context Manifest

- `tools/post-impl-verify.py` — 현재 1회 검증 + 선택적 --no-repair flag
- `tools/repair-from-violations.py` — REQ-026 위반 JSON 기반 자동 수리 (수렴형 N회)
- `rules/models.py` Pydantic SSOT
- 목포 실측: 수동 dispatch 5회로 348 → 0 수렴 확인

## §1 요약

`post-impl-verify.py` 에 **자동 수렴 루프** 도입. validator → 위반 > 0 → codex 재dispatch → validator → 반복. 수렴 조건 (무변경/0 도달/최대 N회) 중 하나 충족까지.

## §2 범위

**포함**:
- `post-impl-verify.py` 신규 옵션:
  - `--converge` : 수렴 루프 활성 (기본 OFF)
  - `--max-iterations N` : 최대 반복 횟수 (기본 5)
  - `--convergence-mode` : `zero-violations` (기본) / `no-change` / `n-iterations`
  - `--dispatch-agent` : 수정 dispatch 에이전트 (기본 `codex-dev`)
- 각 iteration 마다:
  - figma-validate + validate-semantic 실행
  - 위반 JSON 생성 (`.gran-maestro/state/iter-N-violations.json`)
  - `tools/repair-from-violations.py` 호출로 codex 재dispatch
  - 위반 카운트 기록
- 종료 조건:
  - `zero-violations`: 전체 카운트 0 도달
  - `no-change`: 이전 iteration vs 현재 iteration 카운트 변화 없음 (수렴)
  - `n-iterations`: N 회 도달 (도달해도 0 아니면 경고 출력)
- iteration history 기록: `.gran-maestro/state/converge-history.json`
- 신규 테스트 3종

**제외**:
- 결정적 codegen (별도 REQ)
- spec v1 → v2 자동 migration (별도 REQ)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] --converge + zero-violations 수렴 동작

- **Given**: mock 위반 3건 생성 fixture, codex dispatch 는 stub (이미 통과 결과 반환)
- **When**: `post-impl-verify --converge --max-iterations 3 --spec-dir extracted/ --html ... --css ...`
- **Then**: iter 1 에서 0 도달, 루프 종료, iteration history 기록
- **Test**: `pytest tests/unit/test_converge_zero_mode.py -v` (신규)

### AC-002 [automatable] [tdd-required] no-change 수렴 동작

- **Given**: 고정 위반 (수정 불가능한 mock)
- **When**: `--converge --convergence-mode no-change --max-iterations 5`
- **Then**: 이전 iter vs 현재 iter 카운트 동일하면 종료 (최대 N 도달 전)
- **Test**: `pytest tests/unit/test_converge_no_change_mode.py -v` (신규)

### AC-003 [automatable] [tdd-required] max-iterations 한도 도달 경고

- **Given**: 수렴하지 않는 위반
- **When**: `--converge --max-iterations 2`
- **Then**: iter 2 후 종료, stderr 에 "[WARN] 수렴 미달성" 출력, exit 1
- **Test**: `pytest tests/unit/test_converge_max_iter.py -v` (신규)

### AC-004 [automatable] iteration history JSON 기록

- **Given**: --converge 실행
- **When**: 루프 완료 후
- **Then**: `.gran-maestro/state/converge-history.json` 에 `[{iter: 1, total: N, critical: X, major: Y, minor: Z, duration_s: T}, ...]` 기록
- **Test**: `pytest tests/unit/test_converge_history_log.py -v` (신규)

### AC-005 [automatable] [regression-test] 기존 post-impl-verify 동작 유지

- **Given**: --converge 없이 기존 실행
- **When**: 일반 `post-impl-verify --spec ... --html ... --css ...`
- **Then**: 기존 exit code 체계 완전 유지 (0/1/2)
- **Test**: 기존 `tests/unit/test_post_impl_*.py` 전부 통과

## §3.2 Test Scenarios (Pre-Impl)

- AC-001 ~ AC-005: 해당 pytest

## §3.5 Constraints

- 기존 옵션 (`--spec`, `--spec-dir`, `--no-repair`, `--structural-diff`) 동작 완전 유지
- `--converge` 와 `--no-repair` 동시 사용 금지 (argparse error)
- codex dispatch 경로는 기존 `repair-from-violations.py` 재사용
- 기존 pytest 144 passed 회귀 없음
- 코드 주석은 영어만

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | — | codex-dev |

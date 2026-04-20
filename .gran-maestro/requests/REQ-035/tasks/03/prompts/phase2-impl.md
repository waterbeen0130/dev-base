# Implementation Request — REQ-035 / Task 03

**Request**: REQ-035 (Phase B — Pydantic SSOT 자동 파생)
**Task**: 03 — 통합 회귀 테스트 + PAC-3 전체 수렴
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T03`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-035/tasks/03/spec.md`
**Plan**: `/mnt/d/dev-base/.gran-maestro/plans/PLN-010/plan.md`

**선행 작업 (이미 완료)**:
- Task 01 (`5b6a966`): rules/models.py + validation_schema 자동 생성
- Task 02 (`e028e41`): check-rules-drift 승격 + figma-validate handler Pydantic 재정렬

---

## 구현 컨텍스트

Task 01, Task 02 구현 완료 후 **통합 회귀 검증** 및 **증분 테스트** 를 실행하여 PAC-3 (기존 pytest 회귀 없음) 를 최종 수렴한다. 이 태스크는 **테스트 추가/보강만** 수행하며, 구현 코드 수정은 없음.

## 자기탐색 지시

0. `§0 Context Manifest` Read:
   - `tests/regression/test_determinism.py` (결정성 회귀)
   - `tests/integration/test_post_impl_drift_cache.sh` (drift cache 회귀)
   - `tests/regression/test_phase_a_summary.py` (Phase A commit 추적 — 존재 시)
   - `tests/regression/test_backup_byte_exact.py` (backup byte exact)
   - `.gran-maestro/plans/PLN-010/plan.md` 의 PAC-3 전체 수렴 조건

1. 전체 pytest 실행 → baseline 확인:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T03
   pytest tests/ -v 2>&1 | tail -30
   ```
   - 기대: Task 02 기준 123+ passed / 0 failed

2. **결정성 회귀 검증**:
   ```bash
   pytest tests/regression/test_determinism.py -v
   ```
   - 기대: 100회 byte-exact PASS

3. **drift cache 회귀 검증**:
   ```bash
   bash tests/integration/test_post_impl_drift_cache.sh
   ```
   - 2회 연속 실행 시 2번째 "cache hit" 로그 확인
   - integration test가 없으면 skip

4. **신규 통합 테스트 추가** (선택적, 목표 수렴):
   - `tests/integration/test_pln010_phase_b_summary.py` 또는 `tests/regression/test_pln010_phase_b_summary.py` (신규):
     - git log 에 `[REQ-035/01]` 및 `[REQ-035/02]` 커밋이 존재하는지 확인
     - `python -m rules.models` 실행이 `rules/validation_schema.json` 을 성공적으로 재생성하는지 확인
     - `python3 tools/check-rules-drift.py --all` 이 exit 0 + "63/63 rules in sync" 출력하는지 확인
     - 3개 assertion 을 통과해야 전체 REQ-035 완결로 간주
   - 이 테스트가 PAC-3 전체 수렴 증거가 된다

5. **최종 전체 회귀**:
   ```bash
   pytest tests/ -v 2>&1 | tail -40
   ```
   - 기대: Task 02 기준 123 + 신규 Task 03 테스트 추가분 passed / 0 failed

6. **git 커밋 금지** — PM 이 직접 커밋.

## 규칙

- 코드 구현 (tools/, rules/) 은 수정하지 않는다 — 테스트 추가만
- 기존 테스트 파일 내용 변경 금지 (PLN-009 테스트 보존)
- Task 01, Task 02 산출물 (rules/models.py, check-rules-drift.py 등) 은 수정 금지
- 신규 테스트는 `tests/regression/` 또는 `tests/integration/` 에 배치
- 코드 주석은 영어만

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T03`

## [MANDATORY] 응답에 반드시 포함할 것

1. 1번 baseline pytest 출력 (last 30 lines)
2. 2번 결정성 회귀 출력
3. 3번 drift cache 회귀 출력 (있으면)
4. 4번 신규 테스트 파일 전체 내용
5. 5번 최종 회귀 출력 (summary 포함: `=== N passed, M skipped, 0 failed ===`)

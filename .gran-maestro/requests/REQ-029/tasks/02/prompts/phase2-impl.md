# Implementation Request — Self-Exploration Mode

- Request: REQ-029 / Task: 02
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-029-task-02
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-029/tasks/02/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md

## 구현 컨텍스트 (PM 작성)

REQ-029/01 의 구현(schema_version semver + migration 스크립트 + v1/v2 분기 파서 + 정책 3건 enforcement) 이 worktree 에 이미 commit (a1b004b) 되어 있다. 본 task 는 그 위에 **테스트 전용 후행 태스크**로, task 02 spec.md §3 의 통합 AC 7개 + §7 Test Scenarios 7개 + §4 회귀 체크리스트를 모두 PASS 시키는 자동화 테스트 스위트(pytest 기반)를 작성·실행한다. 신규 코드는 작성하지 않고 오직 테스트 파일과 테스트 fixture 만 추가한다. 모든 테스트는 stdlib + pytest 만 사용한다.

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. spec 직접 읽기: `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-029/tasks/02/spec.md`
2. plan 직접 읽기: `cat /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md`
3. task 01 spec 참고: `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-029/tasks/01/spec.md` (구현 AC 13 개와 매핑)
4. task 01 commit 의 모든 파일은 이미 worktree 에 존재 — 신규 파일(`tools/migrate-spec-v1-to-v2.py`, `tools/check-rules-drift.py`, `extracted.v1.backup/`) 모두 사용 가능
5. spec §3 통합 AC + §7 Test Scenarios 를 1:1 매핑하여 테스트 파일 생성

## 테스트 파일 작성 위치 (정확히 이 경로)

- `tests/integration/test_req029_endtoend.sh` — TS-01 (migrate → validate → verify 3단 통합)
- `tests/regression/test_migration_add_only.py` — TS-02 (jq 또는 python diff 로 H1 == H2 검증)
- `tests/regression/test_determinism.py` — TS-03 (figma-section-spec.py 100 회 실행 후 md5 hash 1 종)
  - figma-section-spec.py 는 Figma API 호출이 필요할 수 있으므로, 직접 실행 대신 tests/fixtures/figma_node_sample.json 같은 mock 입력 fixture 를 만들고 정규화 함수만 100 회 호출하여 결정성 검증. 실제 Figma API 호출 없이 단위 함수 레벨에서 byte-exact 비교.
- `tests/integration/test_req029_landing_baseline.sh` — TS-04 (landing/index.html + landing/css/common.css 에 대한 post-impl-verify exit code 회귀)
  - 기존 landing 프로젝트가 본 REQ 적용 후에도 이전 통과 상태를 유지하는지 확인. baseline exit code 는 본 테스트 첫 실행 시 캡처해 저장 가능.
- `tests/unit/test_policy1_margin_bottom.py` — TS-05 (정책 1 PASS / FAIL fixture)
  - PASS fixture: VERTICAL frame + itemSpacing=24 spec → CSS 가 `margin-bottom: 24px` 사용
  - FAIL fixture: 동일 spec → CSS 가 `gap: 24px` 사용 → `[POLICY-1]` 메시지 출력 확인
- `tests/unit/test_policy3_rules_conflict.py` — TS-06 (정책 3 fixture)
  - spec 노드에 `rules_conflict: { rule_id: "no_color_grid", figma_value: "rgb-grid", applied_value: "flexbox" }` 메타 → 해당 rule PASS 처리 + `[RULES-CONFLICT]` 로그 출력
- `tests/regression/test_backup_byte_exact.py` — TS-07 (extracted.v1.backup/ 의 SHA-256 ↔ git show HEAD~1 비교)
  - 백업이 task 01 commit 시점의 v1 원본과 정확히 일치하는지 검증

## 테스트 작성 원칙

- AAA 패턴 (Arrange-Act-Assert)
- 각 테스트는 하나의 동작만 검증
- 외부 의존성 mock 처리 (Figma API 호출 없이 fixture 입력만 사용)
- pytest fixtures 활용 (`tests/fixtures/` 디렉토리에 mock 데이터 배치)
- conftest.py 가 필요하면 `tests/conftest.py` 에 작성
- 모든 테스트는 worktree 루트에서 `pytest tests/` 또는 개별 파일 호출로 실행 가능해야 함
- shell 스크립트(`*.sh`)는 `set -euo pipefail` 사용
- pytest 가 자동 discovery 하도록 파일/함수/클래스 명명 (`test_*.py`, `test_*`, `Test*`)

## 회귀 체크리스트 (§4) 검증 지침

각 항목을 별도 테스트 또는 통합 테스트의 단계로 검증:
- text_nodes[0].characters 한국어 보존 → test_migration_add_only.py 에서 함께 검증
- frame_nodes[0].fills hex SOLID 보존 → 동일
- paddingTop/Right/Bottom/Left 정수 보존 → 동일
- landing 프로젝트 신규 FAIL 0 건 → test_req029_landing_baseline.sh
- build-rules.py schema_version 정수/문자열 모두 처리 → tests/unit/test_build_rules_schema_compat.py 신규 작성

## 이전 피드백

N/A (첫 실행)

## 규칙

- spec §2 의 "테스트 작성" 범위 외 코드 수정 금지 (task 01 의 구현 코드는 이미 commit 되었으므로 절대 수정하지 마라)
- git commit 은 하지 마세요 — PM 이 직접 커밋합니다
- [MANDATORY] 완료 전 `pytest tests/ -v` 와 `bash tests/integration/test_req029_endtoend.sh` 를 실행하고 출력 전체를 응답에 포함하세요
- stdlib + pytest 만 사용 (외부 라이브러리 신규 추가 금지)
- 모든 변경은 worktree (`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-029-task-02`) 내부에서 수행
- pytest 설정(`pyproject.toml` 또는 `pytest.ini`) 이 이미 worktree 에 있으면 그대로 사용

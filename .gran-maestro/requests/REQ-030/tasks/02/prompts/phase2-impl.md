# Implementation Request — REQ-030/02 (Integration Test)

- Request: REQ-030 / Task: 02 (test 후행)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-030-task-02
- Spec: 기본 통합 검증 — task 01 (commit 79d6922) 위에 통합/회귀 테스트만 추가
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md

## 구현 컨텍스트 (PM 작성)

REQ-030/01 (commit 79d6922) 의 구현 (fills_v2 / effects / opacity / blendMode + figma-validate v2 카테고리 7개) 이 worktree 에 이미 존재한다. task 01 이 9 개의 unit test 와 1 개 regression test 를 이미 작성해서 PR 의 spec §3 AC 12 개를 모두 PASS 시킨 상태다. 본 task 02 는 추가로 다음만 수행한다:

1. 실제 `extracted/section_03_spec.json` 과 `extracted/section_04_spec.json` 을 figma-section-spec.py 로 재추출 시도하지 못하므로 (Figma API 토큰 필요), 기존 spec 파일에 대한 figma-validate.py 가 정상 동작하는지 통합 테스트로 검증한다.
2. 기존 landing 프로젝트 (`landing/index.html` + `landing/css/common.css`) 에 대해 `post-impl-verify.py` 를 실행하여 REQ-029 baseline 과 동일한 exit code 가 나오는지 (회귀 0건) 확인하는 shell 스크립트 추가.
3. fills_v2 가 비어있는 v2 spec 도 v2 분기 카테고리에서 graceful skip 되는지 unit test 추가.

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 작성 파일

- `tests/integration/test_req030_endtoend.sh` (신규):
  - `python3 tools/figma-validate.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css` 실행 → exit code 캡처
  - 동일 명령을 section_04 로 재실행 → exit code 캡처
  - 두 exit code 모두 0 이거나 IGNORE-only exit=2 면 PASS
  - `--version-info` 출력에 v2.fills.solid.match / v2.fills.gradient.match / v2.fills.image.match / v2.effects.shadow.match / v2.effects.blur.match / v2.opacity.match / v2.blendMode.match 7 개가 모두 등장하는지 grep
- `tests/integration/test_req030_landing_baseline.sh` (신규 또는 REQ-029 의 test_req029_landing_baseline.sh 확장):
  - `python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css` exit code 가 REQ-029 baseline 과 동일 (0 또는 2)
- `tests/unit/test_v2_empty_fills_graceful.py` (신규):
  - fills_v2 가 빈 배열 `[]` 인 v2 spec 노드를 입력으로 figma-validate.py 의 `v2.fills.*.match` 카테고리가 PASS (스킵 처리) 하는지 검증

## 자기탐색 지시

1. `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-030/tasks/01/spec.md` 의 §11 Test Scenarios 와 §3 AC 확인
2. `tests/regression/test_req030_add_only.py` (task 01 작성) 와 `tests/regression/test_determinism.py` (확장 버전) 를 다시 실행하여 regression PASS 재확인
3. 위 3 신규 파일 작성 후 모두 PASS 시킬 것

## 규칙

- task 01 의 구현 코드 절대 수정 금지 (이미 commit 됨)
- git commit 금지 (PM 처리)
- stdlib + pytest 만 사용
- [MANDATORY] 완료 전 `pytest tests/ -v` (전체) + `bash tests/integration/test_req030_endtoend.sh` 실행 후 출력 응답에 포함
- 모든 변경은 worktree (`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-030-task-02`) 내부에서 수행

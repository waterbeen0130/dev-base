# Implementation Request — REQ-032/02 (Integration Test)

- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-032-task-02
- 선행: REQ-029 (431d0e3) + REQ-030 (7fa6cd2) + REQ-031 (8919608) + REQ-032/01 (0f3716d)

## 구현 컨텍스트 (PM 작성)

REQ-032/01 (0f3716d) 가 componentId + vector path + asset_manifest + 2 v2 카테고리 + 4 unit test 추가했고 35 unit PASS. 본 task 02 는 다음 통합/회귀 검증만 추가:

1. `tests/integration/test_req032_endtoend.sh`:
   - figma-validate.py --version-info 출력에 신규 2 카테고리 (v2.componentId.match, v2.assetManifest.exists) 등장 확인
   - section_03/04 spec 으로 validate 실행 시 baseline 일치
   - asset_manifest.json 자동 생성 옵션 (`--no-emit-asset-manifest` 토글 동작 확인)
2. `tests/regression/test_req032_add_only.py`:
   - REQ-029/030/031 산출물의 기존 v2 키 변경 없음 + REQ-032 신규 키만 추가됨
3. `tests/regression/test_asset_manifest_determinism.py`:
   - 동일 입력으로 manifest 2회 생성 → byte-exact 동일 (sort_keys 순서, hash 결정성)

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. REQ-032/01 prompts/phase2-impl.md 의 spec 확인
2. REQ-031 task 02 패턴 참조

## 규칙

- task 01 의 구현 코드 절대 수정 금지
- git commit 금지
- stdlib + pytest 만 사용
- [MANDATORY] 완료 전 신규 테스트 실행 + endtoend.sh 실행 후 응답에 출력 포함
- worktree 내부에서만 작업

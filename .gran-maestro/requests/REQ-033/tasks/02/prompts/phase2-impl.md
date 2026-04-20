# Implementation Request — REQ-033/02 (Integration Test)

- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-033-task-02
- 선행: REQ-029 ~ REQ-031, REQ-032, REQ-033/01 (7099b9a)

## 구현 컨텍스트 (PM 작성)

REQ-033/01 (7099b9a) 가 _stub_handler 차단 + 누락 규칙 등록 + drift cache 내장을 완료. 본 task 02 는 통합/회귀만 추가:

1. `tests/integration/test_req033_endtoend.sh`:
   - `check-rules-drift.py` (인자 없이) 실행 시 `[OK] N/N rules in sync` 출력 확인
   - `post-impl-verify.py` 실행 시 drift cache 동작 (첫 실행 → 캐시 생성, 두번째 → up-to-date)
   - rules.yaml 임의 touch 후 post-impl-verify 재실행 → drift check 재실행됨 확인
2. `tests/regression/test_req033_existing_validators.py`:
   - REQ-029 의 정책 3건 enforcement (margin-bottom / rules_conflict / constraints) 가 본 REQ 변경 후에도 PASS 유지
   - REQ-030/031/032 의 v2 카테고리들이 정상 작동 (figma-validate --version-info 가 모든 v2 카테고리 출력)
3. `tests/unit/test_meaningful_page_name_clarity.py`:
   - meaningful_page_name 의 description 명확화 후 (파일명 + 본문 모두 검사) HTML 본문에 의미 없는 페이지명 (`page_1`, `sub_01`) 이 있으면 FAIL, 의미있는 영문명 (`greeting`, `products`) 이면 PASS

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. REQ-033/01 prompts/phase2-impl.md 의 spec 참조
2. REQ-031/032 task 02 패턴 참조

## 규칙

- task 01 의 구현 코드 절대 수정 금지
- git commit 금지
- stdlib + pytest 만 사용
- [MANDATORY] 완료 전 신규 테스트 + endtoend.sh 실행 후 응답에 출력 포함
- worktree 내부에서만 작업

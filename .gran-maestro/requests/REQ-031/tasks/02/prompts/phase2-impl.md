# Implementation Request — REQ-031/02 (Integration Test)

- Request: REQ-031 / Task: 02 (test 후행)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-031-task-02
- 선행 commits: REQ-029 (431d0e3), REQ-030 (7fa6cd2), REQ-031/01 (2481ee3)

## 구현 컨텍스트 (PM 작성)

REQ-031/01 (2481ee3) 가 5축 추출 + 5 v2 카테고리 + 11 신규 unit test 를 작성하여 28 unit PASS 상태다. 본 task 02 는 통합/회귀 검증만 추가:

1. `tests/integration/test_req031_endtoend.sh` — figma-validate.py --version-info 출력에 신규 5 카테고리 (v2.strokes.match, v2.cornerRadii.match, v2.layoutSizing.match, v2.textCase.match, v2.textDecoration.match) 모두 등장하는지 확인 + section_03/04 spec 으로 validate 실행 시 exit code REQ-029 baseline 일치
2. `tests/regression/test_req031_add_only.py` — REQ-029/030 산출물 (extracted/section_03/04_spec.json) 의 기존 v2 키 변경 없이 REQ-031 의 신규 5축 키만 추가됐는지 확인 (spec 재추출 없이 정적 분석)
3. `tests/unit/test_paragraph_spacing_indent.py` — paragraphSpacing/paragraphIndent 기본값(0) 명시 검증

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-031/tasks/01/prompts/phase2-impl.md` 의 5축 spec 확인
2. REQ-030 의 task 02 패턴 (`tests/integration/test_req030_endtoend.sh`, `tests/regression/test_req030_add_only.py`) 참조
3. 위 3 신규 파일 작성 후 PASS 시킬 것

## 규칙

- task 01 의 구현 코드 절대 수정 금지
- git commit 금지
- stdlib + pytest 만 사용
- [MANDATORY] 완료 전 `pytest tests/ -v` (전체) + `bash tests/integration/test_req031_endtoend.sh` 실행 후 응답에 출력 포함
- 모든 변경은 worktree 내부에서 수행

# Implementation Request — REQ-034/02 (Final Integration Test)

- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-034-task-02
- 선행: REQ-029 ~ REQ-033, REQ-034/01 (5f0df5a) — Phase A 마지막 (PLN-009 6/6)

## 구현 컨텍스트 (PM 작성)

REQ-034/01 (5f0df5a) 가 post-impl-verify 강화 + repair JSON 계약 + v2 통합 라우터 + backup test fixture 패치 완료. 본 task 02 는 **Phase A 전체** 통합 검증을 마지막으로 수행:

1. `tests/integration/test_phase_a_endtoend.sh`:
   - `pytest tests/ -v --tb=short` 전체 실행 → 모든 PASS (test_backup_byte_exact 포함, REQ-034/01 fixture 패치 적용)
   - `python3 tools/check-rules-drift.py` (전체 모드) → exit=0
   - `python3 tools/figma-validate.py --version-info` → v1 9개 + v2 14개 카테고리 모두 출력 확인
   - `python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css` → exit code 캡처 (REQ-029 baseline 동등)
   - `python3 tools/migrate-spec-v1-to-v2.py --dry-run` → 경고 없이 정상 (이미 v2 상태)
2. `tests/regression/test_phase_a_progress.py`:
   - schema_version 이 spec.json 에 `"2.0.0"` 으로 존재
   - extracted/section_03_spec.json 에 REQ-029~034 의 모든 신규 키 (`fills_v2`, `effects`, `opacity`, `blendMode`, `strokes`, `rectangleCornerRadii`, `layoutSizingHorizontal/Vertical`, `layoutGrow`, `layoutAlign`, `componentId/componentSetId`, vector `viewBox`/`fillGeometryPathData` 등) 가 모두 존재
   - extracted.v1.backup/section_03_spec.json 의 schema_version 이 `1` (원본 보존)
3. `tests/unit/test_phase_a_summary.py`:
   - PLN-009 의 6개 REQ 가 main 에 squash-merge 되었는지 git 로그 확인 (각 commit subject 에 `[REQ-029]` ~ `[REQ-034]` 등장)

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. REQ-034/01 의 변경 (post-impl-verify, repair, figma-validate, test_backup_byte_exact) 확인
2. REQ-029~033 task 02 패턴 참조

## 규칙

- task 01 의 구현 코드 절대 수정 금지
- git commit 금지
- stdlib + pytest 만 사용
- [MANDATORY] 완료 전 endtoend.sh 와 신규 unit/regression 실행 후 응답에 출력 포함
- worktree 내부에서만 작업

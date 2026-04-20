# Implementation Request — REQ-034/01 (마지막)

- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-034-task-01
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md
- 선행 commits: REQ-029 (431d0e3), REQ-030 (7fa6cd2), REQ-031 (8919608), REQ-032 (cc619fc), REQ-033 (18bb9e0)

## 구현 컨텍스트 (PM 작성)

PLN-009 Phase A 마지막(6단계) — post-impl-verify 강화 + repair-from-violations 위반 JSON 계약 + figma-validate 신규 축 통합 + 잔존 정리:

1. **post-impl-verify.py 강화**:
   - **spec 자동 탐색 skip 제거**: 현재 (line 47, _find_spec) `extracted/` 자동 탐색 + 첫 spec 1개 채택 → 오매칭 통과 위험. spec 인자가 명시되지 않으면 exit=1 + `[FATAL] --spec is required` 에러로 변경.
   - **semantic MAJOR exit=1 반영**: 현재 semantic MAJOR 가 exit=0 으로 통과 (line 243-247, 333-340). MAJOR 1건이라도 있으면 exit=1.
   - **IGNORE-only exit=2 의미 명문화**: stdout 에 `[INFO] exit=2 means PASS-with-IGNORE-only (사용자 검수 권장)` 명시. README 또는 spec.md 별도 추가는 X.
2. **repair-from-violations.py 위반 JSON 계약 고정**:
   - 현재 (line 277-290, 412-413) 위반 개수만 사용 → 위반 JSON 의 `{rule_id, file, line, expected, actual, fix_strategy, patch_hint}` **전체 필드** 사용
   - patch_hint 가 있으면 외주 브리프에 그대로 첨부 (Append). 없으면 `"패치 힌트 없음 — 직접 수정 필요"` 명시.
   - 위반 JSON 스키마 검증: 필수 필드 (`rule_id`, `file`) 누락 시 즉시 에러.
   - 자동 재dispatch 수렴형 N회 제한: `config.retry.max_cli_retries` 존중하되, 연속 무변경 (이전 위반 카운트와 동일) 시 조기 종료.
3. **figma-validate.py — 신규 v2 카테고리 통합 검증**:
   - REQ-030/031/032 가 추가한 14 v2 카테고리 (`v2.fills.*`, `v2.effects.*`, `v2.opacity.match`, `v2.blendMode.match`, `v2.strokes.match`, `v2.cornerRadii.match`, `v2.layoutSizing.match`, `v2.textCase.match`, `v2.textDecoration.match`, `v2.componentId.match`, `v2.assetManifest.exists`) 가 모두 단일 진입점에서 호출되도록 통합 검증
   - 통합 카테고리 라우터 함수 (예: `run_v2_categories()`) — 분기 깔끔히 정리
4. **REQ-030/02 의 잔존 이슈 패치**: `tests/regression/test_backup_byte_exact.py` 가 squash-merge 후 HEAD~1 의미 변경으로 fail. 해결:
   - 옵션 A: 테스트를 `extracted.v1.backup/` 의 SHA-256 ↔ `git show $(git rev-list --max-parents=0 HEAD):extracted/...` (root commit) 비교로 변경 — 너무 복잡
   - 옵션 B: 테스트를 marker 기반으로 변경 — `extracted.v1.backup/` 의 SHA-256 hash 를 별도 fixture (`tests/fixtures/req029_backup_hashes.json`) 에 baseline 으로 저장하고 비교
   - PM 권장: **옵션 B** (간단 + 안정적)

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. plan + 선행 REQ-029~033 의 변경사항 (특히 REQ-033 의 drift cache 와 _stub_handler 차단 패턴)
2. `tools/post-impl-verify.py` 의 `_find_spec` (line 47), 심각도 표 (line 13-26, 96-106), exit code 분기 (line 243-247, 333-340, 209-210)
3. `tools/repair-from-violations.py` 의 위반 처리 (line 277-290, 412-413)
4. `tools/figma-validate.py` 의 v2 카테고리 호출 흐름 (REQ-030~032 가 추가한 14 카테고리)

## 핵심 구현 지침

1. **spec 자동 탐색 제거**: `_find_spec` 함수를 deprecated 처리 또는 제거. CLI 인자 `--spec` 가 없으면 즉시 에러 종료.
2. **semantic MAJOR exit code 반영**: 현재 logic 변경 (`if semantic_major > 0: exit_code = 1`)
3. **IGNORE-only exit=2 메시지**: stdout 출력에 의미 명시 1줄 추가
4. **repair JSON 계약**:
   - 위반 JSON 스키마 dict 검증 함수 추가 (`_validate_violation_schema()`)
   - 외주 브리프에 위반 상세 첨부 (rule_id/file/line/expected/actual/fix_strategy/patch_hint 표 형태)
   - 수렴형 N회: `config.retry.max_cli_retries` (기본 2) + 연속 무변경 시 조기 종료
5. **figma-validate v2 통합**: 14 카테고리를 단일 진입점에서 호출 (분기 정리)
6. **test_backup_byte_exact 패치**:
   - 새 fixture 생성: `tests/fixtures/req029_backup_hashes.json` (현재 backup 의 SHA-256 hash 4개)
   - 테스트를 fixture 비교로 변경 — git history 의존 제거
7. **결정성/add-only/stdlib only**

## 작성 테스트

- `tests/unit/test_post_impl_no_spec_fatal.py`: --spec 미지정 시 즉시 exit=1
- `tests/unit/test_post_impl_semantic_major_exit1.py`: semantic MAJOR 시 exit=1
- `tests/unit/test_repair_violation_schema.py`: 위반 JSON 필수 필드 누락 시 에러
- `tests/unit/test_repair_convergence.py`: 연속 무변경 시 조기 종료
- `tests/integration/test_v2_categories_integration.sh`: 14 v2 카테고리 모두 단일 호출에서 실행 확인
- `tests/regression/test_backup_byte_exact.py` 패치 (fixture 기반)

## 규칙

- spec §2 변경 범위 외 파일 수정 금지
- git commit 금지 (PM 처리)
- stdlib 만 사용
- TDD: spec 자동 탐색 제거, repair JSON 계약, figma-validate 통합 모두 [tdd-required]
- [MANDATORY] 완료 전 신규 테스트 + integration 실행 후 응답에 출력 포함
- worktree 내부에서만 작업

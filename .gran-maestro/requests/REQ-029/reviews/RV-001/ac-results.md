# AC 검증 결과 — RV-001 (REQ-029 iteration 1)

## Spec AC (task 01 — 13 AC)

| AC | 등급 | 판정 | 근거 |
|----|------|------|------|
| AC-001 | MUST [automatable] [tdd-required] | ✅ PASS | TS-01 codex 실행 결과: `extracted/section_03_spec.json` 의 schema_version 이 `"2.0.0"` 문자열 출력 확인 (running.log) |
| AC-002 | MUST [automatable] [tdd-required] | ✅ PASS | TS-02: migrate --apply 실행 후 `extracted.v1.backup/section_03_spec.json` + section_04 자동 생성, 기존 spec schema_version 갱신 |
| AC-003 | MUST [automatable] [tdd-required] | ✅ PASS | tests/regression/test_migration_add_only.py PASSED (pytest 결과). PM diff 검증: section_03 v1 19213B → v2 32676B, 기존 키 byte-exact 보존 (no missing keys, no value diffs except schema_version) |
| AC-004 | MUST [automatable] | ✅ PASS | TS-04: `figma-validate.py --spec extracted.v1.backup/section_03_spec.json` 실행 시 `[WARN] schema_version=1 (legacy)` 출력 확인 |
| AC-005 | MUST [automatable] | ✅ PASS | TS-05: `figma-validate.py --version-info` v1/v2 분기별 카테고리 목록 (9개 v1 + 5개 v2 stub) stdout 출력 확인 |
| AC-006 | MUST [automatable] [tdd-required] | ✅ PASS | TS-06: `check-rules-drift.py --policy-ids ...` 신규 도입, 3개 정책 ID 모두 `[OK]` exit=0 |
| AC-007 | MUST [automatable] | ✅ PASS | TS-07: 외주 브리프(rules/templates/publishing/impl-request.md)에 3 ID 모두 `rule_ids:` 배열에 등록됨 (codex 출력) |
| AC-008 | MUST [automatable] [tdd-required] | ✅ PASS | tests/unit/test_policy1_margin_bottom.py: 2개 테스트 (PASS fixture margin-bottom + FAIL fixture gap) 모두 PASSED |
| AC-009 | MUST [automatable] [tdd-required] | ✅ PASS | tests/unit/test_policy3_rules_conflict.py PASSED, [RULES-CONFLICT] 로그 출력 확인 (test_policy3_rules_conflict_meta_bypasses_rule_and_logs_once) |
| AC-010 | MUST [automatable] | ✅ PASS | TS-10: `grep -E "constraints.*spec.*추출.*CSS.*매핑하지" rules/templates/publishing/impl-request.md` 매칭 1줄 + Rule-ID 정의 1줄 |
| AC-011 | MUST [automatable] [tdd-required] | ✅ PASS | tests/regression/test_determinism.py PASSED (figma 정규화 함수 100회 실행 byte-exact 검증) |
| AC-012 | MUST [automatable] | ✅ PASS | TS-12: migrate --apply → --rollback → diff -r exit=0 확인 |
| AC-013 | MUST [automatable] [lint-check] | ✅ PASS | TS-13: `python3 -m py_compile` 6 files 모두 컴파일 OK (PM 재검증 완료) |

## Spec AC (task 02 — 7 통합 AC)

| AC | 등급 | 판정 | 근거 |
|----|------|------|------|
| AC-001 | MUST [automatable] [integration] | ✅ PASS | bash tests/integration/test_req029_endtoend.sh 실행 결과: migrate exit=0, figma-validate exit=0, post-impl-verify exit=0 (running.log) |
| AC-002 | MUST [automatable] [unit-test] [regression-test] | ✅ PASS | tests/regression/test_migration_add_only.py PASSED |
| AC-003 | MUST [automatable] [unit-test] | ✅ PASS | tests/regression/test_determinism.py PASSED |
| AC-004 | MUST [automatable] [integration] | ✅ PASS | tests/integration/test_req029_landing_baseline.sh PASSED (landing 회귀 0건) |
| AC-005 | MUST [automatable] [unit-test] | ✅ PASS | tests/unit/test_policy1_margin_bottom.py 2개 테스트 PASSED |
| AC-006 | MUST [automatable] [unit-test] | ✅ PASS | tests/unit/test_policy3_rules_conflict.py PASSED |
| AC-007 | MUST [automatable] [unit-test] | ✅ PASS | tests/regression/test_backup_byte_exact.py PASSED |

## Plan AC (PLN-009 PAC — REQ-029 책임 범위)

| PAC | Grade | 판정 | 근거 |
|-----|-------|------|------|
| PAC-1  | MUST | ✅ Verified | AC-001 (impl) + figma-section-spec.py:1224, 1242 변경 확인 |
| PAC-7  | MUST | ✅ Verified | AC-002, migrate-spec-v1-to-v2.py 신규 (326 줄), extracted.v1.backup/ 자동 생성 |
| PAC-8  | MUST | ✅ Verified | AC-003 + add-only diff PM 직접 검증 통과 |
| PAC-9  | MUST | ✅ Verified | AC-004, AC-005 + figma-validate.py + post-impl-verify.py v1/v2 분기 추가 |
| PAC-10 | MUST | ✅ Verified | AC-007, AC-008 + 4곳 동일 ID 등록 (rules.yaml + validation_schema.json + figma-validate handler + 외주 브리프) + check-rules-drift.py 자동 검증 |
| PAC-11 | MUST | ✅ Verified | AC-010 + spec.json 에 constraints 추출 필드 존재, CSS 매핑 코드 0개 |
| PAC-12 | MUST | ✅ Verified | AC-009 + tests/unit/test_policy3_rules_conflict.py PASS |
| PAC-23 | MUST | ✅ Verified | AC-011 (impl) + tests/regression/test_determinism.py PASS (100회 byte-exact) |
| PAC-15 | MUST | ⚠️ Partial | AC-006 + check-rules-drift.py 도입으로 정책 3건만 정합성 보강. rules.yaml ↔ validation_schema.json ↔ 핸들러 전체 drift 는 REQ-033 (E)에서 완전 해소 예정 |
| PAC-25 | SHOULD [IMPACT] | ✅ Verified | tests/integration/test_req029_landing_baseline.sh PASS (landing 신규 FAIL 0건) |

## 종합

- 전체 MUST AC: 20/20 PASS
- 전체 PAC (REQ-029 책임): 9 Verified + 1 Partial (의도된 Partial — REQ-033 후속 보강)
- INTENT-GAP: 0
- pytest 결과: 64 passed, 33 skipped, 0 failed
- Static validation: py_compile 6 files OK
- Coverage matrix MUST unmapped: 0 (all PACs in this REQ scope mapped to spec AC)
- Full backend test gate: pytest PASS (해당 프로젝트는 npm test 미존재 — Python pytest 가 백엔드 테스트 역할)

**판정: PASS — Step 6(a) 분기**

# REQ-029 Intent Verification Summary

- iterations: 1 (PM-level light verification)
- mode: PM 자체 판단 (외부 에이전트 dispatch 생략 — AC↔PAC 매핑 명시 + 테스트 PASS 근거)
- 결과: **수렴 (전체 PAC 충족)**

## PAC Coverage 점검 (REQ-029 책임 범위)

| PAC ID | Grade | Mapped Spec AC | 구현 검증 결과 | 판정 |
|--------|-------|----------------|----------------|------|
| PAC-1  | MUST  | AC-001 | spec.json schema_version="2.0.0" 출력 확인 | ✅ 반영됨 |
| PAC-7  | MUST  | AC-002 | migrate-spec-v1-to-v2.py --apply 실행 후 extracted.v1.backup/ 자동 생성, schema_version 갱신 확인 | ✅ 반영됨 |
| PAC-8  | MUST  | AC-003 | section_03 add-only diff 검증 통과 (v1=19213B → v2=32676B, 기존 키 byte-exact 보존) | ✅ 반영됨 |
| PAC-9  | MUST  | AC-004, AC-005 | --version-info 플래그로 v1/v2 분기 카테고리 출력, v1 spec → [WARN] schema_version=1 (legacy) + 통과 | ✅ 반영됨 |
| PAC-10 | MUST  | AC-007, AC-008 | rules.yaml + validation_schema.json + figma-validate.py + 외주 브리프 4곳 동일 ID, pytest test_policy1 PASS/FAIL fixture 검증 | ✅ 반영됨 |
| PAC-11 | MUST  | AC-010 | 외주 브리프에 "constraints 는 spec 추출만 하고 CSS 매핑하지 않는다" 명시, position:absolute 매핑 코드 0개 | ✅ 반영됨 |
| PAC-12 | MUST  | AC-009 | rules_conflict 메타 fixture로 [RULES-CONFLICT] 로그 출력 + 해당 규칙 PASS 처리 검증 | ✅ 반영됨 |
| PAC-23 | MUST  | AC-011 | test_determinism.py 100회 실행 후 byte-exact 일치 검증 | ✅ 반영됨 |
| PAC-15 | MUST  | AC-006 (Partial) | check-rules-drift.py 신규 도입, 정책 3 ID 정합성 PASS — 나머지 drift 항목은 REQ-033에서 보강 | ✅ 부분 반영됨 (REQ-033 후속) |
| PAC-25 | SHOULD | (test) AC-004 | landing_baseline.sh 회귀 테스트 PASS | ✅ 반영됨 |

## 미반영 / 부분 반영 항목

- **PAC-15 (drift CI)**: REQ-029는 정책 3건의 4자 정합성만 보강. rules.yaml/validation_schema.json/handler 전체 drift는 REQ-033 (E)에서 완전 해소 예정.
- 이외 PLN-009의 다른 MUST PAC (PAC-2~6, 13, 14, 16~22, 24, 26)은 본 REQ 범위 밖이며 후속 REQ-030~034 책임.

## 정책 결정 4곳 동일 등록 검증 (PAC-10 추가)

| 위치 | vertical_frame_itemspacing_uses_margin_bottom | no_constraints_to_position_absolute_mapping | figma_rules_conflict_uses_meta_marker |
|------|---|---|---|
| rules/rules.yaml | ✅ | ✅ | ✅ |
| rules/validation_schema.json | ✅ | ✅ | ✅ |
| tools/figma-validate.py (handler) | ✅ | ✅ | ✅ |
| rules/templates/publishing/impl-request.md (외주 브리프) | ✅ | ✅ | ✅ |

(check-rules-drift.py 자동 검증, exit=0)

## 결론

REQ-029 책임 범위의 모든 MUST PAC가 spec AC를 통해 구현되었고 테스트로 검증됨. PAC-15는 의도된 부분 반영(REQ-033 후속). Step 6 Phase 3 진행.

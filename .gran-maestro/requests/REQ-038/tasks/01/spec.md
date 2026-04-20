# Spec — REQ-038 / Task 01: validator 강화 (패턴 확장 + 주석 제외)

**Assigned Agent**: `[config: codex-dev] codex-dev`
**Status**: pending

---

## §0 Context Manifest

- `rules/rules.yaml` — `no_forbidden_class` 룰 정의 (현재 `sec_1|sec_2|section_01|box1|box2`)
- `rules/models.py` — Pydantic SSOT (Phase B)
- `rules/validation_schema.json` — 자동 생성
- `tools/validate-semantic.py` — `forbidden_substring` 검사 구현
- `tools/figma-validate.py` — forbidden_substring 공유 여부 확인

## §1 요약

두 가지 validator 정확도 개선:

1. **패턴 확장**: `no_forbidden_class` 의 regex 를 `sec_\d+|section_\d+|box\d+` 범위로 확장 → 사용자 원래 규칙 의도 ("숫자 섹션 네이밍 전면 금지") 를 완전 커버.
2. **HTML 주석 제외**: `forbidden_substring` 이 HTML 을 스캔할 때 `<!-- ... -->` 내부는 무시 → 주석 false positive 차단.

## §2 범위

**포함**:
- `rules/rules.yaml` 의 `no_forbidden_class.validation.pattern` 업데이트: `sec_\d+|section_\d+|box\d+`
- `rules/rules.yaml` 의 `no_forbidden_class.examples.bad` 업데이트 (예시 보강)
- `rules/models.py` Pydantic 모델로 자동 재생성된 `rules/validation_schema.json` 확인
- `tools/validate-semantic.py` 의 `forbidden_substring` 검사 시 HTML 주석 strip (pre-processing)
- 주석 제외 로직: `<!--.*?-->` 를 `re.DOTALL` 옵션으로 제거 후 검사
- 신규/보강 테스트 3종

**제외**:
- CSS 주석 (`/* ... */`) 제외 처리 (별도 이슈)
- 다른 `forbidden_substring` 룰의 HTML 주석 처리 (공통 유틸로 통합될 경우 간접 영향 OK, 명시적 변경 제외)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] sec_\d+ 전체 범위 감지

- **Given**: HTML `<section class="sec_3">...</section>`
- **When**: `python3 tools/validate-semantic.py --html ... --css ... --profile landing` 실행
- **Then**: `no_forbidden_class` CRITICAL 위반 1건 출력, exit 1
- **Test**: `pytest tests/unit/test_forbidden_class_numeric_range.py -v` (신규)

### AC-002 [automatable] [tdd-required] HTML 주석 내부 sec_1 false positive 차단

- **Given**: HTML `<!-- sec_1 --><div class="main_hero">...</div>` (주석에만 sec_1 존재, 실제 class 에는 없음)
- **When**: validate-semantic 실행
- **Then**: `no_forbidden_class` 위반 0건
- **Test**: `pytest tests/unit/test_forbidden_class_ignores_html_comments.py -v` (신규)

### AC-003 [automatable] [regression-test] 기존 sec_1/sec_2 직접 사용은 여전히 감지

- **Given**: HTML `<section class="sec_1">` (실제 class 사용)
- **When**: validate-semantic 실행
- **Then**: CRITICAL 1건 감지 (regression 없음)
- **Test**: `pytest tests/unit/test_forbidden_class_direct_usage.py -v` (신규)

### AC-004 [automatable] [regression-test] 기존 pytest 137 passed 회귀 없음

- **Given**: main 기준 pytest 137 passed / 33 skipped
- **When**: `pytest tests/ -v` 실행
- **Then**: 137+ passed, 0 failed
- **Test**: `pytest tests/ -v`

### AC-005 [automatable] 63/63 rules in sync 유지

- **Given**: rules.yaml pattern 변경 후 Pydantic 재생성
- **When**: `python3 tools/check-rules-drift.py --all` 실행
- **Then**: exit 0, "63/63 rules in sync"
- **Test**: `tests/regression/test_drift_zero.py` 기존 테스트 그대로 통과

## §3.2 Test Scenarios (Pre-Impl)

- AC-001: `pytest tests/unit/test_forbidden_class_numeric_range.py -v`
- AC-002: `pytest tests/unit/test_forbidden_class_ignores_html_comments.py -v`
- AC-003: `pytest tests/unit/test_forbidden_class_direct_usage.py -v`
- AC-004: `pytest tests/ -v`
- AC-005: `python3 tools/check-rules-drift.py --all`

## §3.3 PAC Mapping

(standalone REQ — no linked plan)

## §3.5 Constraints

- `rules.yaml` 수정 후 `python -m rules.models` 로 `validation_schema.json` 재생성 필수
- `forbidden_substring` 검사 유틸의 시그니처 변경 시 다른 호출부 회귀 없음 확인
- HTML 주석 제외는 HTML target 에만 적용 (CSS target 은 현재 스캔 안 함, 향후 `/* */` 별도)
- Python 3.10+, 기존 의존성만 사용
- 코드 주석은 영어만

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | — | codex-dev |

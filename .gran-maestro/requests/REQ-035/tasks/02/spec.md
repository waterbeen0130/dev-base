# Spec — REQ-035 / Task 02: check-rules-drift 승격 + figma-validate handler Pydantic 재정렬

**Assigned Agent**: `[config: codex-dev] codex-dev` (Python backend refactor + test)
**Status**: pending
**Plan**: PLN-010
**Linked Intent**: INTENT-006

---

## §0 Context Manifest

- `rules/models.py` — Task 01 산출물 (Pydantic v2 SSOT)
- `rules/rules.yaml` — 63 rules 정의
- `rules/validation_schema.json` — Task 01 에서 자동 생성된 schema
- `tools/check-rules-drift.py` — 현재 drift 감지 스크립트
- `tools/figma-validate.py` — v1 9 + v2 14 = 23 카테고리, handler 구현부
- `tools/post-impl-verify.py` — drift cache 내장 (REQ-033) 경로 참고

## §1 요약

Task 01 에서 정의된 Pydantic SSOT 를 활용하여:
1. `tools/check-rules-drift.py` 를 Pydantic 모델 ↔ `rules.yaml` ↔ `figma-validate.py` handler 3자 정합 감지기로 **승격**한다.
2. `tools/figma-validate.py` 의 handler 계약을 Pydantic 모델 `RuleDefinition` 기반으로 재정렬한다 (handler dispatch 시 모델을 인자로 받고, stub/missing handler 는 MAJOR FAIL).

## §2 범위

**포함**:
- `tools/check-rules-drift.py` 리팩토링: Pydantic `ValidationSchema` 로드 → rules.yaml 해시 비교 → figma-validate handler 엔트리 비교
- `tools/figma-validate.py` 의 handler dispatch 를 `RuleDefinition` 인자 기반으로 재정렬
- `--all` 모드 유지 (REQ-033 도입)
- 63/63 in sync 결과 유지
- 기존 `_stub_handler` MAJOR FAIL 정책 유지 (구조 변경 금지, 내부 구현만 Pydantic 기반)

**제외**:
- 새로운 rule 추가/제거
- rules.yaml 구조 변경
- Phase C/D (REQ-036/REQ-037 범위)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] check-rules-drift 가 Pydantic 모델 기반 3자 정합 감지 (PAC-2)

- **Given**: `rules/models.py` SSOT + `rules/rules.yaml` + `tools/figma-validate.py` handler
- **When**: `python3 tools/check-rules-drift.py --all` 실행
- **Then**: exit 0, "63/63 rules in sync" 출력
- **Test**: `pytest tests/regression/test_drift_zero.py -v`

### AC-002 [automatable] Pydantic 모델 변경 시 drift 감지 동작 (PAC-2)

- **Given**: rules/models.py 에 mock rule 1개 강제 누락
- **When**: `python3 tools/check-rules-drift.py --all` 실행
- **Then**: exit 1, drift 감지 메시지 출력
- **Test**: `pytest tests/unit/test_drift_detection_on_injection.py -v` (신규, fixture 기반 주입 후 rollback)

### AC-003 [automatable] figma-validate handler 가 RuleDefinition 모델 인자 수용 (PAC-2)

- **Given**: Pydantic `RuleDefinition` 인스턴스
- **When**: figma-validate 내부 handler 호출
- **Then**: handler 시그니처가 `RuleDefinition` 을 수용하고, stub/missing handler 는 기존처럼 MAJOR FAIL
- **Test**: `pytest tests/unit/test_handler_pydantic_signature.py -v` (신규)

### AC-004 [automatable] [regression-test] v1/v2 = 23 카테고리 전부 동작 (PAC-2)

- **Given**: PLN-009 기준 v1 9 + v2 14 카테고리 활성
- **When**: `python3 tools/figma-validate.py --version-info` 실행
- **Then**: 출력이 REQ-034 시점과 동일 (카테고리 개수/이름 보존)
- **Test**: `pytest tests/regression/test_figma_validate_categories.py -v`

## §3.2 Test Scenarios (Pre-Impl)

- AC-001: `python3 tools/check-rules-drift.py --all` → exit 0, "63/63 rules in sync" 출력
- AC-002: fixture 주입 테스트 `pytest tests/unit/test_drift_detection_on_injection.py -v` → mock 누락 시 exit 1 감지
- AC-003: `pytest tests/unit/test_handler_pydantic_signature.py -v` — handler가 RuleDefinition 수용
- AC-004: `python3 tools/figma-validate.py --version-info` 출력이 REQ-034 시점과 동일 (v1=9 + v2=14)

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-2 | MUST | AC-001, AC-002, AC-003, AC-004 | full |

## §3.5 Constraints

- Task 01 완료(rules/models.py 존재)가 전제
- `tools/check-rules-drift.py` 의 CLI 인터페이스(`--all` 등) 유지 — 사용자/CI 호환
- handler 재정렬 시 기존 handler body 의 동작은 불변, 시그니처만 변경 허용

## §5 선행 작업 (blockedBy)

- REQ-035 / Task 01

## §6 후행 작업 (blocks)

- REQ-035 / Task 03 (최종 회귀)

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | 02, 03 | codex-dev |
| 02 | 01 | 03 | codex-dev |
| 03 | 01, 02 | — | codex-dev |

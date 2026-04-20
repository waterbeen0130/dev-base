# Spec — REQ-035 / Task 01: Pydantic v2 SSOT 모델 정의 + validation_schema 자동 생성

**Assigned Agent**: `[config: codex-dev] codex-dev` (Python backend refactor + test)
**Status**: pending
**Plan**: PLN-010
**Linked Intent**: INTENT-006

---

## §0 Context Manifest

아래 파일들을 반드시 Read 하여 현재 구조/컨벤션을 이해한 뒤 구현한다. 이 목록은 완전하지 않을 수 있으며 에이전트는 worktree 내에서 자율 탐색을 병행한다.

- `rules/rules.yaml` — 63 rules SSOT (현재)
- `rules/validation_schema.json` — rules.yaml 에서 파생된 JSON schema
- `tools/check-rules-drift.py` — 현 drift 감지 스크립트 (Pydantic 기반으로 승격)
- `tools/figma-validate.py` — v1/v2 카테고리 분기, handler 계약
- `tools/build-rules.py` (참고) — 기존 yaml → artifact 생성 스크립트
- `pyproject.toml` — 의존성 정의
- `tests/` — 기존 113 passed pytest suite (회귀 대상)

## §1 요약

`rules/rules.yaml` 을 1차 SSOT 로 유지하되, **Pydantic v2 모델을 검증 엔진의 내부 SSOT** 로 도입한다. Pydantic 모델이 rules.yaml 을 로드하여 구조적으로 검증하고, `model_json_schema()` 로 `rules/validation_schema.json` 을 자동 생성한다. 수동 편집 경로를 제거한다.

## §2 범위

**포함**:
- `rules/models.py` 신규 작성 — Pydantic v2 모델 (`RuleDefinition`, `CategoryDefinition`, `ValidationSchema`, severity/type enum)
- `python -m rules.models` 실행 시 `rules/validation_schema.json` 자동 생성 경로
- `rules/rules.yaml` → Pydantic 모델 로드 + 정합 검증 (63 rules)
- `pyproject.toml` 에 `pydantic>=2.6` 추가
- 생성된 `validation_schema.json` 에 `<!-- AUTO-GENERATED FROM rules/models.py — DO NOT EDIT -->` 헤더 주입

**제외**:
- `tools/figma-validate.py` handler 재정렬 (Task 02 범위)
- `tools/check-rules-drift.py` 승격 (Task 02 범위)
- rules.yaml 자체 구조 변경 (기존 63 rules 정의는 불변)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] Pydantic 모델이 rules.yaml 을 로드하여 63 rules 를 검증한다 (PAC-1)

- **Given**: `rules/rules.yaml` 에 63 rules 가 정의되어 있다
- **When**: `python -c "from rules.models import load_rules; print(len(load_rules()))"` 실행
- **Then**: 출력값이 63 이고, 각 rule 은 `RuleDefinition` 인스턴스로 파싱된다
- **Test**: `pytest tests/unit/test_pydantic_rules_load.py -v` (신규)

### AC-002 [automatable] [tdd-required] model_json_schema() 로 validation_schema.json 이 자동 생성된다 (PAC-1)

- **Given**: `rules/models.py` 의 `ValidationSchema` 모델 정의
- **When**: `python -m rules.models` 실행
- **Then**: `rules/validation_schema.json` 이 생성되고, 기존 파일 대비 의미적 동등 (rule ID 목록 + type enum + severity enum 동일)
- **Test**: `pytest tests/unit/test_schema_autogen.py -v` (신규)

### AC-003 [automatable] 수동 편집 경로 차단 (AUTO-GENERATED 헤더 확인) (PAC-1)

- **Given**: 자동 생성된 `rules/validation_schema.json`
- **When**: 파일 1번째 줄 Read
- **Then**: `// AUTO-GENERATED FROM rules/models.py — DO NOT EDIT` 주석이 존재한다 (JSON comment 지원 안 되면 `"$comment": "AUTO-GENERATED ..."` 필드 최상위 주입)
- **Test**: `pytest tests/unit/test_schema_autogen_header.py -v` (신규)

### AC-004 [automatable] [regression-test] 기존 pytest 전체 회귀 없음 (PAC-3)

- **Given**: PLN-009 기준 pytest 113 passed / 33 skipped
- **When**: `pytest tests/ -v` 실행
- **Then**: 113+ passed, 0 failed (신규 테스트 추가 허용, 기존 테스트 깨짐 금지)
- **Test**: `pytest tests/ -v`

### AC-005 [automatable] pyproject.toml 에 pydantic 의존성 선언 (PAC-1)

- **Given**: `pyproject.toml`
- **When**: `grep "pydantic" pyproject.toml` 실행
- **Then**: `pydantic>=2.6` 또는 동등 선언이 `[project]` 또는 `[tool.poetry.dependencies]` 등 적절한 섹션에 존재한다
- **Test**: `pytest tests/unit/test_pyproject_deps.py -v` (신규)

## §3.2 Test Scenarios (Pre-Impl)

- AC-001: `pytest tests/unit/test_pydantic_rules_load.py -v` — rules.yaml 로드 후 63 rules RuleDefinition 파싱 성공
- AC-002: `python3 -m rules.models` 실행 후 `test -f rules/validation_schema.json` + `pytest tests/unit/test_schema_autogen.py -v`
- AC-003: `head -1 rules/validation_schema.json` 또는 최상위 필드 `$comment`에서 "AUTO-GENERATED FROM rules/models.py" 확인
- AC-004: `pytest tests/ -v` 전체 회귀 (≥113 passed, 0 failed)
- AC-005: `grep -E "^\s*\"?pydantic\"?\s*[:=]" pyproject.toml` — pydantic>=2.6 선언 확인

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-1 | MUST | AC-001, AC-002, AC-003, AC-005 | full |
| PAC-2 | MUST | (Task 02) | deferred-to-task-02 |
| PAC-3 | SHOULD | AC-004 | full |

## §3.5 Constraints

- Python 3.10+ 문법 허용
- Pydantic v2 전용 (v1 API 호출 금지)
- stdlib 외 의존성은 `pydantic` 만 추가 (yaml 로더는 기존 `pyyaml` 재사용 가능)
- `rules/rules.yaml` 의 구조/내용은 본 태스크에서 수정하지 않는다 (읽기 전용)
- `validation_schema.json` 의 기존 rule ID 목록은 100% 보존 (add-only 는 허용, 삭제 금지)

## §4 디자인 힌트

- `RuleDefinition` 필드 예시: `id: str`, `category: CategoryEnum`, `type: ValidationType`, `severity: Severity`, `pattern: str | None`, `message: str`, `profiles: list[str]`, `priority: int | None`, `custom_handler: str | None`
- `ValidationSchema` 는 `rules: list[RuleDefinition]`, `categories: list[CategoryDefinition]`, `schema_version: str` 을 갖는 루트 모델
- `model_json_schema()` 출력을 `rules/validation_schema.json` 에 직렬화할 때 indent=2, sort_keys=False (기존 순서 보존)

## §5 선행 작업 (blockedBy)

- 없음 (REQ-035 첫 태스크)

## §6 후행 작업 (blocks)

- Task 02 (check-rules-drift 승격 + figma-validate handler 재정렬) — 본 태스크의 Pydantic 모델을 전제로 함
- Task 03 (회귀 테스트 최종 수렴)

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

이유: Python 백엔드 리팩토링 + Pydantic 모델 정의 + 테스트 작성은 codex-dev 의 code/refactor/test capability 에 최적. CLAUDE.md §멀티 에이전트 분배 규칙 — "백엔드 전용" 케이스.

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | 02, 03 | codex-dev |
| 02 | 01 | 03 | codex-dev |
| 03 | 01, 02 | — | codex-dev |

## Intent (JTBD)

- When I: Figma→Code 파이프라인의 규칙 정의를 유지보수할 때
- I want to: rules.yaml ↔ validation_schema.json ↔ figma-validate handler 3자 drift 를 구조적으로 불가능하게 만들도록
- So I can: 매번 수동 drift 체크 없이도 63 rules 가 자동으로 3자 정합을 유지할 수 있다
- Motivation: PLN-009 Phase A 에서 수동 drift 체크 + `_stub_handler` MAJOR FAIL 도입으로 일시적 해소했지만, 근본적 해결은 SSOT 단일화임

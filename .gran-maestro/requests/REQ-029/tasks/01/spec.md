# Implementation Spec

- Request ID: REQ-029
- Task ID: 01
- Created: 2026-04-19T06:43:14.000Z
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: backend (Python tool/CLI 변경)] → 최종: codex-dev
- Assigned Team: codex-dev 단독 (외주 에이전트)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-029-task-01
- Complexity: High-Risk

## §0 Context Manifest

> 구현 시작 전 이 목록의 파일을 가장 먼저 Read하세요.
> 이 목록이 완전하지 않을 수 있으며, 에이전트는 자율 탐색을 유지해야 합니다.

- /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md
- /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/synthesis.md
- /mnt/d/dev-base/tools/figma-section-spec.py (line 1224, 1242: schema_version 하드코딩 위치)
- /mnt/d/dev-base/tools/figma-validate.py (1404 줄, validator entry / 9개 카테고리)
- /mnt/d/dev-base/tools/post-impl-verify.py (line 47: _find_spec — 자동 탐색 로직)
- /mnt/d/dev-base/tools/build-rules.py (line 314: schema_version 의존)
- /mnt/d/dev-base/rules/rules.yaml (rules_version: 2)
- /mnt/d/dev-base/rules/validation_schema.json
- /mnt/d/dev-base/rules/templates/publishing/impl-request.md (외주 브리프 템플릿)
- /mnt/d/dev-base/extracted/section_03_spec.json (regression baseline 1)
- /mnt/d/dev-base/extracted/section_04_spec.json (regression baseline 2)

## 1. 요약 (Summary)

선결 정책 3건(VERTICAL itemSpacing / constraints / spec-vs-rules)을 4곳에 동일 문구로 문서화하고, `schema_version`을 숫자 `1` → 문자열 `"2.0.0"` semver 로 전환하며, 전체 프로젝트 spec 을 v1 → v2 로 재생성하는 migration 스크립트와 v1/v2 분기 파서를 도입한다.

## 2. 범위 (Scope)

- **포함**:
  - `tools/figma-section-spec.py` 의 `schema_version` 출력값을 `"2.0.0"` 으로 변경 (1224, 1242 두 지점)
  - `tools/build-rules.py:314` 의 `schema_version` 기본값 호환 처리 (정수/문자열 모두 수용)
  - `tools/figma-validate.py` + `tools/post-impl-verify.py` 에 v1/v2 분기 파서 추가 (v1 spec 은 warn 만 출력하고 통과, v2 는 신규 검증 카테고리 적용 가능 상태로 진입)
  - `tools/migrate-spec-v1-to-v2.py` 신규 스크립트 작성 (stdlib 만 사용)
    - 프로젝트 루트(`/mnt/d/dev-base`) 하위에서 `**/extracted/**/*_spec.json` 전부 스캔
    - 첫 실행 시 `extracted.v1.backup/` 디렉토리 자동 생성 후 원본 복사
    - `figma-section-spec.py` 의 신규 v2 추출기를 통과시키되 기존 값 변경 금지 (add-only diff 보장)
    - `_extra` 키 도입: Figma API 응답에 알 수 없는 필드가 들어오면 누락하지 않고 `_extra` 에 보존
    - `--dry-run` / `--apply` / `--rollback` 3 모드 제공
  - 정책 3건을 동일 문구로 4곳에 추가:
    1. `rules/rules.yaml` — 3개 신규 Rule-ID 항목 (`vertical_frame_itemspacing_uses_margin_bottom`, `no_constraints_to_position_absolute_mapping`, `figma_rules_conflict_uses_meta_marker`)
    2. `rules/validation_schema.json` — 위 3 Rule-ID 의 schema enum / handler binding entries
    3. `rules/templates/publishing/impl-request.md` — 외주 브리프 "## 코딩 규칙" 섹션에 3 정책 명시 (rule_ids 목록에 ID 추가)
    4. `tools/figma-validate.py` — 정책 1·3 enforcement 함수 추가 (정책 1: VERTICAL frame itemSpacing>0 spec → CSS 변환 시 margin-bottom 외에는 FAIL / 정책 3: spec 노드의 `rules_conflict` 메타가 있으면 해당 노드 검증을 PASS 처리)
  - `figma-section-spec.py` 출력 시 결정성 규칙 강화:
    - 모든 좌표/크기 수치 `round(val, 3)` 통과
    - 모든 색상 hex `#rrggbb` 소문자 6자리
    - 배열 정렬은 `children` 의 index 순서 (z-order) 유지 — 좌표 기반 재정렬 금지
    - 값이 없어도 신규 v2 키는 누락하지 않고 `null` 명시
- **제외**:
  - 실제 신규 8축 필드(fills/effects/strokes/...)의 추출 로직 — 그것은 REQ-030/031/032 의 책임
  - Pydantic 도입 — Phase B 로 유보 (`Won't this time`)
  - constraints → CSS position:absolute 매핑 — 정책 2에 따라 **추출만 하고 매핑 코드를 작성하지 않는다**
  - structural diff gate / DOM tree hash — Phase C
- **시작점 힌트**:
  - `tools/figma-section-spec.py:1224-1245` — schema_version 위치 + 출력 payload 구성
  - `tools/post-impl-verify.py:47-77` — _find_spec 자동 탐색 (REQ-034 에서 제거 예정이지만 본 REQ 에선 v1/v2 분기 추가만)
  - `rules/rules.yaml` 끝부분 — 신규 Rule-ID 추가 위치

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable] [unit-test] [tdd-required]
Given: `tools/figma-section-spec.py` 가 임의의 Figma node 데이터를 받아 spec 을 생성한다
When: 출력된 `spec.json` 을 Read 한다
Then: `schema_version` 필드가 문자열 `"2.0.0"` (정수 1 이 아니다)
Test: `python3 -c "import json,subprocess; ..."` 또는 unit test `tests/test_schema_version.py` 작성

#### AC-002 [MUST] [automatable] [unit-test] [tdd-required]
Given: 기존 `extracted/section_03_spec.json`, `extracted/section_04_spec.json` (schema_version=1) 이 존재한다
When: `python3 tools/migrate-spec-v1-to-v2.py --apply` 를 실행한다
Then: 두 파일 모두 schema_version=`"2.0.0"` 으로 갱신되고, `extracted.v1.backup/section_03_spec.json` 와 `extracted.v1.backup/section_04_spec.json` 이 원본 그대로 보존된다
Test: `python3 tools/migrate-spec-v1-to-v2.py --apply && diff <(jq 'del(.schema_version) | del(.. | objects | ._extra?)' extracted/section_03_spec.json) <(jq 'del(.schema_version)' extracted.v1.backup/section_03_spec.json)` — 차이 0

#### AC-003 [MUST] [automatable] [unit-test] [tdd-required]
Given: migration 실행 후
When: 기존 v1 spec 의 임의 키(text_nodes[0].characters, frame_nodes[0].fills, paddingTop 등) 의 값을 비교한다
Then: 기존 키의 값은 1 byte 도 변경되지 않고, 신규 v2 키만 추가되었다 (add-only diff)
Test: `python3 tests/test_migration_add_only.py` (regression test 가 task 02 에 정의됨)

#### AC-004 [MUST] [automatable] [unit-test]
Given: schema_version=1 인 v1 spec 을 입력으로 받는다
When: `python3 tools/figma-validate.py --spec extracted.v1.backup/section_03_spec.json --html ... --css ...` 를 실행한다
Then: validator 가 v1 분기 파서로 진입하여 `[WARN] schema_version=1 (legacy)` 메시지를 stderr 로 출력하지만 검증은 통과 (exit=0)한다
Test: `python3 tools/figma-validate.py --spec extracted.v1.backup/section_03_spec.json --html test/fixtures/sample.html --css test/fixtures/sample.css 2>&1 | grep -q "schema_version=1"`

#### AC-005 [MUST] [automatable] [unit-test]
Given: schema_version="2.0.0" 인 v2 spec 을 입력으로 받는다
When: `figma-validate.py` 가 실행된다
Then: v2 분기 파서로 진입하여 신규 v2 키(`fills` type 분기, `effects`, `strokes`, `layoutSizing*`, `characterStyleOverrides` 등)에 대한 신규 검증 카테고리를 호출 가능한 상태로 만든다 (REQ-030/031 에서 실제 카테고리 구현)
Test: `python3 tools/figma-validate.py --version-info` 가 v1/v2 분기 가능한 카테고리 목록을 stdout 으로 출력

#### AC-006 [MUST] [automatable] [unit-test] [tdd-required]
Given: `rules/rules.yaml` 을 Read 한다
When: 신규 3 Rule-ID(`vertical_frame_itemspacing_uses_margin_bottom`, `no_constraints_to_position_absolute_mapping`, `figma_rules_conflict_uses_meta_marker`) 의 정의를 검사한다
Then: 각 Rule-ID 가 `rules.yaml` 에 등록되어 있고, `validation_schema.json` 의 enum 에도 동일 ID 가 존재하며, `tools/figma-validate.py` 에 매칭되는 handler 함수가 존재한다 (3자 동기)
Test: `python3 tools/check-rules-drift.py --policy-ids vertical_frame_itemspacing_uses_margin_bottom no_constraints_to_position_absolute_mapping figma_rules_conflict_uses_meta_marker` exit=0

#### AC-007 [MUST] [automatable] [unit-test]
Given: `rules/templates/publishing/impl-request.md` 외주 브리프 템플릿
When: 본문을 Read 한다
Then: "## 코딩 규칙" 섹션의 `rule_ids:` 목록에 위 3개 ID가 모두 포함되어 있다
Test: `grep -F "vertical_frame_itemspacing_uses_margin_bottom" rules/templates/publishing/impl-request.md && grep -F "no_constraints_to_position_absolute_mapping" rules/templates/publishing/impl-request.md && grep -F "figma_rules_conflict_uses_meta_marker" rules/templates/publishing/impl-request.md`

#### AC-008 [MUST] [automatable] [unit-test] [tdd-required]
Given: VERTICAL frame + itemSpacing > 0 인 spec 노드와 그에 대응되는 HTML/CSS 가 있다
When: `figma-validate.py` 가 정책 1 enforcement 를 실행한다
Then: CSS 가 `margin-bottom: Npx` (gap 또는 column-gap 아님) 로 작성되었으면 PASS, `gap: Npx` 로 작성되었으면 FAIL 메시지 (`[POLICY-1] VERTICAL frame itemSpacing must map to margin-bottom`) 를 출력한다
Test: 두 fixture (PASS / FAIL) 로 unit test 작성

#### AC-009 [MUST] [automatable] [unit-test] [tdd-required]
Given: spec 노드에 `rules_conflict: { rule_id: "no_color_grid", figma_value: "...", applied_value: "..." }` 메타가 기록되어 있다
When: `figma-validate.py` 가 해당 노드를 검증한다
Then: `rules_conflict.rule_id` 가 가리키는 규칙은 false-positive 로 처리되어 PASS 되고, 해당 사실이 stdout 에 `[RULES-CONFLICT] node {id} bypassed rule {rule_id} (figma: {figma_value} → applied: {applied_value})` 로 기록된다
Test: fixture 기반 unit test

#### AC-010 [MUST] [automatable] [unit-test]
Given: spec 노드의 `constraints` 필드는 추출되어 있다
When: `figma-validate.py` 또는 외주 브리프가 CSS 매핑 시도를 검사한다
Then: 어떤 검증 카테고리도 `constraints` → `position: absolute` 매핑을 요구하지 않으며, 외주 브리프 템플릿(`rules/templates/publishing/impl-request.md`) 본문에서 `constraints` 가 "spec 추출만 하고 CSS 매핑하지 않음" 으로 명시되어 있다
Test: `grep -E "constraints.*spec.*추출.*CSS.*매핑하지" rules/templates/publishing/impl-request.md` 한 줄 매칭

#### AC-011 [MUST] [automatable] [unit-test] [tdd-required]
Given: 동일 Figma node 데이터를 두 번 입력으로 준다
When: `figma-section-spec.py` 를 두 번 연속 실행한다
Then: 두 출력 `spec.json` 의 byte-exact md5 hash 가 동일하다 (결정성)
Test: `md5sum out1.json out2.json` 비교

#### AC-012 [MUST] [automatable] [unit-test]
Given: `tools/migrate-spec-v1-to-v2.py --rollback` 을 실행한다
When: 명령이 완료된다
Then: `extracted/` 의 모든 spec 파일이 `extracted.v1.backup/` 의 원본으로 정확히 복원된다
Test: `python3 tools/migrate-spec-v1-to-v2.py --apply && python3 tools/migrate-spec-v1-to-v2.py --rollback && diff -r extracted/ extracted.v1.backup/` exit=0

#### AC-013 [MUST] [automatable] [lint-check]
Given: 신규/수정 파일 (`tools/figma-section-spec.py`, `tools/figma-validate.py`, `tools/post-impl-verify.py`, `tools/migrate-spec-v1-to-v2.py`)
When: `python3 -m py_compile` 와 (있으면) `ruff check` 를 실행한다
Then: 컴파일 / lint 에러 0 건
Test: `python3 -m py_compile tools/migrate-spec-v1-to-v2.py tools/figma-section-spec.py tools/figma-validate.py tools/post-impl-verify.py`

## 3.2 Intent Trace

| AC-ID | 의도 근거 | 근거 출처 | 신뢰도 |
|-------|-----------|-----------|--------|
| AC-001 | schema_version semver 전환으로 v1/v2 분기 가능하게 함 | plan.md §결정사항 + IDN-002 §D Phase A | High |
| AC-002 | migration 누락 시 기존 extracted/ 전량 무효화 리스크 차단 | plan.md §리스크 레지스터 R1, IDN-002 critic Top 1 | High |
| AC-003 | "add-only diff" 가 plan.md 명시 가정 | plan.md §제약 & 가정 | High |
| AC-004 | v1 호환성 유지 (graceful fallback) | plan.md §결정사항 v1/v2 분기 파서 | High |
| AC-005 | v2 분기 파서가 신규 카테고리 진입점 제공 | plan.md §F REQ-034 전제 | High |
| AC-006 | rules-schema-handler 3자 정합성 (REQ-033 사전 작업) | plan.md §B4 SSOT, IDN-002 §B2 | High |
| AC-007 | 외주 브리프 4곳 동일 문구 (PAC-10) | plan.md §결정사항 정책 1, PAC-10 | High |
| AC-008 | 정책 1 enforcement | plan.md §정책 1, PAC-10 | High |
| AC-009 | 정책 3 (rules 승) — rules_conflict 메타 | plan.md §정책 3, PAC-12 | High |
| AC-010 | 정책 2 (constraints CSS 매핑 제외) | plan.md §정책 2, PAC-11 | High |
| AC-011 | 결정성 규칙 (PAC-23) | plan.md §결정사항 결정성 규칙 | High |
| AC-012 | rollback 안전망 | plan.md §제약 & 가정 (rollback 가능) | High |
| AC-013 | stdlib 의존 + 컴파일 검증 | plan.md §결정사항 의존성 | High |

## 3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-1  | MUST  | AC-001 | Full |
| PAC-7  | MUST  | AC-002 | Full |
| PAC-8  | MUST  | AC-003 | Full |
| PAC-9  | MUST  | AC-004, AC-005 | Full |
| PAC-10 | MUST  | AC-007, AC-008 | Full |
| PAC-11 | MUST  | AC-010 | Full |
| PAC-12 | MUST  | AC-009 | Full |
| PAC-23 | MUST  | AC-011 | Full |
| PAC-15 | MUST  | AC-006 (3자 정합성 부분) | Partial — REQ-033 에서 보강 |
| (SPEC_ONLY) | — | AC-012, AC-013 | rollback/lint 보강 |

> 본 REQ 가 직접 책임지지 않는 PAC (PAC-2~6, PAC-13~22, PAC-24~26) 은 후속 REQ-030/031/032/033/034 에서 매핑된다.

## 3.5 Constraints

- 보안: N/A (로컬 CLI 도구)
- 성능: migration 스크립트는 100 개 spec 처리 시 30초 이내 완료 (참고)
- 호환성: Python 3.10 + stdlib 만 사용 (외부 라이브러리 신규 추가 금지)
- 운영: rollback 모드 필수 제공, dry-run 으로 영향 범위 사전 확인 가능

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: `tools/figma-section-spec.py` 의 기존 출력 payload 구성 패턴 유지. 신규 키는 dict 끝에 추가하되 정렬은 자유 (단, 같은 입력 → 같은 출력 byte-exact).
- **알아야 할 제약**:
  - `CLAUDE.md` 의 "PM은 직접 코드 수정 금지" 원칙 — 본 spec 은 외주 에이전트(codex-dev) 가 수행
  - migration 은 절대 원본을 직접 덮어쓰지 않고 항상 `extracted.v1.backup/` 백업 선행
  - `additionalProperties: true + _extra` 폴백을 v2 에서부터 도입하여 Figma 신규 필드 유입 시 깨지지 않게 함 (plan.md §리스크 R4)
- **접근법 방향**:
  - IDN-002 synthesis §D Phase A 를 그대로 따름 (semver + dict 확장 + 마이그레이션 스크립트)
  - critic Top 3 ("Pydantic SSOT 즉시 도입은 over-engineering") 수용 — Phase A 는 stdlib 만 사용

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): [REQ-029/02 (test task), REQ-030, REQ-033]

## 6. 에이전트 팀 구성 (Agent Team)

- 실행: codex-dev (backend / Python tooling)
- 사유: Python stdlib 기반 CLI 스크립트 변경 + JSON schema/yaml drift 동기화 작업. codex 의 코드/리팩터/테스트 capability 가 적합.

## 7. 팀 판단 기반 결정 (Team-Assisted Decisions)

### 접근 방식 결정 (해당)
- 판단 유형: ideation
- 주제: Figma→Code 파이프라인 v2 확장 + JSON 공식화 가능성
- 결정 내용: Phase A 는 dict 확장 + semver + migration. Pydantic SSOT 는 Phase B 로 유보. 정책 3건은 rules 승 / margin-bottom 치환 / constraints 추출만.
- 근거 파일: `/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/synthesis.md`

## 10. 가정 사항 (Assumptions)

> --plan PLN-009 가 제공되었으므로 본 섹션은 사용자 결정에 의해 채워졌으며, 추가 가정 없음. 모호 사항이 있다면 PM 에게 escalation.

## 11. Test Scenarios (Pre-Impl)

> 구현 착수 전 PM 이 사전 정의한 자동화 검증 시나리오. 각 항목은 §3 의 AC 와 1:1 매핑된다.
> 외주 에이전트는 구현 후 본 시나리오를 모두 PASS 시킨 뒤 PM 에 보고한다.

| # | 대응 AC | 실행 명령 / 확인 방법 | 기대 결과 |
|---|---------|-----------------------|-----------|
| TS-01 | AC-001 | `python3 -c "import json; d=json.load(open('extracted/section_03_spec.json')); assert d['schema_version']=='2.0.0', d['schema_version']"` | exit 0 |
| TS-02 | AC-002 | `python3 tools/migrate-spec-v1-to-v2.py --apply` 후 `ls extracted.v1.backup/section_03_spec.json && python3 -c "import json; assert json.load(open('extracted/section_03_spec.json'))['schema_version']=='2.0.0'"` | 백업 파일 존재 + schema_version 갱신 |
| TS-03 | AC-003 | `python3 tests/regression/test_migration_add_only.py` (test task 02 에서 작성) | exit 0, add-only diff |
| TS-04 | AC-004 | `python3 tools/figma-validate.py --spec extracted.v1.backup/section_03_spec.json --html landing/index.html --css landing/css/common.css 2>&1 \| grep -q "schema_version=1"` | warn 출력 + exit 0 |
| TS-05 | AC-005 | `python3 tools/figma-validate.py --version-info` | v1/v2 분기 카테고리 stdout 출력 |
| TS-06 | AC-006 | `python3 tools/check-rules-drift.py --policy-ids vertical_frame_itemspacing_uses_margin_bottom no_constraints_to_position_absolute_mapping figma_rules_conflict_uses_meta_marker` | exit 0 |
| TS-07 | AC-007 | `for id in vertical_frame_itemspacing_uses_margin_bottom no_constraints_to_position_absolute_mapping figma_rules_conflict_uses_meta_marker; do grep -F "$id" rules/templates/publishing/impl-request.md \|\| exit 1; done` | 3개 모두 매칭 |
| TS-08 | AC-008 | `pytest tests/unit/test_policy1_margin_bottom.py -v` (test task 02 에서 작성) | PASS fixture + FAIL fixture 모두 기대대로 동작 |
| TS-09 | AC-009 | `pytest tests/unit/test_policy3_rules_conflict.py -v` (test task 02 에서 작성) | rules_conflict 메타가 PASS 처리되고 [RULES-CONFLICT] 로그 출력 |
| TS-10 | AC-010 | `grep -E "constraints.*spec.*추출.*CSS.*매핑하지" rules/templates/publishing/impl-request.md` | 1줄 매칭 |
| TS-11 | AC-011 | `python3 tests/regression/test_determinism.py` (100 회 실행 후 md5 1 종) | exit 0, hash 종류 1 |
| TS-12 | AC-012 | `python3 tools/migrate-spec-v1-to-v2.py --apply && python3 tools/migrate-spec-v1-to-v2.py --rollback && diff -r extracted/ extracted.v1.backup/` | exit 0 |
| TS-13 | AC-013 | `python3 -m py_compile tools/migrate-spec-v1-to-v2.py tools/figma-section-spec.py tools/figma-validate.py tools/post-impl-verify.py` | exit 0 |

> Test Scenarios 의 일부(TS-03, TS-08, TS-09, TS-11) 는 task 02 (regression / unit test 스위트) 에서 실제 테스트 파일로 구현된다.

# Implementation Spec

- Request ID: REQ-029
- Task ID: 02
- Created: 2026-04-19T06:43:14.000Z
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: backend test (Python pytest/unit)] → 최종: codex-dev
- Assigned Team: codex-dev (테스트 전용 후행 태스크)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-029-task-02
- Complexity: Standard

## §0 Context Manifest

> 구현 시작 전 이 목록의 파일을 가장 먼저 Read하세요.
> 이 목록이 완전하지 않을 수 있으며, 에이전트는 자율 탐색을 유지해야 합니다.

- /mnt/d/dev-base/.gran-maestro/requests/REQ-029/tasks/01/spec.md (구현 태스크 AC 전체)
- /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md (PAC-23 결정성 규칙, PAC-7/8 migration)
- /mnt/d/dev-base/tools/migrate-spec-v1-to-v2.py (구현 산출물)
- /mnt/d/dev-base/tools/figma-section-spec.py
- /mnt/d/dev-base/tools/figma-validate.py
- /mnt/d/dev-base/extracted/section_03_spec.json (regression baseline)
- /mnt/d/dev-base/extracted/section_04_spec.json (regression baseline)
- /mnt/d/dev-base/extracted.v1.backup/ (migration 후 자동 생성된 원본 백업)

## §1 요약 (Summary)

REQ-029/01 의 구현이 완료된 직후, schema_version semver 전환·migration 스크립트·v1/v2 분기 파서·정책 3건 enforcement 의 통합 동작을 검증하고, 기존 `extracted/` spec 의 add-only diff 와 결정성 byte-exact 보존을 회귀 테스트한다.

## §2 테스트 범위 (Scope: Integration / Incremental / Regression)

- **통합 검증 (Integration Validation)**:
  - migration 스크립트 → 신규 v2 spec → v2 파서 → 정책 enforcement → exit code 매트릭스 전체 흐름이 단절 없이 동작
  - 외주 브리프 템플릿 ↔ rules.yaml ↔ validation_schema.json ↔ figma-validate handler 4자가 정책 3건 ID 에 대해 동일 참조
- **증분 테스트 (Incremental Test)**:
  - 신규 `tools/migrate-spec-v1-to-v2.py` 의 dry-run / apply / rollback 3 모드
  - 신규 v1/v2 분기 파서가 v1 입력을 warn 통과시키고 v2 입력은 신규 카테고리 진입점 호출
  - 정책 1 (margin-bottom) 과 정책 3 (rules_conflict) 의 PASS / FAIL fixture
  - 결정성: 동일 입력 → byte-exact 출력
- **회귀 테스트 (Regression Test)**:
  - 기존 `extracted/section_03_spec.json` · `section_04_spec.json` 의 모든 키-값이 add-only diff 만 있고 기존 값은 1 byte 도 변경되지 않음
  - 기존 `landing/index.html` + `landing/css/*.css` 에 대해 `post-impl-verify.py` 가 기존 PASS 상태를 유지 (PAC-25 회귀 없음)
  - `extracted.v1.backup/` 백업이 원본과 byte-exact 일치

## §3 통합 AC (Integrated Acceptance Criteria)

#### AC-001 [MUST] [automatable] [integration]
Given: REQ-029/01 의 모든 AC 가 PASS 상태이다
When: `python3 tools/migrate-spec-v1-to-v2.py --apply` → `python3 tools/figma-validate.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css` → `python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css` 를 순서대로 실행한다
Then: 세 명령 모두 exit=0 (또는 IGNORE-only exit=2)로 통과하고, stderr 에 schema_version=2.0.0 인식 로그가 출력된다
Test: shell 통합 테스트 스크립트 `tests/integration/test_req029_endtoend.sh` 작성

#### AC-002 [MUST] [automatable] [unit-test] [regression-test]
Given: REQ-029/01 의 migration 적용 전 `extracted/section_03_spec.json` 의 SHA-256 해시 H1, 적용 후의 동일 파일에서 schema_version 과 신규 v2 키를 제거한 잔여물의 SHA-256 해시 H2
When: H1 과 H2 를 비교한다
Then: H1 == H2 (즉, "신규 키만 추가" 보장 — add-only diff)
Test: `python3 tests/regression/test_migration_add_only.py` (jq + python diff 조합)

#### AC-003 [MUST] [automatable] [unit-test]
Given: 동일 Figma node 입력 fixture (`tests/fixtures/figma_node_sample.json`)
When: `tools/figma-section-spec.py` 를 100 회 연속 실행한다
Then: 100 회 출력 모두 byte-exact 동일 (md5 hash 1 종) — 결정성 (PAC-23)
Test: `tests/regression/test_determinism.py`

#### AC-004 [MUST] [automatable] [integration]
Given: `landing/index.html` + `landing/css/common.css` (기존 통과 상태)
When: 본 REQ 적용 후 `python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css` 를 실행한다
Then: 기존과 동일한 exit code (0 또는 2) 가 출력되고, 신규 FAIL 이 발생하지 않는다 (PAC-25 — `[IMPACT]` 회귀 없음)
Test: 본 REQ 적용 전 baseline exit code 를 캡처하고 적용 후 비교

#### AC-005 [MUST] [automatable] [unit-test]
Given: 정책 1 fixture 두 개 — (a) VERTICAL frame + itemSpacing=24 → CSS 가 `margin-bottom: 24px` 사용, (b) 동일 spec → CSS 가 `gap: 24px` 사용
When: `figma-validate.py` 정책 1 enforcement 를 실행한다
Then: (a) PASS, (b) FAIL 메시지 `[POLICY-1] VERTICAL frame itemSpacing must map to margin-bottom`
Test: `pytest tests/unit/test_policy1_margin_bottom.py`

#### AC-006 [MUST] [automatable] [unit-test]
Given: spec 노드에 `rules_conflict: { rule_id: "no_color_grid", figma_value: "rgb-grid", applied_value: "flexbox" }` 메타가 있다
When: `figma-validate.py` 가 해당 노드를 검증한다
Then: 메타가 가리키는 규칙은 PASS 처리되고 `[RULES-CONFLICT]` 로그가 출력된다
Test: `pytest tests/unit/test_policy3_rules_conflict.py`

#### AC-007 [MUST] [automatable] [unit-test]
Given: 백업 디렉토리 `extracted.v1.backup/` 의 모든 파일
When: 원본 commit 시점의 동일 경로 파일과 SHA-256 해시를 비교한다
Then: 모든 파일에서 해시 일치 (백업이 정확히 byte-exact 원본)
Test: git stash 또는 git show HEAD~1 vs current backup 해시 비교 스크립트

## §4 회귀 테스트 항목 (Regression Checklist)

- [ ] 기존 `extracted/section_03_spec.json` 의 `text_nodes[0].characters` 값 (한국어 포함) 변경 없음
- [ ] 기존 `extracted/section_03_spec.json` 의 `frame_nodes[0].fills` 값 (hex SOLID) 변경 없음
- [ ] 기존 `extracted/section_04_spec.json` 의 paddingTop/Right/Bottom/Left 정수값 변경 없음
- [ ] 기존 `landing/index.html` + `landing/css/common.css` 가 `post-impl-verify.py` 에서 신규 FAIL 0 건
- [ ] `build-rules.py` 가 `schema_version` 정수/문자열 모두 정상 처리 (line 314)
- [ ] `tools/figma-section-spec.py --tree` 출력은 본 REQ 변경에 영향 받지 않음 (트리 출력은 별개 경로)
- [ ] `tools/json-to-html.py` 폐기 결정 유지 (본 REQ 에서 건드리지 않음)

## §5 의존성 (Dependencies)

- 선행 작업 (blockedBy): [REQ-029/01]
- 후행 작업 (blocks): []

## §6 에이전트 팀 구성 (Agent Team)

- 실행: codex-dev (backend test)
- 사유: pytest unit/integration 테스트 작성 + shell regression 스크립트. 테스트 스위트 자체는 stdlib + pytest 만 사용.

## §7 Test Scenarios (Pre-Impl)

> 본 task 가 작성·실행할 자동화 검증 시나리오. §3 통합 AC 와 1:1 매핑된다.

| # | 대응 AC | 실행 명령 / 확인 방법 | 기대 결과 |
|---|---------|-----------------------|-----------|
| TS-01 | AC-001 | `bash tests/integration/test_req029_endtoend.sh` | migrate→validate→verify 3 명령 모두 exit 0 또는 IGNORE-only exit 2 |
| TS-02 | AC-002 | `python3 tests/regression/test_migration_add_only.py` (jq + python diff 조합으로 H1 == H2 검증) | exit 0 |
| TS-03 | AC-003 | `python3 tests/regression/test_determinism.py` (figma-section-spec.py 100 회 실행 후 md5 hash 1 종 확인) | exit 0 |
| TS-04 | AC-004 | 본 REQ 적용 전 baseline exit code 캡처 → 적용 후 동일 명령 재실행 → exit code 일치 + 신규 FAIL 0 건 | 동일 exit code |
| TS-05 | AC-005 | `pytest tests/unit/test_policy1_margin_bottom.py -v` | PASS fixture + FAIL fixture 모두 기대대로 |
| TS-06 | AC-006 | `pytest tests/unit/test_policy3_rules_conflict.py -v` | rules_conflict 메타 PASS 처리 + [RULES-CONFLICT] 로그 |
| TS-07 | AC-007 | `python3 tests/regression/test_backup_byte_exact.py` (extracted.v1.backup/ 의 SHA-256 ↔ git show HEAD 비교) | 모든 파일 hash 일치 |

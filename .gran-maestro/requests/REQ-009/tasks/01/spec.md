# Implementation Spec

- Request ID: REQ-009
- Task ID: 01
- Created: 2026-04-13
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: docs/config] → 최종: claude-dev
- Assigned Team: claude-dev 단독 (문서/YAML 소규모 인라인 수정)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-009-01
- Complexity: Lite

## §0 Context Manifest

- .gran-maestro/plans/PLN-004/plan.md
- CLAUDE.md
- rules/claude.md
- rules/rules.yaml
- tools/build-rules.py
- tools/figma-section-spec.py
- tools/figma-validate.py

## 1. 요약 (Summary)

PLN-004에서 신설한 사전·사후 워크플로우(`figma-section-spec.py` + `figma-validate.py`)를 CLAUDE.md / rules/claude.md / rules/rules.yaml에 문서화하여 강제 절차로 편입한다.

## 2. 범위 (Scope)

- **포함**:
  - `CLAUDE.md` 에 **섹션별 워크플로우 갱신** — 기존 "Figma MCP 기반 워크플로우" 섹션의 Phase 1~3을 `figma-section-spec.py → 구현 → figma-validate.py → validate-semantic.py` 플로우로 교체/보강
  - `rules/claude.md` 에 "Figma 섹션 spec sheet 사용 강제" 규칙 추가 (또는 기존 규칙 보강)
  - `rules/rules.yaml` 에 `figma_spec_sheet_required` 신규 룰 항목 추가 (validation 타입은 `metadata` 수준 — 실제 코드 검증이 아니라 워크플로우 강제 표시)
  - `python3 tools/build-rules.py` 재실행으로 `rules/common.md`, `basic.md`, `landing.md`, `validation_schema.json`, `tools/build-prompts.py` 자동 재생성
- **제외**:
  - `tools/figma-section-spec.py`, `tools/figma-validate.py` 동작 변경
  - 기존 rules.yaml의 다른 룰 변경
  - Section_03 적용 검증 (REQ-009-02 책임)
- **시작점 힌트**: `CLAUDE.md`, `rules/claude.md`, `rules/rules.yaml`, `tools/build-rules.py`

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [manual]
Given: CLAUDE.md의 "Figma MCP 기반 워크플로우" 섹션이 기존 상태로 존재
When: 새 워크플로우를 반영한다
Then: 새 섹션에 아래 플로우가 단계 번호와 함께 명시된다 — (1) `figma-section-spec.py`로 spec.md + spec.json 생성 → (2) AI가 spec.md만 보고 HTML/CSS 작성 → (3) `figma-validate.py --spec spec.json --html --css` 실행 → (4) `validate-semantic.py` 실행 → (5) 둘 다 통과해야 commit
Test: 사람 검수 — CLAUDE.md의 해당 섹션을 읽어 5단계가 명시되어 있는지 확인

#### AC-002 [MUST] [manual]
Given: rules/claude.md가 존재
When: 새 워크플로우 절차를 문서화한다
Then: "Figma 추출 전 필수 실행" 체크리스트에 `figma-section-spec.py` 호출 단계가 필수로 포함되고, "raw API 직접 해석 금지" 문구가 명시된다
Test: 사람 검수

#### AC-003 [MUST] [automatable]
Given: rules/rules.yaml이 존재하고 `figma_spec_sheet_required` 룰은 아직 없음
When: 새 룰을 추가한다 (id, description, severity, applies_to 필드 포함)
Then: `python3 -c "import yaml; yaml.safe_load(open('rules/rules.yaml'))"` 가 exit 0, 그리고 파싱 결과에서 `figma_spec_sheet_required` 키가 찾아진다
Test: `python3 -c "import yaml; d=yaml.safe_load(open('rules/rules.yaml')); print('figma_spec_sheet_required' in str(d))"` 출력에 `True` 포함

#### AC-004 [MUST] [automatable] [impact-check]
Given: rules.yaml 수정됨
When: `python3 tools/build-rules.py` 실행
Then: exit 0, 재생성된 `rules/common.md`/`basic.md`/`landing.md`/`validation_schema.json` / `tools/build-prompts.py` 파일들의 AUTO-GENERATED 마커가 유지됨
Test: `cd /mnt/d/dev-base && python3 tools/build-rules.py && head -1 rules/common.md | grep AUTO-GENERATED`

## 3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-6 | SHOULD / TIER-B | AC-001, AC-002 | Full |
| PAC-7 | SHOULD / TIER-B | AC-003, AC-004 | Full |

## 3.5 Constraints

- 호환성: 기존 다른 룰/문서 수정 금지 (새 룰/섹션만 추가)
- 운영: `build-rules.py` 실행 결과물은 반드시 리포에 함께 커밋

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: REQ-005에서 도입한 rules.yaml SSOT 패턴 — 편집은 rules.yaml에만, 나머지는 `tools/build-rules.py`로 재생성
- **알아야 할 제약**: `figma_spec_sheet_required`는 런타임 검증이 아니라 메타데이터 수준 룰 (validation_type 신설 또는 기존 metadata 타입 재활용)

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): [REQ-009-02]

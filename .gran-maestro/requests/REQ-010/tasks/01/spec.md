# Implementation Spec

- Request ID: REQ-010
- Task ID: 01
- Created: 2026-04-13
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: backend/tools] → 최종: codex-dev
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-010-01
- Complexity: Lite

## §0 Context Manifest

- tools/figma-validate.py
- .gran-maestro/requests/REQ-009/tasks/02/dryrun/e2e-dryrun-report.md (갭 #2 재현 기록)

## 1. 요약 (Summary)

`figma-validate.py`의 `compute_element_properties()` 가 CSS 상속을 계산하지 않아 `<li><span>text</span></li>` 처럼 텍스트를 자식 요소에 둔 구조에서 폰트 5필드 false-positive가 발생한다. CSS 상속 속성 6종을 ancestor walk로 반영해 false-positive를 제거한다.

## 2. 범위 (Scope)

- **포함**:
  - `tools/figma-validate.py` 의 `compute_element_properties()` 수정 — 현재 요소 직접 매칭 + ancestor 체인 상속 합성
  - 상속 대상 속성 6종: `font-family`, `font-size`, `font-weight`, `line-height`, `color`, `letter-spacing`
  - 직접 매칭 값이 있으면 그것을 우선, 없으면 가장 가까운 ancestor에서 조회
  - 회귀 테스트: `.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/` 12개 시나리오가 여전히 모두 exit 1로 탐지되는지 확인 (기존 동작 무회귀)
- **제외**:
  - 9개 검증 카테고리 로직 변경 (상속 처리는 폰트 5필드 완결성 카테고리에만 영향)
  - 다른 CSS 속성(background, padding 등 — 상속 속성이 아님)
  - 문서 수정 (T02 책임)
- **시작점 힌트**: `tools/figma-validate.py:722` `compute_element_properties()`, `:940` `validate_text_nodes()`

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable] [unit-test] [regression-test]
Given: `<li class="x_list_item"><span>Hello</span></li>` HTML + `.x_list_item { font-family: "Noto"; font-size: 14px; font-weight: 400; line-height: 1.5; color: #333; }` CSS + text_node `characters="Hello"`
When: `figma-validate.py` 실행
Then: "폰트 5필드 완결성" 카테고리에서 위반 0건 (span이 부모 li로부터 5개 속성 모두 상속)
Test: 새 fixture `regression-fixtures/scenarios/13-inherited-font-ok/` 추가 후 `bash regression-fixtures/run_regression.sh` 에서 exit 0 (base 취급) 또는 별도 pass 케이스 확인

#### AC-002 [MUST] [automatable] [impact-check]
Given: REQ-008-02의 회귀 fixture 12개가 이미 존재
When: 기존 12개 fixture에 대해 `figma-validate.py` 재실행
Then: 12개 모두 기존과 동일하게 exit 1 + 해당 카테고리 위반 탐지 유지 (상속 처리로 인한 false-negative 발생 금지)
Test: `bash .gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/run_regression.sh` — base=exit 0, 12 시나리오=exit 1 전부 유지

#### AC-003 [MUST] [automatable] [lint-check]
Given: 수정된 figma-validate.py
When: `python3 -m py_compile tools/figma-validate.py`
Then: exit 0
Test: `python3 -m py_compile tools/figma-validate.py`

## 3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| (follow-up — PLN-004 외 추가 개선) | — | AC-001, AC-002 | SPEC_ONLY |

## 4. 구현 컨텍스트

- **따라야 할 패턴**: 기존 `compute_element_properties()` 는 element에 매칭되는 CSSRule을 합성해 PropertyValue dict 반환. ancestor walk 추가 시 "자식에 직접 선언된 값 > 부모의 상속값" 순서 유지.
- **알아야 할 제약**: `DOMElement` 가 parent 참조를 갖고 있는지 확인 필요. 없으면 parser에서 parent 링크를 세팅하거나 traversal 시 부모 스택을 유지하는 방식으로 대체.
- **접근법 방향**: 가장 간단한 접근 — `compute_element_properties(el)` 재귀에서 `inherited = compute_element_properties(el.parent) if el.parent else {}` 계산 후 `{**inherited_filtered, **direct}` 병합. `inherited_filtered`는 상속 속성 6종만 필터링.

## 5. 의존성
- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): []

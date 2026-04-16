# Implementation Spec

- Request ID: REQ-008
- Task ID: 02
- Created: 2026-04-13
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: regression-test/QA] → 최종: claude-dev
- Assigned Team: claude-dev 단독 (PM 직접 검증 — 소규모 회귀 시나리오 실행)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-008-02
- Complexity: Lite

## §0 Context Manifest

> 구현 시작 전 이 목록의 파일을 가장 먼저 Read하세요.

- .gran-maestro/plans/PLN-004/plan.md
- .gran-maestro/requests/REQ-008/tasks/01/spec.md
- tools/figma-validate.py (REQ-008-01 산출물)
- tools/figma-section-spec.py

## 1. 요약 (Summary)

REQ-008-01에서 구현된 `figma-validate.py`가 PLN-004 §1에 열거된 12개 실제 누락 사례를 모두 catch하는지 확인한다. 회귀 케이스는 모제림 Section_02 기준으로 구성한다.

## 2. 범위 (Scope)

- **포함**:
  - Section_02의 Figma 데이터로 spec.json 생성 (REQ-007 figma-section-spec.py 사용)
  - 12개 누락 시나리오에 대해 의도적으로 위반한 HTML/CSS 샘플 각각 작성 후 figma-validate.py로 검출 확인
  - 정상 HTML/CSS에 대해서는 0 violation 확인
  - 결과를 회귀 리포트(`REQ-008/tasks/02/regression-report.md`)로 저장
- **제외**:
  - figma-validate.py 로직 수정 (버그 발견 시 REQ-008-01로 피드백)
  - 새 규칙 추가 (9개 고정)
- **시작점 힌트**:
  - PLN-004 plan.md §1 "누락 12종" 목록
  - `tools/figma-section-spec.py`

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [manual]
Given: figma-validate.py가 REQ-008-01에서 구현 완료됨
When: Section_02 정상 버전 HTML/CSS에 대해 figma-validate.py 실행
Then: 위반 0건, exit 0
Test: `python3 tools/figma-validate.py --spec extracted/section_02_spec.json --html <section_02_clean>.html --css <section_02_clean>.css; echo $?`

#### AC-002 [MUST] [manual] [regression-test]
Given: PLN-004 plan.md §1에 12개 누락 사례가 정의됨
When: 각 누락을 의도적으로 재현한 HTML/CSS 샘플(12개)에 대해 figma-validate.py 실행
Then: 12개 모두 해당 카테고리에서 위반으로 검출되고, exit 1 반환
Test: 수동 — 각 샘플 개별 실행 후 violation 표에 기대 위반 카테고리가 나타나는지 대조

#### AC-003 [SHOULD] [manual]
Given: AC-002 실행 결과
When: 검출 결과를 정리한다
Then: `REQ-008/tasks/02/regression-report.md`에 12개 시나리오 × 결과(검출/미검출/부분) 매트릭스 작성, 미검출/부분 시 REQ-008-01에 피드백 태스크 등록
Test: 리포트 파일 존재 + 12개 행 × 3 컬럼(시나리오, 기대 카테고리, 실제 검출) 확인

## 3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-4 | MUST / TIER-A | AC-001, AC-002 | Full (회귀 검증으로 재확인) |
| PAC-8 | SHOULD / TIER-B | AC-002, AC-003 | Partial (Section_02에 한정) |

## 3.5 Constraints

- 환경: Figma API 실제 호출 가능해야 함 (FIGMA_TOKEN 필요)
- 운영: 회귀 샘플은 `.gran-maestro/tmp/REQ-008-02/`에 저장 후 작업 완료 시 정리

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: 기존 도구 회귀 검증 방식 — 소규모 fixture 샘플 + CLI 실행 + 결과 표 작성
- **알아야 할 제약**: 도구 구현은 REQ-008-01의 책임이므로 이 태스크에서는 CLI 실행과 결과 기록만 수행
- **접근법 방향**: Section_02 reference case (plan.md §1 사례 원천) 기준으로 12개 누락 시나리오를 1:1 매핑하여 검증 커버리지 확보

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): [REQ-008-01]
- 후행 작업 (blocks): []

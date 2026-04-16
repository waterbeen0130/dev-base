# Implementation Spec

- Request ID: REQ-009
- Task ID: 02
- Created: 2026-04-13
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: qa/verification] → 최종: claude-dev
- Assigned Team: claude-dev 단독 (워크플로우 적용 검증)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-009-02
- Complexity: Lite

## §0 Context Manifest

- .gran-maestro/plans/PLN-004/plan.md
- .gran-maestro/requests/REQ-009/tasks/01/spec.md
- CLAUDE.md (REQ-009-01 수정 결과)
- tools/figma-section-spec.py
- tools/figma-validate.py

## 1. 요약 (Summary)

REQ-009-01에서 문서화된 새 워크플로우가 실제로 **자기완결적**인지 드라이런으로 검증한다. Section_03(또는 다른 준비된 섹션) 데이터 기반으로 end-to-end 플로우가 막힘없이 수행되고 누락이 0건인지 확인한다.

> **현실화 노트**: PLN-004는 "모제림 Section_03"을 reference case로 언급하지만, 이 프로젝트에는 모제림 프로젝트 파일이 없다. 대신 `extracted/section_03_spec.json` / `section_04_spec.json` 등 기존 추출물을 사용하거나, 합성 spec.json으로 대체한다.

## 2. 범위 (Scope)

- **포함**:
  - CLAUDE.md/rules/claude.md 의 새 워크플로우 절차를 따라 "가상 섹션 1개"에 대해 end-to-end 드라이런:
    1. spec.md + spec.json이 존재한다고 가정 (기존 `extracted/section_03_spec.json` 활용 또는 소형 합성)
    2. 간단한 HTML/CSS 샘플 작성 (실제 디자인 재현 목표가 아니라 워크플로우 흐름 검증용)
    3. `figma-validate.py` 실행 → 위반 목록 확인
    4. `validate-semantic.py` 실행 → 위반 목록 확인
  - 드라이런 중 발견된 **문서화/도구 갭**을 `worktree/e2e-dryrun-report.md` 에 기록
  - 결론: "새 워크플로우로 작업 시 누락 0건 달성 여부 (YES/NO + 근거)"
- **제외**:
  - figma-validate.py / figma-section-spec.py / 문서 수정 (갭 발견 시 후속 REQ로 분리)
  - 실제 피그마 데이터를 완전 재현

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [manual]
Given: REQ-009-01이 완료되어 CLAUDE.md와 rules.yaml의 새 워크플로우가 반영됨
When: "가상 섹션" 1개로 end-to-end 드라이런 실행
Then: 워크플로우 5단계(spec 생성 → HTML/CSS 작성 → figma-validate → validate-semantic → commit) 가 각 단계마다 막히지 않고 수행 가능
Test: 수동 — 드라이런 세션을 진행하며 각 단계 진입 가능 여부 확인

#### AC-002 [MUST] [manual]
Given: 드라이런 진행 중
When: 워크플로우에서 "문서가 없어 막히는 지점"이 발생한다
Then: 해당 갭을 `e2e-dryrun-report.md` 에 카테고리별(문서 부재/도구 버그/절차 불명확)로 기록한다
Test: 리포트 파일 존재 + 각 갭 항목에 분류와 재현 방법 포함

#### AC-003 [MUST] [manual]
Given: 드라이런 완료
When: `e2e-dryrun-report.md` 말미에 최종 결론을 작성한다
Then: 아래 중 하나로 명확히 판정한다 — (a) "누락 0건 — 워크플로우 자기완결적" / (b) "갭 N개 발견 — 후속 REQ로 이관 권장"
Test: 리포트 파일에 결론 섹션 존재

## 3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-8 | SHOULD / TIER-B | AC-001, AC-002, AC-003 | Full |

## 3.5 Constraints

- 운영: 드라이런 산출물은 `.gran-maestro/worktrees/REQ-009-02/` 안에만 작성

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: REQ-008-02와 동일한 접근 — 합성 fixture 기반 워크플로우 검증
- **알아야 할 제약**: 모제림 Section_03 실물 데이터가 없으므로 reference case는 `extracted/section_03_spec.json` (제천/영월 등 기존 프로젝트 산출물) 로 대체

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): [REQ-009-01]
- 후행 작업 (blocks): []

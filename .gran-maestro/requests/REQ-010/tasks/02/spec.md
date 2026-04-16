# Implementation Spec

- Request ID: REQ-010
- Task ID: 02
- Created: 2026-04-13
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: docs] → 최종: claude-dev
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-010-02
- Complexity: Lite

## §0 Context Manifest

- CLAUDE.md (§PLN-004 Figma 워크플로우 섹션)
- tools/validate-semantic.py (--profile 옵션 확인)
- tools/figma-validate.py (9개 카테고리 원천)
- tools/figma-section-spec.py (.md / .json 출력 구조)
- .gran-maestro/requests/REQ-009/tasks/02/dryrun/e2e-dryrun-report.md (갭 #1/#3/#4 원천)

## 1. 요약 (Summary)

REQ-009-02 드라이런에서 발견된 문서 갭 3건을 CLAUDE.md §PLN-004 섹션에 반영한다. 실전 외주 에이전트가 CLAUDE.md만 읽고도 막힘없이 5단계 워크플로우를 수행할 수 있게 만든다.

## 2. 범위 (Scope)

- **포함**:
  - **갭 #1 해결** — `validate-semantic.py --profile {basic|landing|all}` 선택 지침을 5단계 4번 단계에 추가. 선택 기준(basic/landing 프로젝트 구분, 섹션 단일 검증 시 적절한 프로파일)과 예시 커맨드 포함.
  - **갭 #3 해결** — 5단계 3번 단계에 "9개 검증 카테고리" 표 삽입 (카테고리명 + 검증 대상 spec 필드 요약, 각 1줄).
  - **갭 #4 해결** — 5단계 1번 단계에 "spec.md는 사람용 읽기 편의, spec.json은 figma-validate.py 검증 레퍼런스. AI는 두 파일 모두 접근 가능" 문구 추가.
- **제외**:
  - `tools/figma-validate.py` 코드 수정 (T01 책임)
  - `tools/validate-semantic.py` 수정 (프로파일 기본값 변경 없음)
  - `figma-section-spec.py` 의 spec.md 스키마 완결성 개선 (본 REQ 범위 밖)
- **시작점 힌트**: `CLAUDE.md` 의 `## PLN-004 Figma 워크플로우` 섹션 (REQ-009/01에서 추가됨)

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [manual]  <!-- 갭 #1 -->
Given: CLAUDE.md §PLN-004 5단계 4번 단계가 존재
When: `--profile` 지침을 추가한다
Then: 4번 단계 코드 블록에 `--profile` 옵션이 포함되고, 바로 아래에 "basic/landing/all 중 프로젝트에 맞게 선택. 섹션 단일 검증 시 현 프로젝트 타입 또는 `all` 사용" 류의 지침이 명시됨
Test: 사람 검수 — CLAUDE.md 해당 섹션에서 `--profile` 키워드와 선택 기준 문구 확인

#### AC-002 [MUST] [manual]  <!-- 갭 #3 -->
Given: CLAUDE.md §PLN-004 5단계 3번 단계가 존재
When: 9개 카테고리 표를 삽입한다
Then: 카테고리 9종이 표로 명시됨 — (1) 텍스트 위변조 (2) 줄바꿈 보존 (3) 폰트 5필드 완결성 (4) lineHeight 비율 일치 (5) fills color hex 일치 (6) frame padding/gap 반영 (7) clamp 적용 (8) column flex gap 금지 (9) interaction URL 일치. 각 카테고리 옆에 1줄 설명(어떤 spec 필드를 보는지)
Test: 사람 검수 — CLAUDE.md에서 9개 카테고리가 표 형식으로 나열되어 있는지 확인

#### AC-003 [MUST] [manual]  <!-- 갭 #4 -->
Given: CLAUDE.md §PLN-004 5단계 1번 단계
When: spec.md/spec.json 역할 명시를 추가한다
Then: "spec.md는 사람이 읽기 편한 표 형식, spec.json은 figma-validate.py의 검증 레퍼런스. AI 구현자는 두 파일 모두 접근 가능하며 값 불일치 시 .json이 우선" 류의 문구가 1단계에 명시됨
Test: 사람 검수

#### AC-004 [MUST] [automatable]
Given: CLAUDE.md 수정됨
When: `grep -c "figma-validate\|--profile\|9개 카테고리\|spec.json" CLAUDE.md`
Then: 매칭 결과가 4건 이상 (각 갭 #1/#3/#4 키워드 최소 1회)
Test: `grep -c "figma-validate" CLAUDE.md` + 시각 확인

## 3.5 Constraints
- 기존 CLAUDE.md의 다른 섹션 수정 금지 (§PLN-004 내부만)
- rules/claude.md 변경 없음 (이번 REQ는 CLAUDE.md 단일 파일 문서 보강)

## 4. 구현 컨텍스트
- **따라야 할 패턴**: REQ-009/01이 추가한 §PLN-004 섹션의 포맷(번호 목록 + 코드 블록) 유지
- **알아야 할 제약**: 9개 카테고리 순서는 `tools/figma-validate.py` 의 카테고리 상수/함수 호출 순서와 일치시킬 것 (검증 출력 순서와 문서가 일치해야 검수 용이)

## 5. 의존성
- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): []

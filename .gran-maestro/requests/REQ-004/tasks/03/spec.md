# Implementation Spec

- Request ID: REQ-004
- Task ID: 03
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: 퍼블리싱 HTML/CSS 템플릿 재작성] → 최종: gemini-dev
- Assigned Team: gemini-dev 단독 (CLAUDE.md 멀티 에이전트 분배 규칙 — 퍼블리싱 = gemini-dev)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T03
- Complexity: Standard

## §0 Context Manifest

- /mnt/d/dev-base/.gran-maestro/explore/EXP-001/explore-report.md (P1-3 근거)
- /mnt/d/dev-base/rules/common.md (41-42, 213-282, 342-343 — `ul>li`, `.cont`, 부모+태그 선택자 규칙)
- /mnt/d/dev-base/rules/semantic-transform-rules.md (40-46, 66-71, 93-100)
- /mnt/d/dev-base/rules/basic.md (90-109 — 현행 안티패턴 진술, Task 02에서 정리됨)
- /mnt/d/dev-base/rules/templates/sub_list.html (현행 — 재작성 대상)
- /mnt/d/dev-base/rules/templates/sub_view.html (현행 — 재작성 대상)
- /mnt/d/dev-base/rules/templates/css/reset.css
- /mnt/d/dev-base/tools/init-project.py (이 템플릿을 어떻게 배포하는지)
- /mnt/d/dev-base/tools/validate-semantic.py (재작성된 템플릿이 통과해야 함)

## 1. 요약 (Summary)

`templates/sub_list.html`과 `templates/sub_view.html`을 `common.md`/`semantic-transform-rules.md` 규칙(`ul>li`, `.cont`, 부모+태그 선택자, 클래스 최소화, body.page_{name} prefix)을 준수하도록 재작성하여 신규 프로젝트가 안티패턴 골격으로 시작되지 않도록 한다.

## 2. 범위 (Scope)

- **포함**:
  - `rules/templates/sub_list.html` 전면 재작성: `div.list_row > div.list_item` → `ul.{prefix}_list > li > a` 패턴
  - `rules/templates/sub_view.html` 전면 재작성: `.inner` 제거, `.cont` 또는 페이지 prefix wrapper 사용, 모든 자식 요소에 클래스 부여 금지
  - 필요 시 동반 CSS (`templates/css/sub.css` 또는 `common.css` 추가 블록) 재작성
  - 두 파일의 `<body class="page_{name}">` 적용 (Task 02에서 결단된 영문 prefix 정책 준수)
- **제외**:
  - JS 동작 추가
  - 새로운 페이지 타입 템플릿 신설 (`sub_form.html` 등)
  - `init-project.py` 코드 수정 (템플릿 경로만 사용)
- **시작점 힌트**:
  - 현행 두 템플릿의 DOM 구조를 먼저 Read
  - `common.md` `ul>li` 패턴 예시 블록 + `semantic-transform-rules.md`의 부모+태그 선택자 예시
  - `tools/validate-semantic.py`의 검증 항목 (재작성된 결과가 검증 통과해야 함)

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable]
Given: 재작성된 `sub_list.html`, `sub_view.html`
When: `python3 tools/validate-semantic.py` 로 두 파일 + 동반 CSS를 검증
Then: 검증 통과 (에러 0건, warning은 검토)
Test: `python3 /mnt/d/dev-base/tools/validate-semantic.py --html rules/templates/sub_list.html [...]` (실제 인자는 validator help 참조)

#### AC-002 [MUST] [automatable]
Given: 재작성된 `sub_list.html`
When: HTML 구조 grep
Then:
- `div.list_row` 0건, `div.list_item` 0건
- `<ul` 1건 이상, `<li` 1건 이상
- `<body class="page_` 1건
Test: `grep -c "list_row\|list_item" sub_list.html` = 0; `grep -c "<ul\|<li" sub_list.html` ≥ 2

#### AC-003 [MUST] [manual]
Given: 재작성된 두 템플릿
When: 새 임시 프로젝트를 `python3 tools/init-project.py` 로 생성
Then: 생성된 프로젝트의 sub_*.html이 새 템플릿을 그대로 가지며 `common.md` 핵심 규칙을 위반하지 않음
Test: 수동 — `init-project.py /tmp/test-init --type basic --publishing` 후 `cat /tmp/test-init/templates/sub_list.html` 확인

## 3.5 Constraints

- 보안: N/A
- 성능: N/A
- 호환성: 기존 프로젝트에 이미 배포된 구 템플릿 카피본은 자동으로 마이그레이션되지 않음 — 본 태스크는 신규 프로젝트만 영향
- 운영: N/A

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: `common.md`의 CSS 한 줄 셀렉터 규칙, hex 색상, flex 전용, snake_case 클래스
- **알아야 할 제약**: Task 02가 결단한 영문 파일명+body class+prefix를 SoT로 사용. Task 02 spec.md를 먼저 Read해 결단 내용 확인.
- **접근법 방향**: ① 현행 템플릿 read → ② DOM을 `ul/li` + `.cont` 패턴으로 재설계 → ③ CSS 동반 작성 → ④ validate-semantic.py 통과 확인 → ⑤ init-project.py 수동 dry run

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): ["02"]  ← Task 02의 결단(영문 prefix 정책)이 확정되어야 body class 규칙을 반영할 수 있음
- 후행 작업 (blocks): []

## 6. 에이전트 팀 구성 (Agent Team)

- 실행: gemini-dev (퍼블리싱)
- 사유: CLAUDE.md 멀티 에이전트 분배 규칙에서 퍼블리싱(HTML/CSS) = gemini-dev. 대용량 컨텍스트로 common.md/semantic-transform-rules.md 전체를 한 번에 참조.

## 10. 가정 사항 (Assumptions)

- (가정 1) `sub_list.html`은 게시판형 리스트 페이지로 가정 — `<ul class="{prefix}_list"><li><a href><strong>제목</strong><span>날짜</span></a></li></ul>` 패턴 채택. 실제 사용 케이스가 다르면 approve 단계에서 피드백.
- (가정 2) `sub_view.html`은 단일 게시글 상세로 가정 — `.cont` wrapper + `h2` + `.{prefix}_meta`(작성일/조회수) + 본문 영역.
- (가정 3) 동반 CSS는 별도 `templates/css/sub.css` 신설보다 `common.css`에 섹션 주석으로 추가하는 것이 기존 패턴(common.css 한 파일에 누적)과 일치.

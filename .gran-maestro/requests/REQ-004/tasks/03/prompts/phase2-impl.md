# Implementation Request — Self-Exploration Mode

- Request: REQ-004 / Task: 03
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T03
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-004/tasks/03/spec.md
- Plan: N/A

## 구현 컨텍스트 (PM 작성)

EXP-001 탐색에서 발견한 P1-3 안티패턴 템플릿을 재작성한다. 현재 `rules/templates/sub_list.html`과 `sub_view.html`은 `common.md`/`semantic-transform-rules.md`의 핵심 규칙(`ul>li`, `.cont`, 부모+태그 선택자, 클래스 최소화)을 정면으로 위반하며, `init-project.py`가 이 안티패턴을 신규 프로젝트에 자동 배포한다.

**Task 02에서 확정된 결단 (이미 SoT)**:
- HTML 파일명: 영문 snake_case
- body class: `body.page_{name}` 필수 (예: `body.page_sub_list`)
- CSS prefix: 영문 `{name}_{role}` 강제 (예: `sub_list_title`)
- `max(calc(...))` 권장
- 시맨틱 변수명 (`--color_primary`) 권장

**핵심 주의사항**:
1. 두 템플릿을 **완전히 새로 작성**하라. 기존 구조(`div.list_row > div.list_item`, `.inner` wrapper)는 모두 버린다.
2. `sub_list.html`: 게시판 리스트 — `<ul class="sub_list_list"><li><a href="#"><strong>제목</strong><span>날짜</span></a></li></ul>` 패턴
3. `sub_view.html`: 단일 게시글 상세 — `.cont` 또는 페이지 prefix wrapper, `<h2>` 제목, `.sub_view_meta`(작성일/조회수), 본문
4. **부모+태그 선택자 우선** — `li`, `a`, `strong`, `span`에 클래스 부여 금지. 컨테이너 내 유일한 태그면 `.sub_list_list li a`로 충분.
5. CSS는 별도 `templates/css/sub.css` 신설보다 **`templates/css/common.css`에 섹션 주석 추가**가 기존 패턴(common.css 한 파일에 누적). common.css가 없으면 신설.
6. 각 셀렉터 규칙은 **한 줄 포맷**, hex 색상, flex 전용 (Grid 금지).
7. 작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T03`

## 자기탐색 지시

0. spec `## §0 Context Manifest` 파일들을 모두 Read (특히 `common.md`의 ul>li/.cont 예시 블록과 `semantic-transform-rules.md`의 부모+태그 선택자 규칙)
1. spec 직접 읽기: `Read /mnt/d/dev-base/.gran-maestro/requests/REQ-004/tasks/03/spec.md`
2. 현행 두 템플릿 read해서 어떤 구조인지 파악 (반면교사)
3. `templates/css/common.css` 또는 `templates/css/reset.css` 위치/내용 확인
4. 새 `sub_list.html`, `sub_view.html`을 worktree 경로에 Write로 덮어쓰기
5. 동반 CSS를 worktree의 common.css에 추가 (또는 신설)
6. [MANDATORY] §3 AC-002 grep을 worktree에서 실행:
   ```
   grep -c "list_row\|list_item" /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T03/rules/templates/sub_list.html
   grep -c "<ul\|<li" /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T03/rules/templates/sub_list.html
   grep -c "<body class=\"page_" /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T03/rules/templates/sub_list.html /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T03/rules/templates/sub_view.html
   ```
7. AC-001 validate-semantic.py 실행 (가능하면): `python3 /mnt/d/dev-base/tools/validate-semantic.py --html rules/templates/sub_list.html --css rules/templates/css/common.css 2>&1` — validator가 reset.css 링크를 강제할 수 있으니 link 태그 포함 권장.

## 규칙

- spec §2의 변경 범위 외 파일 수정 금지 (= `rules/templates/sub_list.html`, `rules/templates/sub_view.html`, `rules/templates/css/common.css` 또는 신설 sub.css만 허용)
- git commit은 하지 마세요 — PM이 직접 커밋합니다
- [MANDATORY] AC-002 grep 결과를 응답에 포함하세요
- 클래스 최소화: 컨테이너에만 prefix 클래스, 자식은 부모+태그 선택자
- letter-spacing은 em, line-height는 무단위, hex 색상 전용

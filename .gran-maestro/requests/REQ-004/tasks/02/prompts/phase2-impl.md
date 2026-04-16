# Implementation Request — Self-Exploration Mode

- Request: REQ-004 / Task: 02
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T02
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-004/tasks/02/spec.md
- Plan: N/A

## 구현 컨텍스트 (PM 작성)

EXP-001 탐색에서 발견한 직접 모순 6개를 한쪽 방향으로 결단하여 일원화하는 작업이다. EXP-001 보고서가 권장하는 SoT 방향(아래 Decision Log)을 그대로 채택한다. 모든 결단은 spec §2/§10에 명시되어 있으며, 작업은 grep으로 반대 방향 진술을 찾아 제거 또는 정정하는 것이다.

**Decision Log (그대로 적용)**:
1. `max(calc(...))` → **권장** (`common.md`의 금지 진술 제거)
2. 시맨틱 변수명 (`--color_primary`) → **권장** (`common.md`의 금지 진술 제거)
3. HTML 파일명 → **영문 snake_case 강제** (`common.md`/`publishing-workflow-guide.md`의 한글 허용 진술 제거)
4. body class → **`body.page_{name}` 필수** (한글 정책 잔존 진술 제거)
5. CSS prefix → **영문 `{name}_{role}` 강제** (한글/없음 허용 진술 제거)
6. `compare-css.py` 단계 → **deprecated** (rules/CLAUDE.md에서 제거)

핵심 주의사항:
1. spec §0 Context Manifest의 라인 번호를 우선 점프해서 작업하라.
2. 결단 방향과 반대되는 진술을 "한 줄 주석" 처리하지 말고 **완전 삭제** 또는 권장 방향 진술로 **재작성**하라.
3. 작업 후 spec §3의 grep 검증 6개를 모두 실행하여 결과 0건을 확인하라.
4. spec §10에 Decision Log가 이미 있으나, 추가로 작업한 파일과 변경 라인을 §11 형태로 spec.md 끝에 추가해도 좋다.
5. 작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T02`

## 자기탐색 지시

0. spec `## §0 Context Manifest` 파일들을 모두 Read
1. 스펙 직접 읽기: `Read /mnt/d/dev-base/.gran-maestro/requests/REQ-004/tasks/02/spec.md`
2. 6개 결단 항목을 한 번에 모아 작업 계획 수립
3. 항목별 Edit 적용
4. [MANDATORY] §3 AC-001/AC-002/AC-004의 grep 명령을 worktree에서 실행하고 출력 전체를 응답에 포함

작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T02`

## 규칙

- spec §2의 변경 범위 외 파일 수정 금지
- 추가 기능, 리팩토링, 스타일 변경 금지
- git commit은 하지 마세요 — PM이 직접 커밋합니다
- [MANDATORY] 완료 전 §3 Test grep을 실행하고 출력 전체를 응답에 포함하세요

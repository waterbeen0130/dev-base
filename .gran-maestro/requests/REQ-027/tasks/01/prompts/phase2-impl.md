# Implementation Request — REQ-027 / Task 01

- Request: REQ-027 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-027-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-027/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-008/plan.md

## 구현 컨텍스트

REQ-027은 PLN-008 4/5. DBG-001의 H1(컨텍스트 오버플로우) + H5(인라인 브리프 토큰 경쟁) 해소.

**핵심 작업**:
1. `rules/rules.yaml` — 모든 규칙에 `id`, `category`, `priority` 필드 보장. 미존재 시 추가. priority 충돌 해소 규약 문서화.
2. `rules/templates/publishing/impl-request.md` — 인라인 장문 CSS 규칙 블록 전부 삭제. `rule_ids: [all]` 또는 구체 ID 목록 + `rules_version: 2` 필드로 교체. 결과: 127줄 → 63줄 이하 (50%+ 감소).
3. `CLAUDE.md` `## 외주 브리프 규칙 주입` 섹션 — `### CSS 핵심 규칙 (인라인 — 규칙 파일 접근 불가 시 대비)` 블록을 Rule-ID 참조 방식으로 교체. "에이전트는 `rules/rules.yaml`에서 필요한 규칙 ID로 조회" 형태로 변경.

**주의**:
- rules.yaml의 규칙 ID 및 개수(57개, REQ-024/026 이후)는 변경하지 마세요
- CLAUDE.md에서 `## 외주 브리프 규칙 주입` 섹션 **내부만** 수정. 다른 섹션 건드리지 않음
- git commit 하지 마세요 — PM이 처리

[REFERENCE_CONTEXT]
current_date: 2026-04-16
model_cutoff: unknown
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시
1. spec.md 전체 Read
2. `rules/rules.yaml` 전체 Read — 현재 id/category/priority 구조 파악
3. `rules/templates/publishing/impl-request.md` 전체 Read — 인라인 규칙 블록 위치/내용 파악
4. `CLAUDE.md`에서 `## 외주 브리프 규칙 주입` 섹션 Read
5. TDD: TS-001~005 먼저 이해 후 구현
6. [MANDATORY] TS-001~005 전부 실행하고 출력 포함

## 규칙
- rules/rules.yaml, rules/templates/publishing/impl-request.md, CLAUDE.md 3개 파일만 수정 허용
- git commit 금지
- [MANDATORY] TS-001~005 전부 실행 후 출력 포함

# Implementation Request — REQ-025 / Task 01

- Request: REQ-025 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-025-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-025/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-008/plan.md

## 구현 컨텍스트 (PM 작성)

REQ-025는 **Spec-only 원칙 강제** — PLN-008 5단계 개선의 2단계(E). DBG-001이 찾아낸 H6(spec/구현 지시 미분리)를 해소합니다.

**핵심 작업**:
1. `CLAUDE.md`의 `## 피그마 MCP 기반 워크플로우` 섹션 전체를 삭제 (현재 `:367-423` 범위)
2. `CLAUDE.md`에서 "AI가 MCP 응답을 직접 해석" / "섹션별 MCP 호출" / "MCP 응답을 직접 해석하여" 등 MCP 직접 해석 허용 문구 전부 제거
3. `:172` "Figma MCP 응답의 노드 속성을 직접 해석하여 CSS 값 결정"을 "Figma 섹션 작업은 반드시 `figma-section-spec.py`로 생성된 spec.md/spec.json만 참조"로 대체
4. `rules/templates/publishing/impl-request.md`에 MCP 직접 해석 허용 문구가 있으면 제거
5. **PLN-004 섹션(`## PLN-004 Figma 워크플로우`)는 절대 건드리지 마세요** — 이건 Spec-first 경로 명문화된 정식 워크플로우이며 유지 대상

**중요 — 삭제 vs 유지 기준**:
- 삭제: "AI 직접 해석 허용" / "섹션별 MCP 호출로 AI가 해석" / "MCP 응답을 직접 해석" 류
- 유지: `:248` "raw Figma API / Figma MCP 응답을 직접 해석해 HTML/CSS를 작성하는 것을 금지한다" (이건 금지 선언이므로 유지)
- 유지: `figma-section-spec.py` 관련 모든 참조 (PLN-004 플로우의 정식 도구)

**주의**:
- CLAUDE.md는 사용자 핵심 문서이므로 섹션 삭제 시 **앞뒤 마크다운 헤딩 구조가 깨지지 않도록** 신중히 확인
- 삭제된 섹션의 존재 이유를 `rules/deprecated.md`에 한 줄 추가 (선택)
- git commit은 하지 말고 `git add`까지만 (또는 건드리지 말고 PM이 처리)

[REFERENCE_CONTEXT]
current_date: 2026-04-16
model_cutoff: unknown
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. `spec.md` 전체 Read
2. `CLAUDE.md` 전체 Read (550줄)
3. `rules/templates/publishing/impl-request.md` 전체 Read
4. `.gran-maestro/debug/DBG-001/finding-codex.md`에서 H6 부분 확인
5. 스펙 §2 범위 포함/제외 정확히 준수하며 편집
6. 편집 후 `## §3.5 Test Scenarios`의 모든 TS-001~006 명령을 실제 실행하고 출력 전체를 응답에 포함

## 규칙

- `CLAUDE.md` / `rules/templates/publishing/impl-request.md` 2개 파일만 수정 허용
- **PLN-004 섹션 보존 필수** (TS-005로 검증됨)
- git commit은 하지 마세요 — PM이 처리
- [MANDATORY] 완료 전 TS-001~006 전부 실행하고 출력 포함

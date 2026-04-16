# Implementation Request — Self-Exploration Mode

- Request: REQ-024 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-024-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-024/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-008/plan.md

## 구현 컨텍스트 (PM 작성)

이 REQ는 Figma→Code 파이프라인 개선 5단계 시리즈의 1단계 (A: 규칙 슬림 + 충돌 제거)입니다.
DBG-001 진단 결과 rules.yaml 97개 / validation_schema.json 93개의 과밀 규칙 + 내부 충돌이 "AI가 규칙을 무시하는" 근본 원인으로 확인되었습니다.

**핵심 작업 3가지**:
1. 중복/충돌 규칙 통합·삭제 (`flexbox_layout`↔`no_css_grid`, `forbidden_tag`↔`no_figure_figcaption`, `root_var_naming`, `no_raw_calc/no_raw_vw`)
2. `tools/validate-semantic.py`의 `column flex gap 금지` 함수(`:2626-2648`)를 룰 엔진에 연결 (현재 정의만 있고 호출 안됨)
3. `manual_review` 7개 + `documentation` 3개 규칙을 실행 가능화 또는 `rules/deprecated.md`로 이동

**주의**:
- 자동 검증 불가능한 포맷팅 규칙(CSS 한 줄, 미디어쿼리 들여쓰기)은 이번 REQ에서는 `# TODO(REQ-026): remove after auto-fix introduced` 주석만 추가하세요. **실제 삭제는 REQ-026 범위**.
- 모든 변경은 git 커밋 단위로 세분화 (규칙 1개 쌍 또는 1개 결정 = 1 커밋)하여 rollback 용이성 확보. PM이 최종 커밋하므로 당신은 git commit은 하지 마세요.
- `rules/deprecated.md`가 없으면 신규 생성하고, 삭제/이동된 각 규칙 ID에 대해 spec §3.5 Constraints에 명시된 형식으로 기록하세요.
- 회귀 검증은 `extracted/section_03_spec.json`/`section_04_spec.json` 기반으로 수행. 대응 HTML/CSS는 worktree 내 `output/` 또는 `landing/`에서 스스로 탐색하세요.

**TDD 필수**: AC-001/002/004/006은 테스트를 먼저 작성하고 통과시킨 뒤 구현 변경을 진행하세요 (spec §3.5 Test Scenarios 참조).

[REFERENCE_CONTEXT]
current_date: 2026-04-15
model_cutoff: unknown
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

아래 순서로 스펙을 직접 탐색하라. PM이 제공한 요약에 의존하지 말고 원본 파일을 직접 읽어라.

0. `/mnt/d/dev-base/.gran-maestro/requests/REQ-024/tasks/01/spec.md`의 `## §0 Context Manifest` 섹션을 확인하고, 나열된 파일 목록을 구현 전 가장 먼저 Read하라 (특히 DBG-001 finding-codex.md를 읽어 파일:라인 근거를 파악할 것)
1. 스펙 직접 읽기: `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-024/tasks/01/spec.md`
1.1. plan 직접 읽기: `cat /mnt/d/dev-base/.gran-maestro/plans/PLN-008/plan.md`
2. §2 범위의 작업 항목 4종과 제외 범위를 정확히 파악
3. §3 수락 조건(AC-001~006) + §3.5 Test Scenarios (TS-001~006)을 기준으로 구현
4. [MANDATORY] 모든 TS 명령을 실제 실행하고 출력 전체를 응답에 포함하세요 (pytest, grep, post-impl-verify.py 모두)

## 이전 피드백 (Phase 4 → 재실행 시)

N/A (첫 실행)

## 규칙

- spec §2의 변경 범위 외 파일 수정 금지
- 추가 기능, 리팩토링, 스타일 변경 금지
- git commit은 하지 마세요 — PM이 직접 커밋합니다
- [MANDATORY] 완료 전 spec §3.5 Test Scenarios (TS-001~006)의 모든 명령을 실행하고 출력 전체를 응답에 포함하세요
- TDD 필수: AC-001/002/004/006은 테스트 먼저 작성 후 구현 순서 준수
- 변경 파일 단위로 git add는 하되 commit은 하지 말 것 (PM이 `git add -A && commit` 수행)

# Implementation Spec

- Request ID: REQ-004
- Task ID: 02
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: rules/.md 모순 결단 및 정리] → 최종: claude-dev
- Assigned Team: claude-dev 단독
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T02
- Complexity: Standard

## §0 Context Manifest

- /mnt/d/dev-base/.gran-maestro/explore/EXP-001/explore-report.md (모순 6개 근거)
- /mnt/d/dev-base/rules/common.md (77-80, 89, 164-174, 668-670)
- /mnt/d/dev-base/rules/codex.md (49, 74-75, 36-43)
- /mnt/d/dev-base/rules/css-enhancement.md (204-211, 352-386)
- /mnt/d/dev-base/rules/rule_engine.json (178-190, 341-347, 397-403, 429)
- /mnt/d/dev-base/rules/validation_schema.json (60-61)
- /mnt/d/dev-base/rules/gemini.md (131-143)
- /mnt/d/dev-base/rules/publishing-workflow-guide.md (129-132)
- /mnt/d/dev-base/CLAUDE.md (파일명/body class 정책 SoT)

## 1. 요약 (Summary)

`rules/` 전반에 흩어진 직접 모순 6개를 결단하여 한쪽 방향으로 일원화하고 반대쪽 진술을 제거 또는 정정한다.

## 2. 범위 (Scope)

- **포함**: 아래 6개 모순 항목에 대해 각 결단을 적용
  1. **`max(calc(...))` 사용**: 권장 (`codex.md:49`, `css-enhancement.md:204-211` 유지) ↔ `common.md:77-80` 금지 진술 제거 또는 "권장" 으로 변경
  2. **시맨틱 CSS 변수명 (`--color_primary` 등)**: 권장 (`css-enhancement.md:352-386`, `rule_engine.json:341-347` 유지) ↔ `common.md:89` 금지 진술 제거
  3. **HTML 파일명 정책**: 영문 snake_case (`gemini.md:131-143`, `codex.md:36-43`, `rule_engine.json:178-190`, `validation_schema.json:60-61` 유지) ↔ `common.md:164-174,668-670`, `publishing-workflow-guide.md:129-132`의 한글 파일명 허용 진술 제거
  4. **body class 정책**: `body.page_{name}` 필수 (위 영문 파일명과 동일 SoT) ↔ `common.md`의 "body class 없이" 진술 제거
  5. **CSS 클래스 prefix match 정책**: 영문 prefix 강제 (`{name}_{role}`) ↔ `common.md`의 한글/없음 허용 진술 제거
  6. **`rules/CLAUDE.md`의 `compare-css.py` 단계**: 메인 `CLAUDE.md`와 일치하도록 정렬 (제거 또는 메인에 추가) — 결정 1: `compare-css.py`를 deprecated 표기하고 `rules/CLAUDE.md`에서도 제거 (Figma MCP 워크플로우 단일화 방향)
- **제외**:
  - 템플릿 파일(`templates/sub_list.html`) 재작성 (Task 03 범위)
  - `validate-semantic.py` 코드 변경 (별도 REQ)
  - 새 규칙 추가
- **시작점 힌트**:
  - 위 §0 Context Manifest 라인 번호로 직접 점프
  - `rules/CLAUDE.md`와 `/mnt/d/dev-base/CLAUDE.md` diff 대조

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable]
Given: 결단 후 rules/ 파일들
When: 6개 모순 항목 각각에 대해 grep으로 반대 방향 진술 잔존 여부 확인
Then: 각 모순에 대해 "한 방향만" 검색됨 (반대 방향 0건)
Test: 항목별 grep 명령 6개 작성 후 각 0건 확인

#### AC-002 [MUST] [automatable]
Given: 한글 파일명 허용 진술이 제거된 상태
When: `grep -rn "한글 파일명\|한글로 작성" /mnt/d/dev-base/rules /mnt/d/dev-base/CLAUDE.md`
Then: 0건
Test: 위 grep

#### AC-003 [MUST] [manual]
Given: 6개 결단 반영 후
When: 각 결단을 한 줄씩 spec §11에 "Decision Log" 표로 정리하고 PM(사용자)가 검토
Then: 결단 방향과 영향 파일이 명확히 기록되어 있음
Test: 수동 검토 — Decision Log 표 6행 모두 기입 확인

#### AC-004 [MUST] [automatable]
Given: `rules/CLAUDE.md`의 `compare-css.py` 단계 제거
When: `grep -n "compare-css" /mnt/d/dev-base/rules/CLAUDE.md`
Then: 0건 또는 deprecated 주석만 잔존
Test: 위 grep + 잔존 시 주석 형태 확인

## 3.5 Constraints

- 보안: N/A
- 성능: N/A
- 호환성: 결단 방향이 기존 `output/*` 산출물 다수와 어긋나는 경우, 산출물 마이그레이션은 별도 REQ로 위임 — 본 태스크는 규칙 문서만 정리
- 운영: N/A

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: 기존 .md 들여쓰기, 헤딩 스타일 유지
- **알아야 할 제약**: 결단 방향은 EXP-001 보고서 권장(`max(calc())` 권장, `--color_primary` 권장, 영문+body class+prefix)을 SoT로 채택. 사용자가 다른 방향을 원하면 approve 단계에서 피드백.
- **접근법 방향**: 6개 모순을 한 번에 모아 Decision Log 작성 → 항목별 Edit → grep 검증

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): []

## 10. 가정 사항 (Assumptions)

- (가정 1) `max(calc())` 권장 채택 — `css-enhancement.md`와 `codex.md`가 더 상세하고 실제 enhancement 워크플로우의 핵심 패턴이므로 `common.md`의 1줄 금지 진술이 후행 결정으로 무효화됨.
- (가정 2) 시맨틱 변수명(`--color_primary`) 권장 채택 — enhancement 단계에서 색상 변수화는 필수 패턴이며 `rule_engine.json`이 강제하므로 `common.md` 금지 진술 제거.
- (가정 3) 영문+body class+prefix 채택 — `validation_schema.json`이 prefix match를 강제 검증하고 CLAUDE.md 본문이 영문 명시이므로 한글 허용 진술 제거.
- (가정 4) `compare-css.py` 워크플로우 deprecated — Figma MCP 직접 해석 방식이 SoT (CLAUDE.md 본문 강조).
- (가정 5) 위 결단으로 인해 산출물(`output/*`) 일부가 새 규칙과 어긋날 수 있으나 본 태스크는 규칙 정리만 수행하고 산출물 마이그레이션은 별도 REQ로 위임.

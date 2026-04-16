# REQ-025 / Task 01 — Spec-only 원칙 강제

**Assigned Agent**: [config: codex-dev] → codex-dev (문서·템플릿 수정, 텍스트 대체 중심)
**Source Plan**: PLN-008
**Linked Debug**: DBG-001

## §0 Context Manifest

- `/mnt/d/dev-base/CLAUDE.md` (변경 대상, 약 550줄)
- `/mnt/d/dev-base/rules/templates/publishing/impl-request.md` (변경 대상)
- `/mnt/d/dev-base/.gran-maestro/debug/DBG-001/debug-report.md` (근거 — H6 진단)
- `/mnt/d/dev-base/.gran-maestro/debug/DBG-001/finding-codex.md` (파일·라인 근거)

## §1 요약

DBG-001이 식별한 **H6: spec/구현 지시 미분리** 해소. `CLAUDE.md`에 "spec만 참조"(`:264-265`) 원칙과 "MCP 직접 해석"(`:367-373`) 경로가 **동시에 존재**하여 에이전트가 raw Figma 응답을 재해석하는 원인이 됨. MCP 직접 해석 경로를 완전 삭제하고 `figma-section-spec.py` 경유만 유일한 경로로 명시.

## §2 범위

### 포함 (In-scope)

#### CLAUDE.md 수정
1. **"피그마 MCP 기반 워크플로우" 섹션 전체 삭제** — 현재 `:365-423` 범위. 이 섹션은 "섹션별 MCP 호출 → AI가 직접 해석"을 허용하는데 PLN-004 5단계 플로우(`:245-300`)와 정면 충돌.
2. **"Figma 추출 전 필수 실행" 섹션 정리** — 현재 `:166-198`. 그 안의 `:172` "Figma MCP 응답의 노드 속성을 직접 해석하여 CSS 값 결정" 문구 삭제. figma-section-spec.py 경유 강제 문구로 대체.
3. **"피그마 코드 생성 품질 규칙" 섹션** (현재 `:302-357`)의 MCP 관련 언급 정리. `figma-section-spec.py`가 이미 spec.json을 만들어주는 전제에서 재작성.
4. "MCP 응답을 직접 해석" / "AI 직접 해석" 문자열 검색 후 전부 제거 (PLN-004 섹션의 경고 문구 `:248`은 유지 — 이미 금지 선언이므로).

#### rules/templates/publishing/impl-request.md 수정
5. 해당 템플릿에 MCP 직접 해석 경로나 "MCP 응답 해석" 허용 문구가 있으면 삭제. 템플릿은 "spec.md만 참조" 단일 경로만 유지.

### 제외 (Out-of-scope)
- 실제 tool 코드 수정 (REQ-027/028 범위)
- `figma-section-spec.py` 기능 확장 (REQ-028 범위)
- PLN-004 5단계 플로우 문서 자체 재작성 (현재 섹션 유지, MCP 경로만 제거)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] — MCP 직접 해석 경로 문자열 0건
- **Given**: 현재 `CLAUDE.md:367-423` 범위에 "피그마 MCP 기반 워크플로우" 섹션이 존재하고 MCP 직접 해석을 허용함
- **When**: REQ-025 완료 후 아래 검색 실행
- **Then**: 0건 매칭
- **Test**:
  ```bash
  grep -c "AI가 MCP 응답을 직접 해석\|AI 직접 해석 허용\|MCP 응답을 직접 해석하여\|섹션별 MCP 호출" CLAUDE.md
  ```
  기대 출력: `0`

### AC-002 [automatable] [tdd-required] — 피그마 MCP 기반 워크플로우 섹션 삭제
- **Given**: `CLAUDE.md`의 섹션 헤딩 `## 피그마 MCP 기반 워크플로우` 존재
- **When**: 섹션 전체 삭제
- **Then**: 해당 헤딩이 존재하지 않음
- **Test**:
  ```bash
  grep -c "^## 피그마 MCP 기반 워크플로우" CLAUDE.md
  ```
  기대 출력: `0`

### AC-003 [automatable] [tdd-required] — figma-section-spec.py 단일 경로 명시
- **Given**: 현재 CLAUDE.md에 `figma-section-spec.py`가 언급되지만 MCP 직접 해석 경로와 공존
- **When**: MCP 경로 삭제 후, "Figma 작업은 반드시 figma-section-spec.py 경유" 취지의 명시 문장 1개 이상 존재
- **Then**: grep 매칭 1건 이상
- **Test**:
  ```bash
  grep -c "figma-section-spec.py" CLAUDE.md
  ```
  기대 출력: `1` 이상 (기존 PLN-004 섹션 언급 포함)

### AC-004 [manual] — 템플릿 정합성
- **Given**: `rules/templates/publishing/impl-request.md`에 MCP 직접 해석 허용 문구가 있을 수 있음
- **When**: 해당 파일을 검토하여 MCP 직접 해석을 암시하는 문구 제거
- **Then**: 템플릿이 "spec.md 단일 경로"만 제시
- **Test**: `grep -i "MCP 응답을 직접\|AI가 MCP\|MCP 해석" rules/templates/publishing/impl-request.md` → 0건

## §3.3 PAC Mapping

| PAC ID | Grade | Tier | Mapped Spec AC IDs | Coverage |
|--------|-------|------|--------------------|----------|
| PAC-3  | MUST  | TIER-A | AC-001, AC-002 | full |

> PAC-3: "CLAUDE.md에서 'MCP 직접 해석' 경로가 삭제되고 'spec만 참조' 원칙이 단일 경로로 남아있음이 확인된다."

## 3.5 Test Scenarios (Pre-Impl)

### TS-001 (AC-001)
- **명령**: `grep -cE "AI가 MCP 응답을 직접 해석|AI 직접 해석 허용|MCP 응답을 직접 해석하여|섹션별 MCP 호출" CLAUDE.md`
- **기대**: `0`

### TS-002 (AC-002)
- **명령**: `grep -cE "^## 피그마 MCP 기반 워크플로우" CLAUDE.md`
- **기대**: `0`

### TS-003 (AC-003)
- **명령**: `grep -c "figma-section-spec.py" CLAUDE.md`
- **기대**: `>= 1`

### TS-004 (AC-004)
- **명령**: `grep -ciE "MCP 응답을 직접|AI가 MCP|MCP 해석" rules/templates/publishing/impl-request.md`
- **기대**: `0`

### TS-005 (회귀) — 기존 PLN-004 섹션 보존 확인
- **명령**: `grep -c "PLN-004 Figma 워크플로우" CLAUDE.md`
- **기대**: `>= 1` (PLN-004 5단계 플로우 섹션은 유지되어야 함 — Spec-first 경로 명문화된 정식 워크플로우)

### TS-006 (스모크) — 파일 유효성
- **명령**: `wc -l CLAUDE.md && head -20 CLAUDE.md && tail -20 CLAUDE.md`
- **기대**: 파일 읽기 성공, 헤딩 구조 깨지지 않음 (수동 확인)

## §3.5 Constraints

- **MCP 금지 선언은 유지** — `:248`의 "raw Figma API / Figma MCP 응답을 직접 해석해 HTML/CSS를 작성하는 것을 금지한다" 문장은 PLN-004 섹션 소속이며 경고이므로 유지.
- **figma-section-spec.py 자체 참조는 유지** — PLN-004 5단계 플로우에서 이미 쓰임.
- **역호환**: 기존 퍼블리싱 REQ들이 `CLAUDE.md` 섹션을 참조할 수 있으므로, 완전 삭제보다는 "삭제된 경로 이유"를 `rules/deprecated.md`에 한 줄 추가하는 것도 허용 (선택적).
- **섹션 범위 변경 금지**: "피그마 MCP 기반 워크플로우" 외 다른 섹션의 내용 수정 금지 (스코프 제한).

## §5 선행 작업 (blockedBy)
- REQ-024 (rules 슬림 완료 후 문서 정리가 더 일관됨)

## §6 후행 작업 (blocks)
- REQ-026 (auto-fix 루프 — spec-only 원칙 확립 후 repair 경로 설계)

## §7 의존성 요약
- 관련: DBG-001 (H6 진단), PLN-008

## §8 테스트 전략
- grep 기반 automatable AC 4개
- 수동 검토: CLAUDE.md 전체 일독으로 문서 흐름 깨지지 않는지 확인
- 회귀: PLN-004 5단계 플로우 섹션 보존 확인 (TS-005)

## §9 디버그 연계
- **참조**: DBG-001 H6 (spec/구현 지시 미분리)
- **근거 라인** (finding-codex.md 기준):
  - `CLAUDE.md:264-265` "spec만 참조"
  - `CLAUDE.md:367-373` "MCP 직접 해석" (삭제 대상)
- **본 REQ 대응**: 충돌하는 두 경로 중 MCP 직접 해석 경로를 삭제하여 단일 경로 확립

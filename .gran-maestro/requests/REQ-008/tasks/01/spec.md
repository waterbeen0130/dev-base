# Implementation Spec

- Request ID: REQ-008
- Task ID: 01
- Created: 2026-04-13
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: backend/tools] → 최종: codex-dev
- Assigned Team: codex-dev 단독 (Python 스크립트, 외부 의존성 없음)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-008-01
- Complexity: Standard

## §0 Context Manifest

> 구현 시작 전 이 목록의 파일을 가장 먼저 Read하세요.

- .gran-maestro/plans/PLN-004/plan.md
- tools/figma-section-spec.py
- tools/validate-semantic.py
- rules/common.md

## 1. 요약 (Summary)

REQ-007에서 생성된 `spec.json`과 구현된 HTML/CSS를 입력으로 받아 9개 검증 항목(텍스트 위변조, 줄바꿈, 폰트 5필드, lineHeight 비율, 색상, padding/gap 반영, clamp, column flex gap, interaction URL)을 자동 실행하는 `tools/figma-validate.py`를 신설한다.

## 2. 범위 (Scope)

- **포함**:
  - `tools/figma-validate.py` 신규 작성 (CLI 진입점 1개, Python 3.10+, 외부 의존성 금지 — 표준 라이브러리만)
  - 입력: `--spec {section}_spec.json --html output.html --css output.css`
  - 9개 검증 항목 (PLN-004 plan.md §3.2 `figma-validate.py` 전체)
  - 출력: 사람이 읽는 표 + 위반 항목 리스트; exit 0 (PASS) / 1 (FAIL)
  - 누락된 spec 행 목록을 별도 섹션으로 출력
- **제외**:
  - `tools/figma-section-spec.py` 수정 (spec.json 포맷은 현재 구조 그대로 소비)
  - `tools/validate-semantic.py` 로직 변경 (병렬 도구로 공존)
  - Figma API 호출 (spec.json만 소비)
- **시작점 힌트**:
  - `tools/figma-section-spec.py` (spec.json 스키마: `section`, `text_nodes[]`, `frame_nodes[]`, `interactions[]`, `image_refs[]`)
  - `tools/validate-semantic.py` (HTML/CSS 파싱 패턴 재사용 가능)

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable] [unit-test]
Given: `tools/figma-validate.py`가 작성되어 있고 REQ-007에서 생성된 spec.json 샘플이 존재한다
When: `python3 tools/figma-validate.py --spec <sample>_spec.json --html <sample>.html --css <sample>.css` 실행
Then: 9개 검증 항목 모두 실행되고, 위반 0건 시 exit 0 / 위반 발생 시 exit 1, 위반 항목은 "카테고리 | 노드 | 기대값 | 실제값" 형식의 표로 stdout에 출력된다
Test: `python3 tools/figma-validate.py --spec extracted/sample_spec.json --html extracted/sample.html --css extracted/sample.css; echo $?`

#### AC-002 [MUST] [automatable]
Given: spec.json의 text_nodes가 1개 이상 존재한다
When: figma-validate.py가 실행된다
Then: 아래 9개 검증 카테고리가 모두 평가된다
  1. **텍스트 위변조**: 각 text_node의 `characters`가 HTML 텍스트에 존재 (공백/개행 정규화 후 부분 일치)
  2. **줄바꿈 보존**: `\n` → `<br>` 또는 줄바꿈, `\u2028` → `<br>`, `\xa0` → `&nbsp;` 또는 non-breaking space 문자
  3. **폰트 5필드 완결성**: text_node와 매칭되는 CSS 셀렉터에 `font-family`, `font-size`, `font-weight`, `line-height`, `color` 5개가 모두 선언됨 (누락 시 위반)
  4. **lineHeight 비율 일치**: CSS `line-height` 값이 spec의 `lineHeightRatio` 와 일치 (무단위 비율 기준, 오차 ±0.05)
  5. **fills color hex 일치**: CSS `color` / `background` 값이 spec `color` / `fills[].color` 와 hex 일치 (대소문자 무시)
  6. **frame padding/gap 반영**: frame_node의 `paddingTop/Right/Bottom/Left`, `itemSpacing`이 CSS에 반영됨 (값 일치 또는 계산 가능)
  7. **clamp 적용**: padding/gap이 100 이상인 경우 CSS 값이 `clamp()` 사용
  8. **column flex gap 금지**: `layoutMode == "VERTICAL"` 인 frame에 대응하는 CSS가 `gap` 속성을 사용하지 않음 (column flex gap 룰 위반 검출)
  9. **interaction URL 일치**: spec `interactions[].url` 이 HTML에 `<a href="{url}" target="_blank">` 형태로 존재
Test: 각 카테고리별 최소 1개 위반 케이스와 1개 통과 케이스에 대해 수동 실행으로 결과 확인

#### AC-003 [MUST] [automatable]
Given: spec.json의 모든 text_nodes 중 HTML/CSS에서 참조되지 않은 노드가 존재한다
When: figma-validate.py 실행
Then: stdout 말미에 "누락된 spec 행" 섹션에 text_node.id + characters 목록이 출력되고, 누락이 1개 이상이면 exit 1
Test: spec.json에 dummy text_node를 추가한 HTML/CSS 샘플로 실행 → 누락 검출 확인

#### AC-004 [MUST] [automatable] [impact-check]
Given: 기존 `tools/validate-semantic.py`가 정상 동작한다
When: REQ-008 변경 후 `python3 tools/validate-semantic.py --help` 실행
Then: validate-semantic.py는 변경 없이 동일하게 동작 (exit 0, 사용법 출력)
Test: `python3 tools/validate-semantic.py --help`

#### AC-005 [MUST] [automatable] [lint-check]
Given: Python 파일이 작성됨
When: `python3 -m py_compile tools/figma-validate.py` 실행
Then: 컴파일 에러 0건
Test: `python3 -m py_compile tools/figma-validate.py`

## 3.2 Intent Trace

| AC-ID | 의도 근거 | 근거 출처 | 신뢰도 |
|-------|-----------|-----------|--------|
| AC-001 | "spec.json + 결과 HTML/CSS를 입력으로 받아 9개 검증 항목을 모두 실행하고 위반 시 non-zero exit" | plan.md §4 PAC-4 | High |
| AC-002 | "9개 검증 항목 정의" | plan.md §3 `figma-validate.py` | High |
| AC-003 | "누락된 spec 행 목록을 표와 함께 출력" | plan.md §3 출력 | High |
| AC-004 | "기존 validate-semantic.py는 변경 없이 동작 유지" | plan.md §4 PAC-5 [IMPACT] | High |

## 3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-4 | MUST / TIER-A | AC-001, AC-002, AC-003 | Full |
| PAC-5 | MUST / TIER-A [IMPACT] | AC-004 | Full |

## 3.5 Constraints

- 보안: Figma 토큰 사용 없음 (spec.json만 소비)
- 성능: 단일 섹션 검증 < 2초
- 호환성: Python 3.10+, 외부 의존성 금지 (stdlib만)
- 운영: 기존 tools/ 스크립트와 동일한 CLI 컨벤션 유지 (argparse, stderr 에러, stdout 결과)

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**:
  - `tools/figma-section-spec.py`의 CLI/에러 처리 스타일 (argparse, `fail()` 함수, stderr)
  - `tools/validate-semantic.py`의 CSS 파싱 방식 (정규식 기반)
  - spec.json 스키마는 figma-section-spec.py의 `normalize_text_node` / `normalize_frame_node` 출력 그대로 소비
- **알아야 할 제약**:
  - 외부 패키지 금지 (stdlib만) — PLN-004 §5 제약
  - CSS 값 비교 시 shorthand(`padding: 20px 40px`)와 longhand(`padding-top: 20px`) 모두 파싱 필요
  - lineHeight 비교는 무단위 비율 기준 (CSS line-height: 1.5) — px 값은 오차 허용
- **접근법 방향**: spec.json을 SSOT로 취급, HTML/CSS를 파싱해 셀렉터-노드 매칭 후 9개 규칙을 순차 평가. 매칭은 HTML 텍스트 내용으로 찾는 것이 가장 안정적 (클래스명은 규칙에 의해 바뀔 수 있음).

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): [] (REQ-007 done, blockedBy 해제)
- 후행 작업 (blocks): [REQ-008-02]

## 6. 에이전트 팀 구성 (Agent Team)

- 실행: codex-dev (backend/tools)
- 사유: 순수 Python CLI 도구, 파싱/검증 로직 중심 → codex-dev의 code/refactor/test 영역에 정확히 부합

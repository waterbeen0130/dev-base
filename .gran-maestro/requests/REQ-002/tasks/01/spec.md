# REQ-002 T01: figma-extract.py 정규화 엔진 재작성

## §0 Context Manifest

> 아래는 시작점 힌트입니다. 구현 중 자율적으로 추가 탐색하세요.

- `tools/figma-extract.py` — 재작성 대상 (916행)
- `rules/rule_engine.json` — 프로젝트 타입/변환 규칙 정의
- `.gran-maestro/agile/AGI-001/objective/details/normalization-engine.md` — 상세 설계 (중간 JSON 스키마, 변환 규칙 매핑표)
- `.gran-maestro/agile/AGI-001/objective/objective.md` — 프로젝트 목표

## §1 요약

기존 figma-extract.py를 전면 재작성하여 Figma MCP JSON → 정규화된 중간 JSON 변환 엔진을 구축한다. 트리 구조를 보존하며 모든 시각적 속성(레이아웃, 색상, 타이포, 간격, 보더)을 CSS 값으로 확정한다. basic/landing 프로필을 JSON 설정으로 분리하고, 변환 규칙을 docs/conversion-rules.md에 문서화한다.

## §2 범위

### 포함
- `tools/figma-extract.py` 전면 재작성 (단일 Python 파일 유지)
- `tools/profiles/basic.json`, `tools/profiles/landing.json` 신규 생성
- `docs/conversion-rules.md` 신규 생성 (전체 Figma→CSS 매핑표)
- 기존 CLI 인터페이스: --stdin, --tree, --profile 지원

### 제외
- 2차 시멘틱 변환 (DOD-004)
- validate.js 매핑 출력
- 마크다운 테이블 출력
- Figma API 직접 호출 (--node-id 모드)

## §3 수락 조건

### AC-001 [automatable] [tdd-required] 정규화 JSON 출력
- **Given**: Figma MCP JSON이 stdin으로 입력된 상태
- **When**: `python3 tools/figma-extract.py --stdin --profile basic` 실행 시
- **Then**: 정규화된 중간 JSON이 stdout으로 출력되며, `meta` (source, profile, section_name, total_nodes)와 `tree` (id, name, type, layout, visual, text, children) 구조를 포함한다
- **Test**: `echo '<sample_json>' | python3 tools/figma-extract.py --stdin --profile basic | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'meta' in d and 'tree' in d"`

### AC-002 [automatable] [tdd-required] 레이아웃 속성 변환
- **Given**: layoutMode, itemSpacing, padding, alignment, sizing 속성이 있는 Figma 노드
- **When**: 정규화 엔진을 통과할 때
- **Then**: layout 객체에 display, direction, gap, padding(shorthand), justify, align, sizing이 CSS 값으로 포함된다
- **Test**: `pytest tests/test_normalization.py -k "test_layout" -v`

### AC-003 [automatable] [tdd-required] 시각 속성 변환
- **Given**: fills, strokes, cornerRadius 속성이 있는 Figma 노드
- **When**: 정규화 엔진을 통과할 때
- **Then**: visual 객체에 background(hex), border(stroke 기반만), borderRadius(px/50%/2em) 값이 포함된다
- **Test**: `pytest tests/test_normalization.py -k "test_visual" -v`

### AC-004 [automatable] [tdd-required] 타이포그래피 속성 변환
- **Given**: fontSize, fontWeight, lineHeightPx, letterSpacing, fills가 있는 TEXT 노드
- **When**: 정규화 엔진을 통과할 때 (--profile basic)
- **Then**: text.segments[].style에 fontSize(rem), fontWeight, lineHeight(ratio), letterSpacing(em), color(hex) 값이 포함된다
- **Test**: `pytest tests/test_normalization.py -k "test_typography" -v`

### AC-005 [automatable] [tdd-required] characterStyleOverrides 누적 병합
- **Given**: characterStyleOverrides와 styleOverrideTable이 있는 TEXT 노드
- **When**: 정규화 엔진을 통과할 때
- **Then**: text.segments 배열에 각 세그먼트의 text, style(완전 해석), is_override가 정확히 분할된다
- **Test**: `pytest tests/test_normalization.py -k "test_override" -v`

### AC-006 [automatable] [tdd-required] 프로필 분리 (basic vs landing)
- **Given**: 동일한 Figma 노드 (fontSize: 16)
- **When**: --profile basic vs --profile landing으로 각각 실행할 때
- **Then**: basic은 fontSize "1rem", landing은 fontSize "16px"를 출력한다
- **Test**: `pytest tests/test_normalization.py -k "test_profile" -v`

### AC-007 [automatable] 프로필 JSON 파일 존재
- **Given**: 프로젝트 루트
- **When**: tools/profiles/ 디렉토리를 확인할 때
- **Then**: basic.json과 landing.json이 존재하며 font_size_pc, font_size_mobile, rem_base 등 필드를 포함한다
- **Test**: `python3 -c "import json; [json.load(open(f'tools/profiles/{p}.json')) for p in ('basic','landing')]"`

### AC-008 [automatable] 변환 규칙 문서화
- **Given**: 정규화 엔진 구현 완료
- **When**: docs/conversion-rules.md를 확인할 때
- **Then**: 모든 Figma 속성 → CSS 변환 규칙이 매핑표로 정리되어 있다 (레이아웃/시각/타이포/오버라이드/프로필 카테고리별)
- **Test**: `test -f docs/conversion-rules.md && grep -c '|' docs/conversion-rules.md`

### AC-009 [automatable] [impact-check] 기존 --tree 모드 호환
- **Given**: 재작성된 figma-extract.py
- **When**: --tree 플래그로 실행할 때
- **Then**: 기존과 동일한 형식으로 노드 트리가 출력된다
- **Test**: `echo '<sample>' | python3 tools/figma-extract.py --stdin --tree`

### AC-010 [automatable] [impact-check] 기존 smoke test 호환
- **Given**: tests/test_smoke.py의 기존 7개 테스트
- **When**: pytest 실행 시
- **Then**: 7개 테스트 모두 PASSED
- **Test**: `pytest tests/test_smoke.py -v`

## Test Scenarios (Pre-Impl)

각 AC에 매핑된 Test 명령어 참조. 핵심 시나리오:
1. 빈 노드 입력 → 빈 children으로 정상 출력
2. 중첩 3단계 이상 트리 → 재귀 정규화 완료
3. characterStyleOverrides 3+ 세그먼트 → 정확한 분할
4. basic/landing 동일 입력 다른 출력 → 프로필 분기 검증
5. visible:false 노드 → 제외 확인

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-1 | MUST | AC-001 | Covered |
| PAC-2 | MUST | AC-002 | Covered |
| PAC-3 | MUST | AC-003 | Covered |
| PAC-4 | MUST | AC-004 | Covered |
| PAC-5 | MUST | AC-005 | Covered |
| PAC-6 | MUST | AC-006 | Covered |
| PAC-7 | MUST | AC-007 | Covered |
| PAC-8 | MUST | AC-008 | Covered |
| PAC-9 | SHOULD | AC-009 | Covered |
| PAC-10 | SHOULD | AC-010 | Covered |
| PAC-11 | MUST | T02 테스트 태스크 | Covered |

## §3.4 Epic DoD Mapping

| DoD ID | DoD 설명 | Mapped Spec AC IDs | Coverage |
|--------|---------|-------------------|----------|
| DOD-001 | 정규화 JSON 변환 | AC-001, AC-002, AC-003, AC-004, AC-005 | Covered |
| DOD-002 | 변환 규칙 문서화 | AC-008 | Covered |
| DOD-003 | 프로필 분리 | AC-006, AC-007 | Covered |

## §3.5 Constraints
- Python 3.x, 표준 라이브러리만 사용
- 단일 파일 유지 (tools/figma-extract.py)
- stdin 파이프 방식 유지
- 기존 함수 시그니처(rgba_to_hex, extract_fill_color 등) 유지 또는 호환 래퍼 제공

## §5 선행 작업 (blockedBy)
- 없음

## §5 후행 작업 (blocks)
- T02

## §7 Assigned Agent
[config: codex-dev] → codex-dev (Python 전면 재작성, 단일 모듈)

## §8 실행 지시

### 핵심 구현 방향
1. **반드시 `.gran-maestro/agile/AGI-001/objective/details/normalization-engine.md`를 먼저 Read**하여 목표 JSON 스키마와 전체 변환 규칙 매핑표를 숙지한 후 구현을 시작하세요.
2. `rules/rule_engine.json`의 `project_type` 섹션을 참고하여 프로필 JSON을 생성하세요.
3. 기존 figma-extract.py의 핵심 유틸 함수(rgba_to_hex, extract_fill_color, line_height_to_ratio, letter_spacing_to_em, figma_align_to_css)는 동일 시그니처로 유지하거나 호환 래퍼를 제공하세요 — tests/test_smoke.py가 이 함수들을 import합니다.
4. 출력은 트리 구조 JSON (중첩, flat 아님). `meta` + `tree` 최상위 구조.
5. --tree 모드는 기존과 동일한 텍스트 트리 출력을 유지하세요.
6. docs/conversion-rules.md에 모든 변환 규칙을 Figma 속성 | CSS 속성 | 변환 규칙 형태의 매핑표로 문서화하세요.

### 테스트를 먼저 작성한 후 구현하세요 (TDD)

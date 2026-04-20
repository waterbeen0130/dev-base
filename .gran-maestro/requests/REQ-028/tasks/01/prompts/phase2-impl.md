# Implementation Request — REQ-028 / Task 01

- Request: REQ-028 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-028-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-028/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-008/plan.md

## 구현 컨텍스트

REQ-028은 PLN-008 **5/5 마지막** — **가장 큰 구조 개편**. Builder.io/Mitosis IR 패턴 차용.

**핵심**: `figma-section-spec.py`에 `--codegen` 플래그를 추가하여 spec.json으로부터 **Base HTML/CSS 뼈대**와 **디자인 토큰(tokens.json)**을 기계적으로 생성. LLM은 이 뼈대를 받아 시맨틱 교체(`div`→`nav/h2`)와 클래스 네이밍만 수행.

**구현 전략 (추천)**:
- 기존 `figma-section-spec.py`의 `ExtractionResult`(section, text_nodes, frame_nodes)를 입력으로 하는 **별도 모듈 함수** 3종 추가:
  - `generate_base_html(result: ExtractionResult, section_name: str) -> str`
  - `generate_base_css(result: ExtractionResult, section_name: str) -> str`
  - `generate_tokens(result: ExtractionResult) -> dict`
- `main()` 함수에서 `--codegen` 체크 후 3종 호출 + 파일 Write
- Figma API 호출 없이 spec.json을 직접 파싱하는 **오프라인 경로**도 추가 (테스트용):
  - `--from-spec extracted/section_03_spec.json --codegen` → API 미호출, spec.json만 읽어서 base.html/css/tokens.json 생성

**CSS 변환 필수 규칙** (common.md + CLAUDE.md):
- `layoutMode: "VERTICAL"` → `flex-direction: column;` + **gap 금지** (column flex gap 규칙). 수직 간격은 margin으로.
- `layoutMode: "HORIZONTAL"` → `flex-direction: row;` + `gap: {itemSpacing}px;`
- padding 100px+ → `clamp()` 래핑: `clamp({min}, {px}px, {max})` (min=px*0.6, max=px*1.2 정도의 합리적 범위)
- fills → hex 전용 (`#RRGGBB`)
- lineHeightPx/fontSize → 무단위 비율 (소수점 2자리)
- letterSpacing → em 변환 (`letterSpacing / fontSize`)em
- cornerRadius 999/9999 → `2em`, 원형(width==height) → `50%`
- 각 셀렉터 한 줄

**테스트**: 기존 `extracted/section_03_spec.json`을 golden input으로 사용. Figma API 호출 없이 spec.json만으로 테스트 가능하도록 설계.

**DSC-002 합의**: `preprocess_payload/hints` — DSC-002 consensus.md를 Read하여 구현 가능한 부분 반영. 불가능하면 skip + 주석 기록.

**주의**:
- 기존 spec.json/spec.md 포맷은 변경하지 마세요 (추가 필드는 OK)
- ExtractionResult dataclass 기존 필드 변경 금지 (확장만 허용)
- git commit 하지 마세요

[REFERENCE_CONTEXT]
current_date: 2026-04-16
model_cutoff: unknown
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시
1. spec.md 전체 Read
2. `tools/figma-section-spec.py` 전체 Read (661줄 — ExtractionResult 구조, main() 흐름, 현재 출력 방식 파악)
3. `extracted/section_03_spec.json` Read (실제 입력 데이터 구조 파악 — frame_nodes/text_nodes/fills/style 필드)
4. `rules/common.md` Read (CSS 변환 규칙 확인)
5. `.gran-maestro/discussion/DSC-002/` 내 합의 문서 Read (preprocess_payload/hints)
6. TDD: tests/test_codegen.py 먼저 작성 (6+ 테스트) → 실패 확인 → 구현
7. [MANDATORY] TS-001~007 전부 실행하고 출력 포함

## 규칙
- `tools/figma-section-spec.py` + `tests/test_codegen.py` 주요 변경 파일
- git commit 금지
- 결정론성 필수 (동일 입력 → 바이트 동일 출력)
- [MANDATORY] TS-001~007 전부 실행 후 출력 포함

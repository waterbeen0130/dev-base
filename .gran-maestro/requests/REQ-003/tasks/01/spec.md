# REQ-003 T01: json-to-html.py 핵심 품질 개선 4건

## §0 Context Manifest

> Below are known entry points. This list may be incomplete — explore freely.

- `tools/json-to-html.py` — 수정 대상 (665행, SemanticConverter 클래스)
- `tools/figma-extract.py` — 정규화 JSON 구조 참조용 (수정 금지)
- `tools/validate-semantic.py` — 검증 도구 (수정 금지)
- `output/youngwol/` — 검증 대상 output
- `output/a_main/` — 회귀 검증 대상 output

## §1 요약

json-to-html.py의 4가지 핵심 품질 문제를 해결하여 DOD-005(시각적 동일성) 수준을 달성한다.

1. depth limiter에서 텍스트 포함 자식 노드 보존
2. Figma width → flex 비율 자동 변환
3. 범용 클래스명(el_N, txt_N) → 부모 컨텍스트 기반 의미 있는 이름
4. 이미지 이름 중복 시 부모 컨텍스트 반영

## §2 범위

### 수정 대상
- `tools/json-to-html.py` — SemanticConverter 클래스 내부 로직만 수정

### 제외
- `tools/figma-extract.py` 수정 금지
- 반응형 CSS, 시각적 검증 도구, MV 인터랙티브 요소
- 외부 패키지 추가 금지 (Python 표준 라이브러리만)

## §3 수락 조건

### AC-001 [automatable] [tdd-required] — depth limiter 텍스트 무손실
- **Given**: 정규화 JSON에 depth 5 이상의 중첩된 텍스트 노드가 존재할 때
- **When**: json-to-html.py로 변환하면
- **Then**: 모든 텍스트 노드가 HTML output에 보존된다. depth 5 이상에서 flatten되는 노드 중 자식에 텍스트가 있는 노드는 flatten하지 않는다.
- **Test**: 영월 output의 공지사항/리스트 등에서 텍스트가 누락되지 않음을 검증. validate-semantic.py max-dom-depth MAJOR 위반이 해소됨.

### AC-002 [automatable] [tdd-required] — flex 비율 자동 변환
- **Given**: 정규화 JSON의 visual 필드에 width 값이 있고, layout.sizing.horizontal이 "FILL" 또는 형제 노드와 비율 계산이 가능할 때
- **When**: json-to-html.py로 변환하면
- **Then**: CSS에 고정 width px 대신 flex 비율(%, flex:1, flex:0 0 N%)이 적용된다.
  - sizing.horizontal == "FILL" → `flex:1` 또는 `width:100%`
  - sizing.horizontal == "FIXED" + 형제 존재 → 형제 width 합 대비 % 비율
  - sizing.horizontal == "HUG" → width 미지정 (auto)
  - 이미지/아이콘 노드의 고정 width는 예외 허용
- **Test**: 영월 output common.css에서 이미지/아이콘 제외 고정 width px가 0건.

### AC-003 [automatable] — 범용 클래스명 개선
- **Given**: 피그마 노드 이름이 "el", "txt", "btn", "list" 등 범용 이름 + 숫자일 때
- **When**: json-to-html.py로 변환하면
- **Then**: 부모 노드 이름/역할을 접두사로 붙여 의미 있는 클래스명이 생성된다.
  - 예: 부모가 "notice" + 자식 "txt_1" → "notice_txt" (중복 시 _1 suffix)
  - 예: 부모가 "process" + 자식 "el_3" → "process_item" 또는 "process_el"
- **Test**: validate-semantic.py의 excessive-classes 경고에서 main_el_*, main_txt_* 계열이 50% 이상 감소.

### AC-004 [automatable] — 이미지 이름 중복 개선
- **Given**: 같은 이름의 노드가 여러 개 있어 이미지 파일명이 _1, _2 suffix로 생성될 때
- **When**: json-to-html.py에서 이미지 경로를 참조하면
- **Then**: 이미지의 alt 텍스트와 CSS 클래스명에 부모 컨텍스트가 반영된다.
  - 예: "graphic" 이미지가 "notice" 섹션과 "event" 섹션에 각각 → "notice_graphic", "event_graphic"
- **Test**: output img 디렉토리 내 같은 prefix의 이미지들이 부모 컨텍스트로 구분됨.

### AC-005 [automatable] — validate-semantic.py 전체 PASS 유지
- **Given**: 수정된 json-to-html.py로 영월 output을 재생성한 후
- **When**: validate-semantic.py로 검증하면
- **Then**: CRITICAL 0건, MAJOR 0건. MINOR는 기존 대비 감소 또는 동일.
- **Test**: `python3 tools/validate-semantic.py --html output/youngwol/index.html --css output/youngwol/common.css`

### AC-006 [impact-check] — 제천 output 회귀 없음
- **Given**: 수정된 json-to-html.py로 제천(a_main) output을 재생성한 후
- **When**: validate-semantic.py로 검증하면
- **Then**: 기존 대비 CRITICAL/MAJOR 증가 없음.
- **Test**: `python3 tools/validate-semantic.py --html output/a_main/index.html --css output/a_main/common.css`

## §3.2 Intent Trace

| AC | 의도 근거 |
|----|-----------|
| AC-001 | plan.md §결정사항 #1: depth limiter + 텍스트 누락 |
| AC-002 | plan.md §결정사항 #2: flex 비율 변환 |
| AC-003 | plan.md §결정사항 #3: 클래스명 개선 |
| AC-004 | plan.md §결정사항 #4: 이미지 이름 중복 |
| AC-005 | plan.md §제약사항: validate-semantic.py 34개 규칙 통과 유지 |
| AC-006 | plan.md §인수기준 PAC-6: 제천 output 회귀 없음 |

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-1 | MUST | AC-001 | COVERED |
| PAC-2 | MUST | AC-002 | COVERED |
| PAC-3 | SHOULD | AC-003 | COVERED |
| PAC-4 | SHOULD | AC-004 | COVERED |
| PAC-5 | MUST | AC-005 | COVERED |
| PAC-6 | SHOULD | AC-006 | COVERED |

## §3.4 Epic DoD Mapping

| DoD ID | DoD 설명 | Mapped Spec AC IDs | Coverage |
|--------|----------|-------------------|----------|
| DOD-005 | 시각적 동일성 — 수작업 불필요 수준 | AC-001, AC-002, AC-003, AC-004 | COVERED |
| DOD-006 | 자동 품질 검증 연동 | AC-005, AC-006 | COVERED |

## §3.5 Constraints

- Python 3.10+ 표준 라이브러리만 사용
- CSS 값은 정규화 JSON에서 100% 추출 (추측 금지)
- figma-extract.py 수정 금지
- 정규화 JSON의 `layout.sizing` 필드(`horizontal`/`vertical`: FIXED/FILL/HUG) 활용 가능

## §4 기술 맥락

### 현재 구조 분석

**depth limiter (L387-400)**:
```python
if depth >= 5 and children and not text and not img_path:
    # layout/visual 값이 없으면 flatten
    if not layout_has_value and not has_visual:
        for child in children:
            self._render(child, depth, parent_cls)  # ← 자식의 자식 텍스트가 누락됨
        return
```
문제: `not text`는 현재 노드만 체크. 자식 트리에 텍스트가 있어도 flatten됨.

**flex 비율 변환**:
현재 `_layout_to_css()`에서 `display:flex`, `flex-direction`, `gap`, `padding`만 추출.
정규화 JSON에 `visual.width`, `layout.sizing.horizontal` (FIXED/FILL/HUG) 값이 이미 존재하지만 활용하지 않음.

**클래스명 생성 (`_cls`, L108-124)**:
`_remap_name()`이 6개 고정 매핑(sec_1~6)만 처리.
부모 컨텍스트를 전혀 참조하지 않음 — `parent_cls` 파라미터가 `_render()`에 전달되지만 미사용.

**이미지 이름 (L358-381)**:
`image_map`이 node_id → path 매핑이므로 이미 유니크. 그러나 HTML의 alt/class에서 부모 컨텍스트 없이 노드 이름만 사용.

### 수정 접근법

1. **depth limiter**: flatten 전 자식 트리에 텍스트 노드 존재 여부를 재귀 검사하는 `_has_text_descendant()` 헬퍼 추가. 텍스트 자손이 있으면 flatten하지 않고 정상 렌더링.

2. **flex 비율**: `_render()` 컨테이너 노드 처리 부분에서 자식 노드들의 `visual.width` + `layout.sizing` 값을 읽어 CSS flex 속성 생성:
   - FILL → `flex:1`
   - HUG → width 미지정
   - FIXED + 형제 존재 → `flex:0 0 {비율}%` (형제 width 합산 대비)
   - FIXED + 단독 → `width:100%`

3. **클래스명**: `_cls()` 호출 시 `parent_cls`를 활용. 범용 패턴(el_N, txt_N, btn_N, list_N) 감지 시 부모 이름을 접두��로 치환.

4. **이미지 이름**: 이미지 노드 렌더링 시 가장 가까운 의미 있는 부모 이름을 cls에 반영.

## §5 선행 작업 (blockedBy)

없음

## §6 후행 작업 (blocks)

- T02 (통합 검증 태스크)

## §7 에이전트 배정

[config: codex-dev] → codex-dev (단일 파일 Python 로직 수정)

## §8 실행 지시

```
수정 대상: tools/json-to-html.py (SemanticConverter 클래스)

1. depth limiter 수정 (L387-400 부근):
   - _has_text_descendant(node) 재귀 헬퍼 추가
   - depth >= 5 조건에서 텍스트 자손이 있으면 flatten하지 않음

2. flex 비율 변환 로직 추가:
   - _render() 컨테이너 처리 시 자식 노드의 layout.sizing + visual.width 값 활용
   - FILL → flex:1, HUG → auto, FIXED+형제 → flex:0 0 N%
   - 이미지/아이콘/divider 노드는 고정 width 유지

3. _cls() 클래스명 개선:
   - parent_cls 파라미터 활용
   - 범용 패턴(el_N, txt_N, btn_N, list_N) 감지 시 부모 이름 접두사 치환
   - 추론 실패 시 기존 이름 유지 (안전 fallback)

4. 이미지 노드 클래스명/alt에 부모 컨텍스트 반영

5. 변환 완료 후 반드시 검증:
   python3 tools/validate-semantic.py --html output/youngwol/index.html --css output/youngwol/common.css
   python3 tools/validate-semantic.py --html output/a_main/index.html --css output/a_main/common.css
```

## Intent (JTBD)

- When I: json-to-html.py로 피그마 정규화 JSON을 HTML/CSS로 변환할 때
- I want to: depth 제한으로 인한 텍스트 누락, 고정px width, 의미 없는 클래스명 문제가 자동으로 해결되길 원한다
- So I can: 변환 결과물이 디자인 원본과 거의 동일하여 수작업 보정이 불필요한 수준이 된다

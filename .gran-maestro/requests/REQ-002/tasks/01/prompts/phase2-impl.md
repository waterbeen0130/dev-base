# 구현 요청: figma-extract.py 정규화 엔진 전면 재작성

## 핵심 지시

**반드시 아래 파일을 먼저 Read하세요:**
1. `.gran-maestro/agile/AGI-001/objective/details/normalization-engine.md` — 목표 JSON 스키마, 전체 변환 규칙 매핑표
2. `rules/rule_engine.json` — 프로젝트 타입 설정, CSS 규칙 정의
3. `tools/figma-extract.py` — 기존 코드 (전면 재작성 대상)

## 무엇을 만드는가

`tools/figma-extract.py`를 전면 재작성하여 Figma MCP JSON → 정규화된 중간 JSON을 출력하는 엔진을 만든다.

## 왜 만드는가

AI가 raw Figma JSON을 직접 해석할 때 편차가 너무 커서, 모든 시각적 속성을 규칙 기반으로 CSS 값까지 확정한 중간 포맷을 만들어 AI 해석 여지를 제거한다.

## 산출물 4개

### 1. `tools/figma-extract.py` (전면 재작성)

**입력**: stdin으로 Figma MCP JSON
**출력**: stdout으로 정규화된 중간 JSON (트리 구조)

**최상위 구조**:
```json
{
  "meta": { "source": "figma-mcp", "extracted_at": "...", "profile": "basic", "section_name": "...", "section_id": "...", "total_nodes": N },
  "tree": { "id": "...", "name": "...", "type": "FRAME", "layout": {...}, "visual": {...}, "text": {...}, "children": [...] }
}
```

**layout 객체** (FRAME/INSTANCE 노드):
```json
{
  "display": "flex",
  "direction": "column|row",
  "gap": "20px",
  "padding": "40px 30px",
  "justify": "center|flex-start|flex-end|space-between",
  "align": "center|flex-start|flex-end|baseline|stretch",
  "sizing": { "horizontal": "FILL|HUG|FIXED", "vertical": "FILL|HUG|FIXED" }
}
```

**visual 객체**:
```json
{
  "width": 1920,
  "height": 800,
  "background": "#ffffff",
  "border": "1px solid #ccc" | null,
  "borderRadius": "8px" | "50%" | "2em",
  "opacity": 1.0
}
```
- border는 strokes에 visible:true인 것이 있을 때만. 없으면 null.
- borderRadius: 999px → 50% (원형) 또는 2em (pill). 개별 모서리 다르면 4값 shorthand.

**text 객체** (TEXT 노드):
```json
{
  "content": "Hello World",
  "tag_hint": "span|h2|p",
  "has_newline": false,
  "char_length": 11,
  "segments": [
    {
      "text": "Hello ",
      "style": {
        "fontFamily": "Pretendard",
        "fontWeight": 700,
        "fontSize": "1rem",
        "lineHeight": 1.5,
        "letterSpacing": "-0.025em",
        "color": "#090944"
      },
      "is_override": false
    }
  ]
}
```
- tag_hint 규칙: 기본 span, \n 포함 또는 95자 초과 또는 문장형 종결 → p, 섹션 제목 → h2/h3
- fontSize: --profile basic이면 rem (16px 기준), --profile landing이면 px
- lineHeight: 무단위 비율 (lineHeightPx / fontSize)
- letterSpacing: em 단위 (letterSpacing / fontSize)

**characterStyleOverrides 누적 병합**:
- baseStyle = { ...node.style, fills: node.fills }
- 연속 같은 overrideId 문자를 그룹화 → 세그먼트
- id=0 또는 테이블에 없음 → resolved = baseStyle
- 그 외 → resolved = { ...(prev_resolved || baseStyle), ...override }
- 각 세그먼트의 CSS 값을 완전 해석하여 저장

**노드 보존 규칙**:
- visible:false만 제외 (유일한 제외 조건)
- fill-only 얇은 프레임(w≤2 or h≤2) → divider로 보존
- 장식용 노드 → 모두 보존

### 2. `tools/profiles/basic.json`
```json
{
  "font_size_pc": "rem",
  "font_size_mobile": "px",
  "rem_base": 16,
  "reset_css": "separate_file",
  "required_root_vars": ["--width", "--padding"],
  "mobile_spacing": "half_of_pc",
  "mobile_breakpoint": 768
}
```

### 3. `tools/profiles/landing.json`
```json
{
  "font_size_pc": "px",
  "font_size_mobile": "px",
  "reset_css": "inline_top_of_css",
  "required_root_vars": ["--padding", "--header_h", "--width", "--point-color-1"],
  "mobile_spacing": "explicit_px",
  "animation": { "attrs": ["data-delay", "data-direction"], "motion_class": "section_on" }
}
```

### 4. `docs/conversion-rules.md`
Figma 속성 → CSS 변환 규칙 전체 매핑표 (레이아웃/시각/타이포/오버라이드/프로필 카테고리별)

## CLI 인터페이스

```bash
# 주 워크플로우 (MCP stdin)
echo '<json>' | python3 tools/figma-extract.py --stdin --profile basic

# 노드 트리 시각화 (기존 호환)
echo '<json>' | python3 tools/figma-extract.py --stdin --tree

# 프로필 지정
python3 tools/figma-extract.py --stdin --profile landing
```

## 기존 함수 호환 (CRITICAL)

tests/test_smoke.py가 아래 함수를 import합니다. 동일 시그니처를 유지하거나 호환 래퍼를 제공하세요:
- `rgba_to_hex(r, g, b, a=1.0)` → hex string
- `extract_fill_color(fills)` → hex string or None
- `line_height_to_ratio(line_height_px, font_size)` → float ratio
- `figma_align_to_css(value, axis='primary')` → CSS string

## 검증 명령
```bash
# 기존 smoke test 호환
pytest tests/test_smoke.py -v

# 신규 테스트 (T02에서 추가하지만 기본 구조는 여기서도 통과해야 함)
echo '{"type":"FRAME","name":"test","visible":true,"children":[]}' | python3 tools/figma-extract.py --stdin --profile basic | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'meta' in d and 'tree' in d; print('OK')"
```

## 테스트를 먼저 작성한 후 구현하세요 (TDD)

`tests/test_normalization.py`를 먼저 작성하고, 그 테스트가 통과하도록 `figma-extract.py`를 구현하세요.

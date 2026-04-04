# Figma→코드 변환 품질 전문가 의견 (codex-2)

> 작성일: 2026-02-18
> 기반 프롬프트: codex-2-prompt.md
> 분석자: Figma→HTML/CSS 변환 자동화 품질 전문가 (Claude Sonnet 4.6)

---

## 1. Auto Layout 제약 처리 (constraints → CSS)

**제안 규칙**: Figma `constraints.horizontal` / `constraints.vertical` 값을 부모 layoutMode에 따라 CSS로 변환한다.

- `FILL` → `flex: 1 1 0` (부모가 flex일 때) 또는 `width: 100%`
- `FIXED` → `width: {node.width}px` / `height: {node.height}px` 고정
- `SCALE` → `width: {(node.width / parent.width * 100).toFixed(2)}%` (비율 계산)
- `CENTER` (horizontal) → `margin-left: auto; margin-right: auto`
- `MIN` / `MAX` → `align-self: flex-start` / `align-self: flex-end`

**변환 예시**:
```
Figma: constraints { horizontal: "FILL", vertical: "FIXED" }, height: 48
CSS:   flex: 1 1 0; height: 48px;
```

**rule_engine.json 초안**:
```json
"constraints": {
  "horizontal": {
    "FILL": "flex: 1 1 0",
    "FIXED": "width: {node.width}px",
    "SCALE": "width: {(node.width/parent.width*100).toFixed(2)}%",
    "CENTER": "margin-left: auto; margin-right: auto",
    "MIN": "align-self: flex-start",
    "MAX": "align-self: flex-end"
  },
  "vertical": {
    "FILL": "flex: 1 1 0",
    "FIXED": "height: {node.height}px",
    "SCALE": "height: {(node.height/parent.height*100).toFixed(2)}%",
    "CENTER": "margin-top: auto; margin-bottom: auto"
  },
  "forbid_omit": true
}
```

---

## 2. SVG/벡터 노드 처리

**제안 규칙**: 벡터 노드 유형별로 추출 방식을 결정한다.

- `VECTOR`, `BOOLEAN_OPERATION`, `STAR`, `POLYGON` → 항상 인라인 `<svg>` 또는 `<img src=".svg">` (복잡도 임계값: path 개수 > 10이면 외부 파일)
- `ELLIPSE` (fills만 있고 단순 원형) → `<div>` + `border-radius: 50%` + `background-color`로 CSS 처리
- `RECTANGLE` (cornerRadius 있음) → `<div>` + `border-radius` CSS
- 아이콘 성격(16~48px 정사각형 벡터) → `<img>` + `alt="아이콘명"` (간결 alt)
- 장식용 대형 벡터 → 인라인 `<svg>` + `aria-hidden="true"`

**변환 예시**:
```
Figma: ELLIPSE, width:40, height:40, fills:[{color:#FF0000}]
HTML:  <div class="page_circle_icon" aria-hidden="true"></div>
CSS:   .page_circle_icon{width:40px;height:40px;border-radius:50%;background:#ff0000;}
```

**rule_engine.json 초안**:
```json
"vector_nodes": {
  "ELLIPSE_simple": "div + border-radius:50%",
  "RECTANGLE_with_radius": "div + border-radius:{cornerRadius}px",
  "VECTOR_small_icon": "img[alt='{name}']",
  "VECTOR_large_decorative": "svg[aria-hidden=true]",
  "path_count_threshold": 10,
  "complex_vector": "external_svg_file",
  "forbid_canvas_render": true
}
```

---

## 3. 컴포넌트/인스턴스 반복 구조 추출

**제안 규칙**: 동일 `componentId`를 가진 인스턴스가 2개 이상이면 반복 리스트 구조로 추출한다.

- 동일 componentId 인스턴스 N개 → `<ul class="{page}_{role}_list">` + `<li class="{page}_{role}_item">` × N
- 인스턴스 내부 구조는 첫 번째 인스턴스를 기준 템플릿으로 확정, 이후 인스턴스는 텍스트/이미지 값만 치환
- 인스턴스가 1개이거나 componentId 없는 프레임 → 일반 `<div>` 처리
- 컴포넌트 내부 오버라이드(`overrides` 배열) 값은 각 li 항목에 개별 반영

**변환 예시**:
```
Figma: 3x INSTANCE (componentId: "card_001")
HTML:  <ul class="page_card_list">
         <li class="page_card_item">...</li>
         <li class="page_card_item">...</li>
         <li class="page_card_item">...</li>
       </ul>
```

**rule_engine.json 초안**:
```json
"component_instance": {
  "repeat_threshold": 2,
  "repeat_output": "ul > li",
  "template_source": "first_instance",
  "override_apply": "per_item",
  "single_instance_output": "div",
  "forbid_hardcode_duplicate": true
}
```

---

## 4. 이펙트 스타일 매핑 (effects → CSS)

**제안 규칙**: Figma `effects` 배열을 유형별로 CSS 속성으로 1:1 변환한다.

- `DROP_SHADOW` → `box-shadow: {offsetX}px {offsetY}px {radius}px {spread}px rgba({r},{g},{b},{a})`
- `INNER_SHADOW` → `box-shadow: inset {offsetX}px {offsetY}px {radius}px {spread}px rgba(...)`
- `LAYER_BLUR` → `filter: blur({radius}px)`
- `BACKGROUND_BLUR` → `backdrop-filter: blur({radius}px)`
- 복수 이펙트 → 쉼표 연결 `box-shadow: val1, val2`
- `visible: false`인 effect → 무시 (현행 visibility_rule 준용)
- color.a는 CSS rgba 알파값으로 직접 사용 (hex 변환 금지)

**변환 예시**:
```
Figma: effects[{type:"DROP_SHADOW", color:{r:0,g:0,b:0,a:0.15}, offset:{x:0,y:4}, radius:12}]
CSS:   box-shadow: 0px 4px 12px 0px rgba(0,0,0,0.15);
```

**rule_engine.json 초안**:
```json
"effects": {
  "DROP_SHADOW": "box-shadow: {x}px {y}px {radius}px {spread}px rgba({r},{g},{b},{a})",
  "INNER_SHADOW": "box-shadow: inset {x}px {y}px {radius}px {spread}px rgba({r},{g},{b},{a})",
  "LAYER_BLUR": "filter: blur({radius}px)",
  "BACKGROUND_BLUR": "backdrop-filter: blur({radius}px)",
  "multi_effect_separator": ",",
  "skip_invisible": true,
  "forbid_hex_for_shadow_color": true
}
```

---

## 5. 색상 스타일 변수화 (Figma 스타일 → CSS 변수)

**제안 규칙**: Figma 문서 레벨 색상 스타일(`styles` 맵)을 `:root` CSS 변수로 자동 변환한다.

- 스타일 이름 패턴 `Primary/500` → `--point-color-1`(기존 명명 규칙에 따라 순번 부여)
- `Text/Dark`, `Text/Gray` 등 텍스트 색상 → `--font-color-N`
- 중립/배경 계열 → `--bg-color-N`
- 동일 hex 값이 이미 변수로 등록된 경우 재등록 금지 (중복 방지)
- 변수 미지정 노드의 fills hex → 직접 hex 사용 (기존 `color_format: hex_only` 준수)
- 이름 기반 의미 변수 금지 (`--landing-primary` 등) → 순번 방식만 허용

**변환 예시**:
```
Figma style: "Primary/500" = #3B5BDB
CSS: :root { --point-color-1: #3b5bdb; }
```

**rule_engine.json 초안**:
```json
"color_variables": {
  "source": "document.styles",
  "prefix_map": {
    "Primary": "--point-color",
    "Text": "--font-color",
    "Background": "--bg-color"
  },
  "numbering": "sequential_per_prefix",
  "forbid_semantic_name": true,
  "forbid_duplicate_hex": true,
  "fallback_no_style": "hex_direct"
}
```

---

## 6. 그라디언트 처리 (Figma gradient → CSS)

**제안 규칙**: Figma `fills` 중 `gradientType`이 있는 경우 CSS gradient로 변환한다.

- `LINEAR_GRADIENT` → `linear-gradient({angle}deg, {stop1_color} {stop1_pos}%, ...)` — `gradientHandlePositions`로 각도 계산
- `RADIAL_GRADIENT` → `radial-gradient(circle at {cx}% {cy}%, {stops...})`
- `ANGULAR_GRADIENT` → `conic-gradient(from {angle}deg, {stops...})`
- `DIAMOND_GRADIENT` → CSS 직접 표현 불가 시 nearest radial-gradient로 근사 후 주석 `/* diamond approximation */`
- stop color는 hex + rgba 병용 허용 (알파값 있을 때 rgba)
- 배경이 gradient인 경우 `background: {gradient}` (background-color 금지)

**변환 예시**:
```
Figma: LINEAR_GRADIENT, handles[(0,0.5),(1,0.5)], stops[#fff@0, #000@1]
CSS:   background: linear-gradient(90deg, #ffffff 0%, #000000 100%);
```

**rule_engine.json 초안**:
```json
"gradient": {
  "LINEAR_GRADIENT": "linear-gradient({angle}deg, {stops})",
  "RADIAL_GRADIENT": "radial-gradient(circle at {cx}% {cy}%, {stops})",
  "ANGULAR_GRADIENT": "conic-gradient(from {angle}deg, {stops})",
  "DIAMOND_GRADIENT": "radial-gradient(nearest approximation) /* diamond approximation */",
  "stop_color_format": "hex_or_rgba",
  "forbid_background_color_for_gradient": true,
  "angle_calculation": "from_gradientHandlePositions"
}
```

---

## 7. Stroke 두께 및 위치 처리 (stroke-align → CSS border)

**제안 규칙**: Figma stroke의 `strokeAlign`에 따라 CSS border 구현 방식을 결정한다.

- `CENTER` → `border: {strokeWeight}px solid {color}` (표준 CSS border, 기본)
- `INSIDE` → `box-shadow: inset 0 0 0 {strokeWeight}px {color}` (border-box 계산 왜곡 방지)
- `OUTSIDE` → `box-shadow: 0 0 0 {strokeWeight}px {color}` (outline 대신 shadow 사용)
- `strokes.visible !== true` 이면 border/shadow 모두 생성 금지 (기존 `border_from_stroke_only` 준수)
- 복수 stroke → 쉼표 연결 box-shadow (단, CENTER는 border만 사용하고 추가분을 shadow로 보충)
- stroke color의 opacity < 1 → `rgba()` 사용 (hex 금지)

**변환 예시**:
```
Figma: strokes[{color:#000, opacity:1, weight:2, align:"INSIDE", visible:true}]
CSS:   box-shadow: inset 0 0 0 2px #000000;
```

**rule_engine.json 초안**:
```json
"stroke_align": {
  "CENTER": "border: {weight}px solid {color}",
  "INSIDE": "box-shadow: inset 0 0 0 {weight}px {color}",
  "OUTSIDE": "box-shadow: 0 0 0 {weight}px {color}",
  "skip_if_not_visible": true,
  "forbid_outline_property": true,
  "multi_stroke": "comma_separated_shadow",
  "opacity_lt_1": "rgba_required"
}
```

---

## 종합 우선순위 권고

| 항목 | 변환 정확도 기여 | 구현 복잡도 | 도입 우선순위 |
|---|---|---|---|
| 4. 이펙트 매핑 | 높음 | 낮음 | 1순위 |
| 7. stroke-align | 높음 | 낮음 | 1순위 |
| 6. 그라디언트 | 높음 | 중간 | 2순위 |
| 1. constraints | 중간 | 중간 | 2순위 |
| 5. 색상 변수화 | 중간 | 낮음 | 2순위 |
| 3. 컴포넌트 반복 | 높음 | 높음 | 3순위 |
| 2. SVG/벡터 | 중간 | 높음 | 3순위 |

이펙트·stroke 규칙은 기존 `border_stroke` 섹션과 직접 연동되며 즉시 적용 가능합니다. 그라디언트와 constraints는 기존 `layout` / `css` 섹션에 독립 블록으로 추가하면 충돌 없이 통합됩니다.

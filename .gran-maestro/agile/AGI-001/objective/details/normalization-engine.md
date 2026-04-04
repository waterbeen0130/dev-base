# 정규화 엔진

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-001, DOD-002, DOD-003

## 개요

Figma MCP JSON 응답을 AI 해석 개입 없이 규칙 기반으로 정규화된 중간 JSON 포맷으로 변환하는 엔진. 기존 `figma-extract.py`(34.2KB, 916행)를 전면 재설계하여 더 단순하고 명확한 구조로 개선한다.

## 설계 결정

### AD-001: 중간 포맷은 JSON
- **결정**: 정규화 출력을 JSON으로 확정
- **근거**: 기존 매핑 파일이 JSON이며, AI가 파싱하기에 가장 자연스러운 포맷. 마크다운 테이블 출력은 사람이 읽기엔 좋지만 AI가 구조적으로 파싱하기엔 한계가 있음
- **대안 검토**: YAML(가독성 좋으나 파싱 라이브러리 추가 필요), 마크다운 테이블(기존 출력이지만 구조화 한계)
- **영향 범위**: figma-extract.py 출력 형식, 2차 시멘틱 변환 레이어의 입력 형식, validate.js 매핑 연동

### AD-002: figma-extract.py 전면 재작성 허용
- **결정**: 기존 코드 보존보다 더 나은 구조로의 개선에 비중. 복잡한 병합 로직 포함 전면 재작성 가능
- **근거**: 사용자 명시 — "기존 병합 규칙이 복잡하다면 모두 수정해도 상관없어, 더 나은 방향으로 개선함에 더 비중을 크게 둬"
- **대안 검토**: 기존 코드 리팩터링만(하위 호환 유지) — 기각: 구조적 한계로 인해 부분 수정으로는 목표 달성 어려움
- **영향 범위**: 기존 figma-extract.py의 하위 호환성 유지 불필요, CLI 인터페이스는 재설계 가능

### AD-003: 프로젝트 타입 프로필 분리
- **결정**: basic/landing 타입별 차이를 프로필 설정 파일로 분리
- **근거**: 현재 `rule_engine.json`에 타입별 규칙이 이미 정의되어 있으나, 정규화 엔진 코드 내에서 분기가 산재함. 프로필로 분리하면 새 프로젝트 타입 추가도 용이
- **대안 검토**: 코드 내 if/else 분기 유지 — 기각: 타입 증가 시 복잡도 급증
- **영향 범위**: font-size 변환(rem vs px), spacing 정책, reset CSS 처리, 필수 root 변수

## 상세 명세

### 1. 현재 figma-extract.py 구조 분석

현재 파일은 916행, 크게 7개 영역으로 구성:

```
1. 색상 변환 (40-83행)
   - rgba_to_hex(): Figma RGBA(0-1 float) → hex/#rrggbb 또는 rgba()
   - extract_fill_color(): 첫 번째 visible SOLID fill 색상 추출
   - extract_stroke_info(): stroke 색상/두께/정렬 추출

2. CSS 값 변환 (87-124행)
   - line_height_to_ratio(): lineHeightPx → 무단위 비율
   - letter_spacing_to_em(): letterSpacing(px) → em 단위
   - figma_align_to_css(): Figma 정렬값 → CSS flex 정렬

3. 노드 속성 추출 (128-410행)
   - extract_layout_props(): layoutMode/itemSpacing/padding/alignment/sizing
   - extract_visual_props(): fills/strokes/cornerRadius/width/height
   - resolve_style_segments(): characterStyleOverrides 누적 병합 (가장 복잡)
   - extract_font_props(): TEXT 노드의 폰트/색상/텍스트 속성
   - extract_node(): 재귀적 노드 트리 순회

4. 출력 포맷터 (447-597행)
   - to_markdown_layout_table(): 레이아웃 속성 마크다운 테이블
   - to_markdown_visual_table(): 시각 속성 마크다운 테이블
   - to_markdown_font_table(): 폰트 속성 마크다운 테이블
   - to_markdown(): 전체 마크다운 결합
   - to_json_mapping(): validate.js용 JSON 매핑 생성

5. 노드 검색 (601-635행)
   - find_node_by_id(), find_node_by_name(), get_top_frames()

6. Figma API 직접 호출 (638-677행)
   - fetch_figma_node(): REST API 직접 호출 (FIGMA_TOKEN 필요)

7. MCP 응답 파싱 + CLI (680-915행)
   - parse_mcp_response(): 다양한 MCP 응답 구조 대응
   - --tree 모드: 노드 트리 시각화
   - main(): CLI 진입점
```

### 2. 정규화된 중간 JSON 포맷 스키마 (목표)

정규화 엔진이 출력할 중간 JSON의 목표 구조:

```json
{
  "meta": {
    "source": "figma-mcp",
    "extracted_at": "2026-04-04T...",
    "profile": "basic",
    "section_name": "hero_section",
    "section_id": "2252:13736",
    "total_nodes": 42
  },
  "tree": {
    "id": "2252:13736",
    "name": "hero_section",
    "type": "FRAME",
    "layout": {
      "display": "flex",
      "direction": "column",
      "gap": "20px",
      "padding": "40px 30px",
      "justify": "center",
      "align": "center",
      "sizing": { "horizontal": "FILL", "vertical": "HUG" }
    },
    "visual": {
      "width": 1920,
      "height": 800,
      "background": "#ffffff",
      "border": null,
      "borderRadius": "0"
    },
    "children": [
      {
        "id": "...",
        "name": "title",
        "type": "TEXT",
        "text": {
          "content": "Hello World",
          "tag_hint": "h2",
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
            },
            {
              "text": "World",
              "style": {
                "fontFamily": "Pretendard",
                "fontWeight": 400,
                "fontSize": "0.875rem",
                "lineHeight": 1.5,
                "letterSpacing": "-0.025em",
                "color": "#ff0000"
              },
              "is_override": true
            }
          ],
          "has_newline": false,
          "char_length": 11
        },
        "layout": null,
        "visual": { ... },
        "children": []
      }
    ]
  }
}
```

핵심 설계 원칙:
- **트리 구조 보존**: Figma의 부모-자식 관계를 그대로 유지 (flat 배열이 아닌 중첩 트리)
- **CSS 값 확정**: 모든 값이 이미 CSS로 변환된 상태 (AI가 추가 변환 불필요)
- **프로필 적용 완료**: basic이면 rem, landing이면 px — 이미 반영된 값
- **tag_hint 포함**: 텍스트 노드에 대한 태그 힌트 (h2/span/p 등) — 최종 결정은 2차 시멘틱 변환에서

### 3. Figma 속성 → CSS 변환 규칙 전체 매핑

#### 3.1 레이아웃 속성

| Figma 속성 | CSS 속성 | 변환 규칙 |
|-----------|---------|----------|
| `layoutMode: "VERTICAL"` | `flex-direction: column` | VERTICAL → column |
| `layoutMode: "HORIZONTAL"` | `flex-direction: row` | HORIZONTAL → row (기본값) |
| `layoutMode: null` | `display: block` 또는 없음 | 레이아웃 모드 없으면 flex 미적용 |
| `itemSpacing: N` | `gap: Npx` | N > 1이면 px, N ≤ 1이면 0 |
| `paddingTop/Right/Bottom/Left` | `padding: shorthand` | 4값 동일 → 1값, 상하/좌우 동일 → 2값, 나머지 → 4값 |
| `primaryAxisAlignItems: "MIN"` | `justify-content: flex-start` | |
| `primaryAxisAlignItems: "CENTER"` | `justify-content: center` | |
| `primaryAxisAlignItems: "MAX"` | `justify-content: flex-end` | |
| `primaryAxisAlignItems: "SPACE_BETWEEN"` | `justify-content: space-between` | |
| `counterAxisAlignItems: "MIN"` | `align-items: flex-start` | |
| `counterAxisAlignItems: "CENTER"` | `align-items: center` | |
| `counterAxisAlignItems: "MAX"` | `align-items: flex-end` | |
| `counterAxisAlignItems: "BASELINE"` | `align-items: baseline` | |
| `counterAxisAlignItems: "STRETCH"` | `align-items: stretch` | |
| `layoutSizingHorizontal: "FILL"` | `width: 100%` 또는 `flex: 1` | 컨텍스트에 따라 |
| `layoutSizingHorizontal: "HUG"` | 너비 미지정 (content 기반) | |
| `layoutSizingHorizontal: "FIXED"` | `width: Npx` (단, flex 비율 변환 우선) | |
| `layoutSizingVertical: "FILL"` | `height: 100%` 또는 `flex: 1` | |
| `layoutSizingVertical: "HUG"` | 높이 미지정 | |
| `layoutAlign: "STRETCH"` | `align-self: stretch` 또는 `width: 100%` | 자식 요소의 stretch |

#### 3.2 시각 속성

| Figma 속성 | CSS 속성 | 변환 규칙 |
|-----------|---------|----------|
| `fills[].type: "SOLID"` | `background-color: #hex` | RGBA(0-1) → hex. opacity < 1이면 rgba() |
| `fills[].visible: false` | 무시 | visible false인 fill은 skip |
| `strokes[].type: "SOLID"` | `border: Wpx solid #hex` | visible true인 stroke만. **stroke 없으면 border 금지** |
| `strokeWeight` | border 두께 | |
| `strokeAlign: "INSIDE"` | `box-sizing: border-box` 고려 | |
| `cornerRadius: N` | `border-radius: Npx` | 단일 값 |
| `rectangleCornerRadii: [TL,TR,BR,BL]` | `border-radius: TLpx TRpx BRpx BLpx` | 개별 모서리 |
| 원형 판정 (width≈height, radius≈width/2) | `border-radius: 50%` | 999px 금지 |
| pill 판정 (radius > height/2) | `border-radius: 2em` | |
| `absoluteBoundingBox.width/height` | 참조용 (고정 px 출력 아님) | flex 비율 변환의 입력값 |
| `opacity: N` (N < 1) | `opacity: N` | |

#### 3.3 타이포그래피 속성

| Figma 속성 | CSS 속성 | 변환 규칙 (basic) | 변환 규칙 (landing) |
|-----------|---------|-----------------|-------------------|
| `style.fontSize: N` | `font-size` | PC: `N/base rem`, 모바일: `Npx` | PC/모바일 모두: `Npx` |
| `style.fontWeight: N` | `font-weight: N` | 직접 복사 | 직접 복사 |
| `style.fontFamily: "X"` | `font-family: X` | 부모 상속 우선 | 부모 상속 우선 |
| `style.lineHeightPx: N` | `line-height: ratio` | N / fontSize → 무단위 비율 (1.3, 1.5 등) | 동일 |
| `style.letterSpacing: N` | `letter-spacing: Nem` | N / fontSize → em 변환 | 동일 |
| `style.textAlignHorizontal` | `text-align` | LEFT→left, CENTER→center, RIGHT→right, JUSTIFIED→justify | 동일 |
| `fills[0].color` (TEXT 노드) | `color: #hex` | RGBA → hex | 동일 |
| `style.textDecoration` | `text-decoration` | UNDERLINE→underline, STRIKETHROUGH→line-through | 동일 |

#### 3.4 텍스트 오버라이드 (characterStyleOverrides) 변환 규칙

현재 누적 병합 로직 (`resolve_style_segments`, 223-322행):

```
입력:
  - node.characters: "Hello World"
  - node.characterStyleOverrides: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
  - node.styleOverrideTable: { "1": { "fontWeight": 400, "fills": [...] } }
  - node.style: { fontSize: 16, fontWeight: 700, fontFamily: "Pretendard" }

처리:
  1. baseStyle = { ...node.style, fills: node.fills }
  2. 연속된 같은 overrideId를 가진 문자를 그룹화 → 세그먼트
     - 세그먼트 1: id=0, "Hello " 
     - 세그먼트 2: id=1, "World"
  3. 누적 병합:
     - id=0 또는 테이블에 없음 → resolved = baseStyle
     - id=1 → source = (이전 resolved || baseStyle), resolved = { ...source, ...override }
  4. 스타일 차이 감지: fontSize/fontWeight/fontFamily/color가 base와 다르면 is_override=true

출력:
  - segments[]: { text, style(완전 해석됨), is_override }
```

**재설계 방향**:
- 누적 병합 로직 자체는 Figma의 의도를 정확히 반영하므로 로직은 유지
- 코드 구조를 더 명확하게 분리: 세그먼트 분할 → 스타일 해석 → CSS 변환을 독립 함수로
- 각 세그먼트의 최종 CSS 값을 중간 JSON에 포함하여 2차 변환에서 재계산 불필요

#### 3.5 노드 보존 규칙

| 조건 | 처리 |
|------|------|
| `visible: false` | 제외 (유일한 제외 조건) |
| fill-only 얇은 프레임 (w≤2 or h≤2) | **보존** — divider 노드로 처리 |
| 장식용 노드 (배경, 아이콘, 구분선) | **보존** — DOM 요소로 매핑 |
| stroke 없는 fill 노드 | **보존** |
| children 없는 빈 FRAME | 보존 여부 판단 (fill 있으면 보존) |

#### 3.6 특수 변환 규칙

| 상황 | 변환 |
|------|------|
| `\n` in node.characters | `<br>` 태그 삽입 또는 블록 분리 |
| 반복 아이템 2개 이상 (같은 구조) | `<ul><li>` 구조 힌트 |
| 이미지 노드 | `<div class="img_area">` 래핑 힌트 |
| width 고정값 > 비율 변환 | flex 비율(%) 또는 flex: 1 사용 (고정 px 지양) |
| padding/margin < 100px | 고정 px |
| padding/margin ≥ 100px | clamp() 허용 |

### 4. 프로젝트 타입 프로필 구조

현재 `rule_engine.json`의 `project_type` 섹션 기반:

```json
{
  "basic": {
    "font_size_pc": "rem",
    "font_size_mobile": "px",
    "rem_base": "clamp(14px, 1.2vw, 16px)",
    "reset_css": "separate_file",
    "required_root_vars": ["--width", "--padding"],
    "mobile_spacing": "half_of_pc",
    "mobile_breakpoint": 768
  },
  "landing": {
    "font_size_pc": "px",
    "font_size_mobile": "px",
    "reset_css": "inline_top_of_css",
    "required_root_vars": ["--padding", "--header_h", "--width", "--point-color-1"],
    "mobile_spacing": "explicit_px",
    "animation": {
      "attrs": ["data-delay", "data-direction"],
      "motion_class": "section_on"
    }
  }
}
```

정규화 엔진은 프로필을 읽어서 font-size 변환 등에 자동 적용.

### 5. CLI 인터페이스 (재설계)

기존 인터페이스:
```bash
# MCP stdin
echo '<json>' | python3 figma-extract.py --stdin --name "section" --output ./
# API 직접
python3 figma-extract.py --node-id 5135-6427 --file-key xxx --tree
# 로컬 파일
python3 figma-extract.py --figma data.json --frame "2252:13736"
```

재설계 시 유지할 인터페이스:
- `--stdin` (MCP 파이프) — 주 워크플로우
- `--node-id` + `--file-key` (API 직접) — 보조
- `--tree` (노드 트리 시각화) — 디버깅용
- `--profile basic|landing` (프로필 지정) — **신규**
- `--output` (출력 경로)
- `--json-only` / `--md-only` (출력 포맷 선택)

## Q&A 보강 사항

- 사용자는 "AI 해석 편차"가 핵심 문제라고 명확히 밝힘 → 정규화 엔진의 핵심 목표는 AI에게 넘기는 데이터의 해석 여지를 최소화하는 것
- 기존 코드의 복잡한 병합 로직 전면 재작성 허용됨 → 하위 호환성 걱정 없이 최적 구조 추구 가능
- MCP 방식 유지 확정 → stdin 파이프가 주 입력 경로

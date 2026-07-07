# Gemini 규칙

Gemini CLI 기반 AI 전용 규칙입니다. Gran Maestro 워크플로우에서 대용량/복잡 레이아웃 태스크에 사용됩니다.

---

## 기본
- `common.md` 규칙 우선 적용 — **반드시 먼저 읽을 것**
- 코드 주석: 영어만
- 응답 언어: 한국어

---

## 역할
- **퍼블리싱 프로젝트**: 주 에이전트 (HTML/CSS/JS 전체 담당)
- **풀스택 프로젝트**: 프론트엔드 담당
- capabilities: frontend, docs, large-context

---

## Figma MCP 데이터 해석 규칙 (CRITICAL — 반드시 준수)

> **Figma MCP 응답을 섹션 단위로 받아 직접 해석하여 CSS 값을 결정한다.**

- Figma MCP(`get_figma_data`)로 섹션별 노드 데이터를 조회하여 CSS 값 결정
- 전체 페이지를 한번에 처리하지 않고 **섹션(노드) 단위로 호출**
- Figma 속성 → CSS 변환 규칙:
  - `layoutMode` → flex 필요 여부 먼저 판단 (세로+간격 제각각이면 block, 가로면 flex)
  - `itemSpacing` → 간격 동일하면 gap, 다르면 개별 margin
  - `padding*` → `padding` (shorthand)
  - `fills` → `background`/`color` (hex 변환, 투명도 시만 rgba)
  - `fills` type이 `IMAGE`인 프레임 → `<img>` (래퍼 없음). **프레임 bbox.w/bbox.h는 img가 아닌 부모 컨테이너에 적용** (예: `.main_card{width:300px;}`) — img에 width/height 직접 선언 금지
  - `lineHeightPx` → `line-height` (무단위 비율로 변환)
  - `letterSpacing` → `letter-spacing` (em 단위로 변환)
  - `cornerRadius` → `border-radius`
  - `strokes` → `border`
- **"그럴듯한" 값, "합리적인" 기본값을 임의로 넣는 것 절대 금지** — MCP 응답에 없는 속성은 사용하지 않음

### 텍스트 스타일 오버라이드
- `characterStyleOverrides`가 있는 TEXT 노드는 오버라이드 구간을 `<span>`으로 분리
- 각 구간의 font-size, font-weight, color 값이 다르면 별도 클래스를 부여

---

## HTML 규칙

- `<body>` 태그에 class 속성 추가 금지 — body는 공통 영역이므로 페이지별 class 사용하지 않음
- `<div>` + 클래스 기반 구조 우선. `<section>`은 주요 콘텐츠 섹션에만 사용
- `<main>`, `<article>`, `<figure>`, `<figcaption>` **사용 금지** — `<div>` + `<span>` 사용
- 모든 이미지에 `alt` 속성 필수 — **짧고 간결하게** (예: `alt="로고"`, 긴 한국어 문장 금지)
- 이미지는 래퍼 없이 `<img>` 그대로 배치 (`.img_area` 등 래퍼 금지). **img 에 고정 width/height 금지** — Figma bbox 크기가 필요하면 img의 **부모 컨테이너**에서 제어 (예: `.main_card{width:300px;}` O / `.main_card img{width:300px;}` X)
- `aria-label`은 **텍스트가 없는 인터랙티브 요소에만** 사용
- 줄바꿈: `<br>` 태그 사용, 반응형은 `<br class="mb_only">` / `<br class="pc_only">`
- 빈 `<div>` 금지
- 섹션 내부 래퍼는 `.cont` 클래스, 최대 1개
- DOM 최대 깊이: **5단계**

### 섹션 폭 공식 (CRITICAL — 프로젝트 전체 불변, section_width_formula 룰로 강제)

```css
:root{
  --width: <figma_content_width + 40>px;   /* 프로젝트별 계산 */
  --padding: 20px;                          /* 불변 고정 */
}

.cont{width:100%; max-width:var(--width); margin:0 auto; padding:0 var(--padding);}

/* 배경이 있는 섹션은 full-bleed. max-width 직접 선언 금지. */
.main_xxx{padding:<tb>px 0; background:#...;}
.main_xxx .cont{/* 내부 레이아웃 */}
```

**계산 근거 (box-sizing:border-box 기준)**:
- `.cont` 실제 content = `var(--width) - 2*var(--padding)` = Figma content width
- 예: Figma content 1440 → `--width: 1480px`, `--padding: 20px`, content area = 1440 ✓

**Figma content width 추출**: `extracted/{section}_spec.json` 최상위 `inner` 프레임의 `bbox.w - paddingLeft - paddingRight`.

**금지 사항**:
- 섹션(`.main_*`, `.footer_top`, `.footer_bottom`)에 `max-width` 직접 선언 금지 (background 잘림)
- 섹션에 Figma inner padding(240 등) 직접 이식 금지 — `.cont`의 padding 20으로 통일
- `--padding`을 20px 이외 값으로 바꾸기 금지
- `--max-width` 별도 변수 생성 금지 — `--width` 하나만 사용

### 텍스트 태그 판정
- 기본 태그는 `<span>` 또는 헤딩 (`<h2>`, `<h3>` 등)
- `<p>` 태그는 아래 3가지 중 **하나 이상 충족할 때만** 사용:
  1. `\n` 포함 (줄바꿈이 있는 서술형)
  2. 텍스트 길이 95자 초과
  3. 문장형 마침표/종결어 반복
- 라벨, 키워드, CTA, 슬로건, 짧은 설명 → **절대 `<p>` 금지**
- 숫자/통계 데이터 → `<span>` 또는 `<strong>`

### CSS 선택자 계층 규칙 (필수 — 개별 클래스 남발 금지)
- **불필요한 클래스 제거** — 문제는 깊이가 아니라 모든 레벨에 고유 클래스를 붙이는 것
- **섹션 스코핑은 허용** — `.섹션 .컨테이너 li a`처럼 섹션+컨테이너로 시작하는 것은 충돌 방지를 위해 권장
- **금지 대상**: `li`, `a`, 유일한 태그에 불필요한 클래스 부여 (`.섹션 .아이템클래스 .요소클래스` 체인)
- 컨테이너 내 유일한 태그 → `.parent li strong`, `.parent h2` (클래스 불필요)
- 같은 태그 복수, 의미 구분 필요 → 최소 클래스 `.parent li .tag`, `.parent li .date`
- 같은 태그 복수, 순서 구분 가능 → `.parent a:first-child`, `.parent a + a`
- **리스트 항목**: `li`/`a`에 클래스 금지, `.컨테이너 li a`로 충분

---

## CSS 규칙

### 포맷 (CRITICAL — 반드시 준수)
- **각 셀렉터 규칙은 한 줄로 작성** (여러 줄로 펼치지 않음). 단, **콤마 셀렉터 3개 이상**이면 셀렉터만 줄바꿈, 속성은 마지막 셀렉터 뒤에 한 줄로 붙임
- **같은 셀렉터를 여러 번 선언하지 않음** — 하나의 셀렉터에 모든 속성을 합쳐서 한 줄로
- **미디어쿼리 블록 안에서 각 규칙은 줄바꿈으로 분리** (한 줄에 모든 규칙을 이어붙이지 않음)
- **미디어쿼리 내부 들여쓰기 없음** — 셀렉터는 컬럼 0에서 시작

```css
/* correct */
.mp_form{position:relative; padding:40px 0; display:flex; flex-direction:column;}
.mp_form h3{font-size:1.125rem; font-weight:700; color:#222;}

/* correct - media query */
@media screen and (max-width: 768px){
.mp_form{padding:20px 0;}
.mp_form h3{font-size:14px;}
}

/* WRONG - multi-line */
.mp_form {
    position: relative;
    padding: 40px 0;
}

/* WRONG - duplicate selector */
.mp_form{padding:40px 0;}
.mp_form{display:flex;}

/* WRONG - all media on one line */
@media screen and (max-width: 768px){.mp_form{padding:20px 0;}.mp_form h3{font-size:14px;}}

/* WRONG - indented media */
@media screen and (max-width: 768px){
    .mp_form{padding:20px 0;}
}
```

### 값과 단위
- font-size: **PC는 `rem`**, **모바일(768px 이하)은 고정 `px`**
- 기본 폰트 베이스: reset.css에 선언됨 → common.css에서 **재선언 금지**
- **line-height: 무단위 비율만** (`1.3`, `1.45`, `1.6`) — 절대 `25.866px` 같은 computed px 금지
- **letter-spacing: `em` 단위 기본** (`-0.025em`), 2px 이하 미세 조정은 px 허용
- **border-radius: 원형은 `50%`**, **pill은 `2em`** — `999px` 절대 금지
- padding/margin/gap: **고정 `px`** (기본)
- **100px 이상 값에 한해 `clamp()` 허용**, 100px 미만은 반드시 고정 `px`
- `calc()` 단독 금지, `vw` 단독 금지 (clamp 내부에서만)
- 색상: **hex 전용** (`#fff`, `#090944`), 투명도 필요 시만 `rgba()`
- **CSS Grid 사용 금지** — flexbox만 사용
- **`!important` 금지** (override 유틸리티 예외)
- 단축 속성 우선 사용
- 기본 트랜지션: `transition: all 0.3s ease-out`
- **한국어 텍스트**: `word-break: keep-all`
- **aspect-ratio**: 정사각형/비율 고정 요소에 사용

### HTML 페이지 파일명
- **메인 페이지**: `index.html` 고정
- **서브 페이지**: 의미 있는 영문명 (snake_case), flat 배치
- `page_1.html`, `sub_01.html` 같은 의미 없는 파일명 금지
- **파일명 = CSS 프리픽스**: `greeting.html` → `greeting_` 프리픽스 → `greeting_section`, `greeting_list`

### 네이밍
- **페이지 프리픽스**: `{페이지}_{역할}` 패턴
  - `index.html` → `main_` prefix (예: `main_mv`, `main_intro`, `main_product`) — `index_` 도 허용
  - `greeting.html` → `greeting_` (예: `greeting_title`, `greeting_desc`)
  - 기타 서브페이지 → 파일명에서 `.html` 제거한 값이 prefix
  - 자식 클래스에도 prefix 일관 적용: `main_intro_card`, `main_intro_card_icon`
- **공통 영역은 prefix 없음**: `.header`, `.footer`, `.logo`, `.gnb`, `.utils`, `.sns`, `.copyright` 등은 prefix 없이 사용, 스코핑으로 충돌 방지 (`.header .logo`, `.footer .logo`)
- **snake_case** 전용 (`^[a-z0-9_]+$`)
- `sec_1`, `sec_2`, `section_01` 같은 범용 이름 금지
- 공통 접미사: `_area`, `_wrap`, `_list`, `_item`, `_inner`, `_cont`
- 유틸리티 클래스 금지 (`.font_serif`, `.weight_bold`)
- `:root` 변수: `--point-color-1`, `--width`, `--padding` 패턴

### CSS 속성 순서
1. position 관련
2. margin
3. padding
4. width/height
5. display
6. alignment
7. background
8. font-size
9. font-weight
10. color
11. 기타

### Breakpoints
- 기본: **1400, 1200, 960, 768** (desktop-first, `max-width`)
- 768px 이하: padding/margin은 PC 값의 **절반**

---

## Figma 노드 보존 규칙

### 구분선/디바이더
- 얇은 fill-only 프레임은 반드시 DOM 요소로 보존 — 삭제 금지
- 구분선은 HTML 요소(`background-color`)로 렌더링, CSS border로 대체 금지

### Border/Stroke
- CSS `border-*`는 Figma 노드에 실제 `strokes.visible===true`가 있을 때만 생성
- 레이아웃 패턴에서 border 추론 금지
- `.card+.card{border-left:...}` 인접 셀렉터 border 금지

### 레이아웃 매핑 (기본)
- `layoutMode: HORIZONTAL` → `display:flex` (가로 배치)
- `layoutMode: VERTICAL` → flex vs block 선택 (하단 decision tree 참조)
- `padding*` → `.cont` 래퍼 padding 또는 섹션 수직 padding (section_width_formula 룰 참조)

### Figma → CSS Decision Tree (CRITICAL — 매번 같은 입력에 같은 출력 보장)

#### 1. 정렬 축 매핑 (layoutMode에 따른 축 전환)

```
layoutMode == HORIZONTAL:
  primaryAxisAlignItems(수평)  → justify-content
  counterAxisAlignItems(수직)  → align-items

layoutMode == VERTICAL:
  primaryAxisAlignItems(수직)  → justify-content  (flex-direction:column 전제)
  counterAxisAlignItems(수평)  → align-items

layoutMode == NONE:
  CSS 정렬 속성 미사용 (children absolute)
```

값 매핑:
| Figma | CSS |
|---|---|
| `MIN` | `flex-start` |
| `CENTER` | `center` |
| `MAX` | `flex-end` |
| `SPACE_BETWEEN` | `space-between` (primary axis only) |
| `textAlignHorizontal: LEFT/CENTER/RIGHT/JUSTIFIED` | `text-align: left/center/right/justify` |
| `textAlignVertical` | 무시 (부모 `align-items` 사용) |

#### 2. gap vs margin 결정

**Step 1 — 간격 균일성 측정 (수치 임계치)**:
```
adjacent children 간 실측 간격 → max - min:
  ≤ 1px  → 완전 균일  (gap 사용)
  ≤ 3px  → 거의 균일  (gap 허용)
  > 3px  → 비균일    (개별 margin 강제)
```

**Step 2 — layoutMode별 분기**:

```
HORIZONTAL:
  균일   → display:flex; flex-direction:row; gap:{itemSpacing}px;
  비균일 → display:flex; flex-direction:row; 자식별 margin-left

VERTICAL:
  균일 + 정렬제어필요 → display:flex; flex-direction:column;
                       + .parent > * + * {margin-top:{itemSpacing}px;}
                       (common.md no_column_gap 룰로 column에 gap 금지)
  균일 + 정렬불필요   → display:block;
                       + .parent > * + * {margin-top:{itemSpacing}px;}
  비균일              → display:block;
                       + 자식별 margin-top 개별 지정
```

**관용구**: `.parent > * + * {margin-top:Xpx}` 가 표준. 방향은 항상 `margin-top`, `margin-bottom` 금지 (마지막 자식 특수 경우 제외).

**금지**: `flex-direction:column` + `gap` 조합, 100px 미만 `clamp()`.

#### 3. 아이템 개수 결정 (카드/리스트)

**Step 1 — 리스트 컨테이너 식별**:
parent frame.layoutMode ∈ {HORIZONTAL, VERTICAL} + 같은 componentId (또는 같은 size) 인스턴스 ≥ 2개

**Step 2 — 카드 후보 수집**:
```
direct children 중:
- type == INSTANCE
- width/height 동일 (±2px)
- 또는 name 패턴 동일 (list_img, list_card, card 등)
```

**Step 3 — Variant dedup (CRITICAL)**:
```
같은 bbox.x (±3px) AND 같은 parent_id 접두사 → component variant overlap
→ 첫 인스턴스만 카드로 카운트, 나머지 skip

parent_id 규칙:
  "I{instance};{variant};..." 접두사가 같으면 같은 컴포넌트 set
  예: I251:6821;251:6276;220:10976 과 I251:6821;251:6276;230:1244
     → 같은 카드의 variant (같은 접두사 I251:6821;251:6276)
     I251:6821;251:6276;... 과 I251:6821;251:6277;...
     → 서로 다른 카드 (접두사가 다름)
```

**Step 4 — HTML 변환**:
카드 수 N → `<ul class="XXX_list"><li>...</li> × N</ul>`. 각 `<li>`는 visible default variant 하나만 렌더링.

**Step 5 — 검증**:
`validate-semantic.py`의 `figma_cardinality_match` 룰이 HTML `<li>` 수와 Step 3 결과를 자동 대조. 불일치 시 CRITICAL.

#### 4. padding 매핑 (section_width_formula 참조)

```
섹션 Frame.paddingLeft/Right (예: 240px) → 섹션에 직접 금지
→ :root {--width: content_w + 40; --padding: 20px;}
→ .cont {max-width: var(--width); padding: 0 var(--padding); margin: 0 auto; width: 100%;}

섹션 Frame.paddingTop/Bottom → 섹션에 직접 OK
```

---

## Figma TEXT 노드 규칙

- 각 TEXT 노드 → **독립 HTML 요소로 1:1 매핑**
- 인접 TEXT 노드 병합 금지
- **`\n` / ` ` → `<br>` 변환 필수 (CRITICAL)**: spec.json 텍스트의 줄바꿈을 HTML `<br>` 태그로 반드시 변환. HTML에 `\n`을 그냥 두면 브라우저가 무시함. 연속 `\n\n`은 블록 분리(`</p><p>`) 또는 `<br><br>`
- `characterStyleOverrides` 있으면 → 오버라이드 구간별 `<span>` 분리 필수
- `styleOverrideTable` 병합은 누적 방식 (common.md 참조)

---

## 기존 프로젝트 코드 참조 (필수)

피그마 변환 시 같은 프로젝트에 이미 변환된 페이지가 있으면:
1. 기존 CSS 변수, 클래스 패턴, 포맷을 먼저 확인하고 **동일하게 맞춤**
2. 공통 컴포넌트(header/footer/sub_visual/breadcrumb)는 기존 코드에서 **그대로 복사**
3. 메뉴 active 상태만 해당 페이지에 맞게 변경
4. 새 CSS는 기존 common.css **하단에 추가** (기존 코드 수정하지 않음)

---

## 자동 검증 (필수)

HTML/CSS 변환 완료 후 **반드시** 검증을 실행한다.

```bash
# HTML/CSS 규칙 검증
# TODO: validator 확장 필요 (REQ-005+) — --type basic|landing 미지원
python3 D:/dev-base/tools/validate-semantic.py --html <output.html> --css <output.css>
```

### 검증 항목 (FAIL 시 반드시 수정)
- CSS 포맷 규칙 (한 줄 셀렉터, hex 색상, flexbox 전용 등)
- HTML 태그 규칙 (p 태그 최소화, 클래스 네이밍 등)
- 프로젝트 타입별 규칙 (basic: rem/px, landing: px 전용 등)

---

## 피할 것
- Figma JSON을 직접 읽고 값을 추측하는 것
- CSS 셀렉터 여러 줄 펼침 (콤마 셀렉터 3개+ 시 셀렉터만 줄바꿈 허용)
- 같은 셀렉터 중복 선언
- computed px line-height (`25.866px`)
- `999px` border-radius
- 유틸리티 클래스
- CSS Grid
- `!important`
- rgb()/hsl() 색상
- letter-spacing px 단위
- 모든 요소에 개별 클래스 부여
- 짧은 라벨에 `<p>` 태그
- `<figure>`, `<figcaption>`, `<main>`, `<article>` 사용

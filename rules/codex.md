# Codex 규칙

GitHub Copilot, Cursor 등 Codex 기반 AI 전용 규칙입니다.

---

## 기본
- `common.md` 규칙 우선 적용
- 코드 주석: 영어만

---

## 코드 스타일

### HTML
- `<div>` + 클래스 기반 구조 우선. `<section>`은 주요 콘텐츠 섹션에만 사용
- `<main>`, `<article>`, `<figure>`, `<figcaption>` **사용 금지** — `<div class="img_area">` + `<p>` 또는 `<span>` 사용
- 모든 이미지에 `alt` 속성 필수 — **짧고 간결하게** (예: `alt="로고"`, `alt="제품 이미지"`, 긴 한국어 문장 금지)
- 이미지는 래퍼 div 안에 배치 (`.img_area` 등)
- `aria-label`은 **텍스트가 없는 인터랙티브 요소에만** 사용 — 장식 래퍼, span 등에 남발 금지
- `aria-hidden`은 최소한으로 사용
- 줄바꿈: `<br>` 태그 사용, 반응형은 `<br class="mb_only">` / `<br class="pc_only">`
- 빈 `<div>` 금지
- 섹션 내부 래퍼는 `.cont` 클래스, 최대 1개

### CSS
- **각 셀렉터 규칙은 한 줄로 작성** (여러 줄로 펼치지 않음)
- **같은 셀렉터를 여러 번 선언하지 않음** — 하나의 셀렉터에 모든 속성을 합쳐서 한 줄로
- **미디어쿼리 블록 안에서 각 규칙은 줄바꿈으로 분리** (한 줄에 모든 규칙을 이어붙이지 않음)
- **미디어쿼리 내부 들여쓰기 없음** — 셀렉터는 컬럼 0에서 시작
- font-size: **PC는 `rem`**, **모바일(768px 이하)은 고정 `px`**
- 기본 폰트 베이스: `html,body{font-size:clamp(14px, 1.2vw, 16px);}` (rem 기준점)
- **line-height: 무단위 비율만** (`1.3`, `1.45`, `1.6`) — Figma의 computed px 값(`25.866px`, `63.228px`) 금지
- **letter-spacing: `em` 단위 기본**, 2px 이하 미세 조정은 px 허용 (`-0.5px`, `-1px`)
- **border-radius: 원형은 `50%`**, **pill 형태는 `2em`** — `999px` 사용 금지
- **HTML 페이지 파일명**: 메인=`index.html` 고정, 서브=의미 있는 영문명 (snake_case, flat 배치). `page_1.html`, `sub_01.html` 금지. 파일명에서 `.html` 제거한 값 = CSS 프리픽스 (`greeting.html` → `greeting_`)
- 클래스명: **페이지 프리픽스 형식** (`{페이지}_{역할}`), **snake_case** 전용
- `sec_1`, `sec_2` 같은 범용 이름 금지
- 공통 접미사 패턴: `_area`, `_wrap`, `_list`, `_item`, `_inner`, `_cont`
- **공통 컴포넌트 타입**: 재사용 UI는 `listType_N`, `titleType_N` 패턴 사용
- 셀렉터는 부모 컨테이너 하위로 스코핑 (`.main_cont_1 .txt_area`)
- **유틸리티 클래스 금지** — `.font_serif`, `.weight_bold` 같은 범용 타이포그래피 클래스 금지. font-family, font-weight, color는 **부모/섹션 셀렉터에서 상속**
- `:root` 변수 네이밍: `--point-color-N`, `--width`, `--padding` 패턴 사용 (시맨틱 이름 금지)
- ul/ol/li/p 같이 구조 태그에 의존한 스타일은 최소화하고, 필요 시 `section_ul`, `section_li`, `section_p` 형태의 명시적 클래스 스타일로 대체한다.
- padding/margin/gap: 고정 `px` (기본)
- **100px 이상 값에 한해 `clamp()` 허용**
- **100px 미만 값은 반드시 고정 `px`**
- `calc()` 단독 사용 금지, `vw` 단독 사용 금지 (clamp 내부에서만 허용)
- **반응형 섹션 패딩**: `clamp()` 사용 (100px 이상 값에 한해 허용)
- 색상: **hex 전용**, 투명도 필요 시만 `rgba()` 허용
- **CSS Grid 금지** — flexbox만 사용
- **`!important` 금지** — override용 유틸리티 클래스에만 예외 허용
- 단축 속성 사용
- 기본 트랜지션: `transition: all 0.3s ease-out`
- **한국어 텍스트**: `word-break: keep-all` 적용
- **`aspect-ratio`**: 정사각형/비율 고정 요소에 사용 (`aspect-ratio:1/1`, `aspect-ratio:W/H`)
- **멀티라인 말줄임**: `overflow:hidden; display:-webkit-box; -webkit-line-clamp:N; -webkit-box-orient:vertical;`
- **`:before/:after` 점형 불릿**: `width:3px; aspect-ratio:1/1; background-color:{color}; border-radius:50%; display:block; content:"";`

```css
/* correct - each selector rule on one line, all properties merged */
.main_about{position:relative; padding:60px 0; width:100%;}
.main_about .tit h2{font-size:1.5rem; line-height:1.45; letter-spacing:-0.025em;}

/* correct - media query: each rule on its own line, no indent */
@media screen and (max-width: 768px){
.main_about{padding:30px 0;}
.main_about .tit h2{font-size:28px;}
}

/* correct - clamp for values >= 100px */
.main_about{padding:clamp(60px, 8vw, 120px) 0;}

/* correct - clamp for responsive section padding (>=100px) */
.main_about{padding:clamp(55px, 5.73vw, 110px) 0;}

/* correct - aspect-ratio for square/ratio elements */
.icon_wrap{width:40px; aspect-ratio:1/1;}
.logo_area{width:100%; aspect-ratio:685/322;}

/* correct - multiline ellipsis */
.tit{overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;}

/* correct - word-break for Korean */
.main_about p{word-break:keep-all;}

/* correct - before/after bullet dot */
.list li:before{position:absolute; left:0; top:10px; width:3px; aspect-ratio:1/1; background-color:#3182F6; border-radius:50%; display:block; content:"";}

/* wrong - same selector declared multiple times */
.main_about{margin-top:8px; font-size:2rem;}
.main_about{font-size:44px; line-height:63.228px;}
.main_about{color:#333;}

/* wrong - all media rules on one line */
@media screen and (max-width: 768px){.main_about{padding:30px 0;}.main_about .tit h2{font-size:28px;}}

/* wrong - indented inside media query */
@media screen and (max-width: 768px){
    .main_about{padding:30px 0;}
}

/* wrong - multi-line brace expansion */
.main_about {
    position: relative;
    padding: 60px 0;
}

/* wrong - computed px line-height */
.main_about .tit h2{line-height:25.86600112915039px;}

/* wrong - 999px border-radius */
.main_about .btn{border-radius:999px;}

/* wrong - utility class approach */
.landing_font_serif{font-family:var(--font-serif);}
.landing_weight_bold{font-weight:800;}

/* wrong - clamp for value under 100px */
.main_about .gap{margin-bottom:clamp(10px, 1vw, 20px);}

/* wrong - raw calc/vw outside clamp */
.main_about{padding:calc(120 / 1920 * 100vw) 0;}
```

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
- 기본값: **1400, 1200, 960, 768** (desktop-first, `max-width`)
- 선택 사용: **1024** (tablet 중간 대응 필요 시)
- 프로젝트별 커스텀 가능

### 레이아웃
- 컨테이너: `.cont{margin:0 auto; max-width:var(--width); padding:0 var(--padding); width:100%;}`
- 내부 래퍼: `.cont` 클래스, 최대 1개
- **flexbox만 사용** (CSS Grid 금지)
- DOM 최대 깊이: **5단계**
- 빈 div 금지, 익명 래퍼 금지

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
- 예: Figma content 1200 → `--width: 1240px`, `--padding: 20px`, content area = 1200 ✓

**Figma content width 추출 방법**: `extracted/{section}_spec.json` 의 최상위 `inner` 프레임에서 `bbox.w - paddingLeft - paddingRight`.

**금지 사항**:
- 섹션(`.main_*`, `.footer_top`, `.footer_bottom`)에 `max-width` 직접 선언 금지 (background 잘림)
- 섹션에 Figma inner padding(240 등) 직접 이식 금지 (`.cont`의 padding 20으로 통일)
- `--padding`을 20px 이외 값으로 바꾸기 금지
- `--max-width` 별도 변수 생성 금지 (`--width` 하나로 통일)

---

## Figma 노드 보존 규칙

### 구분선/디바이더 노드
- 얇은 fill-only 프레임(divider/bar/separator)은 반드시 DOM 요소로 보존 — 삭제 금지
- 구분선은 HTML 요소(`background-color`)로 렌더링, CSS border로 대체 금지

### Border/Stroke 규칙
- CSS `border-*`는 Figma 노드에 실제 `strokes.visible===true`가 있을 때만 생성
- 레이아웃 패턴에서 border를 추론하는 것 금지
- `.card+.card{border-left:...}` 같은 인접 셀렉터 border 금지
- `node.visible===false`인 노드만 제외, 나머지 visible 노드는 모두 DOM에 출력

---

## Figma TEXT 노드 매핑 규칙 (중요)
- 각 Figma TEXT 노드는 반드시 **독립된 HTML 요소로 1:1 매핑**
- 인접 TEXT 노드끼리 하나로 합치기 금지

## Figma 텍스트 줄바꿈 처리 (중요)
- 텍스트 노드의 `node.characters`에서 `\n`을 감지한다
- **단일 `\n`**: `<br>` 태그로 변환 — 절대 무시 금지
- **연속 `\n\n`**: `</p><p>` 또는 블록 분리로 변환
- 줄바꿈이 원본에 있으면 반드시 HTML 출력에 반영해야 한다

## Figma 텍스트 스타일 분할 (중요)
- 하나의 텍스트 노드 안에서 **아래 속성 중 1개라도 다른 구간이 있으면 반드시 `<span>`으로 분리**한다:
  - `fontSize`, `fontWeight`, `fontFamily`, `fills`(색상), `letterSpacing`, `lineHeightPx`
- **혼합 스타일을 하나의 스타일로 병합(flatten)하는 것을 금지**한다
- 분할된 span에는 인라인 `style` 대신 class를 부여한다

## Figma → CSS 결정 트리 (CRITICAL — 매번 같은 입력에 같은 출력 보장)

### 1. 정렬 축 매핑 (layoutMode에 따른 축 전환)

```
layoutMode == HORIZONTAL:
  primaryAxis(수평)  → justify-content
  counterAxis(수직)  → align-items

layoutMode == VERTICAL:
  primaryAxis(수직)  → justify-content  (flex-direction:column 전제)
  counterAxis(수평)  → align-items

layoutMode == NONE:
  CSS 정렬 속성 미사용 (children absolute)
```

값 매핑 (양쪽 축 공통):
| Figma | CSS |
|---|---|
| `MIN` | `flex-start` |
| `CENTER` | `center` |
| `MAX` | `flex-end` |
| `SPACE_BETWEEN` | `space-between` (primary axis only) |
| `textAlignHorizontal: LEFT/CENTER/RIGHT/JUSTIFIED` | `text-align: left/center/right/justify` |
| `textAlignVertical` | 무시 (부모 `align-items` 로 대체) |

### 2. gap vs margin 결정 (간격 균일성 수치 판정)

**Step 1 — 간격 균일성 측정**:
```
adjacent_children 간 실측 간격 → max - min:
  ≤ 1px  → "완전 균일"  (gap 사용)
  ≤ 3px  → "거의 균일"  (gap 허용, pixel snap 오차)
  > 3px  → "비균일"    (개별 margin 강제)
```

**Step 2 — layoutMode별 분기**:

```
HORIZONTAL:
  균일      → display:flex; flex-direction:row; gap:{itemSpacing}px;
  비균일    → display:flex; flex-direction:row;
              + .parent > * + * {margin-left:{X}px;}  (자식별 다른 값이면 nth-child)

VERTICAL:
  균일 + 정렬필요(align-items)  → display:flex; flex-direction:column;
                                  + .parent > * + * {margin-top:{itemSpacing}px;}
                                  (common.md no_column_gap 룰: column에 gap 금지)
  균일 + 정렬불필요              → display:block;
                                  + .parent > * + * {margin-top:{itemSpacing}px;}
  비균일                         → display:block;
                                  + 자식별 margin-top 개별 지정
```

**Step 3 — 관용구 고정**:
- 표준: `.parent > * + * {margin-top:Xpx;}` (첫 자식 제외)
- 방향: 항상 `margin-top` (다음 자식 위쪽에 부착), `margin-bottom` 금지
- 예외: 마지막 자식 특수 `margin-bottom` 필요 시만 허용

**금지**:
- `flex-direction:column` + `gap` 조합 (common.md `no_column_gap` 룰)
- 100px 미만 값에 `clamp()` 사용 (common.md `no_clamp_under_100`)

### 3. 아이템 개수 결정 (카드/리스트 카운트)

**Step 1 — 리스트 컨테이너 식별**:
```
parent frame.layoutMode ∈ {HORIZONTAL, VERTICAL}
+ children 중 같은 componentId (또는 같은 size) 인스턴스 ≥ 2개
→ "list container"
```

**Step 2 — 카드 후보 수집**:
```
list container의 direct children:
- type == INSTANCE
- width / height 동일 (±2px)
- 또는 name 패턴 동일 (list_img, list_card, card 등)
```

**Step 3 — Variant dedup (CRITICAL)**:
```
같은 bbox.x (±3px) AND 같은 parent_id 접두사 → component variant overlap
→ 첫 인스턴스만 카드로 카운트, 나머지 상태 variant는 skip

Figma parent_id 규칙:
  "I{instance_id};{variant_id};..." 형태에서 접두사가 같으면 같은 컴포넌트 set
  예: I251:6821;251:6276;... 과 I251:6821;251:6277;... 은 다른 카드
      I251:6821;251:6276;220:10976 과 I251:6821;251:6276;230:1244 는 같은 카드의 variant
```

**Step 4 — HTML 변환**:
```
카드 수 N → <ul class="XXX_list"><li>...</li> × N</ul>
각 <li>는 visible default variant 하나만 렌더링
```

**Step 5 — 검증**:
```
validate-semantic.py의 figma_cardinality_match 룰이
HTML <li> 수 == Step 3 결과 N 을 자동 대조 (불일치 시 CRITICAL)
```

### 4. padding 매핑 (section_width_formula 규칙 참조)

```
섹션 Frame.paddingLeft/Right (예: 240px)
→ 섹션에 직접 적용 금지
→ :root {--width: <content_w + 40>; --padding: 20px;}
→ .cont {max-width: var(--width); padding: 0 var(--padding); margin: 0 auto; width: 100%;}

섹션 Frame.paddingTop/Bottom
→ 섹션에 직접 적용 OK (배경이 full-bleed이므로 수직은 섹션이 담당)
```

### Figma MCP 데이터 사용 규칙 (CRITICAL)
- Figma MCP 응답을 섹션별로 받아 직접 해석하여 CSS 값 결정
- Figma 속성 → CSS 변환 규칙 준수 (layoutMode→flex-direction, itemSpacing→gap, fills→hex 색상 등)
- MCP 응답에 없는 속성은 추측하지 않음
- "그럴듯한" 값, "합리적인" 기본값을 임의로 넣는 것 절대 금지
- 완성 후 validate-semantic.py로 규칙 검증 필수

## 텍스트 추출 품질
- 피그마 `TEXT` 노드는 `characterStyleOverrides`와 `styleOverrideTable`를 함께 해석해서 오버라이드 단위로 분리 출력
- 스타일이 달라지는 구간만 `span`으로 분리해 기본 클래스와 함께 적용하고, 색/두께/크기 변화를 보존
- `styleOverrideTable` 항목이 `fontSize`, `fontWeight`, `fontFamily` 등을 누락한 경우는 이전 오버라이드 구간의 실제 적용 스타일을 기준으로 누락값을 상속해 병합한다
- 오버라이드가 적용되는 구간은 인라인 `style` 대신 class 분리 출력한다
- 강제 병합 규칙:
  - `baseStyle = { ...node.style, fills: node.fills }`
  - `previousResolvedStyle = null`
  - 오버라이드 id가 0 또는 누락 → `resolved = baseStyle`
  - 오버라이드 id가 존재 → `resolved = { ...(previousResolvedStyle ?? baseStyle), ...(override.style ?? {}), ...(override.fills ? { fills: override.fills } : {}) }`
  - 출력 시 `resolved`를 기준으로 계산하고 `previousResolvedStyle = resolved`로 갱신
  - `fontSize`, `fontWeight`, `fontFamily`, `fills`의 누락값은 `previousResolvedStyle` 유지
- `lineHeightPx`는 CSS `line-height` **비율로 변환**하여 출력, `letterSpacing`은 `letter-spacing` **em 단위로 변환**하여 출력

---

### JavaScript
- ES6+ 문법
- 들여쓰기: 4 spaces
- 세미콜론 사용
- const/let 사용 (var 금지)

---

## 자동완성 힌트

### 주석으로 의도 전달
```javascript
// remove duplicates from array
const unique = [...new Set(arr)];

// format date as YYYY-MM-DD
const formatDate = (date) => { ... }
```

### 함수명 예시
- `getUserById` - ID로 사용자 조회
- `validateEmail` - 이메일 유효성 검사
- `formatPrice` - 가격 포맷 (콤마 추가)

---

## 선호 패턴

### 조건문
```javascript
// ternary for simple cases
const status = isActive ? 'active' : 'inactive';

// early return for complex cases
if (!user) return null;
```

### 반복문
```javascript
// prefer map, filter, reduce
const names = users.map(user => user.name);
const adults = users.filter(user => user.age >= 18);
```

### 비동기
```javascript
// prefer async/await
const data = await fetchData();
```

---

## 피할 것
- 깊은 중첩
- 매직 넘버/문자열
- 과도한 추상화
- 불필요한 의존성
- `<figure>`, `<figcaption>`, `<main>`, `<article>` 사용
- CSS 셀렉터 여러 줄 펼침 (각 규칙은 한 줄로)
- 같은 셀렉터 중복 선언
- CSS 미디어쿼리 내부 들여쓰기
- 미디어쿼리 안 모든 규칙을 한 줄에 이어붙이기
- computed px line-height (`25.866px` 등)
- `999px` border-radius
- 유틸리티 클래스 (`.font_serif`, `.weight_bold`)
- 시맨틱 :root 변수명 (`--landing-dark`)
- padding/margin에 100px 미만 clamp 사용
- calc/vw 단독 사용
- `sec_1`, `sec_2` 같은 범용 클래스명
- CSS Grid
- `!important` (utility 제외)
- rgb()/hsl() 색상 (hex 사용)
- letter-spacing에 px 단위 (2px 이하 미세 조정은 예외 허용)
- 과도한 aria 속성
- 긴 한국어 alt 텍스트

---

## 자동 검증 (필수)

HTML/CSS 변환 작업이 완료되면 **반드시** 검증 스크립트를 실행한다.

### 실행 명령
```bash
# HTML/CSS 규칙 검증
# TODO: validator 확장 필요 (REQ-005+) — --type basic|landing 미지원
python3 D:/dev-base/tools/validate-semantic.py --html ./html/index.html --css ./html/css/common.css
```

### 검증 워크플로우
1. HTML/CSS 변환 완료 후 검증 스크립트 실행
2. **FAIL** 항목이 있으면 해당 문제를 수정하고 다시 검증
3. **WARN** 항목은 확인 후 필요시 수정
4. **모든 FAIL이 해소될 때까지 반복**
5. 최종 검증 결과를 출력에 포함

### 주의사항
- 파일 경로는 실제 출력 파일 위치에 맞게 조정

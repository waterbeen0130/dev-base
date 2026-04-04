# Gemini 규칙

Gemini CLI 기반 AI 전용 규칙입니다. **퍼블리싱 프로젝트의 주 실행 에이전트**입니다.

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
  - `layoutMode` → `flex-direction` (VERTICAL=column, HORIZONTAL=row)
  - `itemSpacing` → `gap`
  - `padding*` → `padding` (shorthand)
  - `fills` → `background`/`color` (hex 변환, 투명도 시만 rgba)
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

- `<div>` + 클래스 기반 구조 우선. `<section>`은 주요 콘텐츠 섹션에만 사용
- `<main>`, `<article>`, `<figure>`, `<figcaption>` **사용 금지** — `<div class="img_area">` + `<span>` 사용
- 모든 이미지에 `alt` 속성 필수 — **짧고 간결하게** (예: `alt="로고"`, 긴 한국어 문장 금지)
- 이미지는 래퍼 div 안에 배치 (`.img_area` 등)
- `aria-label`은 **텍스트가 없는 인터랙티브 요소에만** 사용
- 줄바꿈: `<br>` 태그 사용, 반응형은 `<br class="mb_only">` / `<br class="pc_only">`
- 빈 `<div>` 금지
- 섹션 내부 래퍼는 `.cont` 클래스, 최대 1개
- DOM 최대 깊이: **5단계**

### 텍스트 태그 판정
- 기본 태그는 `<span>` 또는 헤딩 (`<h2>`, `<h3>` 등)
- `<p>` 태그는 아래 3가지 중 **하나 이상 충족할 때만** 사용:
  1. `\n` 포함 (줄바꿈이 있는 서술형)
  2. 텍스트 길이 95자 초과
  3. 문장형 마침표/종결어 반복
- 라벨, 키워드, CTA, 슬로건, 짧은 설명 → **절대 `<p>` 금지**
- 숫자/통계 데이터 → `<span>` 또는 `<strong>`

### CSS 선택자 계층 규칙 (필수 — 개별 클래스 남발 금지)
- **모든 HTML 요소에 개별 클래스 부여 금지** — 컨테이너 클래스만 유지
- 컨테이너 내 유일한 태그 → `.parent h2`, `.parent strong`
- 같은 태그 복수, 의미 구분 필요 → 최소 클래스 `.parent .en`, `.parent .sub`
- 같은 태그 복수, 순서 구분 가능 → `.parent a:first-child`, `.parent a + a`
- 개별 클래스는 위 방법으로 불가능할 때만 최후 수단

---

## CSS 규칙

### 포맷 (CRITICAL — 반드시 준수)
- **각 셀렉터 규칙은 한 줄로 작성** (여러 줄로 펼치지 않음)
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
- 기본 폰트 베이스: `html,body{font-size:clamp(14px, 1.2vw, 16px);}`
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
- **페이지 프리픽스**: `{페이지}_{역할}` (예: `mp_form`, `mp_list`)
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

### 레이아웃 매핑
- `layoutMode: VERTICAL` → `flex-direction: column`
- `layoutMode: HORIZONTAL` → `flex-direction: row`
- `itemSpacing` → CSS `gap` (spec 테이블의 `css_gap` 값 사용)
- `padding*` → CSS `padding` (spec 테이블의 `css_padding` 값 사용)
- 레이아웃 정보 누락 금지

---

## Figma TEXT 노드 규칙

- 각 TEXT 노드 → **독립 HTML 요소로 1:1 매핑**
- 인접 TEXT 노드 병합 금지
- `\n` → `<br>` 변환 필수
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
node D:/dev-base/tools/validate.js --html <output.html> --css <output.css> --type basic|landing
```

### 검증 항목 (FAIL 시 반드시 수정)
- CSS 포맷 규칙 (한 줄 셀렉터, hex 색상, flexbox 전용 등)
- HTML 태그 규칙 (p 태그 최소화, 클래스 네이밍 등)
- 프로젝트 타입별 규칙 (basic: rem/px, landing: px 전용 등)

---

## 피할 것
- Figma JSON을 직접 읽고 값을 추측하는 것
- CSS 셀렉터 여러 줄 펼침
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

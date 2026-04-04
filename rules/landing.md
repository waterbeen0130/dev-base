# 랜딩페이지 규칙

> `common.md` 규칙 기본 적용, 아래는 랜딩페이지 전용 규칙

---

## Basic과 다른 점

### CSS
- font-size: PC/모바일 모두 **고정 px** (rem 사용 안 함)
- padding/margin: PC/모바일 모두 **고정 px**
- **Figma 좌우 padding → max-width 변환 필수** (CRITICAL):
  - Figma 섹션의 좌우 padding(예: 246px)을 CSS padding으로 직접 사용 금지
  - `max-width: 1920 - (좌우padding * 2) + 40`px, `padding: {상}px 20px {하}px`, `margin: 0 auto`
  - 섹션(배경용)은 full-width, 내부 콘텐츠 래퍼에 max-width 적용
  - 예: Figma `padding: 113px 246px` → 섹션: `padding:113px 0`, 내부: `max-width:1468px; margin:0 auto; padding:0 20px;`
- **line-height: 무단위 비율만** (`1.3`, `1.45`, `1.6`) — computed px 금지
- **letter-spacing: `em` 단위만** (`-0.025em`) — px 금지
- **border-radius: 원형은 `50%`**, **pill 형태는 `2em`** — `999px` 사용 금지
- **같은 셀렉터를 여러 번 선언하지 않음** — 하나의 셀렉터에 모든 속성을 합쳐서 한 줄로
- **유틸리티 클래스 금지** — font-family, font-weight, color는 부모/섹션 셀렉터에서 상속
- `:root` 변수 네이밍: `--point-color-1`, `--width`, `--padding` 패턴 사용

```css
/* landing - PC/모바일 모두 고정 px, line-height ratio */
.section_name{padding:90px 0;}
.section_name .title{font-size:32px; line-height:1.45; letter-spacing:-0.025em;}

@media screen and (max-width: 768px){
.section_name{padding:50px 0;}
.section_name .title{font-size:20px;}
}

/* wrong - computed px line-height */
.section_name .title{line-height:46.080001831054688px;}

/* wrong - 999px border-radius */
.section_name .btn{border-radius:999px;}

/* wrong - utility class */
.landing_font_serif{font-family:var(--font-serif);}

/* wrong - same selector multiple times */
.section_name{font-size:32px;}
.section_name{color:#333;}
```

### HTML
- `<div>` + 클래스 기반 구조 우선
- `<main>`, `<article>`, `<figure>`, `<figcaption>` **사용 금지** — `<div class="img_area">` + `<p>` 또는 `<span>` 사용
- `aria-label`은 **텍스트가 없는 인터랙티브 요소에만** — 장식 래퍼에 남발 금지
- 이미지 `alt`는 **짧고 간결하게** (긴 한국어 문장 금지)

### JS
- **CDN 방식** 사용 (로컬 파일 아님)

---

## 파일 구조
```
project/
├── index.html
├── css/
│   └── [프로젝트명].css
├── js/
│   └── ui_common.js (필요시)
└── img/
```

---

## 기본 포함 파일

### CSS
- 파일명: `[프로젝트명].css`
- reset.css 별도 파일 없음 → CSS 최상단에 reset 스타일 포함

### JS (CDN)
```html
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/slick-carousel@1.8.1/slick/slick.min.js"></script>
```

---

## CSS 필수 포함 (최상단)

### 1. Reset 스타일
- 웹폰트 제외, 순수 reset만 포함
- 프로젝트 CSS 최상단에 명시

### 2. CSS 변수 + GSAP 애니메이션 (필수 유지)
```css
:root {
    --padding: 20px;
    --header_h: 100px;
    --width: 1510px;
    --point-color-1: #df3d6e;
}

[data-delay] { position: relative; transition: all 1s ease; opacity: 0; }
[data-direction="left"] { left: -40px; }
[data-direction="right"] { right: -40px; }
[data-direction="top"] { top: -40px; }
[data-direction="bottom"] { bottom: -40px; }
.section_on [data-delay] { opacity: 1; }
.section_on [data-direction="left"] { left: 0; }
.section_on [data-direction="right"] { right: 0; }
.section_on [data-direction="top"] { top: 0; }
.section_on [data-direction="bottom"] { bottom: 0; }
```

> CSS 변수 값은 프로젝트별로 수정 가능
> 애니메이션 스타일은 GSAP ScrollTrigger와 연동됨

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

## 주의사항
- reset 스타일에 웹폰트 포함 금지
- CSS 변수 및 애니메이션 스타일 삭제 금지
- CDN 버전 변경 시 호환성 확인
- 피그마 줄바꿈(`\n`)은 HTML에서 `<br>`로 그대로 반영 (PC/모바일 각각 적용)
- 이미지 기반 섹션은 원본 이미지 픽셀 높이에 맞춰 섹션 `height` 지정하고 `object-fit: cover` 적용
- 섹션 내부 이미지(`img`)는 `width: 100%` 등 % 기반으로 지정하고 `aspect-ratio`로 비율 유지 (고정 width/height 금지)
- 모바일 전용 이미지는 반드시 사용하고, 모바일 이미지 픽셀 크기 기준으로 배치/크기 조정
- ul/ol/li/p처럼 구조 태그에 직접 묶인 스타일은 가급적 피하고, 가능한 한 각 요소에 `..._ul`, `..._li`, `..._p` 형태 클래스명을 부여해 클래스 단위로 스타일링한다.

---

## Figma TEXT 노드 매핑 규칙 (중요)
- 각 Figma TEXT 노드는 반드시 **독립된 HTML 요소로 1:1 매핑**
- 인접 TEXT 노드끼리 하나로 합치기 금지

## Figma 텍스트 줄바꿸 처리 (중요)
- 텍스트 노드의 `node.characters`에서 `\n`을 감지한다
- **단일 `\n`**: `<br>` 태그로 변환 — 절대 무시 금지
- **연속 `\n\n`**: `</p><p>` 또는 블록 분리로 변환
- 줄바꿈이 원본에 있으면 반드시 HTML 출력에 반영해야 한다

## Figma 텍스트 스타일 분할 (중요)
- 하나의 텍스트 노드 안에서 **아래 속성 중 1개라도 다른 구간이 있으면 반드시 `<span>`으로 분리**한다:
  - `fontSize`, `fontWeight`, `fontFamily`, `fills`(색상), `letterSpacing`, `lineHeightPx`
- **혼합 스타일을 하나의 스타일로 병합(flatten)하는 것을 금지**한다
- 분할된 span에는 인라인 `style` 대신 class를 부여한다

## Figma 레이아웃 매핑 규칙
- `layoutMode: VERTICAL` → `flex-direction: column`
- `layoutMode: HORIZONTAL` → `flex-direction: row`
- `itemSpacing` → CSS `gap` 반영 필수
- `padding*` → CSS `padding` 반영 필수
- `counterAxisAlignItems` → `align-items`
- `primaryAxisAlignItems` → `justify-content`
- 레이아웃 정보 누락 금지

## 텍스트 추출 품질
- 피그마 `TEXT` 노드는 `characterStyleOverrides`와 `styleOverrideTable`를 함께 해석해서 오버라이드 단위로 분리 출력
- 텍스트 추출 시 `characterStyleOverrides`가 있는 노드는 오버라이드 구간별로 `<span>` 분리하여 굵기/크기/색상 차이를 보존
- 오버라이드 텍스트는 추출 후 `textAlign`과 줄바꿈 위치를 실제 Figma 기준으로 1차 검증해야 함
- `styleOverrideTable`에 일부 스타일만 있는 오버라이드(예: `lineHeightPx`만 있는 항목)는 직전 오버라이드 구간의 실제 적용 스타일(폰트/굵기/색상)을 상속해서 병합해야 함
- 텍스트 오버라이드 병합의 강제 규칙:
  - `baseStyle = { ...node.style, fills: node.fills }`
  - `previousResolvedStyle = null`
  - 각 오버라이드 구간 처리:
    - overrideId `0` 또는 오버라이드가 비어 있으면 `resolvedStyle = baseStyle`로 초기화
    - 그 외에는 `resolvedStyle = { ...(previousResolvedStyle ?? baseStyle), ...(override.style ?? {}), ...(override.fills ? { fills: override.fills } : {}) }`
  - `resolvedStyle`로 출력 후 `previousResolvedStyle = resolvedStyle` 갱신
  - `fontSize`, `fontWeight`, `fontFamily`, `fills`는 미지정일 때만 이전 값 유지
- `lineHeightPx`는 CSS `line-height` **비율로 변환**하여 출력, `letterSpacing`은 `letter-spacing` **em 단위로 변환**하여 출력

## 텍스트 오버라이드 검증 필수 규칙 (CRITICAL — 반복 오류 방지)

> **base style을 최종값으로 사용하는 것을 절대 금지한다.**
> `characterStyleOverrides` 배열이 비어있지 않으면, base style은 fallback일 뿐이며 실제 렌더링 값은 반드시 오버라이드를 resolve한 결과다.

### 필수 검증 프로세스 (모든 TEXT 노드에 적용)

1. **오버라이드 존재 확인**: `characterStyleOverrides` 배열이 비어있지 않고 `0`이 아닌 값이 1개 이상이면 오버라이드 활성
2. **resolve 수행**: `styleOverrideTable[overrideId]`에서 실제 적용 스타일을 추출
   - `fontFamily`, `fontWeight`, `fontSize`, `fills`(색상), `letterSpacing` 중 하나라도 오버라이드에 명시되어 있으면 해당 값이 최종값
   - 오버라이드에 없는 속성만 `previousResolvedStyle` 또는 `baseStyle`에서 상속
3. **대조표 출력 (필수)**: CSS 적용 전 아래 형식으로 대조표를 작성하고 확인
   ```
   | 문자 구간 | overrideId | fontFamily | fontWeight | fontSize | color | letterSpacing |
   ```
4. **CSS 적용**: resolve된 값만 CSS에 사용. base style 값을 "대표값"으로 사용 금지
5. **브라우저 검증**: `getComputedStyle`로 실제 렌더링 값을 확인하고 Figma resolve 값과 대조

### 흔한 실수 패턴 (금지)

- base `fontWeight: 100`인데 모든 오버라이드가 `fontWeight: 500` → **CSS에 100 적용하면 오류**. resolve 결과인 500을 적용해야 함
- base `fontFamily: "Big Shoulders Display"`인데 오버라이드가 "MEGA"에 `Playfair Display`, "PEOPLE"에 `Oswald` → **base 폰트를 전체에 적용하면 오류**. 구간별 `<span>` 분리 필수
- base `fontSize: 208`인데 오버라이드가 `fontSize: 160` → **208px로 CSS 작성하면 오류**. 실제 렌더링 크기는 160px

> 브레인바디 랜딩 전용 보정 규칙은 아래 `브레인바디 랜딩 특화 추출 규칙` 블록에서 함께 관리한다.

## 브레인바디 랜딩 특화 추출 규칙 (반복 재현용)

다음 규칙은 동일 페이지를 재추출할 때 동일한 HTML/CSS 차이를 재현하기 위한 전용 필수 규칙입니다.
단, 클래스명은 프로젝트 고정값을 쓰지 않는다. (`.brainbody_inner` 같은 고정 셀렉터 추가 금지)

### 텍스트 태그 규칙
- 문단이 아닌 짧은 라벨/브랜딩 문구는 `<span>`로 유지한다.
- `BrainBody`, `MRI`, `Greenmall`, `영상의학과`, `원스톱 토탈케어` 등 라벨성 키워드는 절대 `<p>`로 바꾸지 않는다.
- `p`는 줄바꿈이 있는 경우나 실제 문단성 텍스트(긴 문장)에 한해서만 허용한다.
- 폰트는 클래스명이 아니라 Figma의 `fontFamily`를 기준으로 매핑한다.
  - `Barlow Semi Condensed`는 `"Barlow Semi Condensed", "Pretendard", sans-serif`로 매핑.

### 클래스 최소화 규칙
- 블록 단위 클래스는 필수 최소 집합만 사용하고, 내부 아이템은 `.title`, `.value` 같은 의미 클래스 + 자식 선택자로 표기한다.
- 동일한 스타일 반복 구간은 `nth-child`보다 의미 클래스를 우선한다(색상 강조/강조색 텍스트 등).
- `t1`, `g137` 같은 연속 클래스 번호 기반 생성 방식은 지양하고, 구조적/의미적 클래스 또는 부모+자식 선택자로 통일한다.

### 레이아웃 규칙
- 같은 부모에서 `y` 정렬이 같고 높이가 유사한 항목은 세로 스택이 아닌 행 구조(`inline-flex`)로 추출한다.
- 고정 폭이 들어간 컨테이너는 반응형에서 `max-width` + `margin: 0 auto` 패턴으로 변환한다.
- 리스트/카드 블록의 `ul > li`는 `ul li`로 완화하고, 구조가 고정될 수 있는 구간만 `>`.
- 고정 폭 변환 시 컨테이너 너비는 기본적으로 `max-width: Npx; width: 100%;` 조합을 사용한다.
- 블록별 동일 규격이 반복되는 폭값은 프로젝트에서 공통 변수화한다.

### 스타일 정리 규칙
- 불필요한 `width: 100%` 제거, 블록 기본은 비워두거나 `max-width` 기반 처리.
- `background-color`는 실제 배경 레이어가 있을 때만 선언.
- `data-delay`, `data-direction`은 기본 오프셋(`left/right/top/bottom: -40px`, `opacity:0`) 유지 후, 진입 시 `section_on`에서 `opacity:1` 및 오프셋 0으로 복원한다.
- GSAP 미탑재 환경에서 `data-delay`가 동작 안 하면 fallback 동작이 누락되지 않도록 예외 처리.
- `cornerRadius`는 기본 유지(원형은 `50%`, pill은 `2em`), `999px` 고정 사용 금지.

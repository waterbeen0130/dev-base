# 공통 규칙

모든 AI 어시스턴트에게 적용되는 규칙입니다.

---

## 언어 설정
- 응답 언어: **한국어**
- 코드 주석: **영어만 사용**
- 변수/함수명: 영어 (camelCase 또는 snake_case)

---

## 작업 흐름
주요 작업: **피그마 디자인 코드 → JSON 데이터 → CSS/HTML 변환**

1. 피그마에서 디자인 토큰 추출 (JSON 형식)
2. JSON을 CSS/HTML로 변환
3. 프로젝트별 breakpoint와 스타일 적용

---

## 코딩 스타일

### 공통
- 들여쓰기: **4 spaces**
- 인라인 스타일/스크립트 사용 금지
- 기존 프로젝트 컨벤션 우선 적용

### HTML
- `<div>` + 클래스 기반 구조 우선. `<section>`은 주요 콘텐츠 섹션에만 사용
- `<main>`, `<article>`, `<figure>`, `<figcaption>` **사용 금지** — `<div class="img_area">` + `<p>` 또는 `<span>` 사용
- 모든 이미지에 `alt` 속성 필수 — **짧고 간결하게** (예: `alt="로고"`, `alt="제품 이미지"`, 긴 한국어 문장 금지)
- 이미지는 반드시 래퍼 div 안에 배치 (`.img_area` 등)
- 버튼에 `type="button"` 명시
- 폼 요소는 `<label>`과 연결
- `aria-label`은 **텍스트가 없는 인터랙티브 요소에만** 사용 — 장식 래퍼, span 등에 남발 금지
- `aria-hidden`은 최소한으로 사용
- 줄바꿈은 `<br>` 태그 사용, 반응형 줄바꿈은 `<br class="mb_only">` / `<br class="pc_only">` 클래스 활용
- 빈 `<div>` 금지
- 섹션 내부 래퍼는 `.cont` 클래스 사용, 최대 1개
- **리스트형 콘텐츠는 반드시 `<ul>` + `<li>` 시맨틱 마크업 사용** — `<a>` 태그만 나열하거나 `<div>`로 반복 항목을 감싸는 것은 금지
  - 네비게이션 메뉴: `ul > li > a` (2depth는 `ul > li > ul > li > a`)
  - 카드형 리스트/배너 리스트: `ul > li > a > (내부 구조)`
  - 게시판/공지 목록: `ul > li > a > (제목 + 날짜)`
  - 갤러리 목록: `ul > li > a > (이미지 + 텍스트)`
  - CSS에서 `list-style:none; margin:0; padding-left:0;` 리셋 필수
  - 반복 항목이 2개 이상이면 무조건 `ul > li` 구조 적용

### CSS 허용 예외 목록

> 아래 항목은 일반 규칙의 예외입니다. 명시된 범위에서만 허용됩니다.

| 예외 항목 | 허용 범위 |
|-----------|-----------|
| `!important` | 마진/패딩/텍스트정렬 등 override용 유틸리티 클래스에만 허용 |
| `rgba()` | 투명도(alpha) 필요 시 — 그림자, 배경 반투명, 그라디언트 stop |
| kebab-case | `is-active`, `has-icon` 등 상태 접두사(`is-`, `has-`)에만 허용 |
| `js-` prefix | Slick 등 외부 라이브러리 JS 훅 클래스에만 허용 |
| letter-spacing px | **2px 이하 미세 조정**에 한해 px 허용 (`-0.5px`, `-1px`) |

---

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
- padding/margin/gap: 고정 `px` 사용 (기본)
- **100px 이상 값에 한해 `clamp()` 허용** (예: `clamp(50px, 5vw, 100px)`)
- **100px 미만 값은 반드시 고정 `px`**
- `calc()` 단독 사용 금지 (clamp 내부에서만 허용)
- `vw` 단독 사용 금지 (clamp 내부에서만 허용)
- **반응형 섹션 좌우 여백**: 좌우 padding 대신 `max-width` + `margin:0 auto`로 콘텐츠 폭 제한. 상하 padding은 고정 `px` 사용
- 768px 이하: padding/margin은 PC 값의 **절반**
- 색상: **hex 전용** (`#fff`, `#090944`), 투명도 필요 시만 `rgba()` 허용
- **CSS Grid 사용 금지** — flexbox만 사용
- **`!important` 사용 금지** — 단, override용 유틸리티 클래스에만 허용
- **단축 속성 우선 사용**
- 기본 트랜지션: `transition: all 0.3s ease-out`
- 셀렉터는 반드시 부모 컨테이너 하위로 스코핑 (`.main_cont_1 .txt_area`)
- **유틸리티 클래스 금지** — `.font_serif`, `.weight_bold` 같은 범용 타이포그래피 클래스 금지. font-family, font-weight, color는 **부모/섹션 셀렉터에서 상속**
- `:root` 변수 네이밍: 시맨틱 이름 사용 권장 (`--color_primary`, `--color_bg`, `--font_heading` 등). 색상 변수화 패턴은 `css-enhancement.md` §9 참조
- **한국어 텍스트**: `word-break: keep-all` 적용 (문장 단위 줄바꿈)
- **`aspect-ratio`**: 정사각형/비율 고정 요소에 `aspect-ratio:1/1` 또는 `aspect-ratio:W/H` 사용
- **멀티라인 말줄임**: `overflow:hidden; display:-webkit-box; -webkit-line-clamp:N; -webkit-box-orient:vertical;`
- **`:before/:after` 점형 불릿**: `width:3px; aspect-ratio:1/1; background-color:{color}; border-radius:50%; display:block; content:"";`

```css
/* correct - each selector rule on one line, all properties merged */
.section_name{position:relative; padding:90px 0; width:100%;}
.section_name .title{font-size:1.5rem; line-height:1.45; letter-spacing:-0.025em;}

/* correct - clamp for values >= 100px */
.section_name{padding:clamp(50px, 5vw, 100px) 0;}

/* correct - media query: each rule on its own line, no indent */
@media screen and (max-width: 768px){
.section_name{padding:45px 0;}
.section_name .title{font-size:14px;}
}

/* wrong - same selector declared multiple times */
.section_name{margin-top:8px; font-size:2rem;}
.section_name{font-size:44px; line-height:63.228px;}
.section_name{color:#333;}

/* wrong - all media rules jammed on one line */
@media screen and (max-width: 768px){.section_name{padding:45px 0;}.section_name .title{font-size:14px;}}

/* wrong - indented inside media query */
@media screen and (max-width: 768px){
    .section_name{padding:45px 0;}
}

/* wrong - multi-line brace expansion */
.section_name {
    position: relative;
    padding: 90px;
}

/* wrong - computed px line-height */
.section_name .title{line-height:25.86600112915039px;}

/* wrong - 999px border-radius */
.section_name .btn{border-radius:999px;}

/* wrong - utility class approach */
.landing_font_serif{font-family:var(--font-serif);}
.landing_weight_bold{font-weight:800;}

/* wrong - clamp for value under 100px */
.section_name .gap{margin-bottom:clamp(10px, 1vw, 20px);}

/* wrong - raw calc/vw outside clamp */
.section_name{padding:calc(90 / 1920 * 100vw) 0;}
```

### 프로젝트 초기화

새 프로젝트 시작 시 반드시 `D:\dev-base\tools\init-project.py`로 초기화한다.

```bash
# basic 프로젝트 (퍼블리싱 템플릿 포함)
python3 D:/dev-base/tools/init-project.py "프로젝트경로" --type basic --publishing

# landing 프로젝트
python3 D:/dev-base/tools/init-project.py "프로젝트경로" --type landing --publishing
```

자동 생성 항목:
- `CLAUDE.md` — rules 참조 포함
- `.claude/settings.local.json` — 도구 자동 허용
- `.gran-maestro/` — MST 워크플로우 구조 + 퍼블리싱 config

### HTML 페이지 파일명 규칙

- **메인 페이지**: `index.html` 고정
- **서브 페이지**: 페이지 내용을 나타내는 **영문 snake_case** 파일명 (예: `greeting.html`, `history.html`)
- 루트 디렉토리에 flat 배치 (폴더 중첩 없음)
- `page_1.html`, `sub_01.html`, `page_a.html` 같은 **의미 없는 번호/문자 기반 파일명 금지**
- **body class 필수**: 파일명에서 `.html`을 제거한 값에 `page_` 프리픽스를 붙여 `<body class="page_{name}">` 형태로 부여
  - `greeting.html` → `<body class="page_greeting">`
  - `products.html` → `<body class="page_products">`

#### CSS 프리픽스 규칙

- 페이지 **고유 콘텐츠 영역에만** CSS 프리픽스를 사용한다
- 프리픽스는 파일명(영문 snake_case)과 동일하게 `{name}_{role}` 패턴으로 지정
- 서브페이지 공통 구조(`sub_wrap`, `sub_visual`, `navi`, `lnb`, `sub_cont` 등)에는 프리픽스 없이 공통 클래스 사용

| 페이지 유형 | 파일명 | body class | CSS 프리픽스 | 프리픽스 적용 대상 |
|------------|--------|-----------|-------------|------------------|
| 메인(홈) | `index.html` | `page_index` | `main_` | 메인 전용 섹션 |
| 인사말 | `greeting.html` | `page_greeting` | `greeting_` | 인사말 고유 콘텐츠 |
| 공지사항 | `notice.html` | `page_notice` | `notice_` | 공지 고유 콘텐츠 |
| 포토갤러리 | `gallery.html` | `page_gallery` | `gallery_` | 갤러리 고유 콘텐츠 |

> **규칙**: 서브페이지 공통 영역은 공통 클래스, 페이지 고유 영역만 프리픽스 적용

### CSS 클래스 네이밍

#### 공통 영역 vs 페이지 영역 구분 (CRITICAL — 필수)

> **공통 영역(header, footer, GNB, 전체메뉴 등)에 페이지 프리픽스를 붙이는 것을 금지한다.**
> 공통 영역은 프리픽스 없이 역할명 그대로 사용하고, 페이지 프리픽스는 해당 페이지 전용 콘텐츠에만 사용한다.

| 영역 | 프리픽스 | 클래스 예시 |
|------|---------|------------|
| **공통 (모든 페이지 공유)** | **없음** | `header`, `gnb`, `gnb_depth`, `util`, `footer`, `footer_info`, `footer_menu`, `total_menu`, `total_header`, `total_content`, `total_group`, `total_links`, `logo`, `copyright`, `btn_top`, `btn_menu`, `btn_close`, `btn_login`, `btn_search`, `btn_family`, `btn_admin` |
| **메인(index) 전용** | `main_` | `main_visual`, `main_quick`, `main_notice`, `main_gallery`, `main_activity` |
| **서브페이지 전용** | `{페이지}_` | `notice_list`, `gallery_card`, `greeting_con` |

**판별 기준**: 2개 이상의 페이지에서 동일하게 사용되는 요소는 공통 영역이다. 공통 영역에 `main_` 등 특정 페이지 프리픽스를 붙이면 안 된다.

#### 일반 규칙
- **페이지 프리픽스 형식**: `{페이지}_{역할}` (예: `main_visual`, `main_about`)
- `sec_1`, `sec_2`, `section_01` 같은 범용 이름 사용 금지
- **snake_case** 전용 (`^[a-z0-9_]+$`)
- 공통 접미사 패턴: `_area`, `_wrap`, `_list`, `_item`, `_inner`, `_cont`
- 페이지 프리픽스 예시: `main_`, `company_`, `product_`, `support_`
- **공통 컴포넌트 타입 네이밍**: 여러 페이지에서 재사용되는 공통 UI는 `{타입}Type_{N}` 패턴 사용
  - 리스트: `listType_1`, `listType_2`, `listType_3` ...
  - 타이틀: `titleType_1`, `titleType_2`, `titleType_3` ...
- ul/ol/li/p처럼 태그 선택자에 의존한 스타일은 최소화하고, 필요 시 `section_ul`, `section_li`, `section_p` 형태의 명시적 클래스 스타일로 대체한다.
- 동일 구조 블록에 대해 클래스가 과도해지면 자식 선택자(`.section ul li`, `.section .title .value`)를 우선 사용한다.
- 동일 패턴일수록 클래스 수를 줄이고, `ul > li`처럼 강한 구조 의존은 필수일 때만 사용한다.

### CSS 선택자 계층 규칙 (필수 — 모든 요소에 개별 클래스 부여 금지)

> **모든 HTML 요소에 고유 클래스를 부여하는 것을 금지한다.**
> 컨테이너/섹션 클래스만 유지하고, 내부 요소는 **부모 클래스 + 태그/구조 선택자**로 스타일링한다.

#### 선택자 우선순위 (위에서 아래로 적용)

1. **부모 클래스 + 태그 선택자** — 컨테이너 내 해당 태그가 유일할 때
   - `.main_visual_content h2` / `.main_sec1_top h3` / `.main_sec2_card strong`
2. **부모 클래스 + 최소 의미 클래스** — 같은 태그가 복수이고 구분이 필요할 때
   - `.main_visual_content .en` / `.main_visual_content .sub`
3. **부모 클래스 + 구조 선택자** — 순서로 구분 가능한 동일 태그 요소
   - `.main_visual_slide1 .btns a:first-child` / `.main_visual_slide1 .btns a + a`
4. **개별 클래스** — 위 방법으로 불가능할 때만 최후 수단

#### 클래스 부여 기준

| 요소 유형 | 클래스 부여 | CSS 선택자 방식 |
|-----------|------------|----------------|
| 섹션/컨테이너/래퍼 | **필수** | `.main_sec1`, `.main_sec1_inner` |
| 컨테이너 내 유일한 h2/h3/p/strong/a | **금지** | `.parent h2`, `.parent strong` |
| 같은 태그 복수 (의미 구분 필요) | **최소 클래스** | `.parent .en`, `.parent .sub` |
| 같은 태그 복수 (순서 구분 가능) | **금지** | `.parent a:first-child`, `.parent a + a` |
| 아이콘/장식 span (빈 요소) | **허용** | `.check_icon` |
| 상태 구분 (slide1 vs slide2) | **필수** | `.main_visual_slide1`, `.main_visual_slide2` |

```css
/* correct - parent + tag selector */
.main_visual_content h2{font-size:4.0625rem; font-weight:700; color:#212121;}
.main_sec1_top h3{font-size:3.4375rem; font-weight:700; color:#212121;}
.main_sec2_card strong{font-size:2rem; font-weight:700; color:#ffffff;}
.main_sec3_btn_wrap a{display:inline-block; padding:15px 0; width:250px;}

/* correct - minimal class for disambiguation */
.main_visual_content .en{font-size:5.625rem; font-weight:800; color:#9fc8f7;}
.main_visual_content .sub{font-size:1.25rem; font-weight:700;}

/* correct - structural selector for buttons */
.main_visual_slide1 .btns a:first-child{padding:14px 48px; background:#ffffff;}
.main_visual_slide1 .btns a + a{padding:14px 48px; border:2px solid #1f7fed;}

/* wrong - individual class on every element */
.main_visual_title{font-size:4.0625rem;}
.main_visual_en{font-size:5.625rem;}
.main_visual_sub{font-size:1.25rem;}
.main_visual_desc{font-size:1.75rem;}
.btn_personal{padding:14px 48px;}
.btn_assoc{padding:14px 48px;}
```
- 예시:
  - 메인: `main_visual`, `main_about`, `main_portfolio`
  - 회사: `company_overview`, `company_history`
  - 제품: `product_list`, `product_detail`

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

### JavaScript
- 들여쓰기: 4 spaces
- 작은따옴표(`'`) 사용
- 세미콜론 사용
- `const` 우선, 필요시 `let` (var 금지)
- 화살표 함수 선호

---

## Breakpoints
- 기본값: **1400, 1200, 960, 768** (desktop-first, `max-width`)
- 선택 사용: **1024** (tablet 중간 대응 필요 시)
- 프로젝트별 커스텀 가능 (디자인 스펙 또는 기존 CSS에서 확인)

---

## 레이아웃
- 컨테이너: `.cont{margin:0 auto; max-width:var(--width); padding:0 var(--padding); width:100%;}`
- 내부 래퍼: `.cont` 클래스, 최대 1개
- **flexbox만 사용** (CSS Grid 금지)
- **flex 양쪽 영역 너비: 양쪽 모두 `%` 지정** — `flex:1` + `width:고정px` 조합 금지. 피그마에서 px로 추출되더라도 부모 대비 비율로 환산하여 `%`로 변환한다. (예: 720px + 400px / 부모 1200px → `width:60%` + `width:34%`)
- block 요소에 불필요한 `width: 100%` 금지
- DOM 최대 깊이: **5단계**
- 빈 div 금지, 익명 래퍼 금지

---

## Figma 노드 보존 규칙

### 텍스트 전문 사용 (CRITICAL — 필수)
- **Figma TEXT 노드의 `characters` 값을 HTML에 사용할 때, 반드시 전문(full text)을 사용한다**
- 미리보기/탐색용 스크립트에서 `[:100]`, `[:120]` 등으로 잘라서 출력한 텍스트를 HTML에 그대로 사용하는 것을 금지한다
- HTML 작성 전에 해당 TEXT 노드의 `characters`를 글자 수 제한 없이 재확인해야 한다
- 줄바꿈(`\n`)도 누락 없이 `<br>` 태그로 변환해야 한다
- 특히 긴 문단(소개글, 비전 설명 등)에서 잘림이 발생하기 쉬우므로 주의

### visible 체크 (CRITICAL — 추출 전 필수)
- **추출/코딩 전에 모든 노드의 `visible` 속성을 반드시 먼저 확인한다**
- `node.visible===false`인 노드는 **추출 대상에서 완전히 제외** — HTML/CSS에 포함하지 않음
- 부모 프레임 안에 숨겨진 자식 노드가 있을 수 있으므로, 프레임의 직계 자식(`children`)을 순회할 때 각 자식의 `visible` 값을 개별 체크해야 한다
- 트리 탐색 시 `visible===false`인 노드의 하위 자식은 탐색하지 않는다 (전체 서브트리 스킵)
- 피그마에서 눈 아이콘으로 숨긴 레이어 = `visible: false` — 디자이너가 의도적으로 제외한 요소

### 구분선/디바이더 노드
- 얇은 fill-only 프레임(divider/bar/separator)은 반드시 DOM 요소로 보존 — 삭제 금지
- 구분선은 HTML 요소(`background-color`)로 렌더링, CSS border로 대체 금지

### Border/Stroke 규칙
- CSS `border-*`는 Figma 노드에 실제 `strokes.visible===true`가 있을 때만 생성
- 레이아웃 패턴에서 border를 추론하는 것 금지
- `.card+.card{border-left:...}` 같은 인접 셀렉터 border 금지

---

## 파일 구조 (Basic 프로젝트)
```
project/
├── index.html
├── css/
│   ├── reset.css
│   └── common.css
├── js/
│   └── ui_common.js
└── img/
```

### Basic 프로젝트 기본 포함 파일
```html
<link rel="stylesheet" href="../css/common.css"/>
<script type="text/javascript" src="../js/jquery-3.7.1.min.js" charset="utf-8"></script>
<script type="text/javascript" src="../js/gsap.min.js"></script>
<script type="text/javascript" src="../js/ScrollTrigger.min.js"></script>
<script type="text/javascript" src="../js/slick.js" charset="utf-8"></script>
<script type="text/javascript" src="../js/ui_common.js" charset="utf-8"></script>
```

---

## 필수 규칙 (반드시 준수)

> **피그마 텍스트 그대로 추출**
> - 피그마에 기재된 텍스트를 그대로 사용
> - 추측해서 변경하거나 추가 금지
> - 오타가 있어도 그대로 추출 (수정 필요시 별도 안내)

### Figma TEXT 노드 매핑 규칙 (중요)
- 각 Figma TEXT 노드는 반드시 **독립된 HTML 요소로 1:1 매핑**
- 인접 TEXT 노드끼리 하나로 합치기 금지
- 동일 문구의 중복 노드/ID가 있어도 노드 단위 우선 정확 변환

### Figma 텍스트 줄바꿈 처리 (중요)
- 텍스트 노드의 `node.characters`에서 `\n`을 감지한다
- **단일 `\n`**: `<br>` 태그로 변환 — 절대 무시 금지
- **연속 `\n\n`**: `</p><p>` 또는 블록 분리로 변환
- 줄바꿈이 원본에 있으면 반드시 HTML 출력에 반영해야 한다 (`forbid_ignore`)

### Figma 텍스트 스타일 분할 (중요)
- 하나의 텍스트 노드 안에서 **아래 속성 중 1개라도 다른 구간이 있으면 반드시 `<span>`으로 분리**한다:
  - `fontSize`, `fontWeight`, `fontFamily`, `fills`(색상), `letterSpacing`, `lineHeightPx`
- **혼합 스타일을 하나의 스타일로 병합(flatten)하는 것을 금지**한다
- 분할된 span에는 인라인 `style` 대신 class를 부여한다

### Figma 텍스트 오버라이드 규칙 (중요)
- 텍스트 노드(`type: TEXT`)에서 `characterStyleOverrides`/`styleOverrideTable`가 존재하면 **반드시 반영**해야 함
- 추출 흐름:
  1) `node.characters`를 기준으로 문자를 순회
  2) 각 문자 인덱스별 `characterStyleOverrides` 값을 읽어 오버라이드 그룹(구간)으로 압축
  3) 구간별 스타일은 `node.style` + `node.fills`를 기본값으로 두고, `styleOverrideTable` 값으로 병합
  4) 오버라이드 값이 `0`인 구간은 기본 스타일 사용
  5) 오버라이드 스타일이 기본과 다르면 `<span>`으로 분할 출력
- `styleOverrideTable`에는 `style`, `fills`, `letterSpacing`, `lineHeightPx` 등 부분 스타일만 있을 수 있으므로 누락 값은 기본 스타일에서 상속
- 필수 병합 알고리즘:
  - `baseStyle = { ...node.style, fills: node.fills }`
  - `previousResolvedStyle = null`
  - 각 오버라이드 구간 처리:
    - overrideId가 `0`이거나 `styleOverrideTable[overrideId]`가 비어있으면 `resolvedStyle = baseStyle`
    - 나머지는 `resolvedStyle = { ...(previousResolvedStyle ?? baseStyle), ...(override.style ?? {}), ...(override.fills ? { fills: override.fills } : {}) }`
  - 출력 시 `resolved`를 기준으로 계산하고 `previousResolvedStyle = resolvedStyle`로 갱신
  - `fontSize`, `fontWeight`, `fontFamily`, `fills`의 누락값은 `previousResolvedStyle` 유지
- `lineHeightPx`는 CSS `line-height` **비율로 변환**하여 출력, `letterSpacing`은 `letter-spacing` **em 단위로 변환**하여 출력

#### Figma MCP 한계 및 REST API 직접 호출 (CRITICAL — 필수)

> **Figma MCP(`get_figma_data`)는 `characterStyleOverrides`/`styleOverrideTable`을 반환하지 않는다.**
> MCP는 텍스트 노드의 base style(`textStyle`)만 제공하므로, 텍스트 내부의 부분 굵기/색상/크기 변경을 감지할 수 없다.

- **텍스트 내부 스타일 오버라이드 확인이 필요할 때**, 반드시 Figma REST API를 직접 호출한다:
  ```bash
  curl -s -H "X-Figma-Token: {TOKEN}" \
    "https://api.figma.com/v1/files/{FILE_KEY}/nodes?ids={NODE_ID}" \
    | python3 -c "
  import json,sys
  data=json.load(sys.stdin)
  node=data['nodes']['{NODE_ID}']['document']
  chars=node.get('characters','')
  overrides=node.get('characterStyleOverrides',[])
  table=node.get('styleOverrideTable',{})
  print(f'text: {chars}')
  print(f'overrides: {overrides}')
  for k,v in table.items():
      fw=v.get('fontWeight','없음')
      fills=v.get('fills',None)
      color='없음'
      if fills:
          c=fills[0].get('color',{})
          r,g,b=int(c.get('r',0)*255),int(c.get('g',0)*255),int(c.get('b',0)*255)
          color=f'#{r:02x}{g:02x}{b:02x}'
      print(f'  override {k}: weight={fw}, color={color}')
  "
  ```
- **확인 시점**: 카드/배지/강조 텍스트 등 부분 스타일이 의심되는 TEXT 노드를 구현할 때
- `characterStyleOverrides` 배열의 인덱스 = `characters` 문자열의 인덱스. 오버라이드 ID로 `styleOverrideTable`에서 스타일을 조회한다
- 오버라이드에 `fontWeight`, `fills`(색상), `fontSize` 등이 포함될 수 있으므로 해당 구간에 `<strong>`, `<span>` + CSS를 적용한다

### Figma 레이아웃 매핑 규칙
- `layoutMode: VERTICAL` → `flex-direction: column`
- `layoutMode: HORIZONTAL` → `flex-direction: row`
- `itemSpacing` → CSS `gap` 반영 필수
- `padding*` → CSS `padding` 반영 필수
- `counterAxisAlignItems` → `align-items`
- `primaryAxisAlignItems` → `justify-content`
- 레이아웃 정보 누락 금지

### Figma MCP 기반 속성 해석 규칙 (CRITICAL — 필수)

> **Figma MCP로 섹션별 데이터를 가져와 AI가 직접 해석한다.**
> 섹션 단위 MCP 호출은 컨텍스트가 작아 AI가 정확하게 해석할 수 있다.

#### 왜 MCP 섹션별 호출인가
- 기존 방식(전체 JSON 파일 → LLM 해석)은 수만 줄 JSON에서 추측값을 넣는 문제가 있었음
- MCP는 노드 단위로 데이터를 반환 → 섹션별 호출 시 컨텍스트가 관리 가능한 크기
- 커서+오푸스 방식(섹션별 MCP → AI 직접 해석)이 가장 높은 품질을 보임

#### 필수 도구

| 도구 | 용도 |
|------|------|
| **Figma MCP** (`get_figma_data`) | 섹션별 노드 데이터 조회 (AI가 직접 해석) |
| **Figma MCP** (`download_figma_images`) | 이미지/아이콘 다운로드 |
| **validate-semantic.py** (`D:\dev-base\tools\validate-semantic.py`) | HTML/CSS 규칙 검증 |
| **figma-extract.py** (`D:\dev-base\tools\figma-extract.py`) | (선택) MCP 응답 → mapping.json 생성 (정밀 값 대조용) |

#### 필수 워크플로우

1. **섹션 구조 파악**: Figma MCP로 프레임 조회 (depth 얕게)
   - 최상위 자식 노드(섹션) 목록과 nodeId 확인

2. **섹션별 구현**: 각 섹션마다 Figma MCP 호출 → AI 직접 해석 → HTML/CSS 생성
   - Figma 속성 → CSS 변환 규칙 준수 (layoutMode→flex-direction, itemSpacing→gap 등)
   - 전체 페이지를 한번에 처리하지 않음 — **반드시 섹션 단위**

3. **검증**: 완성된 HTML/CSS를 validate-semantic.py로 규칙 검증
   ```bash
   # TODO: validator 확장 필요 (REQ-005+) — --type basic|landing 미지원
   python3 D:/dev-base/tools/validate-semantic.py --html <output.html> --css <output.css>
   ```

4. **(선택) 정밀 값 대조**: MCP 응답을 figma-extract.py에 파이프하여 mapping.json 생성 → 값 수준 대조
   ```bash
   echo '<mcp_response>' | python3 D:/dev-base/tools/figma-extract.py --stdin --name "<section>" --output ./extracted/ --json-only
   # TODO: validator 확장 필요 (REQ-005+) — --mapping / --type 미지원 (현재는 일반 검증만 실행)
   python3 D:/dev-base/tools/validate-semantic.py --html <output.html> --css <output.css>
   ```

#### Figma px → CSS 변환 원칙
- Figma의 고정 width/height를 CSS에 그대로 하드코딩하지 않는다
- **고정 px 허용**: padding, margin, gap, border-width, border-radius, font-size
- **고정 px 금지**: 섹션/컨테이너의 width, height — flex/비율 기반으로 변환
  - Figma에서 형제 요소의 width 합 = 부모 width - gap이면, 비율로 계산
  - `layoutSizingHorizontal: FILL` → CSS `flex: 1`
  - `layoutSizingHorizontal: FIXED` + 형제가 FILL → CSS width 비율 또는 flex-basis
- **예외**: 카드, 아이콘, 버튼 등 반복/고정 크기 요소는 고정 px 허용 (min-width 포함)

#### MCP 노드 구조 → HTML 순서 규칙
- MCP children 배열 순서 = HTML 형제 요소 순서 (임의 변경 금지)
- MCP에서 wrapper frame이 있으면 HTML에서도 wrapper div 유지
- 구조를 추측하지 않고, MCP 데이터에 명시된 부모-자식 관계만 반영

### 텍스트 태그 자동 판정 규칙 (p 태그 최소화 — 필수)

> **`<p>` 태그 남용을 금지한다.** 기본 태그는 `<span>` 또는 헤딩(`<h2>`, `<h3>` 등)이며, `<p>`는 아래 3가지 조건 중 **하나 이상 충족할 때만** 허용된다.

#### p 태그 허용 조건 (하나라도 충족해야 함)
1. `characters`에 `\n`이 포함되어 실제 줄바꿈이 있는 경우 (또는 `<br>` 포함 문장)
2. 텍스트 길이가 **95자 초과**이고 문단형 내용인 경우
3. 문장형 마침표(`.`)/종결어(`~다`, `~요`)가 반복되는 서술형 텍스트

#### p 태그 금지 대상 (위 조건 미충족)
- 브랜드명, 슬로건, 키워드, CTA 문구 → `<span>`
- 카드 제목, 라벨, 짧은 설명(95자 이하) → `<span>` 또는 `<strong>`
- 숫자/통계 데이터 → `<span>` 또는 `<strong>`
- 섹션 부제목 → `<span>`

```html
<!-- correct -->
<span>Hospital Treatment is The Fastest</span>
<span>당신의 가장 완벽한 건강 플랜 B</span>
<h2>프리미엄 검진 혜택으로 조기 발견</h2>
<p>비용 부담은 덜어내고 치료 속도를 높이는<br>올케어플랜 B와 함께라면 건강 관리가 쉬워집니다.</p>
<strong>ROL 1,000%</strong>

<!-- wrong - short labels as p -->
<p>Hospital Treatment is The Fastest</p>
<p>당신의 가장 완벽한 건강 플랜 B</p>
<p>ROL 1,000%</p>
<p>지금 바로 건강 리스크 관리를 시작하세요</p>
```

### 레이아웃·타입 디테일 보정 규칙
- block 요소에 불필요한 `width: 100%`를 기본으로 넣지 않는다.
- Figma 고정 폭이 큰 컨테이너는 `max-width` + `margin: 0 auto` 중심으로 반응형 기준을 맞춘다.
- `line-height`는 반드시 `font-size` 대비 비율(`1.2`, `1.45`)로 기록한다.
- 배경색/보더가 명시되지 않은 레이어는 배경 속성 생략을 우선한다.

## 레이아웃 추출 보정 규칙 (좌표 기반)

- Figma에서 동일 부모 내 두 개 이상의 박스가 서로 같은 줄(`y`)에 있고, 동일하거나 유사한 높이를 가질 때는 자동 레이아웃 플래그가 없더라도 실제로는 가로 정렬(1 row)일 가능성이 높다.
- 같은 `y`를 가지는 블록이 2개라면 기본값으로 세로 스택을 배제하고 `inline-flex` 행 정렬을 우선한다.

---

## 주의사항
- 요청하지 않은 기능 추가 금지
- 허락 없이 리팩토링 금지
- 최소한의 변경만
- 보안 이슈 주의 (XSS 등)

---

## 서브페이지 공통 규칙

### 서브페이지 클래스 구조 (CRITICAL — 필수)

> **서브페이지는 공통 영역과 고유 영역을 명확히 분리한다.**
> 공통 영역은 모든 서브페이지에서 동일한 클래스를 사용하고, 고유 영역만 페이지 프리픽스를 적용한다.

#### 공통 클래스 (모든 서브페이지 공유)

| 클래스 | 용도 |
|--------|------|
| `.sub_wrap` | 서브페이지 전체 래퍼 |
| `.sub_visual` | 서브비주얼 영역 (배경이미지 + 타이틀) |
| `.sub_cont` | 서브 콘텐츠 영역 래퍼 |
| `.navi` | 브레드크럼 네비게이션 |
| `.lnb` | 좌측/상단 로컬 네비게이션 (2depth 메뉴) |
| `.page_title` | 페이지 타이틀 영역 |
| `.tab_menu`, `.tab_list` | 탭 메뉴 |
| `.search_bar`, `.search_input`, `.select_box` | 검색 영역 |
| `.pagination`, `.btn_page`, `.num` | 페이지네이션 |
| `.list_bottom`, `.btn_group` | 하단 버튼 영역 |
| `.btn_back`, `.btn_outline` | 공통 버튼 |
| `.info_table` | 정보 테이블 (dl/dt/dd) |

#### 페이지 고유 영역 (프리픽스 적용)

- 해당 페이지에서만 사용되는 콘텐츠 영역에만 `{page}_` 프리픽스 적용
- 프리픽스는 파일명(영문 snake_case)과 동일한 `{name}_` 패턴 사용
- 예: `.greeting_section`, `.notice_list`, `.gallery_card`

#### 서브페이지 간 공통 패턴

- 여러 서브페이지에서 동일한 레이아웃/구조가 반복되면 **공통 클래스로 처리**
- 예: 리스트형 페이지의 `.list_item`, `.list_row` / 상세형 페이지의 `.view_area`, `.view_detail`
- 개별 페이지 프리픽스를 붙이지 않고 공통으로 재사용

### 새 서브페이지 생성 시
1. 같은 프로젝트에 기존 서브페이지가 있으면 공통 컴포넌트(header/footer/sub_visual/navi/lnb/page_title)를 **그대로 복사**
2. 메뉴 active 상태, 브레드크럼/lnb 텍스트만 해당 페이지에 맞게 변경
3. `body` 태그에 페이지 프리픽스 클래스 `page_{name}`을 **반드시 부여** (파일명과 일치)
4. CSS는 기존 common.css **하단에 추가** (기존 코드 수정 안 함)
5. 기존 프로젝트가 없으면 `templates/sub_list.html` 또는 `templates/sub_view.html` 골격 사용

### 서브페이지 작업 워크플로우 (필수)

> **페이지 1개 완성 후 반드시 PM 체크를 거쳐야 다음 페이지 진행 가능**

```
1. 피그마에서 해당 서브페이지 프레임 속성 추출
2. HTML/CSS 코드 작성
3. PM이 코드 검수 (피그마 대조 + 규칙 준수 확인)
4. 불일치/위반 항목 교정
5. PM 승인 후 다음 페이지로 진행
```

- 한 번에 여러 페이지를 동시 작업하지 않음
- PM 체크 없이 다음 페이지로 넘어가는 것 금지

### 서브페이지 CSS 네이밍 패턴
- 리스트 섹션: `.{page}_section` (고유) 또는 `.list_section` (공통 패턴)
- 리스트: `.{page}_list`, `.list_item`, `.list_row`
- 상세 섹션: `.{page}_view` 또는 `.view_area` (공통 패턴)
- 정보 영역: `.{page}_info_area`
- 상세 내용: `.{page}_detail`

### 서브페이지 타입별 상세 규칙
- Basic 프로젝트: `basic.md` 참조
- Landing 프로젝트: `landing.md` 참조

---

## 참고
- Basic 프로젝트 상세 규칙은 `basic.md` 참조
- Landing 프로젝트 상세 규칙은 `landing.md` 참조

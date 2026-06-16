# Claude 규칙 (이 프로젝트)

> 이 파일은 `init-project.py` 로 신규 프로젝트에 배포되는 템플릿입니다.
> dev-base 자체의 규칙은 `D:/dev-base/CLAUDE.md` 참조.

## 기본
- 응답 언어: 한국어
- 코드 주석: 영어만
- `D:/dev-base/rules/common.md` 규칙 우선 적용

---

## 절대 금지 (CRITICAL)

### 도구 / 스크립트
- `generate.py` / `json-to-html.py` 같은 자동 코드 생성 스크립트 작성 금지
- 자동 재시도 / auto-repair 루프 사용 금지
- 폐기 도구 참조 금지: `repair-from-violations`, `structural-diff`, `compare-css`, `check-rules-drift`, `build-prompts`, `brief-checksum`, `run-pipeline`, `split-sections`, `assemble`, `migrate-spec`, `post-impl-verify`

### 룰 / 해석
- `POLICY-1` (VERTICAL frame margin-bottom 강제) — 모던 CSS `gap` 과 충돌, 적용 금지
- Figma 노드명 (`header_b`, `footer_bk`, `sec_1` 등) 을 HTML 클래스에 박기
- `site_`, `g_`, `common_` 같은 추측 prefix
- 한글 / `,` / `&` / `.` / 공백 등 특수문자 클래스명
- `<body>` 태그에 class 속성 추가 (body는 공통 영역, 페이지별 class 금지)
- 공통 영역(header, footer, container, gnb, logo, utils, sns, copyright)에 페이지 prefix 붙이기 (`.index_header` ✗, `.main_footer` ✗ → `.header`, `.footer`)

### 검증 / 보고
- 도구 단위 테스트 통과 = 파이프라인 통과로 간주
- 외주 AI 자가 보고 신뢰 후 사용자 전달 (실제 output grep 검증 필수)

---

## HTML 클래스 규칙

### 공통 영역 (prefix 없음)
다른 페이지에서 재사용하는 영역:

| 영역 | 클래스명 |
|------|---------|
| `.header`, `.footer` | wrapper |
| `.logo`, `.gnb`, `.utils`, `.sns`, `.copyright` | 공통 컴포넌트 |
| `.icon_login`, `.icon_search`, `.icon_menu` | 유틸 아이콘 |
| `.sns_talk`, `.sns_youtube`, `.sns_instagram`, `.sns_facebook` | 소셜 아이콘 |

#### 공통 영역 내부 자식 클래스도 부모 스코핑 강제
공통 영역(`.header`, `.footer`) 내부의 자식 클래스도 반드시 부모 셀렉터와 함께 선언한다. `.logo`, `.gnb`, `.logo_txt` 등은 header와 footer 양쪽에서 사용될 수 있으므로 단독 선언하면 충돌한다.

| ❌ 잘못된 사용 (금지) | ✅ 올바른 사용 |
|----------------------|--------------|
| `.logo{...}` | `.header .logo{...}` |
| `.logo a{...}` | `.header .logo a{...}` |
| `.logo .img_area{...}` | `.header .logo .img_area{...}` |
| `.logo_txt{...}` | `.header .logo_txt{...}` |
| `.logo_txt strong{...}` | `.header .logo_txt strong{...}` |
| `.gnb{...}` | `.header .gnb{...}` |
| `.gnb a{...}` | `.header .gnb a{...}` |
| `.utils{...}` | `.header .utils{...}` |
| `.copyright{...}` | `.footer .copyright{...}` |
| `.sns{...}` | `.footer .sns{...}` |

#### ⚠️ 전역 클래스는 부모 스코핑 금지 (단독 선언 강제)
아래 클래스는 어디에서든 재사용되는 전역 클래스이므로 `body`, `html` 등 어떤 부모도 붙이지 않고 **단독 선언**한다:

| 단독 선언 클래스 | 역할 |
|-----------------|------|
| `.header` | 헤더 컨테이너 |
| `.footer` | 푸터 컨테이너 |
| `.cont` | 섹션 내부 너비 제한 |
| `.img_area` | 이미지 래퍼 |

| ❌ 금지 (body/html 부모 붙이기) | ✅ 올바른 사용 |
|-------------------------------|--------------|
| `body .cont{...}` | `.cont{...}` |
| `body .header{...}` | `.header{...}` |
| `body .footer{...}` | `.footer{...}` |
| `body .img_area{...}` | `.img_area{...}` |

### 페이지 전용 영역 (페이지 prefix 강제)

> **⚠️ 공통 영역(header, footer, gnb, logo, utils, sns, copyright, container)은 어떤 페이지에 있어도 prefix 절대 금지.**
> 이 규칙은 페이지 prefix 규칙보다 항상 우선한다.

페이지 단위 **콘텐츠** 영역에만 prefix 적용:

| 페이지 파일 | prefix | 예시 |
|------------|--------|------|
| `index.html` | `main_` | `.main_mv`, `.main_intro` |
| `greeting.html` | `greeting_` | `.greeting_title` |
| `products.html` | `products_` | `.products_list` |

### 자식 클래스 네이밍 (부모 스코핑 방식)
페이지 prefix는 **섹션 컨테이너에만** 부여. 자식은 **짧은 역할명**, CSS는 `.부모 .자식` 스코핑.

| ❌ 잘못된 사용 (금지) | ✅ 올바른 사용 |
|----------------------|--------------|
| `.main_intro_card` | `.main_intro .card` |
| `.main_intro_card_icon` | `.main_intro .card img` |
| `.main_section_title_area` | `.main_section .title_area` |

#### ⚠️ 공통 영역 prefix 금지 — 자주 발생하는 실수

| ❌ 잘못된 사용 (금지) | ✅ 올바른 사용 |
|----------------------|--------------|
| `.index_header` | `.header` |
| `.index_footer` | `.footer` |
| `.main_container` | `.container` |
| `.sub_logo` | `.logo` |

### 페이지 섹션 내부 클래스는 전부 부모 스코핑 강제
페이지 prefix 섹션(`.main_visual`, `.main_news` 등) 내부의 **모든 자식 클래스**는 반드시 부모 섹션 셀렉터와 함께 선언한다. "범용적 이름인지" 판단하지 않는다 — 섹션 내부이면 무조건 부모를 붙인다.

| ❌ 잘못된 사용 (금지) | ✅ 올바른 사용 |
|----------------------|--------------|
| `.board_list{...}` | `.main_news .board_list{...}` |
| `.news_arrow{...}` | `.main_news .news_arrow{...}` |
| `.news_tab{...}` | `.main_news .news_tab{...}` |
| `.sec_head{...}` | `.main_news .sec_head{...}` |
| `.calendar_area{...}` | `.main_schedule .calendar_area{...}` |
| `.schedule_list{...}` | `.main_schedule .schedule_list{...}` |
| `.popup_box{...}` | `.main_schedule .popup_box{...}` |
| `.gallery_list{...}` | `.main_gallery .gallery_list{...}` |
| `.gallery_util{...}` | `.main_gallery .gallery_util{...}` |

부모 스코핑 예외 (단독 선언 대상): 페이지 prefix가 붙은 섹션 컨테이너 자체(`.main_news`, `.main_schedule` 등)와 전역 공통 클래스(`.header`, `.footer`, `.cont`, `.img_area`)는 `body`/`html` 등 어떤 부모도 붙이지 않고 단독 선언한다.

### 시멘틱 마크업 강제
```html
<nav class="gnb">
    <ul>
        <li><a href="#"><span>회사소개</span></a></li>
        <li><a href="#"><span>제품소개</span></a></li>
    </ul>
</nav>
```

### 장식용 빈 태그 금지
장식 목적의 빈 `<span>`, `<div>`, `<i>` 태그 사용 금지. CSS `::before`/`::after` 가상 선택자로 대체.
- 적용 대상: 텍스트 콘텐츠가 없고 시각적 장식(배경, 선, 도형)만을 위한 빈 태그
- 예외: 아이콘 폰트 `<i>`, 빈 셀 `<td>`, JavaScript로 동적 조작이 필요한 요소

나쁨: `<span class="visual_bg" aria-hidden="true"></span>`
좋음: `.index_visual::before{content:""; position:absolute; inset:0; background:url("../img/mv_bg.jpg") center/cover;}`

### HTML 코드 포맷팅
- 들여쓰기: 4-space
- **줄바꿈 기준은 "자식 태그(child element)"이다. "속성(attribute)" 줄바꿈은 금지.**
- **속성 줄바꿈 금지**: `<meta>`, `<link>`, `<script>`, `<img>` 등 태그의 속성이 길어도 한 줄로 작성. Prettier 스타일의 속성별 줄바꿈 금지
- **인라인 허용 조건**: 자식 태그가 1개 이하이고 전체 줄 길이가 80자 이하인 경우에만 한 줄 허용
- **줄바꿈 강제 조건**: 자식 태그가 2개 이상이거나 줄 길이가 80자를 초과하면 반드시 줄바꿈
- 들여쓰기는 부모 기준 4-space 증가

나쁨:
```html
<h1 class="logo"><a href="index.html"><span class="img_area"><img src="../img/logo.png" alt="로고"></span><span class="logo_txt"><strong>회사명</strong><em>COMPANY</em></span></a></h1>
```
좋음:
```html
<h1 class="logo">
    <a href="index.html">
        <span class="img_area"><img src="../img/logo.png" alt="로고"></span>
        <span class="logo_txt">
            <strong>회사명</strong>
            <em>COMPANY</em>
        </span>
    </a>
</h1>
```

### CSS 포맷
- CSS 셀렉터: 한 줄 형식 (콤마 셀렉터 3개 이상이면 셀렉터만 줄바꿈)

---

## CSS 규칙

### 금지
- `display: grid` (flexbox 전용)
- `rgb()` / `hsl()` 투명도 없이 (hex 전용)
- `letter-spacing` px (em 전용)
- `font-size` rem (landing 은 px 전용)
- padding/margin 100px 미만 clamp
- `calc()` / `vw` 단독 (clamp 내부만 허용)
- `border-radius: 999px`
- 범용 클래스명 (`sec_1`, `page_1`)
- `background-size` 선언 (`--download-assets` 가 1:1 디자인 사이즈로 추출하므로 불필요. spec.json 의 `scaleMode`/`scalingFactor` 는 Figma 내부값이며 CSS 변환 금지)

### 선호
- **색상**: hex (`#fff`, `#212121`), 투명도 필요 시만 rgba
- **font-size**: landing 은 모두 `px`
  - 이유: landing 은 고정 디자인 사이즈로 pixel-perfect 구현이 목표이므로 상대 단위(rem)를 사용하면 base size 변동 시 전체 레이아웃이 어긋남
  - html/body font-size 선언: `html,body{font-size:16px;}` 고정. clamp()/vw/rem 금지
  - 반응형은 미디어쿼리에서 각 요소의 px 값을 직접 변경
  - basic 은 PC rem + 모바일 px 허용
- **letter-spacing**: em (`-0.02em`)
- **line-height**: 무단위 비율 (`1.2`, `1.45`)
- **padding/margin/gap**: 고정 px (≥100px 만 clamp)
- **border-radius**: 원형 `50%`, pill `2em`
- **레이아웃**: flexbox 전용
- **미디어쿼리**: **3대 영역(header / main 페이지 콘텐츠 / footer)** 단위로 기본 CSS 바로 아래에 해당 영역의 breakpoint를 작성한다. main 내부 개별 섹션(.main_visual, .main_quick 등)마다 @media를 쪼개지 않고, main 섹션 전체 base CSS를 먼저 작성한 뒤 main 전체의 @media를 breakpoint별로 모아서 작성한다. 파일 하단에 header/main/footer 전체의 미디어쿼리를 몰아넣는 구조도 금지.

### :root 변수 (landing 필수)
```css
:root {
    --width:1480px;        /* Figma inner content + 40 */
    --padding:20px;
    --header_h:100px;
    --point-color-1:#438eca;
}
```

### .cont 패턴
`.cont`는 **common.css에서 전역으로 선언**한다 (스코핑 래퍼 불필요).
섹션 CSS에서 `.cont`를 재선언하지 않는다.
- `.index_page .cont` 같은 페이지 래퍼 스코핑 금지 — `.cont`는 어떤 섹션 안에서든 동일하게 동작
- 페이지별 `.cont` 커스텀이 필요하면 `.main_intro .cont{max-width:1200px;}` 식으로 섹션 레벨에서 오버라이드

### 이미지 래퍼 (img_area)
모든 `<img>` 태그는 `.img_area` 래퍼 안에 배치한다.
- 예외 없음: 로고, 파트너 로고, 아이콘, 갤러리 모두 포함
- CSS 배경 이미지(`background-image`)만 제외
`.img_area` 는 시맨틱 래퍼 클래스다. common.css 에 기본 CSS 는 두지 않으며, 필요한 스타일은 섹션/전역에서 직접 정의한다(선언 시 `body`/`html` 부모 없이 단독 선언 — `global_class_standalone`).
**img 및 .img_area에 고정 width/height 금지** — 로고 img는 어떤 크기 제어도 금지 (img width/height, 부모 flex-basis/max-width 모두 금지 — 원본 사이즈 그대로 출력). 일반 이미지는 크기가 필요하면 부모 컨테이너에서 제어한다.
**`background-size` 금지** — `--download-assets` 가 이미지를 Figma 디자인 1:1 크기로 다운로드하므로 `background-size` 가 불필요하다. spec.json 의 `scaleMode`(`FILL`/`FIT`/`CROP`), `scalingFactor`, `imageTransform` 은 Figma 내부 렌더링 파라미터이며, CSS `background-size` 로 변환하면 안 된다.
```html
<span class="img_area"><img src="./img/logo.png" alt="..."></span>
```

---

## Figma → 퍼블리싱 워크플로우 (7 Step)

### Step 1: spec.json 추출
```bash
python3 D:/dev-base/tools/figma-section-spec.py \
  --file-key {KEY} --node-id {SECTION_ID} --output extracted/
```

### Step 2: PNG 다운로드
```bash
FIGMA_TOKEN="figd_..." python3 D:/dev-base/tools/figma-png-download.py \
  --file-key {KEY} --node-ids "{MAIN},{S1},..." \
  --output .gran-maestro/figma-png/ --include-fills
```

### Step 3: 자산 복사
```bash
python3 D:/dev-base/tools/asset-copy.py --extracted extracted/ --img img/
```

### Step 4: OMX 로 HTML/CSS 코드 추출
OMX (oh-my-codex) 를 사용하여 코드를 추출한다. 입력:
- `extracted/{section}_spec.json` (정확한 텍스트/폰트/색상/패딩)
- `.gran-maestro/figma-png/{section}.png` (시각 참조)
- 이 CLAUDE.md + `D:/dev-base/rules/common.md` (룰 강제)

코드 추출 시 필수 준수:
- spec.json 의 텍스트는 byte-exact 사용 (NBSP, `\n`, 연속 공백 보존)
- PNG 시각 참조로 구조 결정
- 공통 영역 prefix 없음 / 페이지 prefix 강제
- 자체 검증 결과를 raw 출력 그대로 보고 (거짓 보고 금지)

### Step 5: PM 검증
```bash
python3 D:/dev-base/tools/pm-verify.py \
  --spec-dir extracted/ --html index.html \
  --css css/common.css --img img/ --profile {basic|landing}
```
exit 0 이어야 완료 보고 허용.

### Step 6: Playwright 시각 비교
1920px 렌더 → Figma PNG 와 사용자 비교 → 자연어 피드백 → 수정 → Step 5 또는 Step 4 복귀

---

## 코드 추출 에이전트

HTML/CSS 코드 추출은 **OMX (oh-my-codex)** 를 기본 사용한다.
OMX 는 Codex CLI 기반 멀티 에이전트 오케스트레이션 레이어로, AGENTS.md 와 프로젝트 룰을 자동 로드한다.

---

## 텍스트 태그 자동 판정

- 기본: `<span>` 또는 헤딩 (`<h2>`, `<h3>`)
- `<p>` 사용 조건 (셋 중 하나):
  1. `\n` 포함 (2줄 이상 서술)
  2. 95자 초과
  3. 문장형 마침표 반복
- 짧은 라벨 (COPYRIGHT 한 줄 등): `<small>` 또는 `<span>`

---

## 텍스트 부분 색상 처리 (CRITICAL)

spec.json의 `text_nodes[]`에 `"has_mixed_styles": true`가 있으면 해당 텍스트 내부에 색상/폰트가 다른 구간이 존재한다.
이 경우 반드시 `character_segments` 배열을 읽고, 다른 스타일 구간을 `<span>`으로 분리해야 한다.

### 금지
- `has_mixed_styles: true`인데 전체를 단일 색상으로 출력
- `character_segments`를 무시하고 노드 레벨 `color` 필드만 참조

### 판정 규칙
1. `has_mixed_styles: false` 또는 없음 → 단일 스타일, span 분리 불필요
2. `has_mixed_styles: true` → `character_segments`에서 색상/weight/size 차이 확인, 구간별 `<span>` 분리
3. 기본 색상과 동일 구간은 span 없이, 다른 구간만 `<span>` + 해당 스타일 지정

---

## 하지 말 것
- 요청하지 않은 개선 추가
- 과도한 주석 / 한국어 주석
- 장황한 설명
- CSS 셀렉터 여러 줄 펼치기
- 모든 요소에 개별 클래스 부여

## 선호
- 간결한 응답
- 실용적 솔루션
- 최소한의 변경
- pm-verify 통과 후만 완료 보고

---

## 참조

- 공통 CSS/HTML 룰: `D:/dev-base/rules/common.md`
- Landing 추가 룰: `D:/dev-base/rules/landing.md`
- Basic 추가 룰: `D:/dev-base/rules/basic.md`

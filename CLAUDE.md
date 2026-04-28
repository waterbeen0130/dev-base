# Claude 규칙 (dev-base)

Claude AI 어시스턴트 전용 규칙. Figma → 퍼블리싱 새 워크플로우 기준으로 재작성 (AGI-002).

---

## 기본
- `rules/common.md` 규칙 우선 적용
- 응답 언어: 한국어
- 코드 주석: 영어만

---

## 프로젝트 초기 설정 (CRITICAL — 새 프로젝트 시작 시 필수)

### 권한 자동 허용 설정
새 프로젝트 시작 시 `{project}/.claude/settings.local.json` 을 생성하여 모든 도구 접근을 자동 허용한다.

```json
// 템플릿: D:\dev-base\rules\claude-settings-template.json
{
  "permissions": {
    "allow": [
      "Read", "Write", "Edit", "Glob", "Grep",
      "Bash(*)", "Task", "WebFetch", "WebSearch",
      "NotebookEdit",
      "mcp__plugin_playwright_playwright__*",
      "mcp__plugin_context7_context7__*",
      "mcp__figma__*"
    ]
  }
}
```

새 프로젝트 초기화는 반드시 `tools/init-project.py` 를 사용한다 (DOD-005 이후).

---

## 절대 금지 (CRITICAL)

아래 패턴은 어떤 경우에도 사용하지 않는다. 발견 시 즉시 수정.

### 도구 / 스크립트
- `generate.py` / `json-to-html.py` 같은 자동 코드 생성 스크립트 작성
- `post-impl-verify.py` 의 `--converge` 자동 재시도 루프 사용 (해당 도구 자체가 이미 폐기됨)
- `repair-from-violations.py` 같은 자동 수리 (폐기)
- `structural-diff.py` / `compare-css.py` / `check-rules-drift.py` / `build-prompts.py` / `brief-checksum.py` / `run-pipeline.py` / `split-sections.py` / `assemble.py` / `migrate-spec-v1-to-v2.py` (모두 폐기, 참조 금지)

### 룰 / 해석
- `POLICY-1` (VERTICAL frame margin-bottom 강제) — 모던 CSS `gap` 과 충돌, 적용 금지
- Figma 노드명 (`header_b`, `footer_bk`, `sec_1`, `_v2` 등) 을 HTML 클래스에 박기
- `site_`, `g_`, `common_` 같은 추측 prefix 사용
- 한글 / `,` / `&` / `.` / 공백 등 특수문자 클래스명
- `<body>` 태그에 class 속성 추가 (body는 공통 영역, 페이지별 class 금지)

### 검증 / 보고
- 도구 단위 테스트 통과 = 파이프라인 통과로 간주
- 외주 AI 자가 보고 신뢰 후 사용자 전달 (실제 output grep 검증 필수)
- "이미 안다" 판단으로 룰 파일 안 읽기

---

## HTML 클래스 규칙 (CRITICAL)

### 공통 영역 (prefix 없음)
다른 페이지에서도 재사용하는 영역은 prefix 없이 시멘틱 이름만 사용:

| 영역 | 클래스명 | 예시 |
|------|---------|------|
| 헤더 wrapper | `.header` | `<header class="header">` |
| 푸터 wrapper | `.footer` | `<footer class="footer">` |
| 로고 | `.logo` | header/footer 둘 다 가능 |
| 글로벌 네비 | `.gnb` | header/footer 둘 다 가능 |
| 유틸 (로그인/검색) | `.utils`, `.icon_login`, `.icon_search`, `.icon_menu` | — |
| 소셜 | `.sns`, `.sns_talk`, `.sns_youtube` | — |
| 카피라이트 | `.copyright` | — |

스코핑으로 충돌 방지: `.header .logo {...}`, `.footer .logo {...}`, `.header .gnb a {...}`

### 페이지 전용 영역 (페이지 prefix 강제)
페이지 단위 영역은 반드시 `{페이지}_{역할}` 패턴:

| 페이지 | prefix | 예시 |
|--------|--------|------|
| `index.html` | `main_` 또는 `index_` | `.main_mv`, `.main_intro`, `.main_product` |
| `greeting.html` | `greeting_` | `.greeting_title`, `.greeting_desc` |
| `products.html` | `products_` | `.products_list`, `.products_card` |
| `about.html` | `about_` | `.about_section` |

자식 클래스에도 prefix 일관: `.main_intro_card`, `.main_intro_card_icon`

### 모든 요소에 개별 클래스 부여 금지
컨테이너 클래스만 유지, 내부는 부모+태그 selector:
- 좋음: `.main_intro .intro_card h3`, `.header .gnb a`
- 나쁨: 모든 `<h3>` 에 개별 class 박기

### 시멘틱 마크업 강제
리스트형 반복 요소 (메뉴, 카드, 소셜) 는 `<ul><li>` 구조:
```html
<nav class="gnb">
    <ul>
        <li><a href="#"><span>회사소개</span></a></li>
        <li><a href="#"><span>제품소개</span></a></li>
    </ul>
</nav>
```

### HTML 파일 작성 규칙
- **들여쓰기**: 4-space
- **메인 페이지**: `index.html` 고정
- **서브 페이지**: 의미 있는 영문명 (snake_case), flat 배치
- `page_1.html`, `sub_01.html` 같은 의미 없는 파일명 금지

---

## CSS 규칙 (CRITICAL)

### 금지
- `display: grid` (CSS Grid 금지 — flexbox 전용)
- `rgb()` / `hsl()` 투명도 없이 사용 (hex 전용, 투명도 필요 시만 `rgba()`)
- `letter-spacing` 에 `px` 단위 (em 전용)
- `font-size` 에 `rem` (landing 프로젝트, basic 은 PC rem + 모바일 px 허용)
- `padding` / `margin` 100px 미만 `clamp()` 사용
- `calc()` / `vw` 단독 사용 (`clamp()` 내부에서만 허용)
- `border-radius: 999px` (원형은 `50%`, pill 은 `2em`)
- `sec_1`, `sec_2` 같은 범용 클래스명
- CSS 셀렉터를 여러 줄로 펼치기 (각 규칙은 한 줄, 콤마 셀렉터 3개 이상이면 셀렉터만 줄바꿈 허용)
- 미디어쿼리 내부 들여쓰기
- 한국어 CSS 주석 (영어만)

### 선호
- **색상**: hex (`#fff`, `#212121`, `#438eca`), 투명도 필요 시만 `rgba()`
- **font-size**: landing 은 모두 `px`, basic 은 PC `rem` + 모바일 `px`
- **letter-spacing**: `em` (예: `-0.02em`)
- **line-height**: 무단위 비율 (`1.2`, `1.45`, `1.571`)
- **padding/margin/gap**: 고정 `px` (≥100px 만 `clamp()`)
- **border-radius**: 원형 `50%`, pill `2em`, 일반 `{n}px`
- **레이아웃**: `flexbox` 전용
- **각 셀렉터 규칙**: 한 줄 형식 (콤마 셀렉터 3개 이상이면 셀렉터만 줄바꿈, 속성은 마지막 셀렉터 뒤에 한 줄)
- **미디어쿼리**: 블록 안 각 규칙 줄바꿈 분리, 들여쓰기 없음

### :root 변수 (landing 프로젝트 필수)
```css
:root {
    --width:1480px;        /* Figma inner content + 40 */
    --padding:20px;
    --header_h:100px;
    --point-color-1:#438eca;
}
```

### .cont 패턴 (section_width_formula)
섹션은 full-bleed + background, 너비 제한은 `.cont` 내부에서만.
`.cont` CSS 는 common.css skeleton 에 이미 선언됨 — **섹션 CSS 에서 재선언 금지**.

### 이미지 래퍼 (img_area)
모든 `<img>` 는 `.img_area` 래퍼 안에. `.img_area` CSS 는 common.css skeleton 에 이미 선언됨 — **재선언 금지**.
**img 및 .img_area에 고정 width/height 금지** — 크기가 필요하면 부모 컨테이너에서 제어한다.
```html
<span class="img_area"><img src="./img/logo.png" alt="..."></span>
```

### reset.css 중복 선언 금지 (CRITICAL)
reset.css 에 이미 선언된 속성을 common.css 나 섹션 CSS 에서 재선언하지 않는다:
`font-family`, `font-size`, `color`, `a text-decoration`, `img max-width`, `line-height` 등.

### GSAP 패턴 (landing 필수)
```css
[data-delay] {position:relative; transition:all 1s ease; opacity:0;}
.section_on [data-delay] {opacity:1;}
```

---

## Figma → 퍼블리싱 워크플로우 (7 Step)

### Step 1: Figma 자산 추출 (spec.json + asset_manifest)
```bash
python3 D:/dev-base/tools/figma-section-spec.py \
  --file-key {KEY} --node-id {SECTION_ID} --output extracted/ \
  --download-assets
```
- `--download-assets` 필수 — 없으면 이미지가 디자인 사이즈(1:1)로 추출되지 않음
- 결과: `extracted/{section}_spec.json` + `.md` + `_asset_manifest.json` + `{section}/images/*.png` + `{section}/vectors/*.svg`
- spec.json 의 `text_nodes[].characters` 는 **byte-exact** 그대로 사용 (NBSP, 줄바꿈, 연속 공백 모두 보존)
- raw Figma API / Figma MCP 응답을 직접 해석하는 것 금지

### Step 2: PNG 다운로드 (시각 참조 + AI 외주 선정 입력)
```bash
FIGMA_TOKEN="figd_..." python3 D:/dev-base/tools/figma-png-download.py \
  --file-key {KEY} \
  --node-ids "{MAIN},{SEC_1},{SEC_2},..." \
  --output .gran-maestro/figma-png/ \
  --include-fills \
  --scale 1
```
- 섹션 PNG + IMAGE fill imageRef 자동 다운로드
- ⚠️ **시각 참조 전용** — 이 출력(`figma-png/`)은 원본 해상도이며 프로젝트 자산으로 사용 금지. 프로젝트 이미지는 Step 1 의 `--download-assets` 결과(디자인 1:1 사이즈)만 사용

### Step 3: 자산 복사
```bash
python3 D:/dev-base/tools/asset-copy.py \
  --extracted extracted/ --img img/
```
- manifest 의 `spec_node_id` 기준 (`;` 보존) 으로 `img/` 에 복사

### Step 4: OMX 로 HTML/CSS 코드 추출
OMX (oh-my-codex) 를 사용하여 코드를 추출한다. 입력:
- `extracted/{section}_spec.json` (정확한 텍스트/폰트/색상/패딩)
- `.gran-maestro/figma-png/{section}.png` (시각 참조)
- 이 `CLAUDE.md` + `rules/common.md` (룰 강제)

코드 추출 시 필수 준수 사항:
- spec.json 의 텍스트는 byte-exact 사용 강제
- PNG 시각 참조로 구조 결정
- 공통 영역 prefix 없음 / 페이지 prefix 강제
- 자체 검증 결과를 raw 출력 그대로 보고 (거짓 보고 금지)

### Step 5: PM 검증
```bash
python3 D:/dev-base/tools/pm-verify.py \
  --spec-dir extracted/ --html index.html \
  --css css/common.css --img img/ --profile landing
```
- 신뢰 카테고리 (텍스트 byte-exact + 폰트 5필드 + 색상 + 컨벤션 + broken link) 만 리포트
- 노이즈 카테고리 (layoutSizing / opacity / frame matching 등) 는 집계만, 게이트 X

### Step 6: Playwright 시각 비교
- 1920px 렌더 → PNG 저장 → 사용자에게 Figma PNG 와 나란히 제시
- 자연어 피드백 → 수정 → Step 5 또는 Step 4 복귀

---

## 코드 추출 에이전트

HTML/CSS 코드 추출은 **OMX (oh-my-codex)** 를 기본 사용한다.
OMX 는 Codex CLI 기반 멀티 에이전트 오케스트레이션 레이어로, AGENTS.md 와 프로젝트 룰을 자동 로드한다.

Gran Maestro 워크플로우에서는 claude-dev / codex-dev / gemini-dev 에이전트 디스패치도 가능하나, 사용자가 직접 코드 추출 시 OMX 를 우선 사용한다.

### 코드 추출 시 필수 준수 사항
- `D:/dev-base/rules/common.md` 전체 Read + 모든 내용 준수
- `D:/dev-base/CLAUDE.md` 전체 Read
- 공통 영역 (header/footer/logo/gnb) prefix 없음
- 페이지 전용 (main_*, sub_*) prefix 강제
- 들여쓰기 4-space, 시멘틱 `<nav><ul><li><a>` 구조
- spec.json `text_nodes[].characters` byte-exact 사용 (NBSP/`\n`/공백 보존)
- 색상 hex, letter-spacing em, font-size px (landing)
- 완료 전 `python3 D:/dev-base/tools/pm-verify.py ...` 실행하고 raw 출력 그대로 보고
- 거짓 보고 금지 — 위반 잔여 시 모두 나열

---

## 텍스트 태그 자동 판정

- 기본 태그: `<span>` 또는 헤딩 (`<h2>`, `<h3>` 등)
- `<p>` 태그 사용 조건 (셋 중 하나):
  1. `node.characters` 에 `\n` 포함 (서술형 2줄 이상)
  2. 텍스트 길이 95자 초과
  3. 문장형 마침표/종결어 반복
- 라벨성 텍스트 (브랜드명, 키워드, CTA) 에는 `<p>` 금지
- 짧은 단일 라벨 (COPYRIGHT 한 줄 등) 은 `<small>` 또는 `<span>`

---

## 하지 말 것 (재확인)

- 요청하지 않은 개선 추가
- 과도한 주석 / 한국어 주석
- 불필요한 에러 처리
- 장황한 설명
- 외주 AI 자가 보고 신뢰 후 사용자 전달

## 선호

- 간결한 응답
- 실용적 솔루션
- 최소한의 변경
- pm-verify 통과 후만 commit / 보고

---

## 질문할 때
- 요구사항이 모호할 때
- 여러 접근법이 가능할 때
- 기존 코드와 충돌 가능성 있을 때
- 큰 변경 (파일 10개+) 필요할 때

---

## 참조

- 상세 매뉴얼: `.gran-maestro/agile/AGI-002/objective/details/manual.md`
- 공통 CSS/HTML 룰: `rules/common.md`
- Landing 추가 룰: `rules/landing.md`
- Basic 추가 룰: `rules/basic.md`

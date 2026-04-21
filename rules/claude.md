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

스코핑으로 충돌 방지: `.header .logo {...}`, `.footer .logo {...}`

### 페이지 전용 영역 (페이지 prefix 강제)
| 페이지 파일 | prefix | 예시 |
|------------|--------|------|
| `index.html` | `main_` 또는 `index_` | `.main_mv`, `.main_intro` |
| `greeting.html` | `greeting_` | `.greeting_title` |
| `products.html` | `products_` | `.products_list` |

자식 클래스에도 prefix 일관: `.main_intro_card`, `.main_intro_card_icon`

### 시멘틱 마크업 강제
```html
<nav class="gnb">
    <ul>
        <li><a href="#"><span>회사소개</span></a></li>
        <li><a href="#"><span>제품소개</span></a></li>
    </ul>
</nav>
```

### 들여쓰기
- HTML: 4-space
- CSS 셀렉터: 한 줄 형식

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

### 선호
- **색상**: hex (`#fff`, `#212121`), 투명도 필요 시만 rgba
- **font-size**: landing px 전용, basic PC rem + 모바일 px
- **letter-spacing**: em (`-0.02em`)
- **line-height**: 무단위 비율 (`1.2`, `1.45`)
- **padding/margin/gap**: 고정 px (≥100px 만 clamp)
- **border-radius**: 원형 `50%`, pill `2em`
- **레이아웃**: flexbox 전용

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
```css
.cont {width:100%; max-width:var(--width); margin:0 auto; padding:0 var(--padding);}
```

### 이미지 래퍼
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

### Step 4: 외주 AI 자동 선정
```bash
python3 D:/dev-base/tools/select-ai.py \
  --extracted extracted/ --figma-png .gran-maestro/figma-png/ \
  --img img/ --project-type {basic|landing} --json
```

### Step 5: 선정된 AI 가 HTML/CSS 구현
- spec.json 의 텍스트는 byte-exact 사용 (NBSP, `\n`, 연속 공백 보존)
- PNG 는 시각 참조
- 이 CLAUDE.md 의 룰 강제

### Step 6: PM 검증
```bash
python3 D:/dev-base/tools/pm-verify.py \
  --spec-dir extracted/ --html index.html \
  --css css/common.css --img img/ --profile {basic|landing}
```
exit 0 이어야 commit 허용.

### Step 7: Playwright 시각 비교
1920px 렌더 → Figma PNG 와 사용자 비교 → 자연어 피드백 → 수정 → Step 6 재실행

---

## 외주 AI 선정 기준

| 프로젝트 유형 | 선정 AI | 이유 |
|-------------|--------|------|
| 대용량 / 복잡 / 텍스트 다수 | gemini-dev | frontend + large-context |
| 모션 / 인터랙션 / 코드 정밀 | codex-dev | code + test |
| 단순 인라인 수정 / 문서 | claude-dev | small-inline |

`select-ai.py` 가 PNG 정량 지표 + LLM 판단 혼합으로 자동 선정.

---

## 텍스트 태그 자동 판정

- 기본: `<span>` 또는 헤딩 (`<h2>`, `<h3>`)
- `<p>` 사용 조건 (셋 중 하나):
  1. `\n` 포함 (2줄 이상 서술)
  2. 95자 초과
  3. 문장형 마침표 반복
- 짧은 라벨 (COPYRIGHT 한 줄 등): `<small>` 또는 `<span>`

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
- pm-verify 통과 후만 commit 보고

---

## 참조

- 공통 CSS/HTML 룰: `D:/dev-base/rules/common.md`
- Landing 추가 룰: `D:/dev-base/rules/landing.md`
- Basic 추가 룰: `D:/dev-base/rules/basic.md`

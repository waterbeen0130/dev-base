# Implementation Request — 디에스솔루션 MAIN 페이지 HTML/CSS

- Request: REQ-043 / Task: 01
- Working Directory: `/mnt/d/위링/2026-04-21 디에스솔루션/`
- Spec Directory: `/mnt/d/위링/2026-04-21 디에스솔루션/extracted/`
- Output Target: `/mnt/d/위링/2026-04-21 디에스솔루션/output/a_main/`

## 구현 컨텍스트

디에스솔루션 Figma MAIN 페이지(basic 프로젝트 타입)를 HTML/CSS 로 변환한다. `extracted/` 에는 사전 생성된 6개 섹션 spec (`header_b / MV / sec_1 / sec_2 / sec_5 / footer_bk`) 의 `_spec.md` 와 `_spec.json` 이 있다. spec.md 만 보고 구현하며, raw Figma API / MCP 응답 직접 해석은 금지한다. 출력은 `output/a_main/index.html` + `output/a_main/common.css` + `output/a_main/reset.css` + `output/a_main/img/` 이며, 이미지는 각 섹션의 `{name}_asset_manifest.json` 의 `local_path` 가 `./img/xxx.png` 형태로 기록되어 있으니 그 경로 기준으로 배치한다.

## 자기탐색 지시

아래 순서로 원본 파일을 직접 읽고 구현하라.

1. 스펙 전체 읽기:
   ```bash
   for f in /mnt/d/위링/2026-04-21\ 디에스솔루션/extracted/*_spec.md; do echo "=== $f ==="; cat "$f"; done
   ```
2. 각 섹션의 `_spec.json` 에서 `text_nodes[].characters`, `frame_nodes[].{layoutMode,padding,itemSpacing,fills}`, `images` 필드를 근거 데이터로 사용
3. 템플릿 참조: `/mnt/d/dev-base/templates/index.html` (골격), `/mnt/d/dev-base/templates/css/reset.css` (reset)
4. 출력 생성:
   - `output/a_main/index.html` — 전체 페이지 (header_b → MV → sec_1 → sec_2 → sec_5 → footer_bk 순)
   - `output/a_main/common.css` — 통합 CSS
   - `output/a_main/reset.css` — `/mnt/d/dev-base/templates/css/reset.css` 복사
   - `output/a_main/img/` — 섹션별 `_asset_manifest.json` 의 이미지 다운로드 경로 기준 배치 (PM 이 후속 단계에서 다운로드 지원)
5. 완료 전 self-check:
   - spec `text_nodes[].characters` 가 HTML 에 byte-exact 로 포함되는가? (NBSP `\xa0`, 연속 공백, `\n` → `<br>`, ` ` → `<br>` 변환 포함)
   - spec `frame_nodes` 부모-자식 관계가 HTML DOM 계층으로 매핑되는가? (wrapper 임의 삭제 금지)
   - `asset_manifest` 에 등록된 이미지만 `<img src>` 에 사용되는가? (AI 합성 이미지 금지)

## 규칙 (CRITICAL — 반드시 준수)

### 작업 범위

- spec 외 파일 수정 금지 — `output/a_main/` 하위만 생성
- git commit 금지 (PM 이 후속 처리)
- 완료 전 self-check 필수

### CSS 규칙

- 각 셀렉터 규칙은 **한 줄**, 같은 셀렉터 중복 선언 금지
- 미디어쿼리 내부는 줄바꿈 분리 + 들여쓰기 없음
- 색상 **hex 전용** (`#fff`, `#090944`), 투명도만 `rgba()` 허용
- 레이아웃 **flexbox 전용** — CSS Grid / float 금지
- `line-height` **무단위 비율만** (`1.3`, `1.45`), computed px 금지
- `letter-spacing` **em 단위**, px 금지
- `border-radius` 원형 `50%` / pill `2em`, `999px` 금지
- padding/margin/gap **고정 px**, 100px 이상만 `clamp()` 허용
- `calc()`, `vw` 단독 금지 (clamp 내부만)
- `!important` 금지
- 클래스 **snake_case + 페이지 프리픽스** (`main_visual`, `main_intro` 등 의미 있는 영문명)
- `sec_1`, `section_01`, `box1` 같은 범용 클래스명 **절대 금지**
- `:root` 변수 줄당 하나, `--width` / `--padding` / `--point-color-N` 패턴
- basic 프로파일: PC font-size `rem`, 모바일(768px 이하) `px`, padding/margin 약 절반

### HTML 규칙

- `<figure>`, `<figcaption>`, `<main>`, `<article>` **금지** — `<div class="img_area">` + `<span>` 사용
- 인라인 `style` 금지
- 빈 `<div>` 금지, DOM 최대 깊이 5단계
- 모든 이미지에 짧은 `alt` 필수
- `<nav>` 안은 `ul>li>a` 구조 강제
- `<p>` 는 `\n` 포함/95자 초과/종결어 반복 시에만, 짧은 라벨은 `<span>`
- 모든 요소에 클래스 부여 금지 — 부모+태그 선택자 (`.parent h2`, `.parent li a`) 우선
- header/footer/gnb/logo 에 페이지 프리픽스 **금지**
- 파일명 `index.html` 고정, CSS 프리픽스는 의미 있는 영문 (예: `main_`)

### Figma → HTML/CSS 변환 매핑

- `layoutMode: HORIZONTAL` → `display:flex; flex-direction:row`
- `layoutMode: VERTICAL` → flex-direction:column 시 `gap` 금지, 자식에 `margin-top`
- `itemSpacing` 균일(max-min ≤ 3px) → `gap`, 비균일 → 개별 `margin`
- `paddingTop/Right/Bottom/Left` → `padding` shorthand
- `fills[].color` → hex 변환 (`#xxxxxx`, 소문자)
- `fontFamily/fontSize/fontWeight/lineHeightPx/fills.color` 5필드 완결성 필수
- `lineHeightRatio` (= lineHeightPx / fontSize) → CSS `line-height` 무단위
- `interactions[].url` 존재 → `<a href="..." target="_blank">`
- width/height 고정 px 대신 flex:1 / % 비율 사용 (카드 min-width 예외)
- Figma `visible:false` 노드는 HTML 에서 제외

### 구조 불변 원칙 (CRITICAL)

1. **text byte-exact**: spec `characters` 의 NBSP / line separator / 연속 공백 / 줄바꿈을 원본 그대로 복사. 축약·정리 금지
2. **DOM 계층 보존**: spec `frame_nodes` 의 부모-자식 관계를 HTML 요소 계층으로 그대로 매핑. "의미 없어 보이는 wrapper" 도 유지
3. **수치 정확성**: fills hex, padding, itemSpacing 을 소수점까지 CSS 에 반영
4. **이미지 원본만**: `asset_manifest.json` 등록 이미지만 `<img src>` 에, AI 합성 금지

## 검증 기준 (완료 전 self-check)

완료 전 아래 질문에 모두 YES 로 답할 수 있어야 한다:

1. 6개 섹션(header_b / MV / sec_1 / sec_2 / sec_5 / footer_bk) 모두 HTML 에 반영되었는가?
2. spec `text_nodes[].characters` 중 HTML 에 byte-exact 로 포함되지 않은 것이 있는가? (있으면 FAIL)
3. `frame_nodes` 계층이 HTML DOM 계층과 일치하는가? (wrapper 임의 삭제 없음)
4. CSS 는 한 줄 포맷, hex 전용, flexbox 전용, 무단위 line-height 인가?
5. 클래스명은 snake_case 의미있는 영문이며 `sec_숫자` 는 없는가?
6. `<figure>`, `<main>`, `<article>` 태그가 없는가?

## 완료 신호

위 6개 질문이 모두 YES 이면 작업 완료. PM 이 이어서 `figma-validate.py`, `validate-semantic.py`, `post-impl-verify.py`, `structural-diff.py` 를 실행한다.

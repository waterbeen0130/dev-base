# 모제림 비절개 랜딩 — Section_05 (FUE hair) 퍼블리싱

## 프로젝트 기본 정보

- 프로젝트 폴더: `/mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/`
- 기존 파일:
  - `index.html` — 11 섹션 골격, Hero/Section_02/03/04 구현 완료. **`<section class="fue">` 빈 컨테이너가 이미 존재**, 그 안에만 채울 것
  - `css/common.css` — 113줄, Hero/ba_section/vs_section/plan 스타일. **파일 끝에 Section_05 스타일을 append**할 것
  - `css/reset.css`, `js/main.js`, `js/ba_slider.js`
- 프로젝트 타입: **landing**
- Figma file_key: `T8xEPS7sR5MZCUQ9JVa4hH`
- Figma node-id: `842:206` (Section_05)
- 모바일 breakpoint: `@media (max-width:960px)` — **이번 작업은 PC만 (모바일은 마지막에 일괄)**

## 작업 대상

`<section class="fue">` 내부에 Section_05 (FUE hair) HTML/CSS를 채워넣는다.

## 입력 자료 (반드시 둘 다 Read)

1. `/mnt/d/dev-base/.gran-maestro/tmp/mojelim_section_05/section_05_spec.md` — 사람용 표
2. `/mnt/d/dev-base/.gran-maestro/tmp/mojelim_section_05/section_05_spec.json` — 검증 기준 (값 불일치 시 .json 우선)

## 섹션 구조 요약 (spec 기반)

- 섹션 자체: `Section_05` 1920×1185, padding 173/246/183/246, VERTICAL flex, gap 68
- 상단 타이틀 그룹 (Frame 523, gap 57):
  - 1줄: "오직 남성만을 위한" (Noto Serif KR 45/65.25 #312d2b, lineHeightRatio 1.45, letter-spacing -0.9px = -0.02em)
  - 2줄: "DEEP 플랜" (Pretendard 69/100.05 800 #312d2b, 1.45, -0.02em)
  - 3줄: 설명 본문 3줄 — 텍스트는 spec characters 그대로 사용. `\u2028` → `<br>` (Pretendard 18/29.88 500 #787472, 1.66, -0.02em)
- 4-카드 2×2 그리드 (Frame 548 wrapping):
  - 각 카드: 162×162 아이콘 + 번호("1./2./3./4.", Carattere 63 #916046) + 타이틀 (Noto Serif KR 27 600 #916046) + 설명 (Pretendard 17 500 #787472, 줄바꿈 `\n` → `<br>`)
  - 카드 4개 내용:
    1. 이마 비율 고려 — "황금 비율 기준으로 개인 이마 구조를 정밀 분석해\n최적의 헤어라인 위치를 결정합니다."
    2. M자 라인 설계 — "각도와 깊이를 입체적으로 설계해 자연스러운\nM자 라인을 완성합니다."
    3. 관자놀이 · 측면 보정 — "측면 밸런스와 기존 모발의 흐름을 함께 계산해\n어색함 없는 연결을 구현합니다."
    4. 얼굴형 맞춤 디자인 — "얼굴형 · 인상 · 연령대까지 종합적으로 고려한\n남성 전용 맞춤 비절개 디자인을 제공합니다."
  - 카드 사이 간격: 가로 26px, 세로 18px (Frame 546/548 itemSpacing 참조)
  - 카드 내부: 아이콘과 텍스트 그룹 사이 padding-left 29px, gap 33px
- 배경 거대 텍스트 "FUE hair" (Pretendard 231.6 800 line-height 0.83 #eae5de) — Section 우측 또는 배경 워터마크. spec bbox 보고 위치 결정. text-align right.

## 이미지 자산

`/mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/img/sec05_icon_1.png` ~ `sec05_icon_4.png` (4개, 800×800 PNG, CSS에서 162×162로 표시)

## 작성 규칙 (CRITICAL — 이 프로젝트 표준)

> **참고 우선순위**: 기존 `common.css` (Hero/ba_section/vs_section/plan)의 패턴을 그대로 따른다. 새 패턴 만들지 말 것.

1. **CSS 규칙은 한 줄로** — 같은 셀렉터 중복 금지
2. **클래스명**: `fue_*` 프리픽스 (예: `fue_title`, `fue_lead`, `fue_main`, `fue_desc`, `fue_grid`, `fue_card`, `fue_icon`, `fue_num`, `fue_card_title`, `fue_card_desc`, `fue_bg`)
3. **CSS Grid 절대 금지** — flexbox만. 2×2 그리드는 `display:flex; flex-wrap:wrap` + 카드별 `flex: 0 0 calc(50% - X)` 또는 행 단위 wrapper
4. **수직 여백은 margin** — `flex-direction:column`에 `gap` 사용 금지. 카드 사이 간격은 wrapper 분리 + margin-top
5. **100px 이상 padding/margin은 `clamp()`** — 173/183/246 등은 모두 clamp(min, vw, max) 형태로. 기존 .ba_section padding 패턴 참조
6. **모든 텍스트에 font-family/font-size/font-weight/line-height/color 5필드 명시**
7. **line-height는 무단위 비율** (lineHeightRatio 그대로). 예: 1.45, 1.66, 1.524
8. **letter-spacing은 em 단위** (Figma px / fontSize). 예: -0.9px@45px → -0.02em
9. **font-family 매핑**: Noto Serif KR → `var(--font3)`, Pretendard → `var(--font)` (생략 시 body가 var(--font)이지만 명시 권장), Carattere → `"Carattere", cursive` (Google Fonts CDN 추가 필요)
10. **색상은 hex 소문자**: #312d2b #787472 #916046 #eae5de
11. **DOM depth ≤ 5, inner wrapper ≤ 1** — 과도한 wrapper 금지
12. **번호 "1./2./3./4."**는 `<em>` 또는 `<span>` 사용 — `<p>` 금지 (짧은 라벨)
13. **GSAP scroll trigger**: 타이틀과 4 카드에 `data-delay` 적용 (0.2/0.4/0.6/0.8/1.0)
14. **FUE hair 배경 텍스트**: `<span>` 으로 작성, 절대 위치(`position:absolute`) 또는 섹션 내 별도 wrapper. user-select:none, pointer-events:none.

## 폰트 추가 작업

`Carattere` 폰트가 기존 common.css에 없으므로 `@import url('https://fonts.googleapis.com/css2?family=Carattere&display=swap');` 를 common.css 상단 import 블록에 **추가**.

## 작업 순서

1. spec.md / spec.json 둘 다 Read
2. 기존 `common.css` Read (특히 `.plan` 섹션 패턴 — 가장 비슷한 단일 컬럼 + 텍스트 구조)
3. 기존 `index.html` Read (`<section class="fue">` 위치 확인)
4. **Edit으로 index.html의 `<section class="fue">` 빈 내용을 채움** (전체 파일 재작성 금지)
5. **Edit으로 common.css 끝에 `/* Section_05 — fue (FUE hair 4-card) */` 블록 추가** + 상단 import에 Carattere 추가
6. 검증 실행:
   ```bash
   python3 /mnt/d/dev-base/tools/figma-validate.py \
     --spec /mnt/d/dev-base/.gran-maestro/tmp/mojelim_section_05/section_05_spec.json \
     --html /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/index.html \
     --css /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/css/common.css

   python3 /mnt/d/dev-base/tools/validate-semantic.py \
     --html /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/index.html \
     --css /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/css/common.css \
     --profile landing
   ```
7. 두 도구의 위반 출력을 확인하고, 도구가 지적한 항목을 가능한 한 수정해 위반을 줄임. 단, 이미 작업된 다른 섹션(Hero/ba_section/vs_section/plan)이 트리거하는 위반은 무시 (Section_05 관련 위반만 책임). figma-validate.py는 spec.json 기준이라 Section_05 노드만 검사함 → 이건 0건 목표.
8. 도구 출력 전문을 파일로 저장:
   - `/mnt/d/dev-base/.gran-maestro/tmp/mojelim_section_05/figma-validate.txt`
   - `/mnt/d/dev-base/.gran-maestro/tmp/mojelim_section_05/validate-semantic.txt`

## 금지

- 기존 Hero/ba_section/vs_section/plan 코드 수정 금지
- index.html 전체 재작성 금지 (Edit으로 `<section class="fue">` 내부만 채움)
- common.css 기존 규칙 수정 금지 (append만)
- CSS Grid 사용 금지
- `figure`/`figcaption` 사용 금지
- 짧은 라벨에 `<p>` 사용 금지
- git commit 금지

## 완료 보고 (5~10줄)

- 추가한 HTML 구조 요약 (요소/클래스명)
- 추가한 CSS 줄 수 + 핵심 셀렉터
- figma-validate.py exit code + Section_05 관련 위반 건수
- validate-semantic.py exit code + Section_05 관련 위반 건수 (다른 섹션 위반과 분리)
- 작업 중 spec과 어긋난 결정 사항 (있다면)

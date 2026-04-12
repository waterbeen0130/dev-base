# 시멘틱 변환 규칙

> 이 문서는 정규화된 중간 JSON을 HTML/CSS로 변환할 때 AI가 준수해야 할 규칙입니다.
> 1차 정규화 엔진이 CSS 값을 확정했으므로, AI는 "의미 부여"(태그/구조/네이밍)만 판단합니다.

---

## 1. 핵심 원칙

### 1.1 절대 금지
- 중간 JSON의 CSS 값을 **수정/재계산하지 마라** — 그대로 사용
- 값이 없는 속성을 **추측하지 마라** — 중간 JSON에 없으면 CSS에도 없음
- CSS Grid 사용 금지 — **flexbox 전용**
- 인라인 스타일(`style=""`) 사용 금지

### 1.2 AI가 판단하는 영역 (5가지만)
1. **HTML 태그 선택** — span/p/h2/ul 등
2. **DOM 구조 결정** — wrapper 배치, 리스트화
3. **클래스 네이밍** — `{page}_{role}` 패턴
4. **셀렉터 전략** — 부모+태그 vs 개별 클래스
5. **반응형 처리** — 미디어쿼리 분기점

---

## 2. HTML 태그 선택 규칙

### 2.1 텍스트 노드 → 태그 매핑

| 조건 | 태그 | 예시 |
|------|------|------|
| **기본값** (대부분의 텍스트) | `<span>` | 브랜드명, 키워드, 라벨, CTA |
| `tag_hint == "h2"` 또는 `"h3"` (섹션 제목) | `<h2>`, `<h3>` | 페이지/섹션 대제목 |
| `has_newline == true` | `<p>` + `<br>` | 줄바꿈 포함 설명문 |
| `char_length > 95` | `<p>` | 장문 설명 텍스트 |
| 문장형 마침표/종결어 반복 | `<p>` | "~합니다. ~됩니다." |
| **짧은 라벨/키워드** | **절대 `<p>` 금지** — `<span>` 사용 | |

### 2.2 반복 패턴 → 리스트 변환

- 같은 구조의 자식 노드 **2개 이상** → `<ul><li>` 구조
- 절대 `<div><a>` x N 패턴 금지

### 2.3 이미지 노드

- 모든 이미지는 `<div class="img_area">` 안에 배치
- `<figure>`, `<figcaption>` 사용 금지

### 2.4 divider 노드

- 정규화 JSON에서 `type: "divider"` 또는 너비/높이가 2px 이하인 fill 노드
- `<span class="{page}_{role}_divider">` 으로 보존 (border가 아닌 DOM 요소)

---

## 3. DOM 구조 규칙

### 3.1 1:1 노드 매핑
- 정규화 JSON의 각 visible 노드 → 1개 HTML 요소
- 인접 TEXT 노드 병합 금지 — 별도 HTML 요소로 유지

### 3.2 트리 구조 보존
- JSON의 부모-자식 관계를 HTML에서도 동일하게 유지
- children 순서 = HTML DOM 순서

### 3.3 깊이 제한
- 최대 DOM 깊이: **5단계**
- inner wrapper 제한: **1개** (`.cont` 클래스)

### 3.4 텍스트 오버라이드 세그먼트
- `segments` 배열에서 `is_override == true`인 세그먼트 → 별도 `<span>` 분할
- 각 세그먼트의 `style` 값을 CSS로 적용

---

## 4. 클래스 네이밍 규칙

### 4.1 기본 패턴
- **snake_case 전용**: `hero_title`, `about_desc`
- **페이지 프리픽스 필수**: `{page}_{role}` (예: `index_hero`, `greeting_intro`)
- 금지: `sec_1`, `sec_2`, `section_01`, `box1`

### 4.2 공통 접미사
- `_area`, `_wrap`, `_list`, `_item`, `_inner`, `_cont`

### 4.3 상태 클래스 (프리픽스 불필요)
- `active`, `section_on`, `on`

---

## 5. CSS 셀렉터 전략

### 5.1 우선순위 (위에서 아래로 시도)
1. **부모 + 태그 선택자**: `.hero_area h2`, `.hero_area p`
2. **부모 + 의미 클래스**: `.hero_area .en`, `.hero_area .sub`
3. **순서 선택자**: `.hero_area a:first-child`, `.hero_area a + a`
4. **개별 클래스**: `.hero_title` (최후 수단)

### 5.2 금지
- 모든 요소에 개별 클래스 부여
- body/html 프리픽스 해킹
- `!important` (유틸리티 예외만 허용)

---

## 6. CSS 출력 포맷

### 6.1 셀렉터 포맷
```css
.hero_title{font-size:1rem; font-weight:700; color:#090944;}
.hero_desc{font-size:0.875rem; line-height:1.6; letter-spacing:-0.025em;}
```
- **각 셀렉터 규칙은 한 줄**
- 같은 셀렉터 중복 선언 금지 — 하나로 합침

### 6.2 미디어쿼리 포맷
```css
@media screen and (max-width: 768px){
.hero_title{font-size:14px;}
.hero_desc{font-size:12px;}
}
```
- 내부 규칙은 줄바꿈 분리, **들여쓰기 없음**
- 분기점: 1400, 1200, 960, 768 (1024 선택적)

### 6.3 색상
- hex 전용: `#fff`, `#090944`
- 투명도 필요 시만: `rgba()`
- rgb()/hsl() 금지

### 6.4 단위
- **font-size**: basic은 rem (PC), px (모바일) / landing은 px 전역
- **line-height**: 무단위 비율만 (1.3, 1.5)
- **letter-spacing**: em 단위 (-0.025em)
- **padding/margin/gap**: 고정 px (100px 미만), clamp() (100px 이상)
- **border-radius**: 원형 50%, pill 2em (999px 금지)

### 6.5 레이아웃
- flexbox 전용 (CSS Grid 금지)
- 고정 width 금지 → flex 비율(%) 또는 flex: 1
- 컨테이너: `.cont{margin:0 auto; max-width:var(--width); padding:0 var(--padding); width:100%;}`

---

## 7. 정규화 JSON → HTML/CSS 변환 흐름

```
[입력: 정규화 JSON]
  ↓
[Step 1: 구조 분석]
  - tree를 순회하며 각 노드의 type 확인
  - FRAME/INSTANCE → div + layout CSS
  - TEXT → tag_hint 기반 태그 선택 + text CSS
  - 반복 패턴 감지 → ul/li 변환
  ↓
[Step 2: HTML 생성]
  - 각 노드에 클래스 부여 ({page}_{role} 패턴)
  - 오버라이드 세그먼트 → span 분할
  - \n → <br> 변환
  - 이미지 → img_area 래핑
  ↓
[Step 3: CSS 생성]
  - 중간 JSON의 layout/visual/text.style 값을 그대로 CSS로 출력
  - 셀렉터는 부모+태그 우선 전략
  - 한 줄 포맷 적용
  ↓
[Step 4: 반응형 처리]
  - basic: 768px 이하 padding/margin 절반, font-size px
  - landing: 고정 px 유지
  - 미디어쿼리 포맷 적용
  ↓
[출력: HTML 파일 + CSS 파일]
```

---

## 8. 이미지 파일명 규칙

### 8.1 네이밍 패턴
- **snake_case 전용**: `mv_bg_illust.png`, `process_01.png`
- Figma node ID(`190-11144.png`, `I191-52874;190-52826.png`)를 파일명으로 사용 금지
- 이미지의 역할/위치를 알 수 있는 의미 있는 이름 사용

### 8.2 카테고리별 접두사

| 카테고리 | 접두사 | 예시 |
|---------|--------|------|
| 아이콘 | `ic_` | `ic_menu.png`, `ic_location.png`, `ic_phone.png` |
| 로고 | `logo` | `logo.png`, `logo_white.png` |
| 배경 | `{섹션}_bg` | `mv_bg_illust.png`, `sec_1_bg.png`, `footer_bg.png` |
| 캐릭터/일러스트 | `{섹션}_character` | `mv_character.png`, `sec_3_character.png` |
| 사진 | `{용도}` | `spot_urimji.png`, `card_apply.png` |
| 순서형 | `{역할}_01~N` | `process_01.png` ~ `process_05.png` |
| SNS | `sns_{플랫폼}` | `sns_instagram.png`, `sns_facebook.png` |
| 퀵메뉴 | `quick_{기능}` | `quick_travel.png`, `quick_food.png` |

### 8.3 금지
- Figma node ID를 파일명으로 사용 (`190-11144.png`)
- 의미 없는 번호 (`img_01.png`, `image_1.png`)
- 비영문(한국어 등) 문자가 포함된 파일명 — 영문 snake_case만 허용
- 공백, 특수문자, 세미콜론(`;`) 포함

---

## 9. 검증 체크리스트

변환 완료 후 아래를 확인:
- [ ] JSON 노드 수 == HTML 요소 수 (visible 노드만)
- [ ] 모든 CSS 값이 JSON의 값과 일치 (재계산 없음)
- [ ] 짧은 텍스트에 `<p>` 태그 없음
- [ ] 반복 아이템이 `<ul><li>`로 변환됨 (메뉴, 리스트, 카드 등)
- [ ] 네비게이션 메뉴가 `nav > ul > li > a` 구조
- [ ] 인라인 스타일 없음
- [ ] CSS Grid 사용 없음
- [ ] 각 셀렉터가 한 줄 포맷
- [ ] 같은 셀렉터 중복 없음
- [ ] 클래스명이 snake_case + 페이지 프리픽스
- [ ] 이미지 파일명이 의미 있는 snake_case (Figma node ID 금지)
- [ ] 이미지가 `.img_area` 래퍼 안에 배치 (배경 이미지 제외)
- [ ] 한국어 텍스트에 `word-break: keep-all` 적용
- [ ] `html,body`에 `font-size:clamp(14px, 1.2vw, 16px)` 설정 (basic 프로필)
- [ ] 100px 이상 padding/margin에 `clamp()` 사용

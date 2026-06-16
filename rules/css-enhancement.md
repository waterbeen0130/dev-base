# CSS 고도화 규칙

기존 AI 생성 CSS를 사용자 스타일에 맞게 고도화할 때 적용하는 규칙입니다.
`common.md`의 기본 CSS 규칙을 전제로 하며, 고도화 시 추가로 체크해야 할 항목을 정리합니다.

> 참조 프로젝트: `D:\위링\2025-07-01 enic\html\css\common.css` (사용자 직접 작성)

---

## 1. 시멘틱 마크업 (HTML + CSS 연동)

### 리스트성 요소는 반드시 `ul > li` 구조
- 반복되는 링크/카드/아이템은 `ul > li > a` 또는 `ul > li` 사용
- `div > a × N` 나열 금지 — `ul > li > a`로 변환

```html
<!-- wrong -->
<div class="main_quick">
    <a href="#" class="main_quick_item">...</a>
    <a href="#" class="main_quick_item">...</a>
</div>

<!-- correct -->
<div class="main_quick">
    <ul>
        <li><a href="#">...</a></li>
        <li><a href="#">...</a></li>
    </ul>
</div>
```

### 네비게이션은 `nav > ul > li > a`
```html
<!-- wrong -->
<nav class="main_gnb">
    <a href="#">메뉴1</a>
    <a href="#">메뉴2</a>
</nav>

<!-- correct -->
<nav class="main_gnb">
    <ul>
        <li><a href="#">메뉴1</a></li>
        <li><a href="#">메뉴2</a></li>
    </ul>
</nav>
```

### CSS 셀렉터 연동
- `ul > li` 추가 시 CSS도 태그 선택자로 조정
- 개별 클래스 대신 부모 + 태그 선택자 우선

```css
/* before */
.main_quick{display:flex;}
.main_quick_item{...}

/* after */
.main_quick ul{display:flex;}
.main_quick li{...}
.main_quick a{...}
```

### 시멘틱 체크 대상 패턴

| 패턴 | 변환 |
|------|------|
| `div > a × N` (반복 링크) | `ul > li > a` |
| `nav > a × N` (네비게이션) | `nav > ul > li > a` |
| `div > div × N` (카드 반복) | `ul > li > div` 또는 `ul > li` |
| `div > a` (배너 리스트) | `ul > li > a` |
| footer 메뉴 `div > a × N` | `ul > li > a` |

---

## 2. 미디어쿼리 정리

### specificity 조작 금지
- `body .selector`, `html .selector`, `html body .selector` 패턴 제거
- 미디어쿼리 순서(큰 값 → 작은 값)로 cascade 해결

```css
/* wrong - specificity hack */
@media (max-width:1200px){
body .main_gnb{display:none;}
}
@media (max-width:960px){
html .main_visual{height:380px;}
}
@media (max-width:768px){
html body .main_visual{height:300px;}
}

/* correct - clean selectors, cascade order handles override */
@media screen and (max-width:1200px){
.main_gnb{display:none;}
}
@media screen and (max-width:960px){
.main_visual{height:380px;}
}
@media screen and (max-width:768px){
.main_visual{height:300px;}
}
```

### 미디어쿼리 형식
- `@media screen and (max-width: Npx)` — `screen and` 포함
- 섹션별 코드 바로 아래에 해당 미디어쿼리 배치
- 하나의 파일 끝에 전부 몰아놓지 않음

```css
/* header */
.main_header{...}
.main_gnb{...}

@media screen and (max-width: 1200px){
.main_gnb{display:none;}
}
@media screen and (max-width: 768px){
.main_header{height:60px;}
}

/* main visual - separate section, separate media queries */
.main_visual{...}

@media screen and (max-width: 960px){
.main_visual{height:380px;}
}
```

---

## 3. reset.css 규칙

- 템플릿 reset.css 사용: `D:\dev-base\templates\css\reset.css`
- AI가 자체 생성한 reset (Eric Meyer 등) 사용 금지
- 템플릿에 포함된 항목:
  - form 요소 초기화 (input, select, textarea)
  - @font-face 선언 (Pretendard 로컬)
  - 유틸리티 클래스 (flex, margin, padding)
  - clearfix, IR

---

## 4. 셀렉터 작성 방식

### 직접 자식 선택자(`>`) 활용
- `ul > li`, `nav > ul`, `.gnb>ul>li>a` 등 구조적 관계가 명확할 때 사용
- depth가 깊어지면 중간 단계에서 클래스로 끊음

```css
/* good - clear structure */
.gnb>ul{display:flex;}
.gnb>ul>li{padding:0 35px;}
.gnb>ul>li>a{height:var(--header_h); display:flex; align-items:center; font-size:1.25rem;}
.s_gnb>ul>li>a{font-size:0.9375rem;}

/* good - class break for deep nesting */
.main_cont_2 .list ul li{display:flex; align-items:center;}
.main_cont_2 .list ul li .txt_area{width:53%;}
```

### 태그 선택자 직접 사용 (적절한 스코프 내)
```css
/* footer - tag selector within scoped parent */
footer{background-color:#202731;}
footer hr{...}
footer .info ul li{...}
footer .copyright{...}

/* header - tag selector */
header{position:fixed; left:0; top:0; width:100%; z-index:100;}
header .logo a img{width:192px;}
```

---

## 5. 반응형 패턴

### CSS 변수 오버라이드
```css
:root{
    --padding:20px;
    --header_h:100px;
    --width:1240px;
}

@media screen and (max-width: 768px){
:root{
    --header_h:60px;
}
}
```

### 반응형 전환 패턴
| PC 상태 | 모바일 전환 |
|---------|------------|
| `display:flex` | `display:block` 또는 `flex-direction:column` |
| `width:48%` | `width:100%` |
| `flex-wrap:nowrap` | `flex-wrap:wrap` |
| `position:absolute` | `position:relative; left:auto; top:auto` |
| `br` 줄바꿈 | `br{display:none;}` |

### 큰 padding/margin — `max()` 패턴
```css
/* correct */
.section{padding:max(calc(110/1920*100vw), 55px) 0;}

/* wrong - raw calc */
.section{padding:calc(110/1920*100vw) 0;}
```

---

## 6. 공통 타입 컴포넌트

재사용 UI는 `{타입}Type_{N}` 패턴으로 네이밍:
- `listType_1`, `listType_2` ... `listType_9`
- `titleType_1`, `titleType_2`, `titleType_3`
- `tabType_1`
- `tableType_1`, `tableType_2`

```css
.listType_1>ul{display:flex; gap:3.125rem; flex-wrap:wrap;}
.listType_1>ul>li{padding:40px 20px; width:calc((100% - 3.125rem)/2); ...}
```

---

## 7. 고도화 7-Phase 체크리스트

AI 생성 CSS/HTML을 사용자 스타일로 고도화할 때 아래 Phase를 순서대로 실행.
각 Phase는 이전 Phase 완료를 전제로 하되, 일부는 병렬 실행 가능 (§8 의존성 그래프 참조).

### Phase 1: 기초 설정
- [ ] reset.css 템플릿 교체 (`D:\dev-base\templates\css\reset.css`)
  - AI 생성 reset (Eric Meyer 등) → 프로젝트 표준 reset.css로 교체
  - `@import url("reset.css");` 가 common.css 최상단에 있는지 확인
- [ ] `:root` 변수 정리
  - 중복 변수 제거, 네이밍 통일 (`--padding`, `--header_h`, `--width` 등)
  - 사용되지 않는 변수 삭제
- [ ] 폰트 선언 중복 해소
  - CDN `@import` 1개로 통합 (Pretendard 등)
  - `@font-face` 중복 선언 제거
- [ ] 빈 셀렉터(`{}`) 삭제

### Phase 2: 레이아웃 정규화
- [ ] 컨테이너 너비 패턴 통일
  - `padding` 기반 제한 → `max-width` + `margin:0 auto` + `padding:0 var(--padding)`
  - 공식: `max-width = viewport_width - (여백 × 2) + padding × 2`
  - 예: 1920px 기준, 여백 340px → `max-width: 1240px` + `--padding: 20px`
- [ ] 각 섹션에 동일 패턴 적용 확인
  - `.section_name{max-width:var(--width); margin:0 auto; padding:0 var(--padding);}`
- [ ] 고정 height 사용처 점검
  - 배너/비주얼: `aspect-ratio` 전환 가능 여부 확인
  - 컨테이너: padding/flex 기반 자연 높이로 전환

### Phase 3: 미디어쿼리 구조 정리
- [ ] `body`/`html` specificity 접두사 제거
  - `body .selector` → `.selector`
  - `html body .selector` → `.selector`
  - cascade 순서로 오버라이드 해결
- [ ] `@media` 형식 통일: `@media screen and (max-width: Npx)`
  - `@media (max-width:` → `@media screen and (max-width:`
- [ ] 미디어쿼리 배치 재구성
  - 파일 하단 집중 → 각 섹션 코드 바로 아래로 이동
  - 순서: 큰 breakpoint → 작은 breakpoint (1200 → 960 → 768)
- [ ] 미디어쿼리 선행 공백/불필요한 빈 줄 제거
- [ ] 중복 미디어쿼리 통합 (동일 breakpoint 내 동일 셀렉터)

### Phase 4: 시멘틱 마크업 변환
- [ ] `div > a × N` (반복 링크) → `ul > li > a`
- [ ] `nav > a × N` (네비게이션) → `nav > ul > li > a`
- [ ] footer 메뉴 `div > a` → `ul > li > a`
- [ ] SNS/아이콘 리스트 → `ul > li`
- [ ] CSS 셀렉터 연동 변환
  - `.item_class` → `.parent li a` (부모+태그 선택자)
  - 개별 클래스 최소화
- [ ] 서브페이지 공통 영역 동기화
  - GNB, 푸터, 전체메뉴 등 공통 컴포넌트 마크업을 메인과 일치시킴

### Phase 5: 반응형 유연성 확보
- [ ] 고정 `height` → `aspect-ratio` 전환 (배너, 이미지 영역)
  - 예: `height:500px` → `aspect-ratio:1920/500`
- [ ] flex 자식 고정 `width` px → `%` 환산
  - 예: `width:600px` (부모 1240px) → `width:48.38%` 또는 `calc()` 사용
- [ ] 컨테이너 자연 높이 (padding + flex 기반)
  - `min-height` 삭제 가능 여부 점검
- [ ] 768px 이하 padding/margin 반값 적용 확인 (basic 타입)
- [ ] 768px 이하 font-size 고정 px 확인

### Phase 6: 성능/표준
- [ ] `<script>` 태그 위치 및 속성 정리
  - `</body>` 직전 → `<head>` 내 `defer` 속성
  - 로드 순서 유지: jQuery → gsap → ScrollTrigger → slick → ui_common
- [ ] 불필요한 인라인 스타일 제거 → CSS로 이동
- [ ] 이미지 alt 속성 확인

### Phase 7: CSS 품질 정제
- [ ] 빈 셀렉터(규칙 없는 `{}`) 삭제
- [ ] 중복 셀렉터 통합
  - 동일 셀렉터가 여러 곳에 선언된 경우 하나로 합침
- [ ] 하드코딩 색상 → CSS 변수 전환 (§9 참조)
  - 3회 이상 반복되는 색상값 → `:root` 변수화
- [ ] `border-radius` 규칙 준수
  - `999px` / `120px` → `50%` (원형) 또는 `2em` (pill)
- [ ] 미디어쿼리 포맷 최종 정리
  - 선행 공백, 빈 줄, 들여쓰기 정리
- [ ] 중복 `@import` 제거
- [ ] CSS 한 줄 포맷 확인 (각 셀렉터 규칙이 한 줄인지, 콤마 3개+ 시 셀렉터만 줄바꿈 허용)

---

## 8. Phase 의존성 그래프

```
Phase 1 (기초 설정)
  ↓
Phase 2 (레이아웃) ──────┐
  ↓                      │ 병렬 가능
Phase 3 (미디어쿼리) ←───┘
  ↓
Phase 4 (시멘틱) ←── Phase 2, 3 완료 필수
  ↓
Phase 5 (반응형) ←── Phase 3, 4 완료 필수
  ↓
Phase 6 (성능) ←── Phase 4 완료 필수 (마크업 확정 후)
  ↓
Phase 7 (품질) ←── 전체 완료 후 최종 정제
```

| Phase | 선행 조건 | 병렬 가능 대상 |
|-------|----------|--------------|
| 1 | 없음 | — |
| 2 | Phase 1 | Phase 3과 병렬 가능 |
| 3 | Phase 1 | Phase 2와 병렬 가능 |
| 4 | Phase 2, 3 | — |
| 5 | Phase 3, 4 | Phase 6과 병렬 가능 |
| 6 | Phase 4 | Phase 5와 병렬 가능 |
| 7 | Phase 1~6 전체 | — (최종 단계) |

---

## 9. 색상 변수 전환 패턴

### 변수화 판단 기준
- 동일 색상값이 **3회 이상** 반복되면 `:root` 변수로 전환
- **2회 이하**는 인라인 hex 유지 (과도한 변수화 방지)
- 투명도 변형(`rgba`)은 원본 변수 + alpha로 분리하지 않고 별도 변수

### 매핑 절차
1. CSS 파일에서 모든 `#` hex 값 추출 및 빈도 카운트
2. 3회 이상 색상을 의미별로 그룹화:
   - `--color_primary`: 주 브랜드 색상
   - `--color_secondary`: 보조 색상
   - `--color_bg`: 배경색
   - `--color_text`: 본문 텍스트
   - `--color_text_light`: 보조 텍스트
   - `--color_border`: 테두리
   - `--color_accent`: 강조색
3. 근사값 판단:
   - `#333` / `#333333` / `#343434` → 동일 변수 (`--color_text`)
   - 차이가 RGB 각 채널 ±5 이내면 가장 빈번한 값으로 통일
4. 새 변수 필요 판단:
   - 기존 변수와 RGB 거리가 채널당 ±10 초과 → 새 변수 생성
   - 10 이내 → 기존 변수로 흡수

### 변수 네이밍 규칙
```css
:root{
    /* brand */
    --color_primary:#090944;
    --color_secondary:#1a73e8;
    /* text */
    --color_text:#333;
    --color_text_light:#666;
    --color_text_lighter:#999;
    /* background */
    --color_bg:#f5f5f5;
    --color_bg_dark:#222;
    /* border */
    --color_border:#ddd;
    --color_border_light:#eee;
    /* accent */
    --color_accent:#ff6b35;
}
```

### 교체 예시
```css
/* before */
.header{background-color:#090944;}
.footer{background-color:#090944;}
.gnb a{color:#090944;}

/* after */
.header{background-color:var(--color_primary);}
.footer{background-color:var(--color_primary);}
.gnb a{color:var(--color_primary);}
```

---

## 10. AI 생성 vs 사용자 스타일 차이 요약

| 항목 | AI 생성 (현재) | 사용자 스타일 (목표) |
|------|---------------|-------------------|
| 리스트 구조 | `div > a` 나열 | `ul > li > a` |
| 네비게이션 | `nav > a` | `nav > ul > li > a` |
| 미디어쿼리 접두사 | `body`/`html` 사용 | 접두사 없음 |
| 미디어쿼리 형식 | `@media (max-width:)` | `@media screen and (max-width:)` |
| 미디어쿼리 배치 | 파일 하단 한 곳 | 섹션별 코드 아래 |
| reset.css | Eric Meyer 자체생성 | 템플릿 사용 |
| 셀렉터 | flat 클래스 위주 | 부모>자식 체인 + 태그 선택자 |
| 공통 타입 | 없음 | `listType_N`, `titleType_N` |
| 색상 | 하드코딩 hex 반복 | `:root` CSS 변수 |
| 컨테이너 | padding 제한 | max-width + margin:auto |
| script 위치 | `</body>` 직전 | `<head>` + `defer` |
| 높이 | 고정 height | aspect-ratio / 자연 높이 |

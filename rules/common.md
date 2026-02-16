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
- 시맨틱 태그 사용 (`<header>`, `<main>`, `<section>`, `<article>`, `<footer>`, `<nav>`, `<address>`)
- 모든 이미지에 `alt` 속성 필수
- 버튼에 `type="button"` 명시
- 폼 요소는 `<label>`과 연결
- 텍스트 없는 인터랙티브 요소에 `aria-label` 필수

### CSS
- **모든 셀렉터 한 줄 포맷으로 작성** (미디어쿼리 내부 포함)
- **미디어쿼리 내부 들여쓰기 없음** — 셀렉터는 컬럼 0에서 시작
- font-size: PC는 `rem`, 모바일은 고정 `px`
- padding/margin/gap: 고정 `px` 사용 (clamp, calc, vw 금지)
- 768px 이하: padding/margin은 PC 값의 **절반**

```css
/* correct - single line */
.section_name { position: relative; padding: 90px 0; width: 100%; }
.section_name .title { font-size: 1.5rem; }

/* correct - media query (no indent inside) */
@media screen and (max-width: 768px) {
.section_name { padding: 45px 0; }
.section_name .title { font-size: 14px; }
}

/* wrong - indented inside media query */
@media screen and (max-width: 768px) {
    .section_name { padding: 45px 0; }
}

/* wrong - multi-line */
.section_name {
    position: relative;
    padding: 90px;
}

/* wrong - clamp/calc for spacing */
.section_name { padding: clamp(45px, calc(90 / 1920 * 100vw), 90px) 0; }
```

### CSS 클래스 네이밍
- **페이지 프리픽스 형식**: `{페이지}_{역할}` (예: `main_visual`, `main_about`)
- `sec_1`, `sec_2`, `section_01` 같은 범용 이름 사용 금지
- 페이지 프리픽스 예시: `main_`, `company_`, `product_`, `support_`
- ul/ol/li/p처럼 태그 선택자에 의존해 스타일을 적용할 때는, 가능하면 요소별 클래스(`section_ul`, `section_li`, `section_p`)를 추가해 클래스 스타일로 대체한다.
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
- 프로젝트 설정에 따름 (고정값 없음)
- 디자인 스펙 또는 기존 CSS에서 확인

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

### Figma 텍스트 오버라이드 규칙 (중요)
- 텍스트 노드(`type: TEXT`)에서 `characterStyleOverrides`/`styleOverrideTable`가 존재하면 **반드시 반영**해야 함
- 추출 흐름:
  1) `node.characters`를 기준으로 문자를 순회
  2) 각 문자 인덱스별 `characterStyleOverrides` 값을 읽어 오버라이드 그룹(구간)으로 압축
  3) 구간별 스타일은 `node.style` + `node.fills`를 기본값으로 두고, `styleOverrideTable` 값으로 병합
  4) 오버라이드 값이 `0`인 구간은 기본 스타일 사용
  5) 오버라이드 스타일이 기본과 다르면 `<span>`으로 분할 출력
- `styleOverrideTable`에는 `style`, `fills`, `letterSpacing`, `lineHeightPx` 등 부분 스타일만 있을 수 있으므로 누락 값은 기본 스타일에서 상속
- `styleOverrideTable`가 비어 있는데도 결과가 다르면, 오버라이드 없는 동일 텍스트 노드라도 Figma 텍스트 계층(예: `styleId` 기반 공유 스타일)과 `fills` 비교 확인
- 추출 결과 예시는 텍스트 태그에 기본 클래스 + 오버라이드 구간별 클래스 조합 사용 (`{페이지}_text_{nodeId}_{overrideId}` 형태 권장)
- 오버라이드 노드가 1개라도 있으면 “텍스트 정상 추출됨” 판정에서 제외하고 수동 QA에서 실제 굵기/크기/색상 2차 확인
- `styleOverrideTable`에 폰트/굵기/색상 값이 없고 `lineHeightPx`·`letterSpacing`·`fills`만 있는 항목이 있을 경우, 해당 오버라이드는 직전 출력 구간의 실제 스타일 값을 상속해야 한다.
- 위 규칙 적용: `styleId` 구간별 병합 시 `node.style`를 단순 대입하지 않고, 이전 구간의 해석 결과(`styleId` 이전 구간 적용 스타일)를 기준으로 누락값을 보완해 `50px -> 37px` 같은 기본값 역주입이 일어나지 않게 해야 함.
- 텍스트에서 오버라이드가 붙는 구간은 가능하면 `style` 속성 인라인 대신 class 분리 규칙으로 출력한다.
- 동일한 스타일 서명은 전역 캐시로 묶어 재사용 클래스로 치환하고, 클래스명은 짧게 유지한다. (`t1`, `t2`, `t3` 등)
- 생성기에 의해 추가되는 자동 클래스 block은 `<style id="figma-inline-style-map">...</style>`로 관리해 중복 생성/삭제가 쉬워야 한다.
- 필수 병합 알고리즘:
  - `baseStyle = { ...node.style, fills: node.fills }`
  - `previousResolvedStyle = null`
  - 각 오버라이드 구간 처리:
    - overrideId가 `0`이거나 `styleOverrideTable[overrideId]`가 비어있으면 `resolvedStyle = baseStyle`
    - 나머지는 `resolvedStyle = { ...(previousResolvedStyle ?? baseStyle), ...(override.style ?? {}), ...(override.fills ? { fills: override.fills } : {}) }`
- `resolvedStyle`을 기준으로 클래스/인라인 계산 후 `previousResolvedStyle = resolvedStyle`로 갱신
- `fontSize`, `fontWeight`, `fontFamily`, 색상(`fills`)은 `resolvedStyle`에서 누락된 경우 `previousResolvedStyle` 값이 유지되어야 함
- `lineHeightPx`는 CSS `line-height`로, `letterSpacing`은 `letter-spacing`으로 매핑해 출력

## 레이아웃 추출 보정 규칙 (좌표 기반)

- Figma에서 동일 부모 내 두 개 이상의 박스가 서로 같은 줄(`y`)에 있고, 동일하거나 유사한 높이를 가질 때는 자동 레이아웃 플래그가 없더라도 실제로는 가로 정렬(1 row)일 가능성이 높다.
- 같은 `y`를 가지는 블록이 2개라면 기본값으로 세로 스택을 배제하고 `grid` 또는 `inline-flex` 행 정렬을 우선한다.
- 좌우 폭 차이가 크고 첫 칼럼/둘째 칼럼 위치가 일정하다면 `grid-template-columns`로 고정/비율 너비를 반영한다.
- `brainbody_problem` 구간 사례: 우측 카드 2개는 `y`가 동일한 상태에서 좌우로 존재하므로 HTML/CSS는 2열(가로) 구조로 유지한다.

---

## 주의사항
- 요청하지 않은 기능 추가 금지
- 허락 없이 리팩토링 금지
- 최소한의 변경만
- 보안 이슈 주의 (XSS 등)

---

## 참고
- 상세 HTML/CSS 패턴은 `basic_rules.md` 참조

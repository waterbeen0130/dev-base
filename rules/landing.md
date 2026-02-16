# 랜딩페이지 규칙

> `common.md` 규칙 기본 적용, 아래는 랜딩페이지 전용 규칙

---

## Basic과 다른 점

### CSS
- font-size: PC/모바일 모두 **고정 px**
- padding/margin: PC/모바일 모두 **고정 px**
- rem 단위 사용 안 함

```css
/* landing - PC/모바일 모두 고정 px */
.section_name { padding: 90px 0; }
.section_name .title { font-size: 32px; }

@media screen and (max-width: 768px) {
    .section_name { padding: 50px 0; }
    .section_name .title { font-size: 20px; }
}
```

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

## 주의사항
- reset 스타일에 웹폰트 포함 금지
- CSS 변수 및 애니메이션 스타일 삭제 금지
- CDN 버전 변경 시 호환성 확인
- 피그마 줄바꿈(`\n`)은 HTML에서 `<br>`로 그대로 반영 (PC/모바일 각각 적용)
- 이미지 기반 섹션은 원본 이미지 픽셀 높이에 맞춰 섹션 `height` 지정하고 `object-fit: cover` 적용
- 섹션 내부 이미지(`img`)는 `width: 100%` 등 % 기반으로 지정하고 `aspect-ratio`로 비율 유지 (고정 width/height 금지)
- 모바일 전용 이미지는 반드시 사용하고, 모바일 이미지 픽셀 크기 기준으로 배치/크기 조정
- ul/ol/li/p처럼 구조 태그에 직접 묶인 스타일은 가급적 피하고, 가능한 한 각 요소에 `..._ul`, `..._li`, `..._p` 형태 클래스명을 부여해 클래스 단위로 스타일링한다.
- 텍스트 추출 시 `characterStyleOverrides`가 있는 노드는 오버라이드 구간별로 `<span>` 분리하여 굵기/크기/색상 차이를 보존
- 오버라이드 텍스트는 추출 후 `textAlign`과 줄바꿈 위치를 실제 Figma 기준으로 1차 검증해야 함
- `styleOverrideTable`에 일부 스타일만 있는 오버라이드(예: `lineHeightPx`만 있는 항목)는 직전 오버라이드 구간의 실제 적용 스타일(폰트/굵기/색상)을 상속해서 병합해야 함
- `characterStyleOverrides`에서 라인 간격 값이 바뀌는 구간은 기본 `node.style`로 되돌리는 방식이 아니라 `누적 오버라이드 병합`으로 처리해 폰트 크기, 굵기 튐(예: 50px→37px 역전) 오류를 막는다
- 텍스트 오버라이드 구간은 가능하면 인라인 `style` 대신 클래스 기반으로 출력하고, 동일 스타일은 재사용 클래스로 묶어 길이와 중복을 줄인다.
- 생성된 텍스트 클래스는 `<style id="figma-inline-style-map">` 블록에서 한 번에 관리한다.
- 텍스트 오버라이드 병합의 강제 규칙:
  - `baseStyle = { ...node.style, fills: node.fills }`
  - `previousResolvedStyle = null`
  - 각 오버라이드 구간 처리:
    - overrideId `0` 또는 오버라이드가 비어 있으면 `resolvedStyle = baseStyle`로 초기화
    - 그 외에는 `resolvedStyle = { ...(previousResolvedStyle ?? baseStyle), ...(override.style ?? {}), ...(override.fills ? { fills: override.fills } : {}) }`
  - `resolvedStyle`로 출력 후 `previousResolvedStyle = resolvedStyle` 갱신
  - `fontSize`, `fontWeight`, `fontFamily`, `fills`는 미지정일 때만 이전 값 유지, `lineHeightPx`/`letterSpacing`은 각각 `line-height`/`letter-spacing`으로 매핑

> 브레인바디 랜딩 전용 규칙은 `brainbody_extraction_automation.md`에서 추가로 적용한다.

## 브레인바디 랜딩 특화 추출 규칙 (반복 재현용)

다음 규칙은 동일 페이지를 재추출할 때 동일한 HTML/CSS 차이를 재현하기 위한 전용 필수 규칙입니다.

### 텍스트 태그 규칙
- 문단이 아닌 짧은 라벨/브랜딩 문구는 `<span>`로 유지한다.
- `BrainBody`, `MRI`, `Greenmall`, `영상의학과`, `원스톱 토탈케어` 등 라벨성 키워드는 절대 `<p>`로 바꾸지 않는다.
- `p`는 줄바꿈이 있는 경우나 실제 문단성 텍스트(긴 문장)에 한해서만 허용한다.

### 클래스 최소화 규칙
- 블록 단위 클래스는 필수 최소 집합만 사용하고, 내부 아이템은 `.title`, `.value` 같은 의미 클래스 + 자식 선택자로 표기한다.
- 동일한 스타일 반복 구간은 `nth-child`보다 의미 클래스를 우선한다(색상 강조/강조색 텍스트 등).
- `t1`, `g137` 같은 연속 클래스 번호 기반 생성 방식은 지양하고, 구조적/의미적 클래스 또는 부모+자식 선택자로 통일한다.

### 레이아웃 규칙
- 같은 부모에서 `y` 정렬이 같고 높이가 유사한 항목은 세로 스택이 아닌 행 구조(`inline-flex`/`grid`)로 추출한다.
- 고정 폭이 들어간 컨테이너는 반응형에서 `max-width` + `margin: 0 auto` 패턴으로 변환한다.
- 리스트/카드 블록의 `ul > li`는 `ul li`로 완화하고, 구조가 고정될 수 있는 구간만 `>`.

### 스타일 정리 규칙
- 불필요한 `width: 100%` 제거, 블록 기본은 비워두거나 `max-width` 기반 처리.
- `background-color`는 실제 배경 레이어가 있을 때만 선언.
- `line-height`는 가능하면 비율(`1.2`)로 변환하여 반응형 폭에서 유지.

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
- 시맨틱 태그 사용 (`<header>`, `<main>`, `<section>`, `<article>`, `<footer>`)
- 모든 이미지에 `alt` 속성 필수
- 버튼에 `type="button"` 명시
- 폼 요소는 `<label>`과 연결

### CSS
- **한 줄 포맷으로 작성** (미디어쿼리 블록 제외)
- font-size: PC는 `rem`, 모바일은 고정 `px`
- padding/margin: 고정 `px` 사용
- 768px 이하: padding/margin은 PC 값의 **절반**

```css
/* correct - single line */
.section_name { position: relative; padding: 90px 0; width: 100%; }
.section_name .title { font-size: 1.5rem; }

/* correct - media query (768px 이하) */
@media screen and (max-width: 768px) {
    .section_name { padding: 45px 0; }
    .section_name .title { font-size: 14px; }
}

/* wrong - multi-line */
.section_name {
    position: relative;
    padding: 90px;
}
```

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

## 파일 구조
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

---

## 필수 규칙 (반드시 준수)

> **피그마 텍스트 그대로 추출**
> - 피그마에 기재된 텍스트를 그대로 사용
> - 추측해서 변경하거나 추가 금지
> - 오타가 있어도 그대로 추출 (수정 필요시 별도 안내)

---

## 주의사항
- 요청하지 않은 기능 추가 금지
- 허락 없이 리팩토링 금지
- 최소한의 변경만
- 보안 이슈 주의 (XSS 등)

---

## 참고
- 상세 HTML/CSS 패턴은 `basic_rules.md` 참조

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

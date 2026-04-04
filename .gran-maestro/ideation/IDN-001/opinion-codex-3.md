# 반응형·인터랙션·애니메이션 실전 규칙 제안

> 작성 기준: 현재 프로젝트 규칙 (breakpoints: 1400/1200/960/768, desktop-first, GSAP + Slick 환경) 기반

---

## 1. 터치 영역 최소 크기

**규칙**: 모바일 버튼·링크·아이콘 클릭 영역은 최소 44×44px 확보.
시각적 크기가 작아도 `padding` 또는 `::after` 가상 요소로 터치 영역 확장.

```css
/* 공통 패턴 */
.btn, a, [role="button"] {
  min-height: 44px;
  min-width: 44px;
}

/* 아이콘처럼 시각적으로 작은 요소 */
.icon-btn {
  position: relative;
}
.icon-btn::after {
  content: "";
  position: absolute;
  inset: -10px;   /* 터치 영역 확장 */
}
```

- **적용**: 공통 (basic/landing 모두)
- **rule_engine.json 초안**:
```json
{
  "id": "touch-target-min-size",
  "category": "interaction",
  "scope": "common",
  "rule": "모바일 터치 요소 최소 44×44px (padding 또는 ::after 확장)",
  "pattern": "min-height: 44px; min-width: 44px",
  "breakpoint": "768"
}
```

---

## 2. Hover 상태 규칙 (모바일 비활성화)

**규칙**: PC hover 효과는 `@media (hover: hover) and (pointer: fine)` 조건으로 감싸 터치 기기에서 sticky hover 방지.

```css
/* 잘못된 패턴 — 모바일에서 sticky hover 발생 */
.btn:hover { background: #333; }

/* 올바른 패턴 */
@media (hover: hover) and (pointer: fine) {
  .btn:hover { background: #333; }
  .card:hover .card__thumb img { transform: scale(1.05); }
}
```

- **적용**: 공통
- **rule_engine.json 초안**:
```json
{
  "id": "hover-media-query",
  "category": "interaction",
  "scope": "common",
  "rule": "PC hover 효과는 @media (hover: hover) and (pointer: fine) 내부에만 작성",
  "pattern": "@media (hover: hover) and (pointer: fine) { ... }"
}
```

---

## 3. Slick 슬라이더 마크업 패턴

**규칙**: 슬라이더 래퍼·트랙·네비게이션 클래스명을 BEM 기반으로 표준화하여 JS 초기화 타겟을 일관되게 유지.

```html
<!-- 표준 마크업 구조 -->
<div class="slider-wrap">
  <div class="slider js-slider">          <!-- Slick 초기화 타겟 -->
    <div class="slider__item"> ... </div>
    <div class="slider__item"> ... </div>
  </div>
  <div class="slider-nav">
    <button class="slider-nav__prev" aria-label="이전">&#8249;</button>
    <button class="slider-nav__next" aria-label="다음">&#8250;</button>
  </div>
  <div class="slider-dots"></div>        <!-- appendDots 타겟 -->
</div>
```

```js
$('.js-slider').slick({
  prevArrow: $('.slider-nav__prev'),
  nextArrow: $('.slider-nav__next'),
  appendDots: $('.slider-dots'),
  dots: true
});
```

- **적용**: landing (공통 확장 가능)
- **rule_engine.json 초안**:
```json
{
  "id": "slick-markup-convention",
  "category": "component",
  "scope": "landing",
  "rule": "Slick 초기화 타겟 .js-slider, 아이템 .slider__item, 네비 .slider-nav__prev/.next, 도트 .slider-dots",
  "pattern": ".js-slider / .slider__item / .slider-nav__prev / .slider-nav__next / .slider-dots"
}
```

---

## 4. GSAP ScrollTrigger 초기화 패턴

**규칙**: 섹션 진입 시 `.section_on` 클래스 토글을 ScrollTrigger 단일 패턴으로 표준화. `data-delay` / `data-direction` 속성으로 JS 코드 중복 제거.

```js
/* 표준 초기화 패턴 */
document.querySelectorAll('[data-scroll-section]').forEach(section => {
  const delay = parseFloat(section.dataset.delay) || 0;
  const dir   = section.dataset.direction || 'up';   // up | down | left | right

  const fromVars = {
    up:    { y: 40, opacity: 0 },
    down:  { y: -40, opacity: 0 },
    left:  { x: -40, opacity: 0 },
    right: { x: 40, opacity: 0 }
  }[dir];

  ScrollTrigger.create({
    trigger: section,
    start: 'top 80%',
    onEnter: () => {
      gsap.fromTo(section, fromVars, {
        x: 0, y: 0, opacity: 1,
        duration: 0.7,
        delay,
        ease: 'power2.out',
        onComplete: () => section.classList.add('section_on')
      });
    }
  });
});
```

```html
<section data-scroll-section data-direction="up" data-delay="0.2"> ... </section>
```

- **적용**: landing
- **rule_engine.json 초안**:
```json
{
  "id": "gsap-scroll-trigger-pattern",
  "category": "animation",
  "scope": "landing",
  "rule": "[data-scroll-section] 속성으로 ScrollTrigger 일괄 초기화, data-delay/data-direction 속성 제어",
  "pattern": "data-scroll-section / data-delay / data-direction / .section_on"
}
```

---

## 5. CSS 트랜지션 성능 (will-change / 3D 가속)

**규칙**: 애니메이션 직전 `will-change` 적용, 완료 후 `auto` 해제. GPU 가속은 `translateZ(0)` 또는 `translate3d`를 사용하되 전체 적용 금지.

```css
/* will-change: 애니메이션 요소에만 한정 적용 */
.animate-target {
  will-change: transform, opacity;
}
.animate-target.section_on {
  will-change: auto;   /* 완료 후 해제 */
}

/* transform 3D 가속 — 슬라이더·오버레이 레이어에 적용 */
.slider,
.modal-overlay {
  transform: translateZ(0);   /* 합성 레이어 승격 */
  backface-visibility: hidden;
}
```

- **적용**: 공통
- **rule_engine.json 초안**:
```json
{
  "id": "css-performance-will-change",
  "category": "performance",
  "scope": "common",
  "rule": "will-change는 애니메이션 요소에만, 완료 후 auto 해제. 슬라이더/오버레이는 translateZ(0) 레이어 승격",
  "pattern": "will-change: transform, opacity → will-change: auto / translateZ(0)"
}
```

---

## 6. Sticky/Fixed 요소 처리

**규칙**: 헤더 sticky는 `position: sticky; top: 0`과 `z-index` 계층 관리. Fixed 플로팅 버튼은 모바일 하단 safe area 대응 (`env(safe-area-inset-bottom)`) 포함.

```css
/* 헤더 sticky */
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
}

/* 플로팅 버튼 — iOS safe area 대응 */
.floating-btn {
  position: fixed;
  right: 20px;
  bottom: calc(20px + env(safe-area-inset-bottom));
  z-index: 200;
}

/* z-index 계층 규칙 */
/* header: 100 / floating: 200 / modal: 300 / toast: 400 */
```

- **적용**: 공통
- **rule_engine.json 초안**:
```json
{
  "id": "sticky-fixed-zindex-layer",
  "category": "layout",
  "scope": "common",
  "rule": "z-index 계층: header 100 / floating 200 / modal 300 / toast 400. fixed 하단 요소는 env(safe-area-inset-bottom) 적용",
  "pattern": "z-index: 100/200/300/400 / env(safe-area-inset-bottom)"
}
```

---

## 7. Loading/Skeleton 상태

**규칙**: 랜딩 초기 로딩은 `.page-loader` 오버레이로 처리하고 콘텐츠 로드 완료 시 fade-out 제거. Skeleton UI는 `background: linear-gradient` 애니메이션으로 구현.

```css
/* 페이지 로더 */
.page-loader {
  position: fixed; inset: 0;
  background: #fff;
  z-index: 9999;
  transition: opacity 0.4s ease;
}
.page-loader.is-hidden {
  opacity: 0;
  pointer-events: none;
}

/* Skeleton shimmer */
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}
```

```js
window.addEventListener('load', () => {
  document.querySelector('.page-loader')?.classList.add('is-hidden');
});
```

- **적용**: landing
- **rule_engine.json 초안**:
```json
{
  "id": "loading-skeleton-pattern",
  "category": "ux",
  "scope": "landing",
  "rule": "페이지 로더: .page-loader fixed 오버레이 + .is-hidden fade-out. Skeleton: shimmer gradient 애니메이션",
  "pattern": ".page-loader / .is-hidden / .skeleton / @keyframes shimmer"
}
```

---

*생성일: 2026-02-18 | 작성자: Codex (반응형·인터랙션 전문가 역할)*

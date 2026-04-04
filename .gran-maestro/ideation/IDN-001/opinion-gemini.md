# Gemini 의견서 — 웹 표준·접근성·성능 최적화 규칙 제안

> 작성 기준: 웹 표준(HTML Living Standard), WCAG 2.2, Core Web Vitals 관점
> 작성일: 2026-02-18
> 대상 규칙 체계: basic / landing / 공통

---

## 1. 이미지 최적화 — loading="lazy" 및 srcset/picture

**제안 규칙**: ATF(Above The Fold) 영역 이미지에는 `loading="eager"`(기본값 유지), ATF 외 모든 `<img>`에 `loading="lazy"` 기본 적용. 반응형 이미지는 2x 레티나 대응 기준 이상일 때 `srcset`, 포맷 분기가 필요한 경우(WebP/AVIF 폴백) `<picture>` 사용.
**적용 범위**: 공통 (basic·landing 모두)
**충돌 여부**: 현행 `img 래퍼 필수` 규칙과 충돌 없음. 래퍼 `div`에 aspect-ratio 지정 시 CLS 방지와 시너지.

---

## 2. 폰트 로딩 최적화 — font-display 및 preload

**제안 규칙**: 자체 호스팅 폰트에 `font-display: swap` 필수 적용. 페이지 최초 렌더링에 사용되는 웨이트(통상 Regular·Bold 1~2종)만 `<link rel="preload" as="font" crossorigin>` 힌트 추가. CDN 폰트(Google Fonts 등)는 `&display=swap` 파라미터로 동일 효과 확보.
**적용 범위**: 공통
**충돌 여부**: 현행 규칙에 폰트 관련 항목 없음. 신규 추가이므로 충돌 없음.

---

## 3. 포커스·키보드 네비게이션 — :focus-visible 및 outline

**제안 규칙**: `outline: none` / `outline: 0` 전면 금지. 마우스 클릭 시 포커스 링 숨김은 `:focus:not(:focus-visible) { outline: none }` 패턴으로 한정. `:focus-visible`에는 `outline: 2px solid {브랜드 컬러}; outline-offset: 2px` 이상을 기본 제공.
**적용 범위**: 공통
**충돌 여부**: 현행 `aria-hidden 최소 사용` 방침과 방향 일치. CSS hex 색상 규칙 내에서 outline 색상 정의 가능하므로 충돌 없음.

---

## 4. 시맨틱 헤딩 계층 — h1~h6 사용 기준

**제안 규칙**: 페이지당 `<h1>` 1개 필수. h1→h2→h3 순서로 레벨 건너뛰기 금지(예: h2 다음 h4 사용 불가). 시각적 크기 조정이 필요한 경우 헤딩 레벨은 유지하고 CSS로 재정의. 섹션 제목이 없는 영역은 `aria-label`로 섹션 구분.
**적용 범위**: 공통
**충돌 여부**: 현행 `aria-label 최소화` 방침과 부분 긴장 관계. 단, aria-label 사용을 "섹션 구분 목적으로 한정"하는 예외 조항으로 정리하면 충돌 해소 가능.

---

## 5. 모바일 Safe Area — env(safe-area-inset-*)

**제안 규칙**: 하단 고정 요소(`position: fixed; bottom: 0`)와 전체 화면 배경에 `padding-bottom: env(safe-area-inset-bottom)` 적용. HTML `<meta name="viewport">`에 `viewport-fit=cover` 추가를 필수화하여 env() 값이 활성화되도록 보장.
**적용 범위**: landing (모바일 UX 집중), basic은 선택 적용
**충돌 여부**: 현행 규칙에 viewport 관련 항목 없음. 신규 추가이므로 충돌 없음.

---

## 6. 색상 대비 — WCAG 명도 대비비 기준

**제안 규칙**: 본문 텍스트(18px 미만 일반체, 14px 미만 볼드체 미만)는 배경 대비 **4.5:1 이상**(WCAG AA). 대형 텍스트(18px 이상 일반체 또는 14px 이상 볼드체)는 **3:1 이상**. UI 컴포넌트 경계선 및 아이콘은 3:1 이상. hex 색상 규칙을 유지하되 팔레트 정의 시 대비비 통과 여부를 주석으로 명시.
**적용 범위**: 공통
**충돌 여부**: 현행 `hex only 색상` 규칙과 완전 호환. dark/light 모드 미지원 상태이므로 단일 팔레트 기준 대비비 검증으로 충분.

---

## 7. Print 스타일 — 인쇄 최적화

**제안 규칙**: `@media print` 블록을 공통 스타일시트 말미에 배치. 네비게이션, 사이드바, 동영상, 광고, 고정 헤더/푸터는 `display: none`. 링크 URL 노출은 `a[href]::after { content: " (" attr(href) ")" }` 패턴 적용(단, 내부 앵커·자바스크립트 링크는 제외). 페이지 단절이 부적절한 표·이미지에 `page-break-inside: avoid` 추가.
**적용 범위**: landing (콘텐츠 페이지 중심), basic은 선택 적용
**충돌 여부**: 현행 규칙에 print 관련 항목 없음. 신규 추가이므로 충돌 없음.

---

## 종합 우선순위 권고

| 우선순위 | 항목 | 이유 |
|----------|------|------|
| 즉시 적용 | 3. 포커스/키보드, 4. 헤딩 계층, 6. 색상 대비 | 접근성 법적 요건, WCAG AA 충족 |
| 단기 적용 | 1. 이미지 lazy, 2. 폰트 preload | Core Web Vitals LCP·CLS 직접 영향 |
| 중기 적용 | 5. Safe Area, 7. Print | 모바일 UX 개선 및 콘텐츠 품질 |

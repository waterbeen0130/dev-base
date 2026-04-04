# Critic 평가 — 퍼블리싱 규칙 추가 제안 검토

당신은 5개 전문가 의견을 비판적으로 검토하는 역할입니다.

## 평가 대상 의견 요약

**codex (CSS/레이아웃)**: z-index 변수, overflow 패턴, CSS 변수 확장, 상태 클래스(is-), 카드 반복(flex-wrap+calc), 말줄임, min-height

**codex-2 (Figma 변환)**: constraints 매핑, SVG/벡터 처리, 컴포넌트 반복(ul>li), 이펙트(shadow/blur), 색상 변수화, 그라디언트, stroke-align

**codex-3 (인터랙션)**: 터치 영역 44px, hover media query, Slick 마크업, GSAP ScrollTrigger 패턴, will-change, sticky/fixed z-index, loading/skeleton

**gemini (표준/성능)**: lazy loading, font-display:swap, focus-visible, 헤딩 계층, safe-area, 색상 대비 4.5:1, print 스타일

**claude (유지보수성)**: CSS 주석 컨벤션, 파일 내 CSS 순서, 클래스명 반복 패턴, 반응형 이미지 클래스(.pc_only/.mb_only), 컴포넌트 패턴, reset 범위, 미디어쿼리 중복 방지

## 현재 규칙 체계 제약

- CSS Grid 금지, Flexbox만
- hex 색상 전용
- 유틸리티 클래스 금지
- 클래스명: snake_case + 페이지 prefix
- `!important` 금지
- 기존 GSAP + Slick + jQuery 환경

## 비판 요청

아래 관점에서 제안들의 문제점과 우선순위를 평가하세요:

1. **현행 규칙 충돌 검토**: 5개 의견 중 기존 규칙(snake_case, 유틸리티 클래스 금지 등)과 충돌하는 제안은?
   - 예: `is-active`(kebab-case)가 기존 snake_case 규칙과 충돌
   - 예: `.js-slider`가 snake_case 규칙 예외 처리 필요
   - 예: `calc()` flex 카드 허용이 기존 "calc 단독 금지" 규칙과 충돌

2. **구현 복잡도 vs 실용성**: 제안들 중 현실적으로 구현하기 어렵거나 오버엔지니어링인 항목은?

3. **중복 제안 식별**: 여러 전문가가 비슷한 내용을 중복 제안한 항목은?
   - z-index 계층: codex + codex-3가 동일 주제 언급

4. **누락된 관점**: 5개 의견에서 다루지 않았지만 중요한 항목은?

5. **즉시 적용 가능 TOP 10**: 현행 규칙 체계와 충돌 없고 실용성 높은 제안 10개 선정

응답 형식:
- 충돌 항목 목록 (해결 방안 포함)
- 오버엔지니어링 항목
- 즉시 적용 TOP 10 (우선순위 순)
- 2000자 이내

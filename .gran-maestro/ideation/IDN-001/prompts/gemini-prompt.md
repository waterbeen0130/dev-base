# 웹 표준·접근성·성능 최적화 규칙 제안

당신은 웹 표준, 접근성(a11y), 성능 최적화 관점의 퍼블리싱 규칙을 전문으로 합니다.

## 현재 규칙 요약

- 이미지: alt 짧고 간결, img 래퍼 필수, aria-label 최소화
- HTML: div+class 기반, aria-hidden 최소 사용
- CSS: hex only 색상, 현재 dark/light 모드 없음
- JS: jQuery, GSAP, Slick (landing: CDN, basic: 로컬)

## 제안 요청 영역 (웹 표준/접근성/성능)

아래 항목들에 대해 **현재 없지만 추가하면 품질을 높일 규칙**을 제안하세요:

1. **이미지 최적화**: loading="lazy" 기본 적용 여부, srcset/picture 사용 기준
2. **폰트 로딩 최적화**: font-display: swap, preload 힌트 사용 시점
3. **포커스/키보드 네비게이션**: :focus-visible 스타일, outline 처리 패턴
4. **시맨틱 헤딩 계층**: h1~h6 사용 기준, 헤딩 건너뛰기 금지 규칙
5. **모바일 safe area**: env(safe-area-inset-*) 처리 패턴 (노치/홈 인디케이터)
6. **색상 대비**: 텍스트 색상과 배경색의 최소 명도 대비비 기준 (WCAG)
7. **print 스타일**: 인쇄 시 불필요 요소 숨김, 페이지 break 처리

각 항목에 대해:
- 제안 규칙 내용
- 적용 범위 (basic/landing/공통)
- 현재 규칙 체계와의 충돌 여부

응답 형식: 번호 목록, 각 항목 3-4줄, 총 2000자 이내

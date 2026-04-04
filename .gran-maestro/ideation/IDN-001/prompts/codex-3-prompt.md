# 반응형·인터랙션·애니메이션 실전 규칙 제안

당신은 실제 프로덕션 퍼블리싱에서 자주 필요한 인터랙션·애니메이션 규칙을 전문으로 합니다.

## 현재 규칙 요약

- Breakpoints: 1400, 1200, 960, 768 (desktop-first, max-width)
- 기본 트랜지션: `transition: all 0.3s ease-out`
- GSAP ScrollTrigger + Slick 슬라이더 사용 (landing CDN)
- GSAP 애니메이션: `[data-delay]`, `[data-direction]`, `.section_on` 클래스 토글
- 반응형 줄바꿈: `<br class="mb_only">` / `<br class="pc_only">`
- 모바일: padding/margin PC 값의 절반 (basic 프로젝트)

## 제안 요청 영역 (반응형/인터랙션/애니메이션)

아래 항목들에 대해 **현재 없지만 인터랙션 품질을 높일 규칙**을 제안하세요:

1. **터치 영역 최소 크기**: 모바일 버튼/링크 터치 영역 (44px 이상)
2. **hover 상태 규칙**: PC hover 효과를 모바일에서 비활성화하는 패턴 (@media hover: hover)
3. **Slick 슬라이더 마크업 패턴**: 슬라이더 래퍼 구조, 네비게이션 클래스명 컨벤션
4. **GSAP ScrollTrigger 초기화 패턴**: 섹션 진입 시 section_on 클래스 추가 패턴 표준화
5. **CSS 트랜지션 성능**: will-change 사용 시점, transform 3D 가속 활용 패턴
6. **Sticky/Fixed 요소 처리**: 헤더 sticky, 플로팅 버튼 fixed 포지셔닝 패턴
7. **Loading/Skeleton 상태**: 로딩 중 UI 표현 패턴 (랜딩페이지 초기 로딩)

각 항목에 대해:
- 제안 규칙 내용 (구체적 CSS/HTML 패턴 포함)
- 적용 프로젝트 (basic/landing/공통)
- rule_engine.json 추가 시 JSON 형식 초안

응답 형식: 번호 목록, 각 항목 3-4줄, 총 2000자 이내

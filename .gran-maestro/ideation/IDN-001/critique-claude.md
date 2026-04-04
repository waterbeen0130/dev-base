# Critic 평가 — 퍼블리싱 규칙 추가 제안 비판적 검토

> 작성일: 2026-02-18
> 역할: 5개 전문가 의견 비판적 검토자

---

## 1. 현행 규칙 충돌 항목

| 제안 | 충돌 규칙 | 해결 방안 |
|------|-----------|-----------|
| codex #4 `is-active`/`has-icon` (kebab-case) | snake_case 클래스명 규칙 | 상태 접두사(`is-`, `has-`)를 snake_case 예외로 명시. `is_active` 형태는 가독성이 떨어지므로 kebab 허용이 합리적 |
| codex-3 #3 `.js-slider`, `.slider__item` (BEM/kebab) | snake_case 규칙, 유틸리티 클래스 금지 | JS 훅 클래스(`js-` 접두사)를 별도 예외 카테고리로 분리. Slick은 외부 라이브러리이므로 마크업 컨벤션을 snake_case로 강제하면 오히려 혼란 |
| codex #5 `calc((100% - 48px) / 3)` | calc 단독 사용 금지(clamp 내부만 허용) | flex 카드 폭 계산 한정 calc 예외를 명시. 단, 예외 범위가 넓어지면 규칙 자체가 무력화될 위험 |
| codex-3 #7 `.skeleton`, `.page-loader` | 유틸리티/범용 클래스 금지, snake_case | 페이지 접두사 적용하여 `{page}_loader`, `{page}_skeleton`으로 변환 |
| codex-2 #4 shadow color에 `rgba()` 사용 | hex 색상 전용 규칙 | alpha가 필요한 shadow/gradient 한정 rgba 허용 예외 추가. 이미 그라디언트 stop에서도 동일 문제 발생 |
| codex-3 #6 `z-index: 100/200/300/400` 직접 숫자 | codex #1의 CSS 변수 방식과 충돌 | 두 의견을 통합하여 CSS 변수 방식으로 단일화 |

---

## 2. 오버엔지니어링 항목

- **codex-2 #1 constraints 매핑**: FILL/FIXED/SCALE/CENTER/MIN/MAX 전체 분기를 rule_engine에 넣는 것은 Figma 변환 스크립트 로직이지 퍼블리싱 규칙이 아님. 스크립트 내부 로직으로 처리하고 규칙 문서에서는 제외가 적절
- **codex-2 #6 그라디언트 각도 계산**: `gradientHandlePositions` 기반 각도 계산은 순수 변환 알고리즘 영역. 규칙으로 관리할 대상이 아님
- **codex-3 #4 GSAP ScrollTrigger 표준 패턴**: JS 초기화 코드 전체를 규칙화하는 것은 과도. `data-scroll-section` 속성 컨벤션과 `.section_on` 클래스명 정도만 규칙으로 남기고, 구현 코드는 보일러플레이트 템플릿으로 분리
- **gemini #7 Print 스타일**: 랜딩 페이지 인쇄 수요는 극히 낮음. 우선순위 최하위로 보류
- **codex-3 #7 Skeleton UI**: 현재 프로젝트에서 Skeleton이 필요한 동적 로딩 시나리오가 없다면 시기상조

---

## 3. 중복 제안 식별

- **z-index 계층**: codex #1 (CSS 변수 방식) + codex-3 #6 (숫자 직접 배정) -- codex의 변수 방식이 유지보수에 유리하므로 채택
- **overflow/말줄임**: codex #2 (overflow 패턴) + codex #6 (말줄임 패턴) -- 말줄임이 overflow의 하위 범주이므로 하나의 규칙으로 통합
- **safe-area**: gemini #5 + codex-3 #6 -- 둘 다 `env(safe-area-inset-bottom)` 언급. 통합
- **상태 클래스**: codex #4 (`is-active`) + codex-3 #7 (`.is-hidden`) -- 동일 패턴이므로 codex #4로 통합
- **색상 변수화**: codex #3 (CSS 변수 확장) + codex-2 #5 (Figma 색상 변수화) -- 출력 형태가 동일하므로 하나의 변수 체계 규칙으로 병합

---

## 4. 누락된 관점

- **CSS 속성 선언 순서**: 어떤 의견도 속성 정렬 순서(position > display > box-model > typography > visual > misc)를 다루지 않음. 한 줄 포맷이라 중요도가 더 높음
- **img alt 텍스트 작성 기준**: gemini가 접근성을 다루면서도 alt 텍스트 규칙은 누락. 장식 이미지 `alt=""` vs 의미 이미지 구분 기준 필요
- **transition 속성 범위 제한**: `all` 사용 금지 여부. 성능과 의도 명확성에 영향

---

## 5. 즉시 적용 TOP 10

| 순위 | 제안 | 출처 | 선정 이유 |
|------|------|------|-----------|
| 1 | z-index CSS 변수 계층 | codex #1 | 충돌 없음, 기존 :root 확장, 즉시 검증 가능 |
| 2 | 미디어쿼리 중복 방지 (breakpoint당 1블록) | claude #7 | 충돌 없음, validation 즉시 연동, AI 오류 빈발 구간 |
| 3 | CSS 파일 내 구조 순서 | claude #2 | 충돌 없음, 탐색성 대폭 향상 |
| 4 | reset 범위 명시 | claude #6 | 충돌 없음, 레이아웃 버그 사전 차단 |
| 5 | 말줄임 처리 패턴 (1줄/N줄) | codex #6 | 충돌 없음, 유틸리티 클래스 금지 원칙 부합 |
| 6 | min-height vs height 정책 | codex #7 | 충돌 없음, 반응형 깨짐 예방 |
| 7 | hover media query 분리 | codex-3 #2 | 충돌 없음, 모바일 sticky hover 버그 제거 |
| 8 | font-display: swap 필수 | gemini #2 | 충돌 없음, 신규 추가, LCP 개선 |
| 9 | 이미지 loading="lazy" | gemini #1 | 충돌 없음, 신규 추가, 성능 즉시 개선 |
| 10 | 이펙트(shadow/blur) 매핑 | codex-2 #4 | Figma 변환 정확도 즉시 향상, 기존 border_stroke 섹션 확장 |

---

**총평**: 35개 제안 중 현행 규칙과 직접 충돌하는 항목은 6건이며, 대부분 "예외 조항 추가"로 해소 가능하다. 다만 예외가 누적되면 규칙 체계의 일관성이 약화되므로, snake_case 예외(상태 클래스, JS 훅)와 hex 예외(alpha 필요 시 rgba)는 공통 규칙 상단에 "허용 예외 목록"으로 한 번에 정리하는 것이 바람직하다. claude 의견의 "규칙 중복 문제를 먼저 해결한 후 추가"라는 지적이 가장 핵심적이다.

# IDN-001 종합 의견서
## 퍼블리싱 규칙 추가 제안 — PM 종합

> 참여자: codex (CSS/레이아웃), codex-2 (Figma 변환), codex-3 (인터랙션), gemini (표준/성능), claude (유지보수성)
> Critic: claude | 생성: 2026-02-18

---

## 🏆 즉시 적용 TOP 10 (Critic 선정, 규칙 충돌 없음)

| 순위 | 제안 | 범위 | 핵심 내용 |
|------|------|------|-----------|
| 1 | **z-index CSS 변수 계층** | 공통 | `--z-sticky:100`, `--z-header:300`, `--z-modal:400` `:root`에 정의, 임의 숫자 금지 |
| 2 | **미디어쿼리 중복 방지** | 공통 | 동일 breakpoint `@media` 블록 파일 내 1개만 허용, 큰 값부터 정렬 |
| 3 | **CSS 파일 내 구조 순서** | 공통 | `:root` → reset → 공통 레이아웃 → 섹션별 → 미디어쿼리 |
| 4 | **reset 범위 명시** | 공통 | `box-sizing`, `img{display:block}`, `button{border:none}`, `ul{list-style:none}` 필수 포함 |
| 5 | **말줄임 처리 패턴** | 공통 | 단일줄: `overflow:hidden; text-overflow:ellipsis; white-space:nowrap` 세트 선언 |
| 6 | **min-height vs height 정책** | 공통 | 가변 컨테이너 `height` 금지 → `min-height` 사용, 아이콘/버튼류만 고정 허용 |
| 7 | **hover 미디어쿼리 분리** | 공통 | PC hover는 `@media (hover: hover) and (pointer: fine)` 내부에만 작성 |
| 8 | **font-display: swap** | 공통 | 자체 호스팅 폰트 필수, CDN은 `&display=swap` 파라미터 |
| 9 | **이미지 loading="lazy"** | 공통 | ATF 외 모든 `<img>`에 `loading="lazy"` 기본 적용 |
| 10 | **이펙트(shadow/blur) 매핑** | 공통 | DROP_SHADOW→box-shadow, LAYER_BLUR→filter, BACKGROUND_BLUR→backdrop-filter |

---

## ⚠️ 적용 시 규칙 예외 정리 필요 항목

| 제안 | 충돌 규칙 | 해결 방안 |
|------|-----------|-----------|
| 상태 클래스 `is-active`, `has-icon` | snake_case 전용 | 상태 접두사(`is-`, `has-`)를 kebab-case 허용 예외로 명시 |
| Slick `.js-slider` | snake_case, 유틸리티 금지 | JS 훅 클래스(`js-` 접두사)를 별도 예외 카테고리로 분리 |
| flex 카드 `calc((100%-48px)/3)` | calc 단독 금지 | flex 카드 폭 계산 한정 calc 예외 추가 |
| shadow/gradient `rgba()` | hex 전용 | alpha 필요 시 rgba 허용(기존 조항과 동일, 그림자에도 명시) |

---

## 📐 Figma 변환 추가 규칙 (codex-2 제안, 즉시 연동 가능)

- **이펙트 매핑** (★★★): DROP_SHADOW/INNER_SHADOW → box-shadow, LAYER_BLUR → filter
- **Stroke-align** (★★★): CENTER→border, INSIDE→inset box-shadow, OUTSIDE→box-shadow
- **색상 스타일 변수화** (★★): Figma 문서 색상 스타일 → `--point-color-N` CSS 변수 자동 매핑
- **그라디언트** (★★): LINEAR→linear-gradient, RADIAL→radial-gradient
- **SVG/벡터 노드** (★): ELLIPSE→div+border-radius:50%, 소형 아이콘→img, 대형→svg[aria-hidden]
- **컴포넌트 반복** (★): 동일 componentId 2개↑ → `ul>li` 반복 구조

---

## 🎨 인터랙션/UX 규칙 (codex-3 + gemini 제안)

- **터치 영역 44px**: `::after` 가상 요소 확장 패턴 (공통)
- **Slick 마크업**: `.js-slider` / `.slider__item` / `.slider-nav__prev|next` (landing)
- **GSAP 패턴**: `[data-scroll-section]` 속성 + `.section_on` 클래스 토글 (landing)
- **will-change**: 애니메이션 요소 한정, 완료 후 `auto` 해제 (공통)
- **font-display: swap** + 폰트 preload (공통)
- **Safe Area**: `env(safe-area-inset-bottom)` (landing)

---

## 🏗️ 유지보수성 규칙 (claude 제안)

- **CSS 주석**: `/* ===== SECTION NAME ===== */` 패턴 통일, 설명형 주석 금지
- **클래스명 반복**: `{page}_{role}_{N}` 패턴 (main_about_1, main_about_2)
- **반응형 이미지**: `.pc_only`/`.mb_only` 이미지 전환 패턴 표준화
- **컴포넌트 네이밍**: `{page}_btn`, `{page}_modal`, `{page}_modal_dim`

---

## ❌ 보류 권장 항목

- constraints 매핑 (Figma 변환 스크립트 내부 로직 영역)
- 그라디언트 각도 계산 알고리즘 (변환 코드 영역)
- GSAP 전체 JS 코드 규칙화 (보일러플레이트 템플릿으로 분리 권장)
- Print 스타일 (랜딩 수요 낮음)
- Skeleton UI (동적 로딩 시나리오 없을 때)

---

## 총평

35개 제안 중 **즉시 적용 10개**(충돌 없음), **예외 정리 후 적용 4개**, **Figma 변환 추가 6개**가 실용성 높음.
핵심 조언: snake_case 예외(is-/has-/js-) + hex 예외(shadow rgba)를 `common.md` 상단 "허용 예외 목록"으로 한 번에 정리한 후 적용하는 것이 일관성 유지에 유리.

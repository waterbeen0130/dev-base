# 퍼블리싱 규칙 충돌 분석 결과

> 분석 기준: HTML/CSS 규칙 충돌 탐지 전문가 관점
> 분석 대상: CLAUDE.md, codex.md, common.md, landing.md, rule_engine.json, validation_schema.json

---

## 1. 프로젝트 타입별 충돌 — font-size: rem vs px

**규칙 A (common.md / codex.md)**: `font-size: PC는 rem, 모바일(768px 이하)은 고정 px`
**규칙 B (landing.md)**: `font-size: PC/모바일 모두 고정 px (rem 사용 안 함)`

**충돌 내용**: landing.md가 common.md의 rem 규칙을 덮어쓰지만, 이 override가 명시적 우선순위 선언 없이 파일 분리로만 표현됩니다. 코드 추출기가 프로젝트 타입을 자동 판별하지 못하면 Basic 프로젝트에 px, Landing 프로젝트에 rem이 적용되는 역전 현상이 발생합니다.

**실제 영향**: 추출된 CSS에서 `.landing_title { font-size: 1.6rem; }` 형태가 생성될 수 있으며, 랜딩 특화 디자인 의도(고정 px 기반 정밀 제어)가 무력화됩니다.

---

## 2. CLAUDE.md vs codex.md 충돌 및 누락

**충돌 A — 미디어쿼리 들여쓰기**
- CLAUDE.md `하지 말 것`: "CSS 미디어쿼리 내부 들여쓰기" (금지)
- codex.md: "미디어쿼리 내부 들여쓰기 없음" (동일 방향)
- 이 항목은 충돌 없음. 그러나 표현 방식이 달라 LLM이 두 파일을 각각 참조 시 중복 제약으로 과잉 처리할 수 있습니다.

**누락 B — border-radius 규칙**
- codex.md: `border-radius: 원형 50%, pill 2em — 999px 금지`
- CLAUDE.md: border-radius 관련 규칙 전혀 없음
- CLAUDE.md만 참조하는 환경에서는 999px border-radius가 생성됩니다.

**누락 C — 색상 포맷**
- codex.md: `색상: hex 전용`
- CLAUDE.md: 색상 포맷 규칙 없음
- CLAUDE.md 단독 적용 시 rgba(), hsl() 색상이 출력 코드에 포함될 수 있습니다.

**누락 D — CSS Grid 금지**
- codex.md / common.md: `CSS Grid 사용 금지 — flexbox만`
- CLAUDE.md: Grid 금지 규칙 없음

---

## 3. common.md 기준 — landing.md override 미표시 충돌

**규칙 A (common.md)**: `768px 이하: padding/margin은 PC 값의 절반`
**규칙 B (landing.md)**: `padding/margin: PC/모바일 모두 고정 px` (절반 규칙 언급 없음)

**충돌 내용**: landing.md가 common.md의 "절반" 규칙을 암묵적으로 무효화하지만, 명시적 `OVERRIDES common.md` 선언이 없습니다. 추출기가 두 파일을 병합 적용하면 모바일에서 PC 값의 절반이 적용되어 Landing 디자인 의도와 달라집니다.

**규칙 C (common.md)**: `block 요소에 불필요한 width: 100% 금지`
**landing.md**: 이 규칙 미언급 — 랜딩 페이지 전폭 섹션 구현 시 width: 100%가 필요한 경우와 충돌 가능.

---

## 4. rule_engine.json 충돌 — border_radius.pill 값 모호성

**규칙 A (codex.md)**: `border-radius pill 형태는 2em — 999px 금지`
**규칙 B (rule_engine.json)**: `"pill": "2em or 50%"`

**충돌 내용**: JSON의 `"2em or 50%"` 표현은 두 값 모두 허용하는 것처럼 읽힙니다. 그러나 50%는 원형(circle) 전용 값이며, pill 형태에 50%를 적용하면 직사각형 요소에서 타원형이 아닌 원형에 가까운 형태가 됩니다. 자동 검증 도구가 이 JSON을 파싱할 경우 50% pill을 통과로 처리하여 codex.md 규칙 위반이 검출되지 않습니다.

**실제 영향**: `.landing_btn { border-radius: 50%; }` 생성 후 검증 통과 → 긴 버튼 요소에서 좌우가 원형으로 잘리는 렌더링 버그 발생.

---

## 5. validation_schema.json 이슈

**이슈 A — no_duplicate_selector 중복 등록**
- `no_duplicate_selector` 체크가 checks 배열에 2회 등록됨.
- 영향: 검증 실행 시 동일 규칙이 2번 평가되어 오탐(false positive) 발생 가능. 검증 리포트에 동일 오류가 2건으로 보고되어 실제 오류 수 과산정.

**이슈 B — 랜딩 페이지 font-size 검증 부재**
- `font_size_pc_rem` 체크만 존재하며, Landing 프로젝트 전용 `font_size_all_px` 체크가 없음.
- 영향: 랜딩 페이지 코드에서 rem이 사용되어도 검증 통과. landing.md 규칙(모두 고정 px)이 실질적으로 강제되지 않음.
- 보완 필요: `{ "type": "font_size_landing_px", "scope": "landing", "note": "Landing page uses px for all font-size" }` 항목 추가 필요.

---

## 요약 — 우선순위별 충돌 목록

| 순위 | 파일 간 충돌 | 심각도 | 유형 |
|------|-------------|--------|------|
| 1 | landing.md vs common.md — font-size rem/px | 높음 | 직접 충돌 |
| 2 | rule_engine.json vs codex.md — pill 2em vs 2em or 50% | 높음 | 값 모호성 |
| 3 | validation_schema.json — 랜딩 font-size 검증 없음 | 높음 | 검증 공백 |
| 4 | landing.md vs common.md — 모바일 padding 절반 규칙 | 중간 | 암묵적 override |
| 5 | CLAUDE.md — border-radius/색상/Grid 규칙 누락 | 중간 | 규칙 누락 |
| 6 | validation_schema.json — no_duplicate_selector 중복 | 낮음 | 스키마 오류 |

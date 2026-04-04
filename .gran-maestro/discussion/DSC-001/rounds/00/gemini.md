# MD ↔ JSON 매핑 정합성 분석 결과

> 분석가: Gemini 역할 대리 (MD↔JSON 매핑 정합성 분석가)
> 분석 대상: common.md, landing.md ↔ rule_engine.json, validation_schema.json

---

## 1. 매핑 갭 표 — MD → rule_engine.json 누락/불일치

| MD 규칙 | JSON 반영 여부 | 불일치 내용 |
|---|---|---|
| 768px 이하 padding/margin 절반 | 미반영 | `css` 섹션에 `mobile_spacing_half` 또는 `mobile_halved` 키 없음 |
| p태그 최소화 (span/헤딩 우선, 95자 초과 or \n 포함 시만 p 허용) | 미반영 | `parsing` 또는 `html` 섹션에 `p_tag_policy` 없음 |
| landing font-size 예외 (PC도 px, rem 아님) | 미반영 | `css.font_size`에 `landing_override` 또는 `page_type` 분기 없음 |
| border_radius.pill: MD는 "2em"만 허용 | 표현 불일치 | JSON `pill: "2em or 50%"` — MD는 pill=2em, circle=50%로 명확히 구분. "or 50%"가 혼란 유발 |
| CSS property_order: font-size(8위), font-weight(9위) 분리 | 표현 불일치 | JSON은 `"font"`로 통합. font-size와 font-weight가 별도 위치임을 표현 못 함 |
| 좌표 기반 inline-flex (동일 y 두 박스 → 행 정렬 우선) | 미반영 | `layout` 섹션에 `coordinate_based_row_detection` 없음 |
| GSAP data-delay/data-direction CSS 패턴 (landing 전용) | 부분 반영 | `structure.animation_attrs: ["data-delay","data-direction"]` 존재하나 CSS 패턴(-40px/opacity:0/section_on 토글) 세부 규칙 없음 |
| CDN JS (landing 전용) | 미반영 | `output_policy` 등에 landing 전용 JS 방식 구분 없음 |
| calc() 단독 금지 (clamp 내부에서만 허용) | 부분 반영 | `no_raw_calc: true` 있으나 "clamp 내부에서만 허용"이라는 허용 조건 명시 없음 |
| vw 단독 금지 (clamp 내부에서만 허용) | 부분 반영 | `no_raw_vw: true` 있으나 동일하게 허용 조건 미명시 |
| :root 변수 네이밍 시맨틱 금지 패턴 | 반영 | `root_var_naming` 있음 — OK |
| 구분선 DOM 보존 | 반영 | `node_preservation.divider_bar` 있음 — OK |

---

## 2. 매핑 갭 표 — MD → validation_schema.json 누락 체크

| MD 규칙 | 스키마 체크 여부 | 불일치 내용 |
|---|---|---|
| 768px 이하 padding/margin 절반 | 미검증 | 관련 체크 항목 없음 |
| p태그 최소화 정책 | 미검증 | `p_tag_minimal` 또는 `text_tag_auto_judgment` 체크 없음 |
| landing font-size PC도 px | 미검증 | `font_size_pc_rem` 체크만 존재 — landing 타입 예외 검증 없음 |
| 좌표 기반 inline-flex 추출 | 미검증 | 관련 체크 없음 |
| GSAP CSS 패턴 보존 | 미검증 | `animation_attrs` 관련 체크 없음 |
| no_duplicate_selector | **중복 등록** | index 6번(line 8)과 index 43번(line 44)에 동일 type 2회 선언 |
| padding 반영 (Figma padding* → CSS) | 부분 검증 | `no_layout_info_loss`로 간접 커버되나 padding 전용 체크 없음 |
| counterAxisAlignItems / primaryAxisAlignItems | 부분 검증 | `layout_mode_reflected`, `item_spacing_reflected` 있으나 align-items/justify-content 전용 체크 없음 |

---

## 3. 심각도별 분류

### Critical (즉시 수정 필요)

**C-1. validation_schema.json no_duplicate_selector 중복 등록**
- 위치: checks 배열 index 6 (line 8)과 index 43 (line 44)에 동일한 `"type": "no_duplicate_selector"` 두 번 선언
- 영향: 검증 엔진이 중복 실행되거나 카운트 오류 발생 가능. 총 47개 체크라고 했으나 실제 고유 체크는 46개

**C-2. landing font-size 예외 미반영**
- rule_engine.json `css.font_size.pc: "rem"` 은 landing에서 `px`로 예외 적용되나 JSON에 분기 없음
- validation_schema.json `font_size_pc_rem` 체크가 landing 페이지에도 그대로 적용되면 오탐 발생

### Major (중요 — 다음 버전 반영 권장)

**M-1. border_radius.pill 표현 불일치**
- MD: pill은 `2em` 고정, 999px 금지. circle만 `50%`
- JSON: `"pill": "2em or 50%"` — "or 50%"는 MD에 없는 허용 범위. 구현자 혼란 가능

**M-2. property_order font 통합 문제**
- MD: 8위=font-size, 9위=font-weight로 별도 순서
- JSON: `"font"` 단일 항목으로 통합 → font-family, font-style 등이 같은 위치로 처리되어 순서 모호

**M-3. 768px 이하 padding/margin 절반 규칙 미반영**
- MD common.md 57번째 줄에 명시된 핵심 모바일 규칙
- rule_engine.json과 validation_schema.json 모두 미반영 → 자동 검증 불가

**M-4. p태그 최소화 정책 미반영**
- MD: span/헤딩 우선, p는 `\n` 포함 or 95자 초과 or 문단형일 때만
- JSON 어디에도 `p_tag_policy` 없음 → AI 구현 시 일관성 보장 불가

### Minor (참고용 개선 제안)

**m-1. calc/vw 단독 금지의 허용 조건 미명시**
- `no_raw_calc: true`, `no_raw_vw: true` 있으나 "clamp 내부에서만 허용" 조건이 note로도 없음
- 구현자가 clamp 내 calc/vw도 금지로 오해할 수 있음

**m-2. GSAP CSS 패턴 세부 규칙 미반영**
- landing.md의 `[data-delay]`, `.section_on` 토글 패턴이 JSON에 구체적 CSS 값으로 없음
- `animation_attrs` 선언만으로는 실제 CSS 구현 보장 불가

**m-3. 좌표 기반 inline-flex 규칙 미반영**
- common.md 273-276번째 줄 및 landing.md 브레인바디 규칙에 명시
- rule_engine.json `layout` 섹션에 누락 — 자동화 추출 시 세로 스택으로 잘못 추출될 수 있음

**m-4. CDN JS vs 로컬 파일 구분 미반영**
- landing은 CDN, basic은 로컬 파일 방식이나 rule_engine.json에 분기 없음

---

## 요약

| 분류 | 건수 | 주요 항목 |
|---|---|---|
| Critical | 2 | no_duplicate_selector 중복, landing font-size 예외 미검증 |
| Major | 4 | pill 표현 불일치, property_order 통합, 모바일 spacing 절반, p태그 정책 |
| Minor | 4 | calc/vw 허용조건, GSAP 패턴, 좌표 기반 레이아웃, CDN 구분 |

총 **10개 매핑 갭** 확인. Critical 2건은 즉각 수정, Major 4건은 v2.4.0 반영 권장.

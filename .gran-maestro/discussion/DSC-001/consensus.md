# DSC-001 최종 합의문
## 퍼블리싱 규칙 파일 분석: 충돌·중복·MD↔JSON 불일치·누락 규칙

> 참여자: codex (충돌 분석), codex-2 (중복 탐지), codex-3 (누락 발굴), gemini (매핑 정합성), claude (구조 분석)
> Critic: claude
> 라운드: 1 (초기 수집 후 합의 달성)
> 합의 상태: **실질 합의** — 문제 식별 완전 수렴, 해결 방식 접근법 다양

---

## 🔴 Critical — 즉시 수정 필요 (전원 합의)

### C-1. `validation_schema.json` no_duplicate_selector 중복 등록 버그
- **위치**: checks 배열 index 6 (line 8)과 index 43 (line 44)에 동일 타입 2회 선언
- **영향**: 검증 엔진이 동일 규칙 2회 실행 → 오탐 및 오류 수 과산정
- **조치**: Line 44 항목 삭제. Line 8의 note가 더 구체적이므로 유지
  ```json
  // 삭제: { "type": "no_duplicate_selector", "note": "same selector must not be declared multiple times" }
  ```

### C-2. `landing.md` font-size 예외가 JSON에 미반영
- **충돌**: `landing.md`는 "PC/모바일 모두 고정 px" 명시 ↔ `rule_engine.json css.font_size.pc: "rem"` + `validation_schema.json font_size_pc_rem` 체크
- **영향**: landing 추출 시 rem 오출력, 검증에서 false positive 발생
- **조치** (rule_engine.json):
  ```json
  "css": {
    "font_size": {
      "pc": "rem",
      "mobile": "px",
      "landing_override": "px_all",
      "landing_override_note": "landing project uses fixed px for all font-size, overrides pc:rem default"
    }
  }
  ```
- **조치** (validation_schema.json):
  ```json
  { "type": "font_size_pc_rem", "applies_to": ["basic"], "note": "PC uses rem — basic only. landing uses px_all" },
  { "type": "font_size_landing_px", "applies_to": ["landing"], "note": "Landing page uses fixed px for all font-size, not rem" }
  ```

---

## 🟠 Major — 다음 버전 반영 권장 (전원 합의)

### M-1. `border_radius.pill` 표현 불일치
- **충돌**: MD(codex.md/common.md): "pill 형태는 2em" ↔ `rule_engine.json`: `"pill": "2em or 50%"`
- **영향**: 검증 도구가 50% pill을 통과 처리 → 긴 버튼에 타원 렌더링 버그
- **조치**: `"pill": "2em"` 으로 수정, 별도 note 추가
  ```json
  "border_radius": {
    "circle": "50%",
    "pill": "2em",
    "pill_note": "pill-shaped elements use 2em only. 50% is for circle only. 999px is forbidden in all cases"
  }
  ```

### M-2. `property_order`에서 font 통합 모호성
- **충돌**: MD: `font-size(8위), font-weight(9위)` 분리 ↔ JSON: `"font"` 단일 항목 통합
- **조치**:
  ```json
  "property_order": ["position", "margin", "padding", "width/height", "display", "align", "background", "font-size", "font-weight", "color", "기타"]
  ```

### M-3. 모바일 padding/margin 절반 규칙 미반영
- **내용**: common.md: "768px 이하: padding/margin은 PC 값의 절반" — rule_engine.json, validation_schema.json 모두 미반영
- **조치** (rule_engine.json):
  ```json
  "css": {
    "mobile_spacing_policy": {
      "breakpoint": 768,
      "strategy": "half_of_pc",
      "applies_to": ["basic"],
      "note": "768px and below: padding/margin defaults to half of PC value. landing uses explicit px values"
    }
  }
  ```

### M-4. p태그 최소화 정책 미반영
- **내용**: common.md: "기본 태그는 span/헤딩 계열, p태그는 \n 포함·95자 초과·문장형 마침표 중 하나 충족 시만" — JSON 미반영
- **조치** (rule_engine.json):
  ```json
  "text_tag_selection": {
    "default_tag": "span",
    "p_tag_conditions": ["characters_contains_newline", "characters_length_gt_95", "sentence_ending_repeat"],
    "forbid_p_for_labels": true,
    "forbid_p_for_labels_note": "BrainBody, MRI 등 라벨성 키워드는 span 또는 heading 태그로"
  }
  ```
- **조치** (validation_schema.json):
  ```json
  { "type": "p_tag_condition_enforced", "note": "p tag only when \\n present, length>95, or sentence-ending. labels use span" }
  ```

---

## 🟡 Minor — 개선 권장

### m-1. CLAUDE.md 규칙 누락
- border-radius(999px 금지·pill 2em·circle 50%), 색상 포맷(hex only), CSS Grid 금지 규칙이 CLAUDE.md에 없음
- CLAUDE.md에 `common.md` 명시적 전체 적용 선언 추가 또는 누락 항목 보완 필요

### m-2. calc/vw 허용 조건 미명시
- `rule_engine.json`: `no_raw_calc: true`, `no_raw_vw: true` 있으나 "clamp 내부에서만 허용" 조건이 note로도 없음
- 조치: note 필드에 `"clamp() context only permitted"` 명시

### m-3. GSAP 애니메이션 CSS 패턴 미반영 (landing 전용)
- `structure.animation_attrs: ["data-delay","data-direction"]`만 있고 실제 CSS 값(opacity:0, -40px 등) 없음
- 추가 권장:
  ```json
  "animation_css_pattern": {
    "applies_to": "landing",
    "required_rules": [
      "[data-delay]{position:relative; transition:all 1s ease; opacity:0;}",
      ".section_on [data-delay]{opacity:1;}"
    ]
  }
  ```

### m-4. 좌표 기반 inline-flex 추출 규칙 미반영
- common.md·landing.md: "같은 y를 가지는 블록 2개 → inline-flex 행 정렬 우선" — rule_engine.json에 없음

### m-5. 이미지 섹션 처리 규칙 미반영 (landing)
- 이미지 기반 섹션 height 고정, object-fit:cover, 모바일 전용 이미지 규칙이 JSON에 전혀 없음

---

## 🔵 중복 규칙 — 통합 권장

22개 규칙이 2~4개 파일에 중복 등장. 특히 `styleOverrideTable` 병합 알고리즘은 4개 파일에 미묘하게 다른 표현으로 존재하여 **드리프트가 이미 시작된 상태**.

**즉시 통합 권장 (common.md 단일화 후 참조 방식 전환)**:
- Figma TEXT 노드 1:1 매핑 + 인접 합치기 금지
- 텍스트 줄바꿈 처리 (`\n` → `<br>`, `\n\n` → 블록 분리)
- `styleOverrideTable` 병합 알고리즘 (baseStyle/previousResolvedStyle 전체 코드)
- 텍스트 스타일 분할 규칙 (fontSize/fontWeight 등 차이 시 span 분리)
- Figma 구분선 DOM 보존 + Border/Stroke 조건
- Figma 레이아웃 매핑 (layoutMode, itemSpacing, padding)
- CSS: line-height 비율, letter-spacing em, border-radius, Grid 금지, !important 금지

**참조 방식 예시** (codex.md, landing.md에 추가):
```
> Figma 텍스트/레이아웃/노드 보존 관련 규칙은 `common.md` 참조
```

---

## 🏗️ 장기 아키텍처 개선 제안

```
rules/
├── common.md                  ← Single Source of Truth (유일한 규칙 원본)
├── overrides/
│   ├── claude.md              ← Claude delta (작업 방식·응답 스타일만)
│   ├── codex.md               ← Codex delta (자동완성 힌트·검증 명령만)
│   └── landing.md             ← Landing delta (font-size:px·CDN·파일구조만)
├── validation_workflow.md     ← 공통 검증 절차 (codex.md에서 이동)
├── rule_engine.json           ← project_type 필드 추가, overlay 패턴
└── validation_schema.json     ← applies_to 필드로 타입별 conditional check
```

**핵심 원칙**: 규칙은 common.md에 한 번만 작성, 하위 파일은 차이점(delta)만 선언.

---

## 우선순위 요약 체크리스트

| 우선순위 | 항목 | 대상 파일 | 조치 |
|---|---|---|---|
| ① Critical | `no_duplicate_selector` 중복 제거 | validation_schema.json | line 44 삭제 |
| ② Critical | landing font-size 예외 반영 | rule_engine.json + validation_schema.json | landing_override + applies_to 추가 |
| ③ Major | pill border-radius "2em" 단일화 | rule_engine.json | "2em or 50%" → "2em" |
| ④ Major | property_order font 분리 | rule_engine.json | "font" → "font-size"/"font-weight" |
| ⑤ Major | 모바일 spacing 절반 규칙 | rule_engine.json | mobile_spacing_policy 추가 |
| ⑥ Major | p태그 최소화 정책 | rule_engine.json + validation_schema.json | text_tag_selection 추가 |
| ⑦ Minor | CLAUDE.md 누락 규칙 | CLAUDE.md | border-radius·색상·Grid 추가 |
| ⑧ Minor | calc/vw note 보완 | rule_engine.json | "clamp() context only" note 추가 |
| ⑨ Minor | GSAP 패턴 반영 | rule_engine.json | animation_css_pattern 추가 |
| ⑩ 중복 | styleOverrideTable 알고리즘 단일화 | codex.md, landing.md, CLAUDE.md | common.md 참조로 전환 |

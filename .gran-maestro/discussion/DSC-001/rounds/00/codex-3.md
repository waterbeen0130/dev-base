# 누락된 퍼블리싱 규칙 발굴 — Codex 분석 결과

> 분석 기준: rule_engine.json v2.3.0 / validation_schema.json / common.md / landing.md
> 역할: 퍼블리싱 규칙 체계 완성도 전문가
> 출력 형식: 누락 규칙 TOP 5 + JSON 추가 초안

---

## 누락 규칙 TOP 5 (우선순위 순)

### #1. Landing vs Basic 프로젝트 타입 분리 (font_size 충돌)

**문제**: rule_engine.json의 `css.font_size.pc`가 `"rem"`으로 고정되어 있으나, landing.md는 PC/모바일 모두 고정 `px`를 명시. 엔진이 타입을 구분하지 못하면 landing 추출 시 rem이 출력됨 — 가장 빈번한 실수 유형.

**JSON 추가 초안**:
```json
"project_type": {
  "default": "basic",
  "types": {
    "basic": {
      "css_font_size_pc": "rem",
      "css_font_size_mobile": "px",
      "js_include": "local",
      "reset_css": "separate_file"
    },
    "landing": {
      "css_font_size_pc": "px",
      "css_font_size_mobile": "px",
      "js_include": "cdn",
      "reset_css": "inline_top_of_css",
      "required_root_vars": ["--padding", "--header_h", "--width", "--point-color-1"]
    }
  },
  "override_note": "landing type overrides css.font_size.pc from rem to px"
}
```

---

### #2. 텍스트 태그 자동 판정 규칙 (p 태그 최소화)

**문제**: rule_engine.json과 validation_schema.json에 p 태그 사용 조건이 전혀 없음. 추출 시 기본값으로 p를 남발하면 라벨성 텍스트가 모두 p로 감싸지는 오염이 발생함.

**JSON 추가 초안 (rule_engine.json)**:
```json
"text_tag_selection": {
  "default_tag": "span",
  "p_tag_conditions": [
    "characters contains \\n",
    "characters.length > 95",
    "sentence_ending_repeat"
  ],
  "forbid_p_for_labels": true,
  "forbid_p_for_labels_note": "short label text (brand names, keywords) must use span or heading, never p"
}
```

**validation_schema.json 추가 check**:
```json
{ "type": "p_tag_condition_enforced", "note": "p tag only when \\n present, length>95, or sentence-ending repeat. labels must use span" }
```

---

### #3. GSAP 애니메이션 CSS 패턴 (landing 필수 블록)

**문제**: rule_engine.json `structure.animation_attrs`에 속성명만 있고, 실제 CSS 패턴(opacity:0, position:relative, transition, fallback 예외처리)이 없음. 추출 시 data-delay 속성은 붙지만 대응 CSS가 누락되는 경우 발생.

**JSON 추가 초안**:
```json
"animation_css_pattern": {
  "applies_to": "landing",
  "required_rules": [
    "[data-delay]{position:relative; transition:all 1s ease; opacity:0;}",
    "[data-direction='left']{left:-40px;}",
    "[data-direction='right']{right:-40px;}",
    "[data-direction='top']{top:-40px;}",
    "[data-direction='bottom']{bottom:-40px;}",
    ".section_on [data-delay]{opacity:1;}",
    ".section_on [data-direction='left']{left:0;}",
    ".section_on [data-direction='right']{right:0;}",
    ".section_on [data-direction='top']{top:0;}",
    ".section_on [data-direction='bottom']{bottom:0;}"
  ],
  "gsap_fallback_required": true,
  "gsap_fallback_note": "if GSAP not loaded, data-delay elements must not remain invisible — add JS fallback or CSS @supports guard"
}
```

**validation_schema.json 추가 check**:
```json
{ "type": "gsap_animation_css_present", "applies_to": "landing", "note": "landing output must include [data-delay] and .section_on CSS rules" }
```

---

### #4. 이미지 섹션 처리 규칙

**문제**: rule_engine.json에 이미지 관련 규칙이 전혀 없음. 이미지 기반 섹션에서 height 고정 누락, object-fit 누락, 모바일 전용 이미지 미사용이 반복적으로 발생.

**JSON 추가 초안**:
```json
"image_section": {
  "bg_image_section": {
    "height_from_original_px": true,
    "object_fit": "cover",
    "note": "image-based sections must set height equal to original image pixel height and apply object-fit:cover"
  },
  "inline_img": {
    "width_percent_based": true,
    "aspect_ratio_required": true,
    "forbid_fixed_width_height": true,
    "note": "img inside sections must use width:100% or % and aspect-ratio, never fixed px width/height"
  },
  "mobile_image": {
    "required": true,
    "note": "mobile-specific images must be used; layout/size must follow mobile image pixel dimensions"
  }
}
```

**validation_schema.json 추가 check**:
```json
{ "type": "image_section_height_fixed", "note": "image-based section must have explicit height matching original image px" },
{ "type": "inline_img_no_fixed_dimension", "note": "img inside section must not use fixed px width/height — use % + aspect-ratio" }
```

---

### #5. CSS 필수 변수 목록 (landing 전용)

**문제**: rule_engine.json의 `css.root_var_format`/`root_var_naming`은 형식만 규정하고 필수 변수 목록이 없음. landing 출력 시 `--header_h`, `--padding`, `--width`, `--point-color-1` 중 일부가 누락되는 사례가 있음.

**JSON 추가 초안**:
```json
"root_vars_required": {
  "landing": ["--padding", "--header_h", "--width", "--point-color-1"],
  "basic": ["--width", "--padding"],
  "forbid_semantic_names": ["--landing-dark", "--landing-navy", "--primary", "--secondary"],
  "note": "required root variables must all be declared in :root{} block; semantic naming is forbidden"
}
```

**validation_schema.json 추가 check**:
```json
{ "type": "root_vars_required_present", "applies_to": "landing", "values": ["--padding", "--header_h", "--width", "--point-color-1"], "note": "all four required CSS variables must appear in :root block" }
```

---

## Landing vs Basic 분리 방안 요약

rule_engine.json에 최상위 `"project_type"` 키를 추가하고, `"default": "basic"` 설정 후 각 타입에서 기존 `css.*` 키를 오버라이드하는 구조를 권장합니다.

```json
// rule_engine.json 최상위 구조 예시
{
  "meta": { "version": "2.4.0", ... },
  "project_type": { ... },  // 신규 — 타입별 분기
  "parsing": { ... },
  "css": {
    "font_size": {
      "pc": "rem",           // basic 기본값
      "mobile": "px",
      "landing_override": "px_all"  // landing 예외 명시
    }
  },
  "animation_css_pattern": { ... },  // 신규
  "image_section": { ... },          // 신규
  "root_vars_required": { ... },     // 신규
  "text_tag_selection": { ... }      // 신규
}
```

validation_schema.json에는 `"applies_to"` 필드를 각 check에 추가하여 basic/landing 조건부 검증을 지원합니다.

---

> 분석 완료 | 총 10개 누락 규칙 중 코드 추출 품질 영향도 기준 상위 5개 선정

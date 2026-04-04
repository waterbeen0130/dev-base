# MD ↔ JSON 매핑 정합성 분석 (Gemini 관점)

당신은 문서-코드 일관성을 검증하는 전문 분석가입니다.
아래 퍼블리싱 규칙 MD 파일들의 내용이 rule_engine.json과 validation_schema.json에 **정확하게 반영되어 있는지** 매핑 정합성을 검토하세요.

---

## 분석 대상 파일 요약

### MD 파일 규칙 (핵심 항목)

**common.md 핵심 규칙**:
1. font-size: PC=rem, 모바일=px
2. line-height: 무단위 비율
3. letter-spacing: em 단위
4. border-radius: 원형=50%, pill=2em, 999px 금지
5. clamp: 100px 이상만 허용
6. CSS Grid 금지, Flexbox만
7. !important 금지
8. hex 색상만 (투명도 시 rgba 허용)
9. CSS 속성 순서: position→margin→padding→width/height→display→align→background→font-size→font-weight→color
10. 클래스명 snake_case, page prefix 필수
11. 빈 div 금지
12. DOM 깊이 5단계 이하
13. 이미지 래퍼 안에 배치
14. figure/figcaption 금지
15. 768px 이하: padding/margin 절반
16. p태그 최소화 (span/헤딩 우선)
17. Figma TEXT 1:1 매핑
18. characterStyleOverrides span 분리
19. styleOverrideTable 누적 병합 알고리즘
20. 구분선 DOM 보존
21. border는 stroke 있을 때만
22. 레이아웃 매핑 (layoutMode, itemSpacing, padding)

**landing.md 추가 규칙**:
- font-size: PC도 px (rem 아님)
- GSAP 애니메이션 data-delay/data-direction CSS 패턴
- 좌표 기반 inline-flex 추출
- CDN JS

---

## rule_engine.json 현재 상태

```json
{
  "css": {
    "font_size": { "pc": "rem", "mobile": "px" },
    "line_height": { "format": "ratio", "forbid_computed_px": true },
    "letter_spacing": { "unit": "em" },
    "border_radius": { "circle": "50%", "pill": "2em or 50%" },
    "clamp_threshold": 100,
    "no_grid": true,
    "no_important": true,
    "color_format": "hex_only",
    "property_order": ["position", "margin", "padding", "width/height", "display", "align", "background", "font", "color"],
    "spacing_unit": "px_only",
    "forbid_utility_classes": true,
    "selector_single_line": true,
    "forbid_duplicate_selector": true,
    "media_query_format": { "each_rule_own_line": true, "no_indent": true }
  },
  "naming": {
    "case": "snake_case",
    "page_prefix_required": true,
    "regex": "^[a-z0-9_]+$",
    "forbidden": ["sec_1", "sec_2", "section_01", "box1"]
  },
  "structure": {
    "max_dom_depth": 5,
    "forbid_empty_div": true,
    "flexbox_only": true,
    "animation_attrs": ["data-delay", "data-direction"]
  },
  "html": {
    "no_figure_figcaption": true,
    "minimal_aria": true,
    "img_alt_concise": true,
    "img_in_wrapper": true
  },
  "layout": {
    "container_strategy": "max-width + margin:0 auto",
    "avoid_width_100_block": true,
    "figma_layout_mapping": { ... }
  },
  "parsing": {
    "split_text_on_override": true,
    "override_merge": "cumulative",
    "text_newline": { "single_n": "<br>", "forbid_ignore": true },
    "style_split": { "trigger_props": ["fontSize", "fontWeight", ...], "forbid_flatten": true },
    "text_node_mapping": { "one_node_one_element": true, "forbid_merge_adjacent": true }
  }
}
```

## validation_schema.json 현재 상태 (47개 체크 항목)

포함된 항목:
- max_dom_depth, snake_case_naming, page_prefix_required
- no_forbidden_class, selector_single_line, no_duplicate_selector (×2 중복!)
- media_query_format, clamp_threshold, no_raw_calc, no_raw_vw
- newline_converted_to_br, override_span_split_required, text_newline_preserved
- style_diff_span_required, no_style_flatten, no_inline_style
- inner_wrapper_limit, no_empty_div, hex_color_only
- no_css_grid, no_important, selector_scoped, flexbox_layout
- img_wrapped, text_node_one_to_one, no_adjacent_text_merge
- layout_mode_reflected, item_spacing_reflected, no_layout_info_loss
- root_var_line_separated, divider_node_preserved
- border_from_stroke_only, no_heuristic_border, no_adjacent_selector_border
- visible_node_not_dropped
- line_height_ratio_only, font_size_pc_rem, letter_spacing_em_only
- border_radius_no_999, no_figure_figcaption, no_utility_classes
- root_var_naming, minimal_aria, img_alt_concise

---

## 분석 요청

1. **MD → rule_engine.json 누락 매핑**: MD에 있지만 JSON에 없는 항목 (예: 768px 이하 padding 절반, p태그 최소화, landing font-size 예외)
2. **MD → validation_schema.json 누락 체크**: MD에 있지만 스키마에 없는 검증 항목
3. **rule_engine.json 표현 불일치**: MD 규칙 표현과 JSON 값이 달라 혼란을 줄 수 있는 항목 (예: border_radius.pill "2em or 50%" vs MD "2em만")
4. **property_order 불일치**: MD는 font-size(8위), font-weight(9위) 분리 vs JSON은 "font"로 통합
5. **validation_schema.json 품질 이슈**: no_duplicate_selector 중복 등록, landing 타입 font-size 검증 부재

응답 형식:
- 매핑 갭 표 (MD 규칙 | JSON 반영 여부 | 불일치 내용)
- 심각도별 분류 (Critical / Major / Minor)
- 2000자 이내

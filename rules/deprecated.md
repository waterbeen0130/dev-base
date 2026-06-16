# Deprecated Rules (REQ-024-T01)

## no_css_grid
- 상태: merged_into:flexbox_layout
- 결정 이유: `display:grid` 금지 검사가 `flexbox_layout`과 중복되어 단일 규칙으로 통합.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: `flexbox_layout`

## no_figure_figcaption
- 상태: merged_into:forbidden_tag
- 결정 이유: `<figure>/<figcaption>` 금지 범위가 `forbidden_tag`에 포함되어 중복 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: `forbidden_tag`

## no_999_border_radius
- 상태: merged_into:border_radius_no_999
- 결정 이유: deprecated alias 규칙으로 동등 검증이 중복되어 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: `border_radius_no_999`

## border_from_stroke_only
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 기본 검증 체인에서 지속적으로 skip되어 규칙 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma spec 기반 수동 검토

## divider_node_preserved
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma 원본 대비 수동 검토

## text_node_one_to_one
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma 원본 대비 수동 검토

## no_adjacent_text_merge
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma 원본 대비 수동 검토

## text_newline_preserved
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma 원본 대비 수동 검토

## newline_converted_to_br
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma 원본 대비 수동 검토

## override_span_split_required
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma 원본 대비 수동 검토

## style_diff_span_required
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma 원본 대비 수동 검토

## no_style_flatten
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma 원본 대비 수동 검토

## layout_mode_reflected
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 자동 체인에서 skip 가능성이 높아 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: section spec 대조 수동 검토

## item_spacing_reflected
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 자동 체인에서 skip 가능성이 높아 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: section spec 대조 수동 검토

## no_layout_info_loss
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: section spec 대조 수동 검토

## visible_node_not_dropped
- 상태: deleted
- 결정 이유: figma fidelity 전용 커스텀 규칙군 슬림 대상.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: section spec 대조 수동 검토

## figma_value_gap_match
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 자동 체인에서 skip 가능성이 높아 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma-validate 출력 및 spec 대조

## figma_value_padding_match
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 자동 체인에서 skip 가능성이 높아 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma-validate 출력 및 spec 대조

## figma_value_color_match
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 자동 체인에서 skip 가능성이 높아 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma-validate 출력 및 spec 대조

## figma_value_font_match
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 자동 체인에서 skip 가능성이 높아 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma-validate 출력 및 spec 대조

## figma_value_border_match
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 자동 체인에서 skip 가능성이 높아 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma-validate 출력 및 spec 대조

## figma_value_radius_match
- 상태: deleted
- 결정 이유: mapping 의존 규칙으로 자동 체인에서 skip 가능성이 높아 슬림 단계에서 제거.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: figma-validate 출력 및 spec 대조

## figma_values_pre_extracted
- 상태: moved_to:rules/deprecated.md
- 결정 이유: `manual_review` 전용 규칙으로 자동 실행 불가하여 활성 규칙셋에서 제외.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: PM 체크리스트 수동 점검

## no_plausible_value_fill
- 상태: moved_to:rules/deprecated.md
- 결정 이유: `manual_review` 전용 규칙으로 자동 실행 불가하여 활성 규칙셋에서 제외.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: PM 체크리스트 수동 점검

## agent_distribution_enforced
- 상태: moved_to:rules/deprecated.md
- 결정 이유: `manual_review` 전용 규칙으로 자동 실행 불가하여 활성 규칙셋에서 제외.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: PM 체크리스트 수동 점검

## coordinate_row_layout
- 상태: moved_to:rules/deprecated.md
- 결정 이유: `manual_review` 전용 규칙으로 자동 실행 불가하여 활성 규칙셋에서 제외.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: 수동 시각 검토

## aspect_ratio_preferred
- 상태: moved_to:rules/deprecated.md
- 결정 이유: `manual_review` 전용 규칙으로 자동 실행 불가하여 활성 규칙셋에서 제외.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: 수동 시각 검토

## multiline_ellipsis_pattern
- 상태: moved_to:rules/deprecated.md
- 결정 이유: `manual_review` 전용 규칙으로 자동 실행 불가하여 활성 규칙셋에서 제외.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: 수동 시각 검토

## figma_spec_sheet_required
- 상태: moved_to:rules/deprecated.md
- 결정 이유: `manual_review` 전용 프로세스 규칙으로 자동 실행 불가하여 활성 규칙셋에서 제외.
- 영향 범위: rules/rules.yaml, rules/validation_schema.json
- 대체 방법: PR 체크리스트/프로세스 게이트

## selector_single_line
- 상태: replaced_by:auto_fix
- 결정 이유: selector 한 줄 포맷은 `rules/common.md` 수동 규칙으로 관리 (auto-fix 폐기됨).
- 영향 범위: rules/rules.yaml
- 대체 방법: 수동으로 CSS 셀렉터를 한 줄로 작성 (auto-fix 폐기됨)

## media_query_format
- 상태: replaced_by:auto_fix
- 결정 이유: @media 내부 포맷은 `rules/common.md` 수동 규칙으로 관리 (auto-fix 폐기됨).
- 영향 범위: rules/rules.yaml
- 대체 방법: 수동으로 @media 블록 내부 규칙 한 줄 작성 (auto-fix 폐기됨)

## no_media_indent
- 상태: replaced_by:auto_fix
- 결정 이유: @media 포맷 관리는 `rules/common.md` 수동 규칙으로 통합 (auto-fix 폐기됨).
- 영향 범위: rules/rules.yaml
- 대체 방법: 수동으로 @media 블록 내부 규칙 한 줄 작성 (auto-fix 폐기됨)

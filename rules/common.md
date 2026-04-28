<!-- AUTO-GENERATED FROM rules/rules.yaml. DO NOT EDIT MANUALLY.
     Run: python3 tools/build-rules.py
-->

# 공통 규칙

> 이 파일은 `rules/rules.yaml`에서 자동 생성됩니다.
> 직접 편집하지 마세요. 규칙 변경은 `rules.yaml`을 수정하고 빌드를 재실행하세요.

## CSS 레이아웃

| Rule ID | Severity | Description |
| --- | --- | --- |
| `flexbox_layout` | `error` | 레이아웃은 flexbox만 사용한다 (Grid/float 금지). |
| `no_column_flex_gap` | `error` | flex-direction:column 컨테이너에서는 gap을 사용하지 않는다 (수직 간격은 margin 사용). |

### flexbox_layout (error)

레이아웃은 flexbox만 사용한다 (Grid/float 금지).


---
### no_column_flex_gap (error)

flex-direction:column 컨테이너에서는 gap을 사용하지 않는다 (수직 간격은 margin 사용).

**검증 핸들러**: `check_no_column_gap`

---
## CSS 색상

| Rule ID | Severity | Description |
| --- | --- | --- |
| `hex_color_only` | `error` | 색상은 hex 전용 (#fff, #090944). rgb()/hsl() 금지. 투명도 필요 시만 rgba() 허용. |
| `no_hex8_literal` | `warning` | 8자리 hex 리터럴(#RRGGBBAA)은 사용하지 않는다 (주석 및 url(data:) 내부는 제외). |

### hex_color_only (error)

색상은 hex 전용 (#fff, #090944). rgb()/hsl() 금지. 투명도 필요 시만 rgba() 허용.

**나쁜 예**:
```css
color: rgb(255,255,255);
```
**좋은 예**:
```css
color: #fff;
```

---
### no_hex8_literal (warning)

8자리 hex 리터럴(#RRGGBBAA)은 사용하지 않는다 (주석 및 url(data:) 내부는 제외).

**검증 핸들러**: `_check_no_hex8_literal`

---
## CSS 포맷

| Rule ID | Severity | Description |
| --- | --- | --- |
| `box_sizing_redundant` | `info` | universal reset(*, *::before, *::after) 외 box-sizing:border-box 중복 선언을 금지한다. |
| `empty_media_block` | `warning` | @media 블록 본문이 공백/주석뿐이면 빈 블록으로 간주하고 금지한다 (@media print 예외). |
| `media_query_format` | `warning` | @media 내부 규칙은 줄바꿈 분리하되 들여쓰기 없이 작성한다. 한 줄에 모든 규칙을 이어붙이지 않는다. |
| `no_important` | `warning` | !important는 사용하지 않는다 (mb_/mt_/txt_c 등 유틸리티 클래스만 예외). |
| `no_media_indent` | `info` | @media 블록 내부 규칙에 들여쓰기를 사용하지 않는다. |
| `selector_single_line` | `warning` | 각 CSS 셀렉터 규칙은 한 줄로 작성한다 (여러 줄 펼침 금지). |

### box_sizing_redundant (info)

universal reset(*, *::before, *::after) 외 box-sizing:border-box 중복 선언을 금지한다.

**검증 핸들러**: `_check_box_sizing_redundant`

---
### empty_media_block (warning)

@media 블록 본문이 공백/주석뿐이면 빈 블록으로 간주하고 금지한다 (@media print 예외).

**검증 핸들러**: `_check_empty_media_block`

---
### media_query_format (warning)

@media 내부 규칙은 줄바꿈 분리하되 들여쓰기 없이 작성한다. 한 줄에 모든 규칙을 이어붙이지 않는다.

**검증 핸들러**: `check_media_indent`

---
### no_important (warning)

!important는 사용하지 않는다 (mb_/mt_/txt_c 등 유틸리티 클래스만 예외).

**검증 핸들러**: `check_important`

---
### no_media_indent (info)

@media 블록 내부 규칙에 들여쓰기를 사용하지 않는다.

**검증 핸들러**: `check_media_indent`

---
### selector_single_line (warning)

각 CSS 셀렉터 규칙은 한 줄로 작성한다 (여러 줄 펼침 금지).

**검증 핸들러**: `check_selector_format`

---
## CSS 단위

| Rule ID | Severity | Description |
| --- | --- | --- |
| `clamp_threshold` | `info` | 100px 미만 값에는 clamp()를 사용하지 않는다 (고정 px). 100px 이상만 clamp 허용. |
| `no_clamp_under_100` | `info` | padding/margin에 100px 미만 clamp()를 사용하지 않는다. |
| `no_raw_calc` | `warning` | calc()는 clamp() 내부에서만 사용한다. 단독 사용 금지. |
| `no_raw_vw` | `warning` | vw 단위는 clamp() 내부에서만 사용한다. 단독 사용 금지. |

### clamp_threshold (info)

100px 미만 값에는 clamp()를 사용하지 않는다 (고정 px). 100px 이상만 clamp 허용.


---
### no_clamp_under_100 (info)

padding/margin에 100px 미만 clamp()를 사용하지 않는다.

**검증 핸들러**: `check_clamp_under_100`

---
### no_raw_calc (warning)

calc()는 clamp() 내부에서만 사용한다. 단독 사용 금지.

**검증 핸들러**: `check_raw_calc_vw`

---
### no_raw_vw (warning)

vw 단위는 clamp() 내부에서만 사용한다. 단독 사용 금지.

**검증 핸들러**: `check_raw_calc_vw`

---
## CSS 변수

| Rule ID | Severity | Description |
| --- | --- | --- |
| `root_var_line_separated` | `warning` | :root{} 안의 CSS 변수는 각 줄에 하나씩 선언한다 (한 줄에 여러 변수 금지). |
| `root_var_naming` | `warning` | :root 변수는 --point-color-N, --width, --padding 같은 패턴을 따른다 (시맨틱 이름 금지). |

### root_var_line_separated (warning)

:root{} 안의 CSS 변수는 각 줄에 하나씩 선언한다 (한 줄에 여러 변수 금지).

**검증 핸들러**: `check_root_vars`

---
### root_var_naming (warning)

:root 변수는 --point-color-N, --width, --padding 같은 패턴을 따른다 (시맨틱 이름 금지).

**검증 핸들러**: `root_var_naming`

---
## CSS 선택자

| Rule ID | Severity | Description |
| --- | --- | --- |
| `excessive_individual_classes` | `info` | 같은 접두사 클래스가 8개 이상이면 부모+태그 셀렉터로 축소를 검토한다. |
| `no_duplicate_selector` | `warning` | 같은 셀렉터를 미디어쿼리 밖에서 중복 선언하지 않는다 (한 번만 선언). |
| `no_utility_classes` | `warning` | .font_serif, .weight_bold 같은 유틸리티 클래스를 사용하지 않는다 — 부모 셀렉터에서 직접 처리. |
| `selector_scoped` | `warning` | 셀렉터는 페이지/섹션 스코프 안에 작성한다 (전역 단일 클래스 셀렉터 지양). |

### excessive_individual_classes (info)

같은 접두사 클래스가 8개 이상이면 부모+태그 셀렉터로 축소를 검토한다.

**검증 핸들러**: `check_excessive_individual_classes`

---
### no_duplicate_selector (warning)

같은 셀렉터를 미디어쿼리 밖에서 중복 선언하지 않는다 (한 번만 선언).

**검증 핸들러**: `check_duplicate_selectors`

---
### no_utility_classes (warning)

.font_serif, .weight_bold 같은 유틸리티 클래스를 사용하지 않는다 — 부모 셀렉터에서 직접 처리.


---
### selector_scoped (warning)

셀렉터는 페이지/섹션 스코프 안에 작성한다 (전역 단일 클래스 셀렉터 지양).

**검증 핸들러**: `selector_scoped`

---
## CSS 타이포그래피

| Rule ID | Severity | Description |
| --- | --- | --- |
| `font_family_redundant` | `warning` | 동일 font-family fallback 체인이 *, body, 개별 selector에 과다 반복되면 중복으로 간주한다. |
| `landing_unit_mixed_scale` | `warning` | landing 프로파일에서 html/body font-size에 clamp\|vw\|rem\|calc 혼용을 금지한다. |
| `letter_spacing_unit` | `warning` | letter-spacing은 em 단위를 사용한다. px는 절대값 2px 이하 미세 조정 시에만 허용. |
| `line_height_ratio_only` | `error` | line-height는 무단위 비율(1.3, 1.45)만 사용한다. 25.866px 같은 computed px 금지. |
| `line_height_tidy_ratio` | `warning` | line-height 무단위 비율은 정돈 후보 목록(1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0) 중 하나를 사용한다. |
| `word_break_korean` | `warning` | 한국어 텍스트 단락/헤딩에는 word-break: keep-all을 적용한다. |

### font_family_redundant (warning)

동일 font-family fallback 체인이 *, body, 개별 selector에 과다 반복되면 중복으로 간주한다.

**검증 핸들러**: `_check_font_family_redundant`

---
### landing_unit_mixed_scale (warning)

landing 프로파일에서 html/body font-size에 clamp|vw|rem|calc 혼용을 금지한다.

**검증 핸들러**: `_check_landing_unit_mixed_scale`

---
### letter_spacing_unit (warning)

letter-spacing은 em 단위를 사용한다. px는 절대값 2px 이하 미세 조정 시에만 허용.

**검증 핸들러**: `check_letter_spacing_unit`

---
### line_height_ratio_only (error)

line-height는 무단위 비율(1.3, 1.45)만 사용한다. 25.866px 같은 computed px 금지.

**나쁜 예**:
```css
line-height: 25.866px;
```
**좋은 예**:
```css
line-height: 1.45;
```

---
### line_height_tidy_ratio (warning)

line-height 무단위 비율은 정돈 후보 목록(1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0) 중 하나를 사용한다.

**검증 핸들러**: `_check_line_height_tidy_ratio`

---
### word_break_korean (warning)

한국어 텍스트 단락/헤딩에는 word-break: keep-all을 적용한다.


---
## CSS 테두리

| Rule ID | Severity | Description |
| --- | --- | --- |
| `border_radius_no_999` | `error` | border-radius는 원형 50%, pill 2em을 사용한다. 999px는 금지. |

### border_radius_no_999 (error)

border-radius는 원형 50%, pill 2em을 사용한다. 999px는 금지.

**나쁜 예**:
```css
border-radius: 999px;
```
**좋은 예**:
```css
border-radius: 2em;
```

---
## CSS 간격

| Rule ID | Severity | Description |
| --- | --- | --- |
| `large_side_padding` | `warning` | 좌우 padding 100px 이상이면 max-width + margin:auto 패턴으로 변환해야 한다. |
| `max_width_pattern` | `warning` | 좌우 padding 100px 이상이 발견되면 max-width 기반 레이아웃 패턴 사용을 권장한다. |

### large_side_padding (warning)

좌우 padding 100px 이상이면 max-width + margin:auto 패턴으로 변환해야 한다.

**검증 핸들러**: `check_large_side_padding`

---
### max_width_pattern (warning)

좌우 padding 100px 이상이 발견되면 max-width 기반 레이아웃 패턴 사용을 권장한다.

**검증 핸들러**: `check_max_width_pattern`

---
## HTML 구조

| Rule ID | Severity | Description |
| --- | --- | --- |
| `inner_wrapper_limit` | `warning` | 내부 wrapper div는 최대 1개로 제한한다 (불필요한 중첩 금지). |
| `max_dom_depth` | `warning` | DOM 최대 깊이는 5단계를 초과하지 않는다. |

### inner_wrapper_limit (warning)

내부 wrapper div는 최대 1개로 제한한다 (불필요한 중첩 금지).


---
### max_dom_depth (warning)

DOM 최대 깊이는 5단계를 초과하지 않는다.

**근거**: 과도한 wrapper 중첩 방지로 마크업 단순화

---
## HTML 시맨틱

| Rule ID | Severity | Description |
| --- | --- | --- |
| `forbidden_tag` | `error` | <figure>, <figcaption>, <main>, <article> 태그는 사용하지 않는다. |
| `list_pattern_required` | `warning` | 반복되는 <a> 태그는 ul>li 구조 안에 배치한다 (연속 <a> 2개 이상 금지). |
| `nav_ul_li_structure` | `error` | <nav> 안에는 ul>li>a 구조를 사용한다 (직접 <a> 나열 금지). |
| `no_empty_div` | `warning` | 빈 div(<div></div>) 사용 금지. |
| `no_inline_style` | `error` | 인라인 style 속성을 사용하지 않는다. |

### forbidden_tag (error)

<figure>, <figcaption>, <main>, <article> 태그는 사용하지 않는다.


---
### list_pattern_required (warning)

반복되는 <a> 태그는 ul>li 구조 안에 배치한다 (연속 <a> 2개 이상 금지).

**검증 핸들러**: `check_list_pattern`

---
### nav_ul_li_structure (error)

<nav> 안에는 ul>li>a 구조를 사용한다 (직접 <a> 나열 금지).

**검증 핸들러**: `check_nav_structure`

---
### no_empty_div (warning)

빈 div(<div></div>) 사용 금지.


---
### no_inline_style (error)

인라인 style 속성을 사용하지 않는다.


---
## HTML 네이밍

| Rule ID | Severity | Description |
| --- | --- | --- |
| `common_area_prefix` | `error` | header/footer/gnb/logo 같은 공통 영역에 페이지 프리픽스를 사용하지 않는다. |
| `generic_class_name` | `error` | sec_숫자, section_숫자, box숫자 같은 범용 클래스명을 모두 금지한다. |
| `meaningful_page_name` | `error` | 의미 있는 영문 페이지명을 위해 HTML 파일명 + 본문(class/markup) 모두에서 page_1/sub_01 같은 기계식 이름을 금지한다. |
| `no_body_class` | `error` | body 태그에 class 속성을 추가하지 않는다 — body는 공통 영역이므로 페이지별 class 금지. |
| `no_forbidden_class` | `error` | sec_1, sec_2, section_01 같은 범용 클래스명을 금지한다. |
| `page_filename_class_prefix_match` | `warning` | CSS 클래스 프리픽스는 HTML 파일명과 일치해야 한다 (greeting.html → greeting_). |
| `page_prefix_required` | `warning` | 각 페이지의 본문 클래스는 페이지 프리픽스({페이지}_{역할}) 패턴을 따른다. |
| `snake_case_naming` | `warning` | HTML 클래스명은 snake_case 만 사용한다 (kebab-case, camelCase 금지). |

### common_area_prefix (error)

header/footer/gnb/logo 같은 공통 영역에 페이지 프리픽스를 사용하지 않는다.

**검증 핸들러**: `check_common_area_prefix`

---
### generic_class_name (error)

sec_숫자, section_숫자, box숫자 같은 범용 클래스명을 모두 금지한다.


---
### meaningful_page_name (error)

의미 있는 영문 페이지명을 위해 HTML 파일명 + 본문(class/markup) 모두에서 page_1/sub_01 같은 기계식 이름을 금지한다.


---
### no_body_class (error)

body 태그에 class 속성을 추가하지 않는다 — body는 공통 영역이므로 페이지별 class 금지.


---
### no_forbidden_class (error)

sec_1, sec_2, section_01 같은 범용 클래스명을 금지한다.

**나쁜 예**:
```html
<section class="sec_3"><div class="box5">
```
**좋은 예**:
```html
<section class="about_intro">
```

---
### page_filename_class_prefix_match (warning)

CSS 클래스 프리픽스는 HTML 파일명과 일치해야 한다 (greeting.html → greeting_).

**검증 핸들러**: `page_filename_class_prefix_match`

---
### page_prefix_required (warning)

각 페이지의 본문 클래스는 페이지 프리픽스({페이지}_{역할}) 패턴을 따른다.


---
### snake_case_naming (warning)

HTML 클래스명은 snake_case 만 사용한다 (kebab-case, camelCase 금지).


---
## HTML 이미지

| Rule ID | Severity | Description |
| --- | --- | --- |
| `img_wrapped` | `warning` | 콘텐츠 이미지는 div.img_area 래퍼 안에 배치한다 (배경/로고/아이콘 제외). |

### img_wrapped (warning)

콘텐츠 이미지는 div.img_area 래퍼 안에 배치한다 (배경/로고/아이콘 제외).

**검증 핸들러**: `check_img_wrapper`

---
## HTML 텍스트

| Rule ID | Severity | Description |
| --- | --- | --- |
| `p_tag_condition_enforced` | `warning` | <p> 태그는 텍스트에 \n이 있거나, 길이 95자 초과거나, 종결어미 반복일 때만 사용. 짧은 라벨은 <span> 사용. |
| `p_tag_misuse` | `info` | 20자 미만 짧은 텍스트에 <p> 태그를 사용하지 않는다 — <span> 사용. |

### p_tag_condition_enforced (warning)

<p> 태그는 텍스트에 \n이 있거나, 길이 95자 초과거나, 종결어미 반복일 때만 사용. 짧은 라벨은 <span> 사용.

**검증 핸들러**: `check_p_tag_misuse`

---
### p_tag_misuse (info)

20자 미만 짧은 텍스트에 <p> 태그를 사용하지 않는다 — <span> 사용.

**검증 핸들러**: `check_p_tag_misuse`

---
## 접근성

| Rule ID | Severity | Description |
| --- | --- | --- |
| `img_alt_concise` | `info` | img alt 텍스트는 짧고 간결하게 (한국어 문장 전체 금지). |
| `minimal_aria` | `info` | aria-label은 시각적 텍스트가 없는 인터랙티브 요소에만 사용한다 (남용 금지). |

### img_alt_concise (info)

img alt 텍스트는 짧고 간결하게 (한국어 문장 전체 금지).

**검증 핸들러**: `img_alt_concise`

---
### minimal_aria (info)

aria-label은 시각적 텍스트가 없는 인터랙티브 요소에만 사용한다 (남용 금지).

**검증 핸들러**: `minimal_aria`

---
## Figma 매핑

| Rule ID | Severity | Description |
| --- | --- | --- |
| `no_constraints_to_position_absolute_mapping` | `error` | Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다. |
| `vertical_frame_itemspacing_uses_margin_bottom` | `error` | Figma VERTICAL frame 의 itemSpacing > 0 은 자식 요소의 margin-bottom 으로 변환한다. column flex gap / row-gap 사용 금지. |

### no_constraints_to_position_absolute_mapping (error)

Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다.

**검증 핸들러**: `enforce_policy2_constraints_extract_only`

---
### vertical_frame_itemspacing_uses_margin_bottom (error)

Figma VERTICAL frame 의 itemSpacing > 0 은 자식 요소의 margin-bottom 으로 변환한다. column flex gap / row-gap 사용 금지.

**검증 핸들러**: `enforce_policy1_vertical_margin_bottom`

---
## Figma 충실도

| Rule ID | Severity | Description |
| --- | --- | --- |
| `figma_rules_conflict_uses_meta_marker` | `error` | Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지). |

### figma_rules_conflict_uses_meta_marker (error)

Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지).

**검증 핸들러**: `enforce_policy3_rules_conflict_bypass`

---

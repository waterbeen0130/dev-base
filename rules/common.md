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
| `no_css_grid` | `error` | CSS Grid는 사용하지 않는다 — flexbox 전용. |
| `section_width_formula` | `error` | 섹션 폭 공식 강제: --width = Figma inner content width + 40, --padding = 20px, .cont 클래스 패턴 필수, 섹션은 full-bleed + background, 너비 제한은 .cont 내부에서만. |

### flexbox_layout (error)

레이아웃은 flexbox만 사용한다 (Grid/float 금지).


---
### no_css_grid (error)

CSS Grid는 사용하지 않는다 — flexbox 전용.

**나쁜 예**:
```css
.container { display: grid; }
```
**좋은 예**:
```css
.container { display: flex; }
```

---
### section_width_formula (error)

섹션 폭 공식 강제: --width = Figma inner content width + 40, --padding = 20px, .cont 클래스 패턴 필수, 섹션은 full-bleed + background, 너비 제한은 .cont 내부에서만.

**근거**: 프로젝트마다 반복되는 실수 방지: section에 Figma inner padding(240 등)을 직접 이식해
background가 가운데만 나오고 content 정렬이 깨지는 문제. 공식을 코드로 강제한다.

공식:
- :root { --width: <figma_content_width + 40>; --padding: 20px; }
- .cont { width: 100%; max-width: var(--width); margin: 0 auto; padding: 0 var(--padding); }
- 배경이 있는 섹션은 full-width 유지 (max-width 직접 선언 금지, .cont 하위 사용)
- border-box 기준 .cont 내부 content = --width - 2*--padding = Figma content width

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

**나쁜 예**:
```css
.btn {
  color: #fff;
  padding: 10px;
}
```
**좋은 예**:
```css
.btn{color:#fff;padding:10px}
```
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
| `multiline_ellipsis_pattern` | `info` | 다중행 말줄임 패턴은 -webkit-line-clamp 등 표준 패턴을 사용한다 (수동 시각 비교 필요). |
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
### multiline_ellipsis_pattern (info)

다중행 말줄임 패턴은 -webkit-line-clamp 등 표준 패턴을 사용한다 (수동 시각 비교 필요).

**검증 핸들러**: `manual_review`

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
| `no_figure_figcaption` | `error` | <figure>/<figcaption> 사용 금지 — div.img_area + p/span 구조 사용. |
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
### no_figure_figcaption (error)

<figure>/<figcaption> 사용 금지 — div.img_area + p/span 구조 사용.


---
### no_inline_style (error)

인라인 style 속성을 사용하지 않는다.


---
## HTML 네이밍

| Rule ID | Severity | Description |
| --- | --- | --- |
| `body_page_class_unnecessary` | `info` | body 태그에 page_ 클래스를 부여하지 않는다 (불필요). |
| `common_area_prefix` | `error` | header/footer/gnb/logo 같은 공통 영역에 페이지 프리픽스를 사용하지 않는다. |
| `generic_class_name` | `error` | sec_숫자, section_숫자, box숫자 같은 범용 클래스명을 모두 금지한다. |
| `meaningful_page_name` | `error` | HTML 파일명은 페이지 내용을 반영한 의미 있는 영문명이어야 한다 (page_1.html, sub_01.html 금지). |
| `no_forbidden_class` | `error` | sec_1, sec_2, section_01 같은 범용 클래스명을 금지한다. |
| `page_filename_class_prefix_match` | `warning` | CSS 클래스 프리픽스는 HTML 파일명과 일치해야 한다 (greeting.html → greeting_). |
| `page_prefix_required` | `warning` | 각 페이지의 본문 클래스는 페이지 프리픽스({페이지}_{역할}) 패턴을 따른다. |
| `snake_case_naming` | `warning` | HTML 클래스명은 snake_case 만 사용한다 (kebab-case, camelCase 금지). |

### body_page_class_unnecessary (info)

body 태그에 page_ 클래스를 부여하지 않는다 (불필요).


---
### common_area_prefix (error)

header/footer/gnb/logo 같은 공통 영역에 페이지 프리픽스를 사용하지 않는다.

**검증 핸들러**: `check_common_area_prefix`

---
### generic_class_name (error)

sec_숫자, section_숫자, box숫자 같은 범용 클래스명을 모두 금지한다.


---
### meaningful_page_name (error)

HTML 파일명은 페이지 내용을 반영한 의미 있는 영문명이어야 한다 (page_1.html, sub_01.html 금지).


---
### no_forbidden_class (error)

sec_1, sec_2, section_01 같은 범용 클래스명을 금지한다.

**나쁜 예**:
```html
<section class="sec_1">
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
| `aspect_ratio_preferred` | `info` | 이미지/카드 영역에 aspect-ratio 사용을 권장한다 (수동 시각 비교 필요). |
| `img_wrapped` | `warning` | 콘텐츠 이미지는 div.img_area 래퍼 안에 배치한다 (배경/로고/아이콘 제외). |

### aspect_ratio_preferred (info)

이미지/카드 영역에 aspect-ratio 사용을 권장한다 (수동 시각 비교 필요).

**검증 핸들러**: `manual_review`

---
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
| `figma_alignment_axis_mapping` | `info` | Figma primaryAxis/counterAxis 정렬은 layoutMode에 따라 CSS justify-content/align-items 매핑이 바뀐다. |
| `gap_vs_margin_decision` | `info` | Figma itemSpacing → CSS gap 또는 margin 선택은 간격 균일성·layoutMode·정렬 복잡도로 결정한다. |

### figma_alignment_axis_mapping (info)

Figma primaryAxis/counterAxis 정렬은 layoutMode에 따라 CSS justify-content/align-items 매핑이 바뀐다.

**근거**: 기존 문서는 primaryAxisAlignItems→justify-content 1:1 매핑만 명시했고
layoutMode에 따른 축 전환(HORIZONTAL: primary=수평, VERTICAL: primary=수직)은 빠져 있어서
세션마다 매핑 결과가 달라졌다.

Decision tree:
┌─ layoutMode == HORIZONTAL
│    primaryAxis(수평)  → justify-content
│    counterAxis(수직)  → align-items
│
├─ layoutMode == VERTICAL
│    primaryAxis(수직)  → justify-content  (flex-direction:column 전제)
│    counterAxis(수평)  → align-items
│
└─ layoutMode == NONE
     children absolute positioned — CSS 정렬 속성 미사용

Value mapping (양쪽 축 공통):
  MIN           → flex-start
  CENTER        → center
  MAX           → flex-end
  SPACE_BETWEEN → space-between  (primary axis only)

textAlignHorizontal → text-align (LEFT/CENTER/RIGHT/JUSTIFIED)
textAlignVertical   → 무시 (inline 요소는 vertical-align 대신 부모 align-items로 처리)

---
### gap_vs_margin_decision (info)

Figma itemSpacing → CSS gap 또는 margin 선택은 간격 균일성·layoutMode·정렬 복잡도로 결정한다.

**근거**: 기존 문서는 '동일 간격이면 gap, 다르면 margin'이라는 정성적 판단만 제시했다.
이번 룰은 수치 임계치와 decision tree로 고정한다.

Step 1 — 간격 균일성 측정:
  적응성 판정: child 간 실측 간격의 max - min 값
  ≤ 1px  → "완전 균일" (gap 사용 가능)
  ≤ 3px  → "거의 균일" (gap 허용, 1px 오차는 pixel snap)
  > 3px  → "비균일" (개별 margin 강제)

Step 2 — layoutMode별 분기:

  layoutMode == HORIZONTAL:
    - 균일 → display:flex; flex-direction:row; gap:{itemSpacing}px;
    - 비균일 → display:flex; flex-direction:row; + 자식별 margin-left:{gap_n}px
              (첫 자식 제외, `.parent > * + * {margin-left:Xpx}` 관용구)

  layoutMode == VERTICAL:
    - 균일 + 정렬 제어 필요(align-items 사용) → display:flex; flex-direction:column
              + 자식별 margin-top (common.md no_column_gap 규칙상 column에 gap 금지)
    - 균일 + 정렬 제어 불필요 → display:block; 자식별 margin-top 동일값
    - 비균일 → display:block; 자식별 margin-top 개별값

Step 3 — 관용구:
  - `.parent > * + * {margin-top:Xpx}` 이 표준 (첫 자식 margin 불필요)
  - 방향은 항상 `margin-top` (다음 자식 위쪽에 붙임), `margin-bottom` 금지
  - 단, 마지막 자식 특수 margin-bottom 이 필요하면 허용

Step 4 — 혼합 케이스:
  - HORIZONTAL wrap 레이아웃에서 `row-gap`/`column-gap` 분리 지정 가능
  - gap의 두 값 형식 `gap: row column;` 는 허용

---
## Figma 충실도

| Rule ID | Severity | Description |
| --- | --- | --- |
| `figma_cardinality_match` | `error` | Figma 카드 슬롯 수(component variant dedup 후) == HTML main section <li> 수. variant를 별개 카드로 오인 방지. |
| `figma_item_count_rule` | `info` | Figma 카드/리스트 아이템 개수 결정: 고유 bbox 슬롯 수 + component variant dedup + instance 그룹. |
| `text_from_spec_required` | `error` | extracted/*_spec.json의 text_nodes[].characters는 반드시 HTML에 나타나야 한다. AI가 텍스트를 추론/축약/복원하면 안 된다. |

### figma_cardinality_match (error)

Figma 카드 슬롯 수(component variant dedup 후) == HTML main section <li> 수. variant를 별개 카드로 오인 방지.

**근거**: Figma 컴포넌트 variant(default/hover/state 등)가 같은 위치에 stacked되어 있으면
text_nodes로 뽑을 때 variant 수만큼 중복이 나온다. HTML 작성자가 이를 별개 카드로
오인하면 카드 수가 잘못됨. 예: 에이스디펜스 main_company는 Figma 3 슬롯 + 2 variant
overlap이지만 HTML이 4 카드로 작성됐던 실제 사례.

---
### figma_item_count_rule (info)

Figma 카드/리스트 아이템 개수 결정: 고유 bbox 슬롯 수 + component variant dedup + instance 그룹.

**근거**: 기존 룰이 전무했기 때문에 text_nodes[] 개수로 카드 수를 추정했고 component variant overlap 시
variant를 별개 카드로 오인하는 사례가 반복됐다. 이 규칙은 figma_cardinality_match 와 짝으로 동작한다.

카드 개수 결정 알고리즘:

Step 1 — 리스트 컨테이너 식별:
  부모 frame이 layoutMode=HORIZONTAL (또는 VERTICAL) + children 중
  같은 componentId(또는 같은 size 반복) 인스턴스가 2개 이상 → "list container"

Step 2 — 카드 후보 수집:
  list container의 direct children 중:
  - type == INSTANCE (component instance)
  - width/height 동일 (±2px)
  - 또는 frame name 패턴이 동일 (예: list_img_company, list_card 등)

Step 3 — Variant dedup:
  같은 bbox.x 에 ±3px 이내로 겹치는 인스턴스 → component variant overlap으로 간주
  → 첫 번째 인스턴스만 카드로 계수 (나머지는 상태 variant)

  판단 근거: Figma에서 `I<instance_id>;<variant_id>;...` 형태로 parent_id 접두사가 같으면
  같은 컴포넌트 set의 다른 variant.

Step 4 — HTML 변환:
  카드 수 N → `<ul class="XXX_list"><li>` × N
  각 li는 type=INSTANCE의 visible default variant 하나만 사용

Step 5 — 검증:
  figma_cardinality_match 룰이 HTML <li> 수와 Step 4의 N을 자동 대조하여 불일치 시 CRITICAL.

---
### text_from_spec_required (error)

extracted/*_spec.json의 text_nodes[].characters는 반드시 HTML에 나타나야 한다. AI가 텍스트를 추론/축약/복원하면 안 된다.

**검증 핸들러**: `text_from_spec_required`

---

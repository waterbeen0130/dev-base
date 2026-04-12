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
## CSS 색상

| Rule ID | Severity | Description |
| --- | --- | --- |
| `hex_color_only` | `error` | 색상은 hex 전용 (#fff, #090944). rgb()/hsl() 금지. 투명도 필요 시만 rgba() 허용. |

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
## CSS 포맷

| Rule ID | Severity | Description |
| --- | --- | --- |
| `media_query_format` | `warning` | @media 내부 규칙은 줄바꿈 분리하되 들여쓰기 없이 작성한다. 한 줄에 모든 규칙을 이어붙이지 않는다. |
| `no_important` | `warning` | !important는 사용하지 않는다 (mb_/mt_/txt_c 등 유틸리티 클래스만 예외). |
| `no_media_indent` | `info` | @media 블록 내부 규칙에 들여쓰기를 사용하지 않는다. |
| `selector_single_line` | `warning` | 각 CSS 셀렉터 규칙은 한 줄로 작성한다 (여러 줄 펼침 금지). |

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
| `letter_spacing_unit` | `warning` | letter-spacing은 em 단위를 사용한다. px는 절대값 2px 이하 미세 조정 시에만 허용. |
| `line_height_ratio_only` | `error` | line-height는 무단위 비율(1.3, 1.45)만 사용한다. 25.866px 같은 computed px 금지. |
| `multiline_ellipsis_pattern` | `info` | 다중행 말줄임 패턴은 -webkit-line-clamp 등 표준 패턴을 사용한다 (수동 시각 비교 필요). |
| `word_break_korean` | `warning` | 한국어 텍스트 단락/헤딩에는 word-break: keep-all을 적용한다. |

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

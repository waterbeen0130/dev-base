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
| `no_fixed_height` | `warning` | 고정 px height/min-height/max-height (및 logical block-size 변형) 를 선언하지 않는다. min/max 가릴 것 없이 고정 px 금지. Figma 프레임 높이 직역은 반응형을 저해한다 — 높이는 콘텐츠/패딩이 결정한다. 0/auto/%/vh/var() 등 비-px 는 허용. (img/.img_area 는 img_no_fixed_size 가 담당) |
| `no_margin_first_child_reset` | `warning` | :first-child/:last-child 에서 margin 을 0 으로 리셋하지 않는다. `.list li{margin-left:30px} .list li:first-child{margin-left:0}` 식 형제 간격 처리는 flex gap 으로 대체한다 — gap 을 쓰면 first/last-child 리셋 자체가 불필요하다. |
| `no_min_width_wrapper` | `warning` | 페이지 래퍼 또는 body에 min-width를 선언하지 않는다. 반응형 레이아웃에서 min-width는 모바일 대응을 방해한다. |

### flexbox_layout (error)

레이아웃은 flexbox만 사용한다 (Grid/float 금지).


---
### no_fixed_height (warning)

고정 px height/min-height/max-height (및 logical block-size 변형) 를 선언하지 않는다. min/max 가릴 것 없이 고정 px 금지. Figma 프레임 높이 직역은 반응형을 저해한다 — 높이는 콘텐츠/패딩이 결정한다. 0/auto/%/vh/var() 등 비-px 는 허용. (img/.img_area 는 img_no_fixed_size 가 담당)

**나쁜 예**:
```css
.box{height:448px;}  /  .card{max-height:300px;}  /  .v{min-block-size:685px;}
```
**좋은 예**:
```css
.box{padding:40px 0;}  (콘텐츠가 높이 결정)  /  .hero{min-height:100vh;}
```
**검증 핸들러**: `check_no_fixed_height`

---
### no_margin_first_child_reset (warning)

:first-child/:last-child 에서 margin 을 0 으로 리셋하지 않는다. `.list li{margin-left:30px} .list li:first-child{margin-left:0}` 식 형제 간격 처리는 flex gap 으로 대체한다 — gap 을 쓰면 first/last-child 리셋 자체가 불필요하다.

**나쁜 예**:
```css
.program_list li{inline-size:340px;margin-left:30px;}  .program_list li:first-child{margin-left:0;}
```
**좋은 예**:
```css
.program_list{display:flex;gap:30px;}  .program_list li{inline-size:340px;}
```
**검증 핸들러**: `check_no_margin_first_child_reset`

---
### no_min_width_wrapper (warning)

페이지 래퍼 또는 body에 min-width를 선언하지 않는다. 반응형 레이아웃에서 min-width는 모바일 대응을 방해한다.

**근거**: min-width:1200px 같은 선언은 모바일에서 가로 스크롤을 강제함

---
## CSS 색상

| Rule ID | Severity | Description |
| --- | --- | --- |
| `hex_color_only` | `error` | 색상은 hex 전용 (#fff, #090944). rgb()/hsl() 금지. 투명도 필요 시만 rgba() 허용. |
| `no_body_background` | `error` | body/html 에 page background(background-color/background-image) 를 선언하지 않는다. body 는 공통 영역이라 전 페이지가 오염된다. 페이지 배경은 섹션/페이지 래퍼에서 지정한다 (white/투명 제외). |
| `no_hex8_literal` | `warning` | 8자리 hex 리터럴(#RRGGBBAA)은 사용하지 않는다 (주석 및 url(data:) 내부는 제외). |
| `no_redundant_white_background` | `warning` | 기본값 #fff 를 불필요하게 선언하지 않는다. white 는 페이지 기본값이므로 그냥 선언하면 의미 없다. colored 배경(섹션 등) 위에 흰 영역을 올릴 때만 정당 — colored 섹션 클래스 아래로 스코핑된 경우에만 허용한다. |

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
### no_body_background (error)

body/html 에 page background(background-color/background-image) 를 선언하지 않는다. body 는 공통 영역이라 전 페이지가 오염된다. 페이지 배경은 섹션/페이지 래퍼에서 지정한다 (white/투명 제외).

**나쁜 예**:
```css
body{background:#eef4f7;}
```
**좋은 예**:
```css
.main_visual{background:#eef4f7;}  /  .sub_wrap{background:#eef4f7;}
```
**검증 핸들러**: `check_no_body_background`

---
### no_hex8_literal (warning)

8자리 hex 리터럴(#RRGGBBAA)은 사용하지 않는다 (주석 및 url(data:) 내부는 제외).

**검증 핸들러**: `_check_no_hex8_literal`

---
### no_redundant_white_background (warning)

기본값 #fff 를 불필요하게 선언하지 않는다. white 는 페이지 기본값이므로 그냥 선언하면 의미 없다. colored 배경(섹션 등) 위에 흰 영역을 올릴 때만 정당 — colored 섹션 클래스 아래로 스코핑된 경우에만 허용한다.

**나쁜 예**:
```css
.card{background:#fff;}  (colored 배경 위가 아님)
```
**좋은 예**:
```css
.main_visual{background:#eef4f7;}  .main_visual .visual_box{background:#fff;}  (tint 위 흰 카드)
```
**검증 핸들러**: `check_no_redundant_white_background`

---
## CSS 포맷

| Rule ID | Severity | Description |
| --- | --- | --- |
| `box_sizing_redundant` | `info` | universal reset(*, *::before, *::after) 외 box-sizing:border-box 중복 선언을 금지한다. |
| `empty_media_block` | `warning` | @media 블록 본문이 공백/주석뿐이면 빈 블록으로 간주하고 금지한다 (@media print 예외). |
| `media_query_by_section` | `warning` | CSS 파일에서 미디어쿼리는 3대 영역(header / main 페이지 콘텐츠 / footer) 단위로 기본 CSS 바로 아래에 해당 영역의 breakpoint를 작성한다. main 내부 개별 섹션마다 @media를 쪼개지 않고, main 전체 base CSS 후 main 전체 @media를 breakpoint별로 모아 작성한다. 파일 하단에 전체 미디어쿼리를 몰아넣는 구조도 금지. |
| `media_query_format` | `warning` | @media 내부 규칙은 줄바꿈 분리하되 들여쓰기 없이 작성한다. 한 줄에 모든 규칙을 이어붙이지 않는다. |
| `no_important` | `warning` | !important는 사용하지 않는다 (mb_/mt_/txt_c 등 유틸리티 클래스만 예외). |
| `no_korean_css_comment` | `warning` | CSS 주석은 영어만 사용한다 (한국어 주석 금지). /* */ 블록 내 한글을 검출. |
| `reset_property_duplicate` | `warning` | reset.css에 이미 선언된 속성(a{color:inherit}, img{max-width}, font-family, font-size 등)을 common.css에서 중복 선언하지 않는다. |
| `selector_single_line` | `warning` | 각 CSS 셀렉터 규칙은 한 줄로 작성한다 (여러 줄 펼침 금지). 콤마 셀렉터 3개 이상이면 셀렉터만 줄바꿈, 속성은 마지막 셀렉터 뒤에 한 줄로 붙인다. |

### box_sizing_redundant (info)

universal reset(*, *::before, *::after) 외 box-sizing:border-box 중복 선언을 금지한다.

**검증 핸들러**: `_check_box_sizing_redundant`

---
### empty_media_block (warning)

@media 블록 본문이 공백/주석뿐이면 빈 블록으로 간주하고 금지한다 (@media print 예외).

**검증 핸들러**: `_check_empty_media_block`

---
### media_query_by_section (warning)

CSS 파일에서 미디어쿼리는 3대 영역(header / main 페이지 콘텐츠 / footer) 단위로 기본 CSS 바로 아래에 해당 영역의 breakpoint를 작성한다. main 내부 개별 섹션마다 @media를 쪼개지 않고, main 전체 base CSS 후 main 전체 @media를 breakpoint별로 모아 작성한다. 파일 하단에 전체 미디어쿼리를 몰아넣는 구조도 금지.

**근거**: 3대 영역 단위 분리로 유지보수성 향상. 섹션별 과도한 분리 방지

---
### media_query_format (warning)

@media 내부 규칙은 줄바꿈 분리하되 들여쓰기 없이 작성한다. 한 줄에 모든 규칙을 이어붙이지 않는다.

**검증 핸들러**: `check_media_indent`

---
### no_important (warning)

!important는 사용하지 않는다 (mb_/mt_/txt_c 등 유틸리티 클래스만 예외).

**검증 핸들러**: `check_important`

---
### no_korean_css_comment (warning)

CSS 주석은 영어만 사용한다 (한국어 주석 금지). /* */ 블록 내 한글을 검출.

**나쁜 예**:
```css
/* 헤더 영역 */
```
**좋은 예**:
```css
/* header area */
```
**검증 핸들러**: `check_korean_css_comment`

---
### reset_property_duplicate (warning)

reset.css에 이미 선언된 속성(a{color:inherit}, img{max-width}, font-family, font-size 등)을 common.css에서 중복 선언하지 않는다.

**근거**: reset.css 중복은 유지보수 시 양쪽을 모두 수정해야 하는 문제 유발

---
### selector_single_line (warning)

각 CSS 셀렉터 규칙은 한 줄로 작성한다 (여러 줄 펼침 금지). 콤마 셀렉터 3개 이상이면 셀렉터만 줄바꿈, 속성은 마지막 셀렉터 뒤에 한 줄로 붙인다.

**검증 핸들러**: `check_selector_format`

---
## CSS 단위

| Rule ID | Severity | Description |
| --- | --- | --- |
| `clamp_threshold` | `info` | 100px 미만 값에는 clamp()를 사용하지 않는다 (고정 px). 100px 이상만 clamp 허용. |
| `no_clamp_under_100` | `info` | padding/margin에 100px 미만 clamp()를 사용하지 않는다. |
| `no_raw_calc` | `warning` | calc()와 vw 단위는 clamp() 내부에서만 사용한다. 단독 사용 금지. |

### clamp_threshold (info)

100px 미만 값에는 clamp()를 사용하지 않는다 (고정 px). 100px 이상만 clamp 허용.


---
### no_clamp_under_100 (info)

padding/margin에 100px 미만 clamp()를 사용하지 않는다.

**검증 핸들러**: `check_clamp_under_100`

---
### no_raw_calc (warning)

calc()와 vw 단위는 clamp() 내부에서만 사용한다. 단독 사용 금지.

**검증 핸들러**: `check_raw_calc_vw`

---
## CSS 네이밍

| Rule ID | Severity | Description |
| --- | --- | --- |
| `child_prefix_nesting` | `error` | 자식 클래스에 부모 prefix를 중첩하지 않는다. main_project_list 같은 패턴은 .main_project .list 로 부모 스코핑해야 한다. 섹션 컨테이너 자체(main_project)의 2-토큰 네이밍은 허용. |

### child_prefix_nesting (error)

자식 클래스에 부모 prefix를 중첩하지 않는다. main_project_list 같은 패턴은 .main_project .list 로 부모 스코핑해야 한다. 섹션 컨테이너 자체(main_project)의 2-토큰 네이밍은 허용.

**나쁜 예**:
```css
.main_project_list{...}, .main_intro_card_icon{...}
```
**좋은 예**:
```css
.main_project .list{...}, .main_intro .card img{...}
```
**근거**: prefix 중첩은 클래스명이 길어지고 스코핑 구조가 CSS에 반영되지 않음

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
| `common_area_child_scope` | `warning` | 공통영역 자식 클래스(.logo, .gnb, .utils, .sns, .copyright, .logo_txt 등)는 .header/.footer 부모 셀렉터와 함께 선언한다. 단독 선언(.logo{}, .gnb a{})은 header/footer 양쪽 충돌 위험으로 금지. |
| `cont_redundant_scoping` | `warning` | .X .cont 스코핑이 전역 .cont 기본값(max-width:var(--width), margin:0 auto, width:min(100%,var(--width)))만 재선언하면 중복이다. 전역 .cont 공통값을 그대로 쓰고, 값이 다른 특수 케이스에서만 별도 선언한다. |
| `excessive_individual_classes` | `warning` | 같은 접두사 클래스가 5개 이상이면 부모 스코핑(.parent .child) + 태그 셀렉터로 축소해야 한다. 자식에 부모 prefix를 중첩하지 않는다. |
| `generic_class_parent_scope` | `warning` | 페이지 prefix 섹션(.main_visual, .main_news 등) 내부의 모든 자식 클래스는 반드시 부모 섹션 셀렉터와 함께 선언한다. 범용적 이름인지 판단하지 않는다 — 섹션 내부이면 무조건 부모를 붙인다. 예외: 전역 공통 클래스(.header/.footer/.cont/.img_area)는 global_class_standalone 규칙에 따라 단독 선언하며 이 규칙 대상이 아니다. |
| `global_class_standalone` | `warning` | 전역 클래스(.header, .footer, .cont, .img_area)는 body/html 등 부모를 붙이지 않고 단독 선언한다. 섹션 레벨 오버라이드(.main_intro .cont)는 허용. |
| `no_duplicate_selector` | `warning` | 같은 셀렉터를 미디어쿼리 밖에서 중복 선언하지 않는다 (한 번만 선언). |
| `no_utility_classes` | `warning` | .font_serif, .weight_bold 같은 유틸리티 클래스를 사용하지 않는다 — 부모 셀렉터에서 직접 처리. |
| `selector_scoped` | `warning` | 셀렉터는 페이지/섹션 스코프 안에 작성한다 (전역 단일 클래스 셀렉터 지양). |

### common_area_child_scope (warning)

공통영역 자식 클래스(.logo, .gnb, .utils, .sns, .copyright, .logo_txt 등)는 .header/.footer 부모 셀렉터와 함께 선언한다. 단독 선언(.logo{}, .gnb a{})은 header/footer 양쪽 충돌 위험으로 금지.

**나쁜 예**:
```css
.logo{...}  /  .gnb a{...}
```
**좋은 예**:
```css
.header .logo{...}  /  .header .gnb a{...}
```
**검증 핸들러**: `check_common_area_child_scope`

---
### cont_redundant_scoping (warning)

.X .cont 스코핑이 전역 .cont 기본값(max-width:var(--width), margin:0 auto, width:min(100%,var(--width)))만 재선언하면 중복이다. 전역 .cont 공통값을 그대로 쓰고, 값이 다른 특수 케이스에서만 별도 선언한다.

**나쁜 예**:
```css
.header .cont,.footer .cont{width:min(100%,var(--width));margin:0 auto;}
```
**좋은 예**:
```css
.cont{margin:0 auto;max-width:var(--width);padding:0 var(--padding);}  (전역 1회)  /  .header .cont{max-width:1920px;padding:0 50px;}  (값이 다른 특수)
```
**검증 핸들러**: `check_cont_redundant_scoping`

---
### excessive_individual_classes (warning)

같은 접두사 클래스가 5개 이상이면 부모 스코핑(.parent .child) + 태그 셀렉터로 축소해야 한다. 자식에 부모 prefix를 중첩하지 않는다.

**검증 핸들러**: `check_excessive_individual_classes`

---
### generic_class_parent_scope (warning)

페이지 prefix 섹션(.main_visual, .main_news 등) 내부의 모든 자식 클래스는 반드시 부모 섹션 셀렉터와 함께 선언한다. 범용적 이름인지 판단하지 않는다 — 섹션 내부이면 무조건 부모를 붙인다. 예외: 전역 공통 클래스(.header/.footer/.cont/.img_area)는 global_class_standalone 규칙에 따라 단독 선언하며 이 규칙 대상이 아니다.

**근거**: 섹션 내부 클래스가 부모 스코핑 없이 단독 선언되면 다른 페이지/섹션과 충돌 가능

---
### global_class_standalone (warning)

전역 클래스(.header, .footer, .cont, .img_area)는 body/html 등 부모를 붙이지 않고 단독 선언한다. 섹션 레벨 오버라이드(.main_intro .cont)는 허용.

**나쁜 예**:
```css
body .header{...}  /  html .cont{...}
```
**좋은 예**:
```css
.header{...}  /  .cont{...}  /  .main_intro .cont{...}
```
**검증 핸들러**: `check_global_class_standalone`

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
| `font_variable_required` | `warning` | non-reset 폰트 선언은 CSS 변수(--font, --font2 등)와 CDN @import를 사용한다. common.css에 직접 font-family:'Pretendard' 같은 하드코딩을 하지 않는다 (reset.css의 @font-face 선언은 예외). |
| `landing_unit_mixed_scale` | `warning` | landing 프로파일에서 html/body font-size에 clamp\|vw\|rem\|calc 혼용을 금지한다. |
| `letter_spacing_unit` | `warning` | letter-spacing은 em 단위를 사용한다. px는 절대값 2px 이하 미세 조정 시에만 허용. |
| `line_height_ratio_only` | `error` | line-height는 무단위 비율(1.3, 1.45)만 사용한다. 25.866px 같은 computed px 금지. |
| `line_height_tidy_ratio` | `warning` | line-height 무단위 비율은 정돈 후보 목록(1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0) 중 하나를 사용한다. |
| `word_break_korean` | `warning` | 한국어 텍스트 단락/헤딩에는 word-break: keep-all을 적용한다. |

### font_family_redundant (warning)

동일 font-family fallback 체인이 *, body, 개별 selector에 과다 반복되면 중복으로 간주한다.

**검증 핸들러**: `_check_font_family_redundant`

---
### font_variable_required (warning)

non-reset 폰트 선언은 CSS 변수(--font, --font2 등)와 CDN @import를 사용한다. common.css에 직접 font-family:'Pretendard' 같은 하드코딩을 하지 않는다 (reset.css의 @font-face 선언은 예외).

**근거**: 폰트를 변수화하면 프로젝트 간 폰트 교체가 용이하고 CDN 관리가 통합됨

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
## css / image

| Rule ID | Severity | Description |
| --- | --- | --- |
| `img_no_fixed_size` | `error` | img 및 .img_area에 고정 width/height CSS를 선언하지 않는다. 로고 img는 어떤 크기 제어도 금지 (img width/height, 부모 flex-basis/max-width 모두 금지 — 원본 사이즈 그대로 출력). 일반 이미지는 크기가 필요하면 부모 컨테이너에서 제어한다. |
| `no_background_size` | `error` | background-size 선언을 금지한다. --download-assets가 이미지를 Figma 디자인 1:1 크기로 추출하므로 background-size가 불필요하다. spec.json의 scaleMode/scalingFactor/imageTransform은 Figma 내부 렌더링 파라미터이며 CSS로 변환하면 안 된다. |
| `no_img_area_declaration` | `warning` | .img_area 를 단독으로 선언(기본 CSS)하지 않는다. 이미지 반응형은 reset.css 의 img{max-width:100%} 가 처리하므로 .img_area 기본 규칙은 중복이다. |

### img_no_fixed_size (error)

img 및 .img_area에 고정 width/height CSS를 선언하지 않는다. 로고 img는 어떤 크기 제어도 금지 (img width/height, 부모 flex-basis/max-width 모두 금지 — 원본 사이즈 그대로 출력). 일반 이미지는 크기가 필요하면 부모 컨테이너에서 제어한다.

**검증 핸들러**: `check_img_no_fixed_size`

---
### no_background_size (error)

background-size 선언을 금지한다. --download-assets가 이미지를 Figma 디자인 1:1 크기로 추출하므로 background-size가 불필요하다. spec.json의 scaleMode/scalingFactor/imageTransform은 Figma 내부 렌더링 파라미터이며 CSS로 변환하면 안 된다.

**나쁜 예**:
```css
['background-size:cover → 삭제', 'background-size:contain → 삭제', 'background-size:200px 300px → 삭제']
```
**좋은 예**:
```css
['background-size 없이 background-image만 선언', '이미지 크기는 부모 컨테이너에서 제어']
```
**검증 핸들러**: `check_no_background_size`

---
### no_img_area_declaration (warning)

.img_area 를 단독으로 선언(기본 CSS)하지 않는다. 이미지 반응형은 reset.css 의 img{max-width:100%} 가 처리하므로 .img_area 기본 규칙은 중복이다.

**나쁜 예**:
```css
.img_area{display:block;overflow:hidden;}  /  .img_area img{max-width:100%;}
```
**좋은 예**:
```css
(선언 없음 — reset.css img{max-width:100%} 사용)
```
**검증 핸들러**: `check_no_img_area_declaration`

---
## HTML 구조

| Rule ID | Severity | Description |
| --- | --- | --- |
| `html_formatting` | `error` | HTML 태그는 적절히 줄바꿈하고 4-space 들여쓰기를 적용한다. 자식 태그가 2개 이상이거나 줄 길이가 80자를 초과하면 반드시 줄바꿈한다. |
| `inner_wrapper_limit` | `warning` | 내부 wrapper div는 최대 1개로 제한한다 (불필요한 중첩 금지). |
| `max_dom_depth` | `warning` | DOM 최대 깊이는 5단계를 초과하지 않는다. |
| `no_section_id` | `error` | 퍼블리싱에서 <section> 태그에 id 속성을 사용하지 않는다. 앵커 링크가 필요하면 내부 요소에 id를 부여한다. |

### html_formatting (error)

HTML 태그는 적절히 줄바꿈하고 4-space 들여쓰기를 적용한다. 자식 태그가 2개 이상이거나 줄 길이가 80자를 초과하면 반드시 줄바꿈한다.

**나쁜 예**:
```html
<ul><li>A</li><li>B</li><li>C</li></ul>
<div class="card"><span class="img_area"><img src="img/photo.jpg" alt=""></span><span class="title">Title</span></div>
```
**좋은 예**:
```html
<ul>
    <li>A</li>
    <li>B</li>
    <li>C</li>
</ul>
<div class="card">
    <span class="img_area"><img src="img/photo.jpg" alt=""></span>
    <span class="title">Title</span>
</div>
```
**근거**: 복잡한 중첩 태그를 한 줄로 이어붙이면 가독성이 저하됨

---
### inner_wrapper_limit (warning)

내부 wrapper div는 최대 1개로 제한한다 (불필요한 중첩 금지).


---
### max_dom_depth (warning)

DOM 최대 깊이는 5단계를 초과하지 않는다.

**근거**: 과도한 wrapper 중첩 방지로 마크업 단순화

---
### no_section_id (error)

퍼블리싱에서 <section> 태그에 id 속성을 사용하지 않는다. 앵커 링크가 필요하면 내부 요소에 id를 부여한다.

**나쁜 예**:
```html
<section id="about">
```
**좋은 예**:
```html
<section class="main_about">
```
**근거**: section id는 JS 프레임워크 패턴이며 퍼블리싱에서는 클래스 기반 선택이 표준

---
## HTML 시맨틱

| Rule ID | Severity | Description |
| --- | --- | --- |
| `forbidden_tag` | `error` | <figure>, <figcaption>, <main>, <article> 태그는 사용하지 않는다. |
| `list_pattern_required` | `warning` | 반복되는 <a> 태그는 ul>li 구조 안에 배치한다 (연속 <a> 2개 이상 금지). |
| `nav_ul_li_structure` | `error` | <nav> 안에는 ul>li>a 구조를 사용한다 (직접 <a> 나열 금지). |
| `no_decorative_empty_tag` | `warning` | 장식 목적의 빈 span/div/i 태그 사용을 금지한다. CSS ::before/::after 가상 선택자로 대체한다. 예외: 아이콘 폰트 <i>, 빈 셀 <td>, JavaScript 동적 조작 요소. |
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
### no_decorative_empty_tag (warning)

장식 목적의 빈 span/div/i 태그 사용을 금지한다. CSS ::before/::after 가상 선택자로 대체한다. 예외: 아이콘 폰트 <i>, 빈 셀 <td>, JavaScript 동적 조작 요소.

**근거**: 의미 없는 빈 태그는 접근성 저하와 마크업 비대화를 유발

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
| `common_area_prefix` | `error` | header/footer/gnb/logo/container/utils/sns/copyright 같은 공통 영역에 페이지 프리픽스를 사용하지 않는다. 공통 영역은 어떤 페이지(index.html, greeting.html 등)에 있어도 prefix 없이 사용한다. 이 규칙은 page_prefix_required 보다 항상 우선한다. |
| `cont_class_required` | `error` | 섹션 내부 너비 제한에는 .cont 공통 클래스를 사용한다. eos_inner, sec_inner, content_wrap 같은 커스텀 inner wrapper 클래스를 금지한다. |
| `meaningful_page_name` | `error` | 의미 있는 영문 페이지명을 위해 HTML 파일명 + 본문(class/markup) 모두에서 page_1/sub_01 같은 기계식 이름을 금지한다. |
| `no_body_class` | `error` | body 태그에 class 속성을 추가하지 않는다 — body는 공통 영역이므로 페이지별 class 금지. |
| `no_figma_nodeid_class` | `error` | Figma 노드명을 그대로 박은 클래스(main_f0, main_v53, main_t12, hero_v2 같은 {접두}_{f\|v\|t}{숫자} 패턴)를 금지한다. 디자이너 레이어 식별자이며 시맨틱 의미가 없다. 페이지 prefix + 역할명(main_intro, greeting_title)을 사용한다. |
| `no_forbidden_class` | `error` | sec_1, sec_2, section_01 같은 범용 클래스명을 금지한다. |
| `no_guess_prefix` | `warning` | site_, g_, common_ 같은 추측성 prefix 클래스를 금지한다. 공통영역은 prefix 없이(.header), 페이지 콘텐츠는 파일명 기반 prefix(main_, greeting_)를 사용한다. |
| `no_wrapper_class` | `error` | eos_site, wrap_all, page_wrapper 같은 비표준 전체 래퍼 클래스를 금지한다. 전체 페이지 래퍼가 필요하면 기존 body 또는 시멘틱 태그를 활용한다. |
| `page_filename_class_prefix_match` | `warning` | CSS 클래스 프리픽스는 HTML 파일명과 일치해야 한다 (greeting.html → greeting_). |
| `page_prefix_required` | `warning` | 페이지 prefix는 섹션 컨테이너에만 부여한다 ({페이지}_{역할} 패턴, 예: main_intro, main_product). index.html은 main_ prefix를 사용한다. 기타 서브페이지는 파일명이 prefix (greeting.html → greeting_). 자식 요소는 짧은 역할명(.card, .list, .title_area)으로 선언하고 CSS는 .main_intro .card 형태로 부모 스코핑한다. 자식에 부모 prefix를 중첩하지 않는다 (.main_intro_card 금지 → .main_intro .card). 공통 영역(header/footer/gnb/logo/container/utils/sns)은 prefix 없이 사용. |
| `snake_case_naming` | `warning` | HTML 클래스명은 snake_case 만 사용한다 (kebab-case, camelCase 금지). |

### common_area_prefix (error)

header/footer/gnb/logo/container/utils/sns/copyright 같은 공통 영역에 페이지 프리픽스를 사용하지 않는다. 공통 영역은 어떤 페이지(index.html, greeting.html 등)에 있어도 prefix 없이 사용한다. 이 규칙은 page_prefix_required 보다 항상 우선한다.

**나쁜 예**:
```html
.index_header, .main_footer, .sub_container, .index_gnb
```
**좋은 예**:
```html
.header, .footer, .container, .gnb (모든 페이지에서 prefix 없이 동일)
```
**검증 핸들러**: `check_common_area_prefix`

---
### cont_class_required (error)

섹션 내부 너비 제한에는 .cont 공통 클래스를 사용한다. eos_inner, sec_inner, content_wrap 같은 커스텀 inner wrapper 클래스를 금지한다.

**나쁜 예**:
```html
<div class="eos_inner">, <div class="sec_inner">
```
**좋은 예**:
```html
<div class="cont">
```
**근거**: .cont는 common.css에 전역 선언된 표준 패턴이며 커스텀 inner wrapper는 일관성을 해침

---
### meaningful_page_name (error)

의미 있는 영문 페이지명을 위해 HTML 파일명 + 본문(class/markup) 모두에서 page_1/sub_01 같은 기계식 이름을 금지한다.


---
### no_body_class (error)

body 태그에 class 속성을 추가하지 않는다 — body는 공통 영역이므로 페이지별 class 금지.


---
### no_figma_nodeid_class (error)

Figma 노드명을 그대로 박은 클래스(main_f0, main_v53, main_t12, hero_v2 같은 {접두}_{f|v|t}{숫자} 패턴)를 금지한다. 디자이너 레이어 식별자이며 시맨틱 의미가 없다. 페이지 prefix + 역할명(main_intro, greeting_title)을 사용한다.

**나쁜 예**:
```html
<div class="main_f0"><span class="main_v53"><p class="main_t12">
```
**좋은 예**:
```html
<div class="main_intro"><span class="main_visual">
```

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
### no_guess_prefix (warning)

site_, g_, common_ 같은 추측성 prefix 클래스를 금지한다. 공통영역은 prefix 없이(.header), 페이지 콘텐츠는 파일명 기반 prefix(main_, greeting_)를 사용한다.

**나쁜 예**:
```html
<div class="site_header"><span class="common_wrap">
```
**좋은 예**:
```html
<div class="header"><span class="main_intro">
```

---
### no_wrapper_class (error)

eos_site, wrap_all, page_wrapper 같은 비표준 전체 래퍼 클래스를 금지한다. 전체 페이지 래퍼가 필요하면 기존 body 또는 시멘틱 태그를 활용한다.

**나쁜 예**:
```html
<div class="eos_site">, <div class="wrap_all">
```
**좋은 예**:
```html
body 직속으로 header/section/footer 배치
```
**근거**: 비표준 래퍼는 불필요한 DOM 깊이를 추가하고 프로젝트 간 일관성을 해침

---
### page_filename_class_prefix_match (warning)

CSS 클래스 프리픽스는 HTML 파일명과 일치해야 한다 (greeting.html → greeting_).

**검증 핸들러**: `page_filename_class_prefix_match`

---
### page_prefix_required (warning)

페이지 prefix는 섹션 컨테이너에만 부여한다 ({페이지}_{역할} 패턴, 예: main_intro, main_product). index.html은 main_ prefix를 사용한다. 기타 서브페이지는 파일명이 prefix (greeting.html → greeting_). 자식 요소는 짧은 역할명(.card, .list, .title_area)으로 선언하고 CSS는 .main_intro .card 형태로 부모 스코핑한다. 자식에 부모 prefix를 중첩하지 않는다 (.main_intro_card 금지 → .main_intro .card). 공통 영역(header/footer/gnb/logo/container/utils/sns)은 prefix 없이 사용.


---
### snake_case_naming (warning)

HTML 클래스명은 snake_case 만 사용한다 (kebab-case, camelCase 금지).


---
## HTML 이미지

| Rule ID | Severity | Description |
| --- | --- | --- |
| `img_wrapped` | `warning` | 모든 <img> 태그는 .img_area 래퍼 안에 배치한다 (CSS 배경 이미지만 제외). 로고, 아이콘, 파트너 로고 등 예외 없음. |

### img_wrapped (warning)

모든 <img> 태그는 .img_area 래퍼 안에 배치한다 (CSS 배경 이미지만 제외). 로고, 아이콘, 파트너 로고 등 예외 없음.

**검증 핸들러**: `check_img_wrapper`

---
## HTML 텍스트

| Rule ID | Severity | Description |
| --- | --- | --- |
| `newline_to_br_required` | `error` | spec.json 텍스트의 \n 및 \u2028은 HTML에서 반드시 <br> 태그로 변환한다. HTML 원문에 \n을 그냥 두면 브라우저가 무시하므로 <br>로 명시 변환 필수. 연속 \n\n은 블록 분리(</p><p>) 또는 <br><br>로 처리. |
| `p_tag_condition_enforced` | `warning` | <p> 태그는 텍스트에 \n이 있거나, 길이 95자 초과거나, 종결어미 반복일 때만 사용. 짧은 라벨은 <span> 사용. |

### newline_to_br_required (error)

spec.json 텍스트의 \n 및 \u2028은 HTML에서 반드시 <br> 태그로 변환한다. HTML 원문에 \n을 그냥 두면 브라우저가 무시하므로 <br>로 명시 변환 필수. 연속 \n\n은 블록 분리(</p><p>) 또는 <br><br>로 처리.

**근거**: 거의 모든 프로젝트에서 외주 에이전트가 \n → <br> 변환을 누락하여 줄바꿈이 사라지는 문제 반복 발생.

---
### p_tag_condition_enforced (warning)

<p> 태그는 텍스트에 \n이 있거나, 길이 95자 초과거나, 종결어미 반복일 때만 사용. 짧은 라벨은 <span> 사용.

**검증 핸들러**: `check_p_tag_misuse`

---
## 접근성

| Rule ID | Severity | Description |
| --- | --- | --- |
| `img_alt_concise` | `info` | img alt 텍스트는 짧고 간결하게 (한국어 문장 전체 금지). |
| `minimal_aria` | `info` | aria-label은 시각적 텍스트가 없는 인터랙티브 요소에만 사용한다 (남용 금지). |
| `no_duplicate_ir_class` | `warning` | reset.css 의 .ir 과 동일한 IR/스크린리더 숨김 패턴(left:-10000px, text-indent 음수, clip 등)을 새 클래스로 재정의하지 않는다. 기존 reset.css 의 .ir 을 사용한다. |

### img_alt_concise (info)

img alt 텍스트는 짧고 간결하게 (한국어 문장 전체 금지).

**검증 핸들러**: `img_alt_concise`

---
### minimal_aria (info)

aria-label은 시각적 텍스트가 없는 인터랙티브 요소에만 사용한다 (남용 금지).

**검증 핸들러**: `minimal_aria`

---
### no_duplicate_ir_class (warning)

reset.css 의 .ir 과 동일한 IR/스크린리더 숨김 패턴(left:-10000px, text-indent 음수, clip 등)을 새 클래스로 재정의하지 않는다. 기존 reset.css 의 .ir 을 사용한다.

**나쁜 예**:
```css
.text_bank{position:absolute;left:-10000px;inline-size:1px;block-size:1px;overflow:hidden;}
```
**좋은 예**:
```css
(reset.css 의 .ir 사용)
```
**검증 핸들러**: `check_no_duplicate_ir_class`

---
## Figma 매핑

| Rule ID | Severity | Description |
| --- | --- | --- |
| `no_constraints_to_position_absolute_mapping` | `error` | Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다. |

### no_constraints_to_position_absolute_mapping (error)

Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다.

**검증 핸들러**: `enforce_policy2_constraints_extract_only`

---
## Figma 충실도

| Rule ID | Severity | Description |
| --- | --- | --- |
| `figma_rules_conflict_uses_meta_marker` | `error` | Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지). |

### figma_rules_conflict_uses_meta_marker (error)

Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지).

**검증 핸들러**: `enforce_policy3_rules_conflict_bypass`

---
## spec / schema

| Rule ID | Severity | Description |
| --- | --- | --- |
| `spec_extraction_method_warning` | `warning` | MCP 수동 폴백으로 추출된 spec.json은 타이포그래피 정확도가 미보장된다. figma-section-spec.py로 재추출 권장. |
| `spec_typography_required` | `error` | spec.json text_nodes에 타이포그래피 메타데이터(fontSize/fontWeight/fontFamily)가 누락되면 코드 추출 진입을 차단한다. figma-section-spec.py --download-assets로 재추출 필요. |

### spec_extraction_method_warning (warning)

MCP 수동 폴백으로 추출된 spec.json은 타이포그래피 정확도가 미보장된다. figma-section-spec.py로 재추출 권장.

**근거**: MCP 수동 폴백은 id/characters만 추출하여 fontSize/fontWeight 등이 전면 누락됨

---
### spec_typography_required (error)

spec.json text_nodes에 타이포그래피 메타데이터(fontSize/fontWeight/fontFamily)가 누락되면 코드 추출 진입을 차단한다. figma-section-spec.py --download-assets로 재추출 필요.

**근거**: 타이포그래피 메타데이터 없는 spec으로 코드 추출 시 에이전트가 폰트값을 추측하여 오류 발생

---

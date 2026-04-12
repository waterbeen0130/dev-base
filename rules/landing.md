<!-- AUTO-GENERATED FROM rules/rules.yaml. DO NOT EDIT MANUALLY.
     Run: python3 tools/build-rules.py
-->

# Landing 추가 규칙

> 이 파일은 `rules/rules.yaml`에서 자동 생성됩니다.
> 공통 규칙은 `common.md`를 참고하세요.

## CSS 포맷

| Rule ID | Severity | Description |
| --- | --- | --- |
| `gsap_animation_css_present` | `warning` | landing 프로젝트는 [data-delay] opacity/position 룰과 .section_on 토글 룰이 있어야 한다. |

### gsap_animation_css_present (warning)

landing 프로젝트는 [data-delay] opacity/position 룰과 .section_on 토글 룰이 있어야 한다.


---
## CSS 변수

| Rule ID | Severity | Description |
| --- | --- | --- |
| `root_vars_required` | `warning` | landing 프로젝트는 :root에 --padding, --header_h, --width, --point-color-1 4개 변수가 모두 존재해야 한다. |

### root_vars_required (warning)

landing 프로젝트는 :root에 --padding, --header_h, --width, --point-color-1 4개 변수가 모두 존재해야 한다.


---
## CSS 타이포그래피

| Rule ID | Severity | Description |
| --- | --- | --- |
| `font_size_landing_px` | `warning` | landing 프로젝트: 모든 font-size는 PC/모바일 모두 고정 px만 사용 (rem 사용 금지). |

### font_size_landing_px (warning)

landing 프로젝트: 모든 font-size는 PC/모바일 모두 고정 px만 사용 (rem 사용 금지).


---

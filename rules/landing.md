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
| `root_width_derivation` | `warning` | :root --width 는 Figma 콘텐츠폭 + 양측 --padding 과 일치해야 한다 (--width = content_width + 2×--padding). content_width 는 extracted/*_spec.json 의 frame inner width 에서 추출하며, spec 미발견 시 비차단 skip. |

### root_vars_required (warning)

landing 프로젝트는 :root에 --padding, --header_h, --width, --point-color-1 4개 변수가 모두 존재해야 한다.


---
### root_width_derivation (warning)

:root --width 는 Figma 콘텐츠폭 + 양측 --padding 과 일치해야 한다 (--width = content_width + 2×--padding). content_width 는 extracted/*_spec.json 의 frame inner width 에서 추출하며, spec 미발견 시 비차단 skip.

**나쁜 예**:
```css
:root{--padding:20px;--width:1400px;}  (콘텐츠폭 1440인데 1400)
```
**좋은 예**:
```css
:root{--padding:20px;--width:1480px;}  (= 콘텐츠폭 1440 + 2×20)
```
**검증 핸들러**: `check_root_width_derivation`

---
## CSS 타이포그래피

| Rule ID | Severity | Description |
| --- | --- | --- |
| `font_size_landing_px` | `warning` | landing 프로젝트: 모든 font-size는 PC/모바일 모두 고정 px만 사용 (rem 사용 금지). |

### font_size_landing_px (warning)

landing 프로젝트: 모든 font-size는 PC/모바일 모두 고정 px만 사용 (rem 사용 금지).


---

<!-- AUTO-GENERATED FROM rules/rules.yaml. DO NOT EDIT MANUALLY.
     Run: python3 tools/build-rules.py
-->

# Basic 추가 규칙

> 이 파일은 `rules/rules.yaml`에서 자동 생성됩니다.
> 공통 규칙은 `common.md`를 참고하세요.

## CSS 포맷

| Rule ID | Severity | Description |
| --- | --- | --- |
| `reset_css_separate` | `warning` | basic 프로젝트: reset.css는 별도 파일로 분리한다. |
| `reset_duplicate` | `warning` | common.css에 reset.css의 핵심 패턴(* margin/padding/box-sizing 등)을 중복 작성하지 않는다. |

### reset_css_separate (warning)

basic 프로젝트: reset.css는 별도 파일로 분리한다.


---
### reset_duplicate (warning)

common.css에 reset.css의 핵심 패턴(* margin/padding/box-sizing 등)을 중복 작성하지 않는다.

**검증 핸들러**: `check_reset_duplicate`

---
## CSS 타이포그래피

| Rule ID | Severity | Description |
| --- | --- | --- |
| `font_size_pc_rem` | `warning` | basic 프로젝트: PC font-size는 rem 단위, 모바일(@media max-width:768px)에서만 px 사용. |

### font_size_pc_rem (warning)

basic 프로젝트: PC font-size는 rem 단위, 모바일(@media max-width:768px)에서만 px 사용.

**검증 핸들러**: `check_font_size_base`

---
## CSS 간격

| Rule ID | Severity | Description |
| --- | --- | --- |
| `mobile_spacing_half` | `info` | basic 프로젝트 768px 이하: padding/margin은 PC 값의 약 절반 사용. |

### mobile_spacing_half (info)

basic 프로젝트 768px 이하: padding/margin은 PC 값의 약 절반 사용.

**검증 핸들러**: `mobile_spacing_half`

---

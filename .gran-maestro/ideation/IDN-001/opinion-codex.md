# CSS/레이아웃 구현 품질 향상 추가 규칙 제안

작성일: 2026-02-18
역할: CSS/레이아웃 구현 품질 향상 전문가

---

## 1. z-index 관리 — 레이어 체계 정의

**제안 규칙**: `:root`에 레이어 변수를 숫자 단계로 고정 선언한다. `--z-base:1`, `--z-sticky:100`, `--z-dropdown:200`, `--z-header:300`, `--z-modal:400`, `--z-popup:500`, `--z-toast:600`. 각 컴포넌트는 반드시 해당 변수를 사용하고 임의 숫자 직접 입력 금지. 예: `.main_header{z-index:var(--z-header);}`.

**기존 규칙과의 관계**: 신규 추가. 현재 `:root` 변수 규칙(`--point-color-1`, `--width` 등)의 확장으로 적용.

**rule_engine.json 초안**:
```json
"z_index": {
  "strategy": "css_variable",
  "layers": {"base":1,"sticky":100,"dropdown":200,"header":300,"modal":400,"popup":500,"toast":600},
  "forbid_raw_z_index": true,
  "var_format": "--z-{layer}"
}
```

---

## 2. overflow 처리 패턴

**제안 규칙**: 가로 스크롤 방지는 최상위 래퍼에서만 `overflow-x:hidden` 적용, 하위 요소 남발 금지. 텍스트 오버플로우는 `overflow:hidden`+`text-overflow:ellipsis`+`white-space:nowrap` 세트로 항상 묶어서 선언. 스크롤 영역은 `-webkit-overflow-scrolling:touch`와 함께 `overflow-y:auto` 사용.

**기존 규칙과의 관계**: 신규 추가. 현재 flexbox-only 규칙과 함께 가로 레이아웃 오버플로우 방지 역할.

**rule_engine.json 초안**:
```json
"overflow": {
  "horizontal_scroll_block": "root_wrapper_only",
  "text_ellipsis_bundle": ["overflow:hidden","text-overflow:ellipsis","white-space:nowrap"],
  "scroll_area_touch": true,
  "forbid_overflow_hidden_on_flex_child": false
}
```

---

## 3. CSS 변수 체계 확장

**제안 규칙**: 현재 `--point-color-1`, `--font-color-1`, `--width`, `--padding` 외에 타이포(`--font-size-base`, `--font-size-sm`, `--font-size-lg`), 간격(`--gap-sm:8px`, `--gap-md:16px`, `--gap-lg:24px`), 전환(`--trans-default:all 0.3s ease-out`)을 추가한다. 단, 변수명은 시맨틱 금지 원칙 유지 — 역할이 아닌 스케일 기반 명명.

**기존 규칙과의 관계**: 기존 `:root` 변수 네이밍 패턴의 직접 확장. 시맨틱 이름 금지 원칙 유지.

**rule_engine.json 초안**:
```json
"root_vars_extended": {
  "typography": ["--font-size-base","--font-size-sm","--font-size-lg"],
  "spacing": ["--gap-sm","--gap-md","--gap-lg"],
  "transition": ["--trans-default"],
  "naming_rule": "scale_based_not_semantic",
  "forbid_semantic_names": true
}
```

---

## 4. 상태 클래스 네이밍

**제안 규칙**: 상태 클래스는 `is-` 접두사 단일 기준으로 통일. `is-active`, `is-open`, `is-disabled`, `is-error`, `is-hidden`. `has-` 접두사는 하위 요소 존재 표시에만 허용(`has-icon`). 기존 `section_on` 패턴은 레거시 예외로만 허용하고 신규 작성 금지. JS에서 토글 시 반드시 이 클래스를 사용.

**기존 규칙과의 관계**: 신규 추가. 기존 snake_case 네이밍 규칙의 예외 — 상태 클래스는 kebab-case(`is-active`) 허용.

**rule_engine.json 초안**:
```json
"state_classes": {
  "prefix_active": "is-",
  "prefix_has": "has-",
  "allowed": ["is-active","is-open","is-disabled","is-error","is-hidden"],
  "kebab_exception": true,
  "forbid_legacy_on_suffix_new": true
}
```

---

## 5. 반복 패턴 규칙 — 카드 리스트/그리드 대체

**제안 규칙**: 동일 폭 카드 N열 배치는 `flex-wrap:wrap` + 각 아이템에 `width:calc((100% - gap*(N-1)) / N)` 패턴으로 통일. `nth-child`를 이용한 끝 아이템 `margin` 제거보다 부모 `gap` 속성 우선 사용. 3열 예시: `.main_card_list{display:flex; flex-wrap:wrap; gap:24px;} .main_card_item{width:calc((100% - 48px) / 3);}`.

**기존 규칙과의 관계**: 기존 CSS Grid 금지 및 flexbox-only 규칙의 구체적 구현 패턴 추가. calc는 clamp 내부 외 사용 금지 원칙과 충돌하므로 flex 카드 레이아웃 한정 calc 허용 예외 명시 필요.

**rule_engine.json 초안**:
```json
"card_grid_pattern": {
  "method": "flex_wrap_width_calc",
  "gap_over_nth_child_margin": true,
  "calc_exception": "flex_card_width_only",
  "example": ".list{display:flex;flex-wrap:wrap;gap:24px;} .item{width:calc((100% - 48px)/3);}"
}
```

---

## 6. 텍스트 오버플로 — 말줄임 처리 패턴

**제안 규칙**: 단일 줄 말줄임은 `overflow:hidden; text-overflow:ellipsis; white-space:nowrap;` 세트를 항상 묶어서 한 줄 선언. 다중 줄 말줄임은 `-webkit-line-clamp` 패턴 사용: `overflow:hidden; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:N;`. 클래스명은 `_ellipsis` 접미사 사용 금지 — 부모 셀렉터에 직접 선언.

**기존 규칙과의 관계**: 신규 추가. 기존 유틸리티 클래스 금지 원칙 적용 — 별도 `ellipsis` 클래스 생성 금지.

**rule_engine.json 초안**:
```json
"text_ellipsis": {
  "single_line": "overflow:hidden; text-overflow:ellipsis; white-space:nowrap",
  "multi_line": "overflow:hidden; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:N",
  "forbid_utility_ellipsis_class": true,
  "apply_on_parent_selector": true
}
```

---

## 7. min-height vs height — 컨테이너 높이 처리

**제안 규칙**: 콘텐츠가 가변적인 컨테이너에는 `height` 고정 금지, `min-height` 사용. 디자인 고정 높이가 명확한 아이콘/버튼/배지류만 `height` 고정 허용. 전체 화면 섹션은 `min-height:100vh` 허용. `height:100%`는 부모에 명시적 height가 있을 때만 사용.

**기존 규칙과의 관계**: 신규 추가. 기존 100px 이상 clamp 허용 정책과 연계 — `min-height`도 100px 이상 시 clamp 적용 가능.

**rule_engine.json 초안**:
```json
"height_policy": {
  "content_container": "min-height preferred",
  "fixed_height_allowed": ["icon","button","badge","divider"],
  "full_screen": "min-height:100vh",
  "forbid_height_100_without_parent": true,
  "clamp_applies_to_min_height": true
}
```

---

## 종합 우선순위

| 순위 | 항목 | 이유 |
|------|------|------|
| 1 | z-index 레이어 변수 | 모달/헤더 충돌 빈도 높음 |
| 2 | 상태 클래스 네이밍 | JS 연동 패턴 일관성 |
| 3 | min-height vs height | 반응형 깨짐 원인 1위 |
| 4 | 텍스트 말줄임 패턴 | 반복 구현 비효율 |
| 5 | CSS 변수 체계 확장 | 유지보수 효율 |
| 6 | overflow 처리 | 가로 스크롤 버그 예방 |
| 7 | 카드 반복 패턴 | Grid 금지 대안 명확화 |

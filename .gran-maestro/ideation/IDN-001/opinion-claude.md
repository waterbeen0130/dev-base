# IDN-001 유지보수성/스타일 가이드 체계 분석 의견서

> 분석 대상: `common.md`, `claude.md`, `codex.md`, `landing.md`, `rule_engine.json`, `validation_schema.json`
> 분석 관점: 프롬프트 `claude-prompt.md`의 7개 제안 요청 영역

---

## 1. CSS 주석 컨벤션

**제안 규칙**: 섹션 구분 주석을 `/* ===== SECTION NAME ===== */` 패턴으로 통일하고, 설명형 주석(무엇을 하는지 풀어쓰는 주석)은 금지한다. 허용 주석은 섹션 구분, TODO, 브레이크포인트 경계 표시 3가지로 한정한다.

**적용 범위**: 공통 (basic/landing 모두)

**기대 효과**: 현재 규칙 체계에 주석 관련 규칙이 전혀 없다. `common.md`에 "코드 주석: 영어만"이 있으나 이는 프로그래밍 언어 주석이고 CSS 주석 패턴은 미정의 상태다. 한 줄 포맷 CSS 특성상 섹션 경계를 놓치기 쉬우므로, 통일된 구분 주석이 파일 탐색성을 크게 높인다. 불필요한 설명 주석 금지는 기존 "과도한 주석 추가 금지" 원칙과도 일관된다.

---

## 2. 파일 내 CSS 구조 순서

**제안 규칙**: CSS 파일 내부 구조를 다음 순서로 강제한다: `:root` 변수 → reset 스타일 → 공통 레이아웃(`.cont`, 애니메이션) → 섹션별 스타일(DOM 순서대로) → 미디어쿼리(큰 breakpoint부터). 미디어쿼리는 파일 하단에 breakpoint별로 1개 블록씩 모은다.

**적용 범위**: 공통. 단, landing은 reset이 CSS 파일 최상단에 인라인 포함(별도 파일 없음)이므로 이 순서가 자연스럽게 맞고, basic은 `reset.css`가 분리되어 있으므로 `common.css`에서 reset 단계를 건너뛴다.

**기대 효과**: 현재 `landing.md`에 ":root + 애니메이션은 최상단" 정도의 순서 힌트만 있고, 전체 구조 순서 규칙은 없다. 섹션별 스타일이 DOM 순서를 따르면 HTML과 CSS를 교차 참조할 때 위치 예측이 가능해진다. `rule_engine.json`의 `root_var_line_separated` 검증과도 연결되며, validation에 "구조 순서 검증" 항목을 추가할 근거가 된다.

---

## 3. 클래스명 반복 패턴

**제안 규칙**: 동일 역할 섹션이 페이지 내 반복될 때 접미사 숫자를 사용한다. 패턴은 `{page}_{role}_{N}` (예: `main_about_1`, `main_about_2`). 단, 역할이 다르면 숫자 대신 의미 접미사를 붙인다(예: `main_about_team`, `main_about_history`). 숫자는 1부터 시작하며, 단독 섹션이면 숫자를 생략한다.

**적용 범위**: 공통

**기대 효과**: 현재 `naming` 규칙에서 `sec_1` 같은 범용 이름은 금지하지만, 같은 역할이 실제로 반복될 때의 네이밍 전략은 정의되어 있지 않다. 이 공백 때문에 AI가 `main_about`, `main_about_2`처럼 비일관적 넘버링을 하거나, 반대로 역할이 다른데도 숫자만 붙이는 문제가 생긴다. 명시적 규칙이 있으면 검증 스키마에서도 패턴 매칭이 가능해진다.

---

## 4. 반응형 이미지 클래스

**제안 규칙**: PC/모바일 이미지 전환은 `.pc_only` / `.mb_only` 클래스를 표준으로 사용한다. CSS 구현은 `@media (max-width:768px){ .pc_only{display:none;} }` / `@media (min-width:769px){ .mb_only{display:none;} }` 패턴으로 통일한다. `<picture>` + `<source media>` 패턴은 사용하지 않는다. 이미지 래퍼(`.img_area`)에 두 이미지를 함께 넣고 클래스로 전환한다.

**적용 범위**: 공통. `common.md`에 `<br class="mb_only">` / `<br class="pc_only">`가 이미 정의되어 있으나, 이미지 전환에 대한 명시적 패턴은 `landing.md`의 주의사항("모바일 전용 이미지는 반드시 사용")에만 간접적으로 언급되어 있다.

**기대 효과**: `rule_engine.json`의 `br_class_responsive`에 `["mb_only", "pc_only"]`가 있지만 이미지에 대한 적용은 누락 상태다. 표준 패턴을 명시하면 `<picture>` 태그 사용(현재 금지 태그 목록에 없음)을 사전 차단하고, validation에서 `.pc_only` / `.mb_only` 이미지 쌍 존재 여부를 검증할 수 있다.

---

## 5. 공통 UI 컴포넌트 패턴

**제안 규칙**: 공통 버튼은 `{page}_btn` 또는 `{page}_{section}_btn` 패턴을 사용하고, 범용 `.btn` 클래스는 금지한다. 공통 폼 요소는 `{page}_input`, `{page}_select` 패턴. 모달은 `{page}_modal` + `{page}_modal_dim` 패턴. 각 컴포넌트의 기본 스타일(border-radius, padding, transition)은 섹션 셀렉터 하위에서 정의한다.

**적용 범위**: basic 중심. landing은 단일 페이지 특성상 컴포넌트 재사용 빈도가 낮으므로 선택 적용.

**기대 효과**: 현재 유틸리티 클래스 금지 규칙은 있지만, 그 대안으로 "컴포넌트를 어떻게 네이밍하고 구조화하는가"에 대한 가이드가 없다. `.btn` 같은 범용 클래스 없이 버튼을 어떻게 일관되게 만드는지 AI가 판단하기 어려운 구간이다. 이 규칙이 추가되면 `naming` 규칙의 `common_suffixes`에 `_btn`, `_input`, `_modal`을 추가하여 검증 연동이 가능하다.

---

## 6. CSS 초기화(reset) 범위

**제안 규칙**: reset에 반드시 포함할 항목을 명시한다: `*, *::before, *::after{box-sizing:border-box; margin:0; padding:0;}`, `body{font-family:inherit; line-height:1.4;}`, `img{display:block; max-width:100%;}`, `a{text-decoration:none; color:inherit;}`, `button{border:none; background:none; cursor:pointer;}`, `ul,ol{list-style:none;}`. 웹폰트 선언은 reset 영역이 아닌 `:root` 아래 별도 블록에 배치한다.

**적용 범위**: 공통. basic은 `reset.css` 파일, landing은 CSS 최상단 인라인.

**기대 효과**: `landing.md`에 "웹폰트 제외, 순수 reset만 포함"이라는 원칙이 있으나, 구체적으로 어떤 속성을 reset하는지 정의되어 있지 않다. 이로 인해 매번 reset 범위가 달라지고, `img{display:block}` 누락 같은 사소한 차이가 레이아웃 버그로 이어진다. 명시적 reset 목록은 `validation_schema.json`에 "reset 항목 존재 검증" 규칙을 추가할 수 있게 한다.

---

## 7. 미디어쿼리 중복 방지

**제안 규칙**: 같은 breakpoint의 `@media` 블록은 파일 내 1개만 허용한다. 예: `@media screen and (max-width:768px){...}`가 파일에 2번 이상 나타나면 위반. 모든 768px 대응 규칙은 하나의 블록에 모은다. breakpoint별 블록 순서는 큰 값부터(1400 → 1200 → 960 → 768).

**적용 범위**: 공통

**기대 효과**: 현재 `rule_engine.json`에 `media_query_format`(내부 포맷)은 있지만, 동일 breakpoint 중복 블록에 대한 규칙은 없다. AI가 섹션별로 작업할 때 같은 `768px` 미디어쿼리를 여러 번 선언하는 패턴이 빈번하다. 이 규칙은 `validation_schema.json`에 `"type": "no_duplicate_media_breakpoint"` 항목으로 바로 추가 가능하며, CSS 파일 크기 절감과 유지보수 편의성에 직접 기여한다.

---

## 종합 소견

현재 규칙 체계는 **"무엇을 하지 말 것"** (금지 규칙)은 촘촘하나, **"어떻게 할 것"** (표준 패턴)이 부족한 구간이 있다. 위 7개 항목 중 특히 **2번(CSS 구조 순서)**, **6번(reset 범위)**, **7번(미디어쿼리 중복 방지)** 는 즉시 적용 가능하고 `validation_schema.json`에 검증 규칙을 연동할 수 있어 우선순위가 높다. 나머지 항목은 실제 프로젝트에서 패턴을 1-2회 검증한 후 확정하는 것이 안전하다.

규칙 중복 문제(21개 항목 2-4개 파일 반복)는 이 7개 규칙을 추가하기 전에 먼저 해결하는 것이 바람직하다. override 메커니즘 없이 규칙을 늘리면 중복이 가속화되기 때문이다. `applies_to` 필드 기반의 단일 소스 구조로 전환한 후 위 규칙들을 추가하는 순서를 권장한다.

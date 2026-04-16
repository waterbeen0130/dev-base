# EXP-001 종합 리포트 — `rules/` 폴더 개선 방안

## 탐색 범위
- **codex**: `rules/*.md`, `rule_engine.json`, `validation_schema.json`, `rules/templates/publishing/*`, `tools/validate-semantic.py`, `tools/figma-extract.py`, `CLAUDE.md`, `rules/CLAUDE.md`, `templates/sub_list.html`, `sub_view.html`, `templates/css/reset.css` — **파일:라인 단위 감사**
- **gemini**: `rules/` 전체 + `tools/build-prompts.py`, `init-project.py`, `compare-css.py` — **아키텍처/파이프라인 흐름**

두 탐색자 모두 exit_code 0으로 정상 완료.

---

## 발견 사항 (양쪽이 일치하는 핵심 결론)

### 1. 검증 계약이 깨져 있다 (CRITICAL)
- 문서·설정은 `tools/validate.js --type/--mapping`을 호출하라고 지시하지만 **실제 파일은 존재하지 않음**. 실구현은 `tools/validate-semantic.py`뿐이다.
  - 근거: `common.md:541-561`, `rule_engine.json:238-240`, `rules/templates/publishing/config.json:135-137`, `ai-pipeline.md:67-71` ↔ `tools/validate-semantic.py:9-10,520-524`
- `figma-extract.py --name/--json-only`, `validate.js --mapping`도 문서에만 있고 실제 CLI에는 없다.
  - 근거: `common.md:558-561`, `CLAUDE.md:299-305` ↔ `tools/figma-extract.py:835-848`

### 2. 규칙이 3곳에 분산되어 있고 SSOT가 없다
- 동일 규칙이 (a) 자연어 `.md`, (b) 스키마 `.json`, (c) Python `validate-semantic.py`에 각각 따로 존재.
  - 예: "CSS Grid 금지" → `common.md` + `validation_schema.json:no_css_grid` + `validate-semantic.py:check_css_grid`
- 추가로 `tools/build-prompts.py`의 `PROFILE_RULES` 딕셔너리에 규칙이 **하드코딩**되어 있어, `.md`만 고치면 프롬프트엔 반영 안 됨 (gemini 발견)
- `validation_schema.json`에 65개 규칙이 선언돼 있으나 `validate-semantic.py`는 35개만 구현 → **선언만 있고 실행 없는 규칙 30개**

### 3. 직접 모순 (서로 반대로 말함)
- `max(calc(...))`: `common.md:77-80` 금지 ↔ `codex.md:49`, `css-enhancement.md:204-211` 권장
- 시맨틱 CSS 변수명: `common.md:89` 금지 ↔ `css-enhancement.md:352-386`, `rule_engine.json:341-347` 권장 (`--color_primary`)

### 4. 파일명/body class 정책 충돌
- "한글 파일명 + body class 없음" (`common.md:164-174,668-670`, `publishing-workflow-guide.md:129-132`)  
  ↔ "영문 파일명 + body class + prefix match" (`gemini.md:131-143`, `codex.md:36-43`, `rule_engine.json:178-190`, `validation_schema.json:60-61`)
- CLAUDE.md 본문은 후자(영문 + prefix)를 명시하므로 사실상 후자가 의도, 전자는 잔존 텍스트.

### 5. 템플릿 자체가 핵심 규칙을 위반
- `common.md`/`semantic-transform-rules.md`는 `ul>li`, `.cont`, 부모+태그 선택자 우선  
- `templates/sub_list.html:23,62-103`, `templates/sub_view.html:23,62-109`, `basic.md:90-109`는 `div.list_row > div.list_item`, `.inner`, 모든 요소에 클래스 부여
- 즉 템플릿이 안티패턴 그 자체 → 신규 프로젝트 init 시 위반 코드가 자동 배포됨

### 6. 에이전트별 분기는 **실제로 거의 같다**
- `gemini.md` ↔ `codex.md` 본문은 90% 중복. `common.md` 재해석 + 강조에 가까움.
- 퍼블리싱 config는 Codex를 끄도록 설정(`rules/templates/publishing/config.json:14-19`, `agents.json:38-42`)되어 있어 `codex.md`는 사실상 죽은 규칙.
- `rules/CLAUDE.md`에만 `compare-css.py` 단계가 추가돼 있으나 본 PM CLAUDE.md엔 없음 → 어느 쪽이 SoT인지 모름.

### 7. 두 개의 Figma 워크플로우가 공존
- 구(舊): `figma-extract.py` → `mapping.json` → `compare-css.py` 값 대조
- 신(新): Figma MCP 직접 호출 → AI 직접 해석
- CLAUDE.md는 신을 강조하지만 구 도구가 여전히 살아있고 일부 규칙에서 참조됨 → 어느 길로 가야 할지 모호

### 8. 검증 커버리지 공백
- `landing` 전용 규칙(`root_vars_required`, `gsap_animation_css_present`)은 schema에 선언되었으나 validator 미구현
- 반대로 validator는 landing에도 `reset.css` 링크와 base clamp를 강제 → landing.md(`landing.md:76,94-113`)와 충돌
- `figma_value_*` (mapping 기반 1:1 값 대조)는 schema에만 존재, 도구 지원 없음

---

## 구조적 관계

### 규칙 → 검증 매핑 (codex)
| 선언처 | 실행/검증 | 판정 |
|---|---|---|
| `common/basic/landing.md` | `validate-semantic.py` 일부 | 부분 매핑 |
| `validation_schema.json` (65개) | `validate-semantic.py` (35개) | 선언 과다 |
| `rule_engine.json`의 `validate.js --mapping --type` | **실구현 없음** | 깨진 계약 |
| `enhancement-flow.md`의 grep 규칙 | schema/tool 미반영 | 자연어 잔존 |

### 의존 흐름 (gemini)
```
Figma data ──> figma-extract.py / Figma MCP ──> 정규화 JSON ─┐
                                                              ├──> 프롬프트 생성 ──> Gemini 에이전트 ──> HTML/CSS ──> validate-semantic.py
rules/*.md ──> tools/build-prompts.py (PROFILE_RULES 하드코딩)─┘                                                              ↑
                                                                                                            validation_schema.json
```
- **규칙 주입은 build-prompts.py 한 지점에 종속** → 여기를 안 고치면 .md 변경이 무용지물
- `.md`와 `.json`/`.py` 사이에 공식 import 없음, 수동 동기화

---

## 미탐색 영역
- 실제 산출물(`output/*`)에 validator를 돌려 오탐/미탐 계측은 안 함
- `rules/templates/` 외 템플릿이 init 외에 어떻게 소비되는지 깊은 분석 미수행

---

## 개선 방안 (양쪽 제안 종합)

### 우선순위 1 — 깨진 계약부터 메우기 (즉시)
1. `validate.js` 참조를 전부 `validate-semantic.py`로 치환 (또는 `validate.js`를 실제로 만들거나 wrapper 추가). 영향 파일: `common.md`, `rule_engine.json`, `rules/templates/publishing/config.json`, `ai-pipeline.md`, `CLAUDE.md`.
2. 직접 모순 6개(`max(calc())`, 시맨틱 변수명, 파일명/body class)에 대해 **결정 내리고 한쪽으로 일원화**. CLAUDE.md 본문 의도를 SoT로 보면: 영문 파일명 + body class + prefix match, `max(calc())` 권장, `--color_primary` 시맨틱 변수 허용.
3. 템플릿(`templates/sub_list.html`, `sub_view.html`, `basic.md`의 골격) 다시 작성: `ul>li`, `.cont`, 부모+태그 선택자, 클래스 최소화. **init-project.py가 배포하는 코드가 규칙을 위반하면 안 됨**.

### 우선순위 2 — SSOT 확립 (1~2주)
4. 단일 규칙 정의 파일(예: `rules/rules.yaml` 또는 기존 `rule_engine.json` 확장)로 **자연어 + 스키마 + 검증 메타데이터 통합**:
   - 각 규칙: id, 자연어 설명, severity, 적용 프로필(basic/landing/공통), 검증 타입(regex / ast / 값 대조), 검증 파라미터, 예외 조건
5. `rules.yaml` → `common.md` / `basic.md` / `landing.md` / `validation_schema.json` 자동 생성기 (`build-rules.py`). `.md`는 사람이 읽는 산출물일 뿐, 직접 편집 금지.
6. `tools/build-prompts.py`의 `PROFILE_RULES` 하드코딩 제거 → `rules.yaml`에서 적용 프로필 필터링으로 동적 주입.

### 우선순위 3 — 검증기 데이터 기반화 (2~3주)
7. `validate-semantic.py`의 `check_*` 하드코딩 함수를 제거하고 `validation_schema.json`(또는 `rules.yaml`)을 동적 해석하는 **범용 검증 엔진**으로 리팩터링.
   - 검증 타입: `regex_must_match`, `regex_must_not_match`, `ast_selector_count`, `value_equals_mapping(figma)` 등을 enum화
   - 새 규칙 추가 = YAML 한 줄 추가 → Python 코드 수정 불필요
8. 누락 규칙(landing 전용, `figma_value_*` mapping 대조) 6~10개를 새 엔진에서 1차 구현.

### 우선순위 4 — 에이전트 분기 정리 (병행)
9. `codex.md`와 `gemini.md` 본문 차이를 diff로 내고, 실제 다른 부분(예: tool 호출 방식)만 남기고 공통 본문은 `common.md`에 흡수.
10. 퍼블리싱 config가 Codex를 끄는 현 상태와 일치시키고 `codex.md`는 "백엔드/풀스택 프로젝트 전용" 헤더를 명시.

### 우선순위 5 — Figma 워크플로우 일원화 (병행)
11. CLAUDE.md의 "정밀 값 대조 검증 (선택)" 섹션과 `compare-css.py`/`figma-extract.py --mapping` 경로를 **둘 중 하나로 결단**:
    - (A) 신 워크플로우만 남기고 `compare-css.py` deprecated 표기 + tools에서 격리
    - (B) 정밀 검증이 실제 가치 있다면 `validate-semantic.py`에 흡수해 단일 검증 진입점으로 통합

---

## 후속 탐색용 요약 (최대 500토큰)

`/mnt/d/dev-base/rules/`는 ① 자연어 .md ② JSON 스키마 ③ Python validator ④ build-prompts.py 하드코딩 4곳에 규칙이 분산되어 SSOT가 없다. 가장 시급한 문제는 **검증 계약 파괴**: 문서/설정이 `validate.js --type/--mapping`을 호출하지만 그 파일은 존재하지 않고 실구현은 `validate-semantic.py`뿐이다. `validation_schema.json`은 65개 규칙을 선언하나 validator는 35개만 구현. 추가로 `templates/sub_list.html`, `sub_view.html`이 `common.md`/`semantic-transform-rules.md`의 핵심 규칙(`ul>li`, `.cont`, 클래스 최소화)을 위반하며, `init-project.py`가 이 안티패턴을 신규 프로젝트에 자동 배포한다. 직접 모순 항목: (1) `max(calc())` 금지 vs 권장, (2) 시맨틱 변수명 금지 vs 권장, (3) 한글 파일명+no body class vs 영문+body class+prefix. `gemini.md`/`codex.md`는 90% 중복이며 퍼블리싱 config는 Codex를 끄는데 codex.md는 살아있다. 개선 방향: ① validate.js 참조를 실파일/래퍼로 통일 ② 모순 결단 후 일원화 ③ 템플릿 재작성 ④ rules.yaml SSOT + build-rules.py 생성기 ⑤ validate-semantic.py를 데이터 기반 범용 엔진으로 리팩터링 ⑥ codex.md/gemini.md 차이만 남기고 common.md 흡수 ⑦ compare-css.py 경로 단일화. 미탐색: 실제 output/*에 validator 돌려 오탐/미탐 측정 필요.

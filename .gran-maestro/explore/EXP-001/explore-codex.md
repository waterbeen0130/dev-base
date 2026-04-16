[MST skill=mst:explore step=2/5 return_to=null]
# explore-codex

## 탐색 범위
- read: 필수 `rules/*.md`, `rule_engine.json`, `validation_schema.json`, `rules/templates/publishing/*`, `tools/validate-semantic.py`, `tools/figma-extract.py`, `CLAUDE.md`, `rules/CLAUDE.md`
- read: `templates/sub_list.html`, `templates/sub_view.html`, `templates/css/reset.css`

## 발견 사항
- **검증 계약이 깨져 있다**: 문서·설정은 `validate.js --type/--mapping`을 요구하지만 실파일은 없고 실제 구현은 `validate-semantic.py`뿐이다. `common.md:541-561`, `rule_engine.json:238-240`, `rules/templates/publishing/config.json:135-137` ↔ `ai-pipeline.md:67-71`, `tools/validate-semantic.py:9-10,520-524`.
- **CLI 예시도 구현과 불일치**: `figma-extract.py --name/--json-only`, `validate.js --mapping`은 문서에만 있다. `common.md:558-561`, `CLAUDE.md:299-305` ↔ `tools/figma-extract.py:835-848`, `tools/validate-semantic.py:521-524`.
- **파일명/body class가 서로 충돌**: 공통/가이드는 “한글 파일명 + body class 없음”, 에이전트/엔진/스키마는 “영문 파일명 + body class + prefix match”를 요구한다. `common.md:164-174,668-670`, `publishing-workflow-guide.md:129-132` ↔ `gemini.md:131-143`, `codex.md:36-43`, `rule_engine.json:178-190,429`, `validation_schema.json:60-61`.
- **템플릿이 핵심 규칙을 어긴다**: 공통/시멘틱은 `ul>li`, `.cont`, 부모+태그 선택자 우선인데 basic/템플릿은 `div.list_row > div.list_item`, `.inner`, `body class`를 쓴다. `common.md:41-42,213-282,342-343`, `semantic-transform-rules.md:40-46,66-71,93-100` ↔ `basic.md:90-109`, `templates/sub_list.html:23,62-103`, `templates/sub_view.html:23,62-109`.
- **직접 모순이 남아 있다**: `max(calc())` 금지 vs 권장, 시맨틱 CSS 변수명 금지 vs `--color_primary` 권장. `common.md:77-80,89` ↔ `codex.md:49,74-75`, `css-enhancement.md:204-211,352-386`, `rule_engine.json:341-347,397-403`.
- **검증 커버리지가 부족하다**: schema 65개, validator 35개. landing 전용(`root_vars_required`, `gsap_animation_css_present`)·매핑값 대조(`figma_value_*`)는 빠졌고, validator는 landing에도 `reset.css` 링크와 base clamp를 강제한다. `validation_schema.json:42-67` ↔ `landing.md:76,94-113`, `tools/validate-semantic.py:199-230,471-515`. 또 `figma-extract.py` mapping은 CSS/패턴 없는 노드를 생략해 1:1 검증 재료가 부족하다. `rule_engine.json:55-82` ↔ `tools/figma-extract.py:704-781`.
- **에이전트별 문서는 과분기**: 퍼블리싱 config는 Codex를 끄는데 Codex/Gemini 규칙 본문은 대부분 중복이고, `rules/CLAUDE.md`만 `compare-css.py` 단계를 추가한다. `rules/templates/publishing/config.json:14-19`, `agents.json:38-42`, `rule_engine.json:255-260`, `rules/CLAUDE.md:233-282`.

## 구조적 관계
| 선언 | 실행/검증 | 판정 |
|---|---|---|
| `common/basic/landing` | `validate-semantic.py` 일부 구현 | 부분 매핑 |
| `validation_schema.json` 65 | `validate-semantic.py` 35 | 선언 과다 |
| `rule_engine.json`의 `validate.js`, `--mapping`, `--type` | 실구현 없음 | 깨진 계약 |
| `enhancement-flow.md`의 grep 규칙 | schema/tool 미반영 | 자연어 잔존 |

## 미탐색 영역
- 실제 산출물(`output/*`)에 validator를 돌려 오탐/미탐을 계측하진 않았다.

## 후속 탐색 제안
1. canonical source를 하나로 정하라: `common/basic/landing` vs `rule_engine/schema`.
2. `validate.js` 참조를 실제 도구명/CLI로 통일하고 landing/type/mapping 지원을 명시하라.
3. 파일명/body class와 `.cont`/`.inner`, `ul>li`/template 구조를 정렬하라.
4. `enhancement-flow`·`compare-css` 규칙을 schema로 끌어올려 선언형 검증으로 바꿔라.

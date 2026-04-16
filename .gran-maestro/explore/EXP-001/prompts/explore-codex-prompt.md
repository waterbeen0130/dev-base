# 코드베이스 탐색 요청

## 스킬 실행 마커 (MANDATORY)
- 모든 응답의 첫 줄 또는 각 Step 시작 줄에 `[MST skill=mst:explore step=2/5 return_to=null]` 출력

## 탐색 목표
`/mnt/d/dev-base/rules/` 폴더는 Figma에서 추출된 디자인 데이터를 HTML/CSS로 변환하기 위한 규칙을 선언해 둔 장소다.
이 폴더 전체를 읽고 **더 나은 방향으로 수정할 수 있는 방안**을 근거와 함께 제시하라.

핵심 질문:
1. 규칙 간 **중복/모순/누락**이 있는가? (예: common.md ↔ basic.md ↔ landing.md ↔ claude.md/gemini.md/codex.md)
2. 규칙이 **실행 가능한 검증**(rule_engine.json, /mnt/d/dev-base/tools/validate.js)과 얼마나 **1:1 매핑**되는가? 선언만 있고 검증이 없는 규칙, 검증만 있고 선언이 없는 규칙을 찾아라.
3. 에이전트별 규칙(claude/gemini/codex)이 불필요하게 분기되어 있는가, 아니면 공통으로 합쳐야 할 부분이 있는가?
4. templates/ 하위 샘플이 규칙과 실제로 일치하는가? (reset.css, sub_list.html, sub_view.html 등)
5. Figma → HTML/CSS 변환 단계에서 **선언적 규칙으로 자동화 가능한데 여전히 자연어 지시로만 남아있는 항목**이 있는가?

## 당신의 역할
당신은 **codex 탐색자**입니다. 담당 각도: **코드/규칙 파일 레벨 감사** — 각 `.md`/`.json`/`validate.js`를 실제로 읽고, 파일:라인 단위로 모순·중복·커버리지 공백을 짚어라.

## 조사 지침
1. 읽기 전용 탐색만 수행한다. 파일 수정/생성/삭제 금지.
2. 반드시 다음 파일들을 읽어라:
   - `/mnt/d/dev-base/rules/common.md`
   - `/mnt/d/dev-base/rules/basic.md`
   - `/mnt/d/dev-base/rules/landing.md`
   - `/mnt/d/dev-base/rules/claude.md`
   - `/mnt/d/dev-base/rules/gemini.md`
   - `/mnt/d/dev-base/rules/codex.md`
   - `/mnt/d/dev-base/rules/css-enhancement.md`
   - `/mnt/d/dev-base/rules/enhancement-flow.md`
   - `/mnt/d/dev-base/rules/semantic-transform-rules.md`
   - `/mnt/d/dev-base/rules/ai-pipeline.md`
   - `/mnt/d/dev-base/rules/publishing-workflow-guide.md`
   - `/mnt/d/dev-base/rules/rule_engine.json`
   - `/mnt/d/dev-base/rules/validation_schema.json`
   - `/mnt/d/dev-base/rules/templates/` 하위 (ls 후 샘플 1~2개 read)
3. 보조 참조(규칙과의 정합성 대조용):
   - `/mnt/d/dev-base/tools/validate.js`
   - `/mnt/d/dev-base/tools/figma-extract.py`
   - `/mnt/d/dev-base/CLAUDE.md` (규칙 파일과 충돌/중복 여부)
4. 규칙을 "있어야 할 것"과 "있는데 어긋나는 것"으로 구분해 제시하고, 각 지적마다 **파일:라인**을 표기하라.
5. 추측과 사실을 구분하라. "확인 필요"는 명시적으로 표기.

## 집중 영역
`rules/` 폴더 전체 + 해당 폴더를 실제로 소비하는 tools(validate.js, figma-extract.py)와 CLAUDE.md의 규칙 주입 경로.

## 출력 형식
응답을 `explore-codex.md`에 마크다운으로 작성하고 아래 섹션을 포함하라.
- **탐색 범위**: 실제 read한 파일 목록
- **발견 사항**: 중복/모순/누락/커버리지 공백을 `파일:라인` 표기로 나열
- **구조적 관계**: 규칙 선언 ↔ 검증(rule_engine.json / validate.js) 매핑 표
- **미탐색 영역**: 시간/증거 부족으로 확인 못한 부분
- **후속 탐색 제안**: 다음에 우선 확인할 경로/질문

글자 수 제한: 3000자 이내.

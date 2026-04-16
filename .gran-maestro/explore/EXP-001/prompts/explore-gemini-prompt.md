# 코드베이스 탐색 요청

## 스킬 실행 마커 (MANDATORY)
- 모든 응답의 첫 줄 또는 각 Step 시작 줄에 `[MST skill=mst:explore step=2/5 return_to=null]` 출력

## 탐색 목표
`/mnt/d/dev-base/rules/` 폴더는 Figma에서 추출된 디자인 데이터를 HTML/CSS로 변환하기 위한 규칙을 선언해 둔 장소다.
이 폴더 전체를 읽고 **더 나은 방향으로 수정할 수 있는 방안**을 아키텍처/흐름 관점에서 제시하라.

핵심 질문:
1. rules/ 내부 파일들의 **역할 분담과 우선순위**가 명확한가? (common vs basic vs landing vs 에이전트별 파일의 상속/오버라이드 관계)
2. Figma 추출 → 정규화 → HTML/CSS 생성 → 검증 → 고도화(css-enhancement) 파이프라인에서 rules/는 **어느 지점에서 주입**되고 어느 에이전트에 도달하는가? 빠진 주입 지점이 있는가?
3. 규칙이 자연어(.md) / 스키마(.json) / 코드(validate.js) 3곳에 분산되어 있는데 **Single Source of Truth**로 좁힐 여지가 있는가?
4. 에이전트별 규칙 파일(claude/gemini/codex)은 실제로 다르게 동작해야 할 부분만 분리돼 있는가, 아니면 그냥 복붙인가?
5. 이 구조를 **한 단계 더 자동화**하려면 (예: 규칙 → 검증 자동 생성, 템플릿 → 규칙 자동 추출) 어떤 리팩터링이 필요한가?

## 당신의 역할
당신은 **gemini 탐색자**입니다. 담당 각도: **아키텍처/파이프라인/흐름 관점** — 파일 간 관계, 의존 그래프, 데이터 흐름, 책임 분리를 본다.

## 조사 지침
1. 읽기 전용 탐색만 수행한다. 파일 수정/생성/삭제 금지.
2. 다음 파일들을 반드시 훑어라 (대용량 컨텍스트 활용):
   - `/mnt/d/dev-base/rules/` 전체 (common, basic, landing, claude, gemini, codex, css-enhancement, enhancement-flow, semantic-transform-rules, ai-pipeline, publishing-workflow-guide, rule_engine.json, validation_schema.json, templates/*)
   - `/mnt/d/dev-base/CLAUDE.md` (PM이 규칙을 어떻게 주입하는지)
   - `/mnt/d/dev-base/tools/validate.js`, `tools/figma-extract.py`, `tools/compare-css.py`, `tools/init-project.py`, `tools/build-prompts.py` (있다면)
3. 파일 간 참조 관계(다른 규칙 파일을 명시적으로 링크/참조하는 곳)를 그래프로 정리하라.
4. Figma → 정규화 → HTML/CSS → 검증 → enhancement 파이프라인 각 단계에서 **어떤 규칙이 어느 에이전트에 전달되는지** 흐름도로 기술하라.
5. "더 나은 방향"은 아래 4가지 축으로 제안:
   - 중복 제거 / SSOT
   - 자연어 규칙 → 실행 가능한 검증으로 승격
   - 에이전트별 분기 축소
   - 파이프라인 단계별 규칙 주입 자동화

## 집중 영역
`rules/` 내부 구조 + 이를 소비하는 파이프라인 전체.

## 출력 형식
응답을 `explore-gemini.md`에 마크다운으로 작성하고 아래 섹션을 포함하라.
- **탐색 범위**: 실제 읽은 파일과 관계
- **발견 사항**: 아키텍처/흐름 이슈 목록 (각 항목에 파일 근거)
- **구조적 관계**: 규칙 파일 의존 그래프 + 파이프라인 주입 지점 흐름
- **미탐색 영역**
- **후속 탐색 제안**: SSOT화/자동화 리팩터링 우선순위 TOP 3

글자 수 제한: 3000자 이내.

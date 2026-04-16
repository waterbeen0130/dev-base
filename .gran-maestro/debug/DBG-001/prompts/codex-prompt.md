# 버그 조사 요청 — Figma MCP → Code 파이프라인 구조 진단 (Codex)

## 스킬 실행 마커 (MANDATORY)
- 응답 첫 줄에 다음을 출력: `[MST skill=debug step=2/7 return_to=null]`

## 이슈
현재 프로젝트는 Figma MCP 응답을 해석하여 HTML/CSS 퍼블리싱 코드를 생성하는 파이프라인이다. 현재 순서는:

피그마 분석 → 레이아웃 → 컨텐츠 배열 체크 → 텍스트 추출 → CSS 작성 → 시맨틱 마크업 → CSS 규칙 변환 → PM 검수

### 증상
1. 많은 단계가 자동화되어 있지 않음 (수동 개입 다수)
2. 규칙이 너무 까다로워 AI가 지시/규칙을 아예 무시
3. 결과 품질이 형편없어 섹션당 최소 5~6회 수동 수정 필요
4. `rules/common.md`, `rules/gemini.md`, `CLAUDE.md`에 다량의 규칙 (CSS 한 줄 포맷, hex 전용, flex 전용, 폰트 5필드 완결성, clamp 규칙 등)
5. `tools/figma-section-spec.py → figma-validate.py → validate-semantic.py → post-impl-verify.py` 체인 존재

## 당신의 조사 역할
당신은 **Codex**입니다. 조사 각도: **코드/도구 체인 구조 진단**.

tools/ 의 Python 스크립트들과 rules/ 의 규칙 파일들을 소스 레벨에서 읽고, 구조적 결함과 커버리지 공백을 파악하세요. 개선안은 tool/rule 관점에서 제시합니다.

## 조사 지침

### A. 현재 구조 진단 (소스 레벨)
1. `tools/figma-section-spec.py`, `tools/figma-validate.py`, `tools/validate-semantic.py`, `tools/post-impl-verify.py`를 **실제로 Read**하고 각 도구의 입력/출력/검증 대상/놓치는 지점을 정리한다.
2. `rules/common.md`, `rules/gemini.md`, `rules/codex.md`, `rules/rules.yaml`, `rules/validation_schema.json`를 Read하여:
   - 규칙 개수와 카테고리 분포
   - 상호 충돌 가능성 (예: "flex 전용"과 특정 레이아웃 요구사항의 충돌)
   - 우선순위 명시 여부
   - 예외 처리/탈출구 존재 여부
3. `CLAUDE.md`의 "피그마 워크플로우 / 5단계 플로우 / 피그마 코드 생성 품질 규칙 / 포스트 추출 고도화" 섹션을 Read하여 PM 지시와 tool/rule 간 정합성을 확인한다.
4. 각 파이프라인 단계를 다음 관점으로 분석:
   - 자동화 여부 (자동/반자동/수동)
   - 실패 시 피드백 루프 존재 여부
   - 측정 가능한 합격 기준 유무
   - 실패 원인이 에이전트에게 구조화된 형태로 전달되는지
5. `figma-validate.py`의 9개 검증 카테고리와 `validate-semantic.py`의 규칙 커버리지를 교차 확인하여 **어떤 규칙이 자동 검증되지 않는지** (= 에이전트가 무시해도 탐지 불가한 규칙) 열거한다.
6. `.gran-maestro/discussion/DSC-002/` 가 있다면 Read하여 이전에 논의된 문제점과 현 상태의 차이를 요약.

### 에이전트가 규칙을 무시하는 근본 원인 가설
다음 가설을 **코드/규칙 구조 근거**로 검증:
- H1: 규칙 수가 과다해 컨텍스트 오버플로우
- H2: 규칙이 자연어 서술 위주이고 자동 검증 커버리지가 낮아 "무시해도 통과" 가능
- H3: 피드백 루프가 post-hoc이라 수정 비용이 높음 (생성 후 거부)
- H4: 규칙 우선순위/예외가 명시되지 않아 내부 충돌 시 에이전트가 자의적 선택
- H5: 브리프 주입 방식이 인라인 텍스트여서 토큰 경쟁에 밀림
- H6: Spec(figma-section-spec.md)와 구현 지시서가 분리되지 않아 에이전트가 raw Figma 응답을 다시 해석

각 가설에 대해 **실제 파일의 증거 라인**을 제시하고 채택/기각을 판단.

### B. 업계 사례 리서치 (간단히)
코드 관점으로 아는 범위에서, LLM 기반 코드 생성에서 "규칙 순응도"를 높이는 기법을 정리:
- constrained decoding / grammar-guided generation
- AST 기반 사후 검증 + auto-fix
- spec-first (JSON 스키마) + template rendering
- few-shot exemplar + negative example
- iterative refinement (validator → LLM repair loop)

### C. 개선안 (보완·추가·수정·삭제)
각 항목을 네 범주로 분류해서 **구체적 파일/도구 이름**과 함께 제시:

- **보완**: 현재 존재하지만 미흡 (예: figma-validate.py에 XX 카테고리 추가)
- **추가**: 없어서 도입해야 함 (예: auto-fix 루프 도구, 디자인 토큰 파이프라인)
- **수정**: 현재 방식이 잘못됨 (예: 인라인 규칙 주입 → 규칙 ID 기반 체크리스트)
- **삭제**: 오히려 해가 됨 (예: 중복 규칙, 충돌 규칙, 자동 검증 불가능한 모호 규칙)

우선순위는 **P0 (재작업 50% 감축 잠재력) / P1 / P2**로 표기.

## 집중 영역
`/mnt/d/dev-base/tools/`, `/mnt/d/dev-base/rules/`, `/mnt/d/dev-base/CLAUDE.md`, `/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/`

## 출력 형식
`/mnt/d/dev-base/.gran-maestro/debug/DBG-001/finding-codex.md` 에 마크다운으로 작성.

다음 섹션 포함:
- **Symptom**: 관찰된 현상 + 파일/라인 근거
- **Hypothesis**: H1~H6 가설과 우선순위
- **Experiment**: 가설 검증을 위해 읽은 파일과 확인한 라인
- **Result**: 가설 채택/기각, 근본 원인 결론, 수정 제안 (A/B/C)
- **Open Questions**: 미검증 항목과 후속 확인 계획

글자 수: 3000자 이내 엄수.

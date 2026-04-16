# 버그 조사 요청 — Figma MCP → Code 파이프라인 진단 (Gemini)

## 스킬 실행 마커 (MANDATORY)
- 응답 첫 줄에 다음을 출력: `[MST skill=debug step=2/7 return_to=null]`

## 이슈
현재 프로젝트는 Figma MCP 응답을 해석하여 HTML/CSS 퍼블리싱 코드를 생성하는 파이프라인이다. 현재 순서는:

피그마 분석 → 레이아웃 → 컨텐츠 배열 체크 → 텍스트 추출 → CSS 작성 → 시맨틱 마크업 → CSS 규칙 변환 → PM 검수

### 증상
1. 많은 단계가 수동
2. 규칙이 너무 까다로워 AI가 지시/규칙을 아예 무시
3. 섹션당 최소 5~6회 수동 수정 필요
4. rules/*, CLAUDE.md에 다량 규칙 (CSS 한 줄 포맷, hex 전용, flex 전용, clamp 규칙, 폰트 5필드 완결성 등)
5. `tools/figma-section-spec.py → figma-validate.py → validate-semantic.py → post-impl-verify.py` 체인 존재

## 당신의 조사 역할
당신은 **Gemini**입니다. 조사 각도: **업계 사례 리서치 + 광역 컨텍스트 진단**.

Gemini의 대용량 컨텍스트 강점을 살려, 여러 파일을 한 번에 읽고 전체 워크플로우 관점에서 구조적 결함을 진단하세요. 동시에 업계 사례를 폭넓게 조사하여 비교 분석합니다.

## 조사 지침

### A. 현재 구조 진단 (광역 관점)
1. 아래 파일들을 모두 Read하여 **전체 규칙 집합을 한 번에 이해**:
   - `/mnt/d/dev-base/CLAUDE.md`
   - `/mnt/d/dev-base/rules/common.md`
   - `/mnt/d/dev-base/rules/gemini.md`
   - `/mnt/d/dev-base/rules/codex.md`
   - `/mnt/d/dev-base/rules/rules.yaml`
   - `/mnt/d/dev-base/rules/validation_schema.json`
   - `/mnt/d/dev-base/tools/figma-section-spec.py`
   - `/mnt/d/dev-base/tools/figma-validate.py`
   - `/mnt/d/dev-base/tools/validate-semantic.py`
   - `/mnt/d/dev-base/tools/post-impl-verify.py`
   - `.gran-maestro/discussion/DSC-002/` 내부 파일 (있다면)
2. 파이프라인 단계별로 "인간 개입 필요도 %"를 정성 평가.
3. 규칙 전체 분류:
   - 자동 검증 가능한 규칙 / 불가능한 규칙
   - 서로 충돌 가능성이 있는 규칙 쌍
   - 우선순위 없이 병렬 나열된 규칙
4. 에이전트 규칙 무시의 근본 원인을 다음 관점에서 진단:
   - 인지 부하 (rule count, ambiguity)
   - 브리프 주입 방식의 효과성
   - Figma 원본과 spec 문서의 역할 분리 여부
   - 피드백 루프 타이밍 (생성 전 / 생성 중 / 생성 후)
   - 재dispatch 시 실패 원인이 에이전트에게 구조화 전달되는지

### B. 업계 사례 리서치 (핵심)
다음 사례를 **구체적 메커니즘 수준**까지 조사하고 현 파이프라인과 대조:

1. **Locofy** — AI 기반 Figma→React/Next.js/HTML. LCN(Large Design Model), 컴포넌트 인식, 디자인 토큰 추출 방식.
2. **Builder.io Visual Copilot** — Mitosis AST, Figma 플러그인 → 프레임워크 비종속 IR → 코드 변환. LLM 역할 경계.
3. **Anima** — Figma → 코드. 디자인 시스템/컴포넌트 매칭, 디자인 의도 보존.
4. **TeleportHQ** — 비주얼 에디터 기반 코드 생성, IR 방식.
5. **Figma Dev Mode MCP (공식)** — 2024~2025년 출시. Figma 팀이 제안하는 표준 노드 해석 방식과 code connect 기능.
6. **Penpot / UXPin Merge** — 컴포넌트 우선 접근.
7. **전문 퍼블리셔/에이전시 워크플로우** — 수동 기반일 때 디자인 토큰/컴포넌트 라이브러리/검수 체크리스트를 어떻게 운영하는가.

각 사례에서 다음을 추출:
- IR(중간 표현) 유무와 형태
- 디자인 토큰 파이프라인 존재 여부
- 컴포넌트/패턴 인식 메커니즘
- 수정 루프(editable vs regenerate)
- 휴먼 인 더 루프 지점

### LLM 규칙 순응도 향상 기법
다음 기법의 원리와 적용 가능성을 정리:
- **Spec-first + template rendering**: LLM이 JSON 스펙만 채우고 템플릿이 HTML/CSS 렌더
- **Constrained generation / grammar-guided decoding**
- **Few-shot with negative examples** (나쁜 예/좋은 예 쌍)
- **Iterative refinement loop** (validator → LLM repair)
- **AST post-processing / auto-fix**
- **Rule compilation** (자연어 규칙 → 기계 검증 가능한 DSL)
- **Deterministic codegen + LLM 보조**: LLM은 의미 결정만, 코드 생성은 결정론적

### C. 개선안 (보완·추가·수정·삭제)
각 항목을 네 범주로 분류해서 **구체적 제안**으로 제시:

- **보완**: 현재 존재 but 미흡
- **추가**: 없어서 도입 필요
- **수정**: 현재 방식 교체 필요
- **삭제**: 해가 되는 것 제거

우선순위 P0/P1/P2 표기. 각 개선안에 대해 **업계 사례의 어떤 기법을 차용하는지** 명시.

## 집중 영역
`/mnt/d/dev-base/` 전체 (특히 rules/, tools/, CLAUDE.md, .gran-maestro/discussion/DSC-002/)

## 출력 형식
`/mnt/d/dev-base/.gran-maestro/debug/DBG-001/finding-gemini.md` 에 마크다운으로 작성.

섹션:
- **Symptom**: 관찰된 현상 + 파일 근거
- **Hypothesis**: 규칙 무시의 근본 원인 가설
- **Experiment**: 읽은 파일과 업계 사례 조사 결과 요약
- **Result**: 최종 진단 + 개선안 A/B/C
- **Open Questions**: 추가 검증 필요 항목

글자 수: 3000자 이내 엄수.

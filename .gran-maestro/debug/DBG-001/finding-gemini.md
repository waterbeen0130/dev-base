# Figma MCP → Code 파이프라인 진단 (Gemini)

## Symptom (관찰된 현상 및 근거)
1. **과도한 규칙과 분산된 컨텍스트**: `rules.yaml`, `gemini.md`, `common.md`, `CLAUDE.md` 등 규칙이 너무 많고(수십 개) 구체적입니다(예: `border-radius: 2em`, `line-height` 정돈 비율, `margin` vs `gap` 로직 등). 
2. **높은 수동 개입률**: 자동 검증기(`validate-semantic.py`, 요청하신 파이프라인 진단 및 업계 사례 비교 분석 리포트를 작성하여 지정된 경로에 저장했습니다.

파일 경로: `/mnt/d/dev-base/.gran-maestro/debug/DBG-001/finding-gemini.md`

진단 결과 요약:
현재 파이프라인은 결정론적으로 매핑해야 할 레이아웃 구조와 CSS 수치 변환(80%)까지 확률 모델인 LLM의 자연어 이해력에 의존하고 있어 인지 부하가 발생합니다. 업계(Builder.io, Locofy 등) 트렌드처럼 Figma 노드를 IR(AST)로 기계적 변환하거나, 후처리(Auto-fix) 단계를 두어 LLM의 역할을 시맨틱 의미 부여에 집중시키고 엄격한 룰은 파이썬 스크립트 내 하드코딩으로 대체하는 구조적 개선을 제안했습니다. 

추가 검증이나 후속 작업이 필요하시다면 알려주시기 바랍니다.
� 남발 등)에 압도당합니다.
- **Feedback Loop의 한계**: 코드를 모두 짠 후의 Post-generation 검증이므로, LLM은 왜 틀렸는지 맥락을 잃습니다. 또한 재dispatch 시 "부분 수정(AST 단위 수정)"이 아닌 전체 재생성으로 진행되어 비효율적입니다.
- **Figma 변환의 성격**: Figma Node → CSS는 80%가 기계적이고 결정론적인 매핑(IR)이며, 20%만이 시맨틱(네이밍, 태그 선택)입니다. 이 80%마저 LLM의 추론에 맡기고 있습니다.

## Experiment (업계 사례 리서치 비교)
업계 도구들은 LLM에 "바닥부터 짜라"고 하지 않습니다.
1. **Builder.io / Mitosis**: Figma 노드를 프레임워크 비종속적인 **IR(AST, Abstract Syntax Tree)** 로 먼저 **기계적 변환(결정론적)** 합니다. LLM은 단지 이 IR을 보고 시맨틱한 의미(컴포넌트명, 변수명)만 다듬습니다. 엄격한 레이아웃/CSS 규칙은 AST 변환기 코드(Python/JS) 내부에 하드코딩됩니다.
2. **Locofy LCN**: 디자인 토큰을 사전에 추출해 전역 변수로 분리합니다. 
3. **Anima / Code Connect**: 기존에 정해진 디자인 시스템 컴포넌트에 매핑만 시킵니다.

**LLM 순응도 향상 기법 비교**:
- 현재 파이프라인은 자연어 지시(Prompt)에 너무 많이 의존합니다.
- 기계 검증 가능한 DSL/AST 단위의 후처리(Auto-fix)가 업계 트렌드입니다.

## Result (최종 진단 및 개선안)
현재 파이프라인은 **"LLM을 CSS 컴파일러로 오용"**하고 있습니다. LLM은 HTML 시맨틱 구조와 클래스 네이밍에 집중하게 하고, CSS 수치/레이아웃 변환은 Python이 통제해야 합니다.

### [P0] 수정: Deterministic Codegen (IR 기반 구조로 전환)
- `figma-section-spec.py`에서 단순히 Spec MD를 만드는 것을 넘어, **Base CSS(토큰/기본 레이아웃 뼈대)**를 기계적으로 생성해버립니다. (Builder.io 방식 차용)
- LLM은 이렇게 생성된 뼈대에 HTML 시맨틱 마크업(`div` → `nav`, `h2` 등)과 클래스명을 매핑하는 역할만 수행하도록 역할을 축소합니다.

### [P0] 추가: AST 기반 Auto-fix (Post-processing)
- `validate-semantic.py`에서 위반 사항을 찾았을 때, LLM에게 재dispatch 하지 말고 Python 스크립트가 정규식이나 AST 파서(Tinycss2 등)를 이용해 코드를 **직접 강제 수정(Auto-fix)** 합니다.
- 예: `border-radius: 999px` 발견 시 스크립트가 `2em`으로 직접 문자열 치환. 8자리 hex 발견 시 6자리나 rgba로 변환.

### [P1] 보완: Iterative Refinement 강화
- 불가피하게 LLM 재dispatch가 필요하다면, 전체 코드를 다시 쓰라고 하지 말고 `diff` 포맷이나 `patch` 파일 형태로 특정 위반 라인만 핀포인트로 고치도록 프롬프트를 보완해야 합니다. (Cursor/Codex Partial Edit 활용)

### [P2] 삭제: 불필요한 자연어 규칙 다이어트
- Auto-fix 로직이 도입되면, `gemini.md`나 `codex.md`에서 모델에 인지 부하를 주던 수많은 포맷팅 룰(CSS 한 줄 쓰기, 미디어쿼리 들여쓰기 금지 등)을 삭제합니다. 기계가 린팅/포맷팅 해주는 것은 LLM에게 가르칠 필요가 없습니다.

## Open Questions
- CSS AST/Formatter 도구(Python `cssutils` 또는 Node `stylelint/prettier`)를 파이프라인에 통합할 수 있는가?
- 기존 `figma-section-spec.py`를 어느 정도 수준의 AST/IR 컴파일러로 격상할 수 있는가? (레이아웃 Decision Tree를 파이썬 로직으로 완전 이관)EXIT_CODE:0

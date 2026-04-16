# Implementation Spec

- Request ID: REQ-005
- Task ID: 02
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: Python tooling / 코드 생성기] → 최종: codex-dev
- Assigned Team: codex-dev 단독
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T02
- Complexity: Standard

## §0 Context Manifest

- /mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/01/spec.md (T01 결과물)
- /mnt/d/dev-base/rules/rules.yaml (T01에서 생성 — 입력)
- /mnt/d/dev-base/rules/common.md (출력 대상 — 기존 패턴 유지)
- /mnt/d/dev-base/rules/basic.md (출력 대상)
- /mnt/d/dev-base/rules/landing.md (출력 대상)
- /mnt/d/dev-base/rules/validation_schema.json (출력 대상)
- /mnt/d/dev-base/tools/build-prompts.py (PROFILE_RULES 갱신 대상)
- /mnt/d/dev-base/tools/figma-extract.py (코드 스타일 참고)
- /mnt/d/dev-base/tools/validate-semantic.py (코드 스타일 참고)

## 1. 요약 (Summary)

T01에서 작성된 `rules/rules.yaml`을 단일 입력으로 받아 `common.md`/`basic.md`/`landing.md`/`validation_schema.json`/`tools/build-prompts.py`의 `PROFILE_RULES` 딕셔너리를 자동 생성하는 `tools/build-rules.py`를 작성한다.

## 2. 범위 (Scope)

- **포함**:
  - 새 파일 `tools/build-rules.py` (Python 3.10+, 외부 의존성 최소화 — `pyyaml` 1개만 허용)
  - CLI 인자: `--input rules/rules.yaml` (default), `--output-dir rules/` (default), `--check` (생성만 하고 diff 출력 — 작성 안 함), `--profile {basic|landing|all}` (선택적 필터)
  - 생성 산출물:
    1. `rules/common.md` — 모든 `applies_to: [common, basic, landing]` 룰을 카테고리별로 묶어 자연어로 출력. 상단에 `<!-- AUTO-GENERATED FROM rules/rules.yaml. DO NOT EDIT MANUALLY. -->` 마커.
    2. `rules/basic.md` — `basic` 프로필 추가 룰
    3. `rules/landing.md` — `landing` 프로필 추가 룰
    4. `rules/validation_schema.json` — 모든 룰을 기존 스키마 형식으로 변환
    5. `tools/build-prompts.py`의 `PROFILE_RULES` 딕셔너리 — Python AST로 안전하게 갱신 (또는 마커 사이 치환)
  - 카테고리 분류 메타: `rules.yaml`의 룰에 `category` 필드(예: `css.format`, `css.color`, `html.naming`, `accessibility`)를 추가하거나 ID prefix로 추론
  - `--check` 모드: 생성 결과와 현재 파일을 비교해 diff를 stdout에 출력. exit code 0(동일) 또는 1(다름).
  - 멱등성: 같은 yaml에서 두 번 실행해도 결과 동일 (정렬 안정성, 키 순서 고정)
- **제외**:
  - `validate-semantic.py` 코드 변경 (REQ-006 범위)
  - 새 룰 enum 추가
  - jinja2 등 외부 템플릿 엔진 (Python f-string 또는 string.Template로 충분)
- **시작점 힌트**:
  - `tools/figma-extract.py`의 argparse + main 패턴 참고
  - 출력 형식은 현재 `rules/common.md`의 헤딩/표 구조를 보존 (자동 생성이지만 사람이 읽어도 자연스럽게)

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable]
Given: T01 완료 후 `rules/rules.yaml` 존재
When: `python3 tools/build-rules.py --check` 실행
Then: 명령이 정상 실행되고 diff 출력 (exit 0 또는 1)
Test: `python3 /mnt/d/dev-base/tools/build-rules.py --check 2>&1 | head -50`

#### AC-002 [MUST] [automatable]
Given: 빌드 실행 후 산출물
When: `python3 -c "import json; json.load(open('rules/validation_schema.json'))"` 실행
Then: 파싱 성공, 기존 65개 이상 룰 포함
Test: 위 명령 + `python3 -c "import json; print(len(json.load(open('rules/validation_schema.json'))['rules']))"` ≥ 65

#### AC-003 [MUST] [automatable]
Given: 빌드 실행 후 `rules/common.md`
When: AUTO-GENERATED 마커 grep
Then: 첫 50줄 안에 `AUTO-GENERATED FROM rules/rules.yaml` 마커 존재
Test: `head -50 /mnt/d/dev-base/rules/common.md | grep -c "AUTO-GENERATED"` ≥ 1

#### AC-004 [MUST] [automatable]
Given: 빌드 두 번 연속 실행
When: 두 번째 실행 후 git diff
Then: 변경 0건 (멱등)
Test: `python3 tools/build-rules.py && git diff --stat rules/ tools/build-prompts.py | wc -l` = 0 (or only newline diff)

#### AC-005 [MUST] [automatable]
Given: `tools/build-prompts.py`의 `PROFILE_RULES`가 갱신됨
When: `python3 -c "import sys; sys.path.insert(0,'tools'); import build_prompts; print(type(build_prompts.PROFILE_RULES).__name__, len(build_prompts.PROFILE_RULES))"` (또는 동등한 ast 검증)
Then: dict이며 비어있지 않음, 기존 키(`basic`, `landing`)가 존재
Test: 위 명령 또는 `python3 -m py_compile tools/build_prompts.py` (syntax 검증)

## 3.5 Constraints

- 보안: N/A
- 성능: 빌드 1회 < 5초 (수십 KB yaml + 5개 출력 파일)
- 호환성: Python 3.10+, `pyyaml` 외 외부 의존성 금지
- 운영: 빌드 실패 시 기존 파일을 손상시키지 않도록 임시 파일에 쓰고 atomic rename

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: `tools/figma-extract.py`의 argparse 구조, 한국어 docstring, 영어 코드 주석
- **알아야 할 제약**: `tools/build-prompts.py`의 `PROFILE_RULES`는 다른 코드가 import해서 사용하므로 형태(dict[str, list[str]])를 유지해야 함
- **접근법 방향**: ① yaml 파싱 → ② 룰 분류 (common/basic/landing/figma/enhancement) → ③ 5개 출력 파일 각각 별도 함수로 생성 → ④ atomic write → ⑤ `--check`는 stdout diff만

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): ["01"]
- 후행 작업 (blocks): ["03"]

## 6. 에이전트 팀 구성 (Agent Team)

- 실행: codex-dev
- 사유: Python 코드 작성 + 파일 I/O + AST 조작은 codex-dev capabilities(code, refactor, test)에 정확히 부합

## 10. 가정 사항 (Assumptions)

- (가정 1) `tools/build-prompts.py`의 `PROFILE_RULES` 갱신은 marker 기반 치환(`# BEGIN AUTO-GEN PROFILE_RULES ... # END AUTO-GEN`)이 가장 안전. T02가 marker가 없으면 한 번 추가하고 이후 그 사이만 치환.
- (가정 2) `rules.yaml`에 `category` 필드가 없으면 ID prefix(`css_*`, `html_*`, `naming_*`)로 추론.
- (가정 3) 출력 .md의 표/예시는 yaml의 `examples` 필드에서 가져옴. 없으면 description만 출력.

# Implementation Spec

- Request ID: REQ-005
- Task ID: 01
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: 스키마 설계 + YAML 데이터 마이그레이션] → 최종: claude-dev
- Assigned Team: claude-dev 단독 (구조 설계 + 기존 규칙 전수 정리)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T01
- Complexity: Standard

## §0 Context Manifest

> 구현 시작 전 이 목록의 파일을 가장 먼저 Read하세요.

- /mnt/d/dev-base/.gran-maestro/explore/EXP-001/explore-report.md (P2 권장 근거)
- /mnt/d/dev-base/rules/common.md (CSS/HTML 공통 규칙 — 가장 큰 SoT)
- /mnt/d/dev-base/rules/basic.md (basic 프로필 규칙)
- /mnt/d/dev-base/rules/landing.md (landing 프로필 규칙)
- /mnt/d/dev-base/rules/validation_schema.json (65개 검증 룰 스키마)
- /mnt/d/dev-base/rules/rule_engine.json (CSS 변수, 색상 정책, 검증 도구 메타)
- /mnt/d/dev-base/tools/validate-semantic.py (실구현 — 35개 check_* 함수에서 패턴 추출)
- /mnt/d/dev-base/tools/build-prompts.py (`PROFILE_RULES` 하드코딩 위치)
- /mnt/d/dev-base/rules/css-enhancement.md
- /mnt/d/dev-base/rules/semantic-transform-rules.md

## 1. 요약 (Summary)

자연어 `.md` / JSON 스키마 / Python validator / `build-prompts.py` 4곳에 흩어져 있는 모든 규칙을 단일 `rules/rules.yaml` 파일로 통합한다. 이번 태스크는 **YAML 스키마 설계 + 기존 규칙 전수 마이그레이션**까지만 수행하며, 자동 생성기(T02)와 검증(T03)은 분리한다.

## 2. 범위 (Scope)

- **포함**:
  - 새 파일 `rules/rules.yaml` 신설
  - 스키마 설계: 각 규칙당 `id` / `description` / `severity` / `applies_to[]` / `validation` / `rationale` / `examples` (옵션) 필드
  - `validation` 서브 스키마: `type` (enum) + `target` (css/html) + `pattern` 또는 `selector` 등 type별 파라미터
  - 허용 `validation.type` enum 정의 (10~15개): `regex_must_not_match`, `regex_must_match`, `regex_should_match`, `ast_selector_count`, `value_equals_mapping`, `html_tag_required`, `forbidden_substring`, `required_substring`, `naming_pattern`, `numeric_range` 등
  - `applies_to` enum: `basic`, `landing`, `common`, `figma`, `enhancement`
  - 기존 규칙 마이그레이션:
    - `validate-semantic.py`의 35개 `check_*` 함수에서 패턴 추출
    - `validation_schema.json`의 65개 룰 항목 추출
    - `common.md` / `basic.md` / `landing.md` / `css-enhancement.md` / `semantic-transform-rules.md`의 자연어 규칙을 빠짐없이 룰 객체화
    - 중복 규칙은 단일 ID로 병합 (예: `no_css_grid`가 .py + .json 양쪽에 있으면 하나로)
  - `rules.yaml` 상단에 스키마 버전 + `<!-- AUTO-GENERATED... -->` 주석 가이드 추가 (T02가 사용)
- **제외**:
  - `build-rules.py` 작성 (T02 범위)
  - 기존 `.md` / `.json` 파일을 자동 생성물로 교체 (T02 범위)
  - `validate-semantic.py` 코드 변경 (REQ-006 범위)
  - 새 검증 enum 추가 (현재 패턴을 표현할 수 있는 최소 enum만)
- **시작점 힌트**:
  - `rules/validation_schema.json` 전체 read → 65개 항목을 표 형태로 정리
  - `tools/validate-semantic.py`의 `check_*` 함수 시그니처 grep → 35개 매핑
  - 두 목록 합집합/교집합 계산 → 최종 룰 ID 목록 확정

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable]
Given: `rules/rules.yaml` 신규 작성됨
When: `python3 -c "import yaml; yaml.safe_load(open('rules/rules.yaml'))"` 실행
Then: 파싱 에러 0건
Test: 위 명령 (exit 0)

#### AC-002 [MUST] [automatable]
Given: `rules.yaml` 작성 완료
When: 룰 객체 개수 카운트
Then: 최소 65개 이상 (현행 `validation_schema.json` 룰 수와 동일하거나 더 많음)
Test: `python3 -c "import yaml; d=yaml.safe_load(open('rules/rules.yaml')); print(len(d['rules']))"` ≥ 65

#### AC-003 [MUST] [automatable]
Given: `rules.yaml` 룰 객체
When: 각 룰의 필수 필드 검증 (`id`, `description`, `severity`, `applies_to`, `validation`)
Then: 모든 룰이 5개 필수 필드를 가짐, `severity`는 `error|warning|info` 중 하나, `validation.type`은 enum 목록 중 하나
Test: 검증 스크립트 작성 (`python3 -c "..."` 인라인 또는 spec §4 코드)

#### AC-004 [MUST] [manual]
Given: 마이그레이션 완료
When: 기존 `validation_schema.json`의 65개 룰 ID와 `rules.yaml`의 룰 ID를 1:1 대조
Then: 누락 0건 (이름이 달라진 경우 매핑 표를 spec §11에 첨부)
Test: 수동 — 대조 표 첨부

## 3.5 Constraints

- 보안: N/A
- 성능: N/A
- 호환성: 기존 `validation_schema.json`, `.md`, `validate-semantic.py`는 본 태스크에서 변경하지 않음 (T02에서 처리)
- 운영: N/A

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: YAML 들여쓰기 2 spaces, 키 snake_case, 문자열은 quote 최소화 (특수문자 포함 시만)
- **알아야 할 제약**: 한국어 description은 그대로 보존 (사람용 자연어). enum 값과 ID는 영문 snake_case.
- **접근법 방향**: ① validation_schema.json 65개 + check_* 35개 합집합 산출 → ② 합집합에 .md 자연어 보충 → ③ rationale은 옵션이지만 가능한 채움 → ④ 검증 스크립트로 AC-001~003 자체 검증

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): ["02", "03"]

## 6. 에이전트 팀 구성 (Agent Team)

- 실행: claude-dev
- 사유: 다중 .md/.json/.py 파일을 동시에 read/대조하며 YAML 스키마를 설계하는 작업으로, 큰 컨텍스트 + 정밀 매핑이 필요. 외주 worktree보다 PM 직접 위임이 효율적.

## 10. 가정 사항 (Assumptions)

- (가정 1) YAML이 JSON Schema보다 사람이 읽기 쉽고 description 멀티라인 기록이 자연스러우므로 SSOT 포맷으로 채택. JSON Schema는 T02가 yaml에서 자동 생성.
- (가정 2) 검증 enum 10~15개로 현재 65개 룰을 모두 표현 가능하다. 표현 불가능한 1~2개 룰은 `type: custom`으로 표시하고 T02/REQ-006에서 핸들러를 추가.
- (가정 3) 마이그레이션 중 발견되는 죽은 룰(선언만 있고 의미 없는 항목)은 yaml에 포함하되 `severity: deprecated`로 표시.

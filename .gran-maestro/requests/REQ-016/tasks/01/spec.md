# REQ-016 / T01 — figma-section-spec.py 정확성 재검증 + 필요 시 근본 수정 + fixture 회귀 테스트

- **Assigned Agent**: [config: codex-dev] → codex-dev (Python tool 수정, TDD 가능)
- **Plan**: PLN-006
- **Cynefin**: Complicated (가설 검증 후 분기)

## §0 Context Manifest

> 이 목록은 시작점 힌트입니다. 완전하지 않을 수 있으며 에이전트는 자율적으로 주변 코드를 탐색해야 합니다.

- `tools/figma-section-spec.py` (주 수정 대상)
- `tools/figma-validate.py` (검증 기준 — 입력 spec 포맷 이해)
- `rules/common.md` (CSS/HTML 변환 규칙 — spec 필드 소비자 관점)
- `/mnt/d/위링/2026-04-15 목포플레이파크/extracted/A_Main_spec.md` (현재 산출물 — 비교 대상)
- `/mnt/d/위링/2026-04-15 목포플레이파크/extracted/A_Main_spec.json` (정규화 원본)

## §1 요약

`tools/figma-section-spec.py`가 생성한 `A_Main_spec.json`이 Figma 원본과 정말 일치하는지 raw API 응답 기반으로 재검증한다. 불일치가 발견되면 근본 원인을 파악해 수정하고, 이후 회귀를 방지할 fixture 기반 테스트를 추가한다.

**PM 주의사항 (중요)**: PLN-006 배경 설명에 "`characters` / `character_segments` 불일치"라는 초기 진단이 기록되어 있으나, spec.md 테이블의 `name` 컬럼(Figma 레이어 마스터명)과 `characters` 컬럼(실제 인스턴스 렌더링 텍스트)을 혼동했을 가능성이 있다. **첫 번째 작업은 이 초기 진단을 재검증하는 것**이며, 진단이 틀린 경우 실제 불일치 지점을 새로 찾아야 한다.

## §2 범위

### 포함
- Figma REST API `/v1/files/:key/nodes?ids=134:6708` 응답을 원본 JSON으로 취득해 `tests/fixtures/figma_mokpo_a_main.json`으로 저장.
- 저장된 fixture를 입력으로 `figma-section-spec.py`를 실행한 결과 `A_Main_spec.json`을 Figma raw JSON과 **필드 단위로 교차 검증**.
- 불일치 발견 시 원인 분석 → 최소 변경으로 수정.
- fixture 기반 회귀 테스트 스크립트 또는 pytest 추가 (`tests/test_figma_section_spec.py`).
- 수정 후 목포 `A_Main_spec.json`과 `extracted/A_Main_spec.md`를 재생성해 갱신.

### 제외
- `figma-validate.py` / `validate-semantic.py` / `post-impl-verify.py` 본체 로직 수정 (PLN-006 제약 사항).
- MCP 호출 경로 리팩터링.
- 섹션 자동 분할 heuristic (PLN-006 Could 범위, 이 REQ에서 제외).
- 에이스디펜스/목포의 HTML 재작성 (REQ-017/018에서 처리).

## §3 수락 조건

### AC-001 [automatable] [tdd-required] — Figma raw API fixture 확보

- **Given**: `FIGMA_TOKEN` 환경 변수와 목포 file-key, node-id `134:6708`이 주어진다.
- **When**: 에이전트가 `tools/figma-section-spec.py`의 `api_get_json` 경로와 동일한 URL로 raw JSON을 받아 `tests/fixtures/figma_mokpo_a_main.json`에 저장한다.
- **Then**: 파일 크기 ≥ 50KB, 최상위 `nodes["134:6708"].document.id == "134:6708"`, 하위에 `children` 배열이 존재한다.
- **Test**: `python3 -c "import json; d=json.load(open('tests/fixtures/figma_mokpo_a_main.json'))['nodes']['134:6708']['document']; assert d['id']=='134:6708' and isinstance(d.get('children'), list); print('OK')"` → exit 0.

### AC-002 [automatable] [tdd-required] — 초기 진단(characters/segments 불일치) 재검증

- **Given**: fixture 기반으로 재실행한 `A_Main_spec.json`이 존재한다.
- **When**: 에이전트가 모든 `text_nodes[]` 항목에 대해 `characters == "".join(seg["text"] for seg in character_segments)` 를 검증한다.
- **Then**: 불일치 건수가 0건이거나, 0건이 아닌 경우 원인(어떤 필드가 어떤 이유로 어긋났는지)을 `discussion/root-cause.md`에 기록한다. 0건인 경우에도 "초기 진단 정정"으로 `root-cause.md`에 명시한다.
- **Test**: fixture 기반 재실행 결과에 대해 위 불변식 검증 스크립트를 돌려 결과(pass/fail + count)를 stdout에 출력.

### AC-003 [automatable] [tdd-required] [regression-test] — Figma raw ↔ spec.json 필드 교차 검증

- **Given**: fixture JSON의 모든 TEXT 노드 목록 `L_raw`, 재생성된 spec.json의 `text_nodes` `L_spec`.
- **When**: 에이전트가 두 목록을 `id`로 매칭하고 각 필드(`characters`, `style.fontFamily`, `style.fontSize`, `style.fontWeight`, `style.lineHeightPx`, `style.letterSpacing`, `fills[0].color`, `absoluteBoundingBox`)를 raw와 spec이 일치하는지 확인한다.
- **Then**: 모든 매칭 노드에서 위 필드가 완전히 일치한다. 예외가 필요한 필드(예: 정수 반올림)가 있으면 허용 오차를 명시적으로 `tolerances.md`에 기록한다.
- **Test**: `python3 tests/test_figma_section_spec.py` 실행 시 exit 0, "RAW↔SPEC match: N/N OK" 출력.

### AC-004 [automatable] [tdd-required] — Instance 노드 텍스트 처리 확인

- **Given**: fixture JSON에 타입 `INSTANCE` 노드가 1개 이상 존재하고, 그 자식 중 TEXT 노드의 `characters`가 마스터 컴포넌트와 다른 override 값을 가진다.
- **When**: spec.json의 해당 TEXT 노드 id를 raw JSON에서 찾아 `characters`가 render된 override 값인지 확인한다.
- **Then**: 최소 1개의 instance-child TEXT 노드가 master 기본값이 아닌 instance의 override 텍스트로 기록되어 있다. 불일치 시 `figma-section-spec.py`의 관련 경로(`walk_and_extract` / `normalize_text_node`) 수정.
- **Test**: 동일 테스트 스크립트 내 assertion으로 검증.

### AC-005 [automatable] — fixture 회귀 테스트 추가

- **Given**: AC-001~004의 검증 로직이 확립되었다.
- **When**: 에이전트가 `tests/test_figma_section_spec.py`(또는 이에 준하는 실행 가능한 스크립트)를 추가하고, `tests/fixtures/figma_mokpo_a_main.json`을 golden input으로 사용한다.
- **Then**: 스크립트는 (a) fixture를 로드해 `walk_and_extract` 호출, (b) AC-002~004의 검증을 실행, (c) 모두 통과 시 exit 0, 실패 시 exit 1과 위반 목록 출력.
- **Test**: `python3 tests/test_figma_section_spec.py` → exit 0.

### AC-006 [automatable] [impact-check] — 기존 PLN-003~005 산출물 하위 호환

- **Given**: `dev-base/extracted/` 에 기존 PLN-003~005 에서 생성한 spec.json이 있거나, 없다면 이전 포맷을 재현한 최소 샘플을 테스트에 포함.
- **When**: 수정된 `figma-section-spec.py`를 기존 fixture(또는 기존 포맷 샘플)에 돌린다.
- **Then**: 출력 필드 집합이 기존 스키마의 슈퍼셋이어야 하며, 기존 필드명/타입/값이 변경되지 않는다 (새 필드는 optional 로만 추가 가능).
- **Test**: `tests/test_figma_section_spec.py` 의 `test_backward_compatible_schema` 서브 테스트 또는 별도 `test_schema_compat.py` 로 검증, exit 0.

### AC-007 [automatable] — 목포 산출물 재생성

- **Given**: 도구 수정 완료.
- **When**: 에이전트가 `FIGMA_TOKEN`을 사용해 `python3 tools/figma-section-spec.py --file-key <KEY> --node-id 134:6708 --output "/mnt/d/위링/2026-04-15 목포플레이파크/extracted/"` 를 실행한다.
- **Then**: 새 `A_Main_spec.json` / `A_Main_spec.md`가 생성되고, AC-002~004 불변식을 다시 충족한다.
- **Test**: 재생성 후 `python3 tests/test_figma_section_spec.py --spec "/mnt/d/위링/2026-04-15 목포플레이파크/extracted/A_Main_spec.json"` → exit 0.

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-1 (characters/segments 일치) | MUST / TIER-A | AC-002, AC-003 | covered |
| PAC-2 (instance override 기록) | MUST / TIER-A | AC-004 | covered |
| PAC-3 (fixture 회귀 검증 추가) | MUST / TIER-A | AC-005 | covered |
| PAC-8 (기존 PLN-003~005 회귀) | SHOULD / IMPACT / TIER-B | AC-006 | covered |

## §3.5 Constraints

- Python 표준 라이브러리만 사용 (추가 의존성 금지). 테스트도 `unittest` 또는 스크립트 직접 실행 형태 허용.
- `figma-section-spec.py`의 공개 함수 시그니처 변경 금지 (`walk_and_extract(root)` 유지).
- 출력 spec 스키마는 슈퍼셋만 허용, 필드 제거/이름 변경 금지.
- 네트워크 호출이 필요한 AC-001/AC-007은 `FIGMA_TOKEN` 이 없으면 graceful skip + 명시적 에러 로그.

## §4 가정 사항

- 목포 file-key 와 node-id(`134:6708`)는 사용자에게 확인 요청 필요. 현재 spec.md의 `134:6708`을 신뢰하고 진행하되, 실행 시점에 file-key를 사용자로부터 수신.
- 초기 진단이 컬럼 혼동에서 비롯된 경우, REQ-A는 "회귀 테스트 추가 + 초기 진단 정정 기록"만 수행하고 실제 코드 수정은 발생하지 않을 수 있음.

## §5 선행 작업 / 후행 작업

- blockedBy: 없음
- blocks: REQ-017, REQ-018

## §6 테스트 전략

- [build-check] 미적용 (Python 스크립트, 빌드 없음)
- [unit-test] `tests/test_figma_section_spec.py` — fixture 로드 + AC-002/003/004/006 검증
- [regression-test] AC-006 서브 테스트
- TDD 필수: AC-002~004 각각 실패하는 테스트를 먼저 작성 후 통과시킴.

## §7 의존성 테이블

| 태스크 | blockedBy | blocks |
|---|---|---|
| REQ-016/T01 | (없음) | REQ-017/T01, REQ-018/T01 |

## §8 Assigned Agent 근거

- config `workflow.default_agent = codex-dev` → 기본값 유지
- 작업 성격: Python tool 수정 + 단위 테스트 (TDD), 퍼블리싱 아님 → codex-dev 유지 (override 조건 없음)

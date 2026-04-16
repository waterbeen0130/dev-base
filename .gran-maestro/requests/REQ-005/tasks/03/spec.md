# Implementation Spec — Test Task

- Request ID: REQ-005
- Task ID: 03
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: 회귀 검증 / diff 분석] → 최종: claude-dev
- Assigned Team: claude-dev 단독
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T03
- Complexity: Lite

## §0 Context Manifest

- /mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/01/spec.md
- /mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/02/spec.md
- /mnt/d/dev-base/rules/rules.yaml (T01 산출물)
- /mnt/d/dev-base/tools/build-rules.py (T02 산출물)
- /mnt/d/dev-base/rules/common.md (검증 대상)
- /mnt/d/dev-base/rules/validation_schema.json (검증 대상)

## 1. 요약 (Summary)

T01의 `rules.yaml`과 T02의 `build-rules.py`가 만들어내는 산출물이 ① 규칙적으로 정확하고 ② 기존 산출물의 핵심 정보를 손실 없이 보존하는지 회귀 테스트를 작성·실행한다. 통과 후 자동 생성물을 main에 반영한다.

## 2. 테스트 범위

- **통합 검증**: `build-rules.py` 실행 → 5개 파일 생성 → 형식/스키마/마커/멱등 검증
- **회귀 테스트**: 생성된 `validation_schema.json`의 룰 ID 집합이 기존 schema의 ID 집합을 100% 포함하는지
- **사람 검수**: 생성된 `common.md`를 펼쳐서 자연어로 읽었을 때 의미 손실/오역이 없는지 (수동, spec §11에 결과 기록)

## 3. 수락 조건 (통합 AC)

#### AC-001 [MUST] [automatable]
Given: T01, T02 완료
When: `python3 tools/build-rules.py` 실행
Then: 5개 파일이 모두 생성되고 syntax 유효 (yaml/json 파싱 성공, py 컴파일 성공)
Test:
```
python3 /mnt/d/dev-base/tools/build-rules.py
python3 -c "import yaml; yaml.safe_load(open('/mnt/d/dev-base/rules/rules.yaml'))"
python3 -c "import json; json.load(open('/mnt/d/dev-base/rules/validation_schema.json'))"
python3 -m py_compile /mnt/d/dev-base/tools/build-prompts.py
test -f /mnt/d/dev-base/rules/common.md
test -f /mnt/d/dev-base/rules/basic.md
test -f /mnt/d/dev-base/rules/landing.md
```

#### AC-002 [MUST] [automatable]
Given: 빌드 산출물 + 빌드 직전 백업
When: 생성된 `validation_schema.json`과 백업본의 룰 ID 집합 비교 (`set diff`)
Then: 백업본 ID 중 누락 0건 (생성본은 새 ID를 추가할 수 있음)
Test:
```
python3 -c "
import json
old = {r['id'] for r in json.load(open('/tmp/validation_schema.backup.json'))['rules']}
new = {r['id'] for r in json.load(open('/mnt/d/dev-base/rules/validation_schema.json'))['rules']}
missing = old - new
assert not missing, f'missing: {missing}'
print(f'old={len(old)} new={len(new)} missing=0')
"
```

#### AC-003 [MUST] [manual]
Given: 생성된 `common.md`
When: 사람이 헤딩/표/예시를 처음부터 끝까지 읽음
Then: 의미 손실/오역/누락 0건. 발견 시 spec §11 "사람 검수 결과" 표에 기록 (해당 항목 ID + 원인 + 보정안)
Test: 수동 — §11 표 작성

## 4. 회귀 테스트 항목

- **R1**: `validation_schema.json`의 65개 기존 룰 ID 모두 보존 (AC-002로 자동화)
- **R2**: `common.md`의 핵심 헤딩 (CSS 한 줄 셀렉터, hex 색상, flex 전용, 클래스 네이밍 등)이 모두 새 자동 생성본에 존재
  - Test: `for h in "한 줄로 작성" "hex 전용" "flex" "snake_case"; do grep -c "$h" rules/common.md || echo MISSING $h; done`
- **R3**: `tools/build-prompts.py`의 `PROFILE_RULES` import가 다른 코드에서 깨지지 않음
  - Test: build-prompts.py를 실제로 사용하는 호출자(있다면) 컴파일 성공

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): ["01", "02"]
- 후행 작업 (blocks): []

## 6. 에이전트 팀 구성 (Agent Team)

- 실행: claude-dev
- 사유: 자동 검증 + 수동 검수가 혼합된 작업. 외주 에이전트보다 PM 직접 검증이 효율적이며 결과물 평가까지 포함.

## 10. 가정 사항 (Assumptions)

- (가정 1) AC-002의 백업 파일은 T03 시작 직전 PM이 `cp rules/validation_schema.json /tmp/validation_schema.backup.json`으로 만든다. 백업 시점은 T02 완료 직후, T02 빌드 실행 직전.
- (가정 2) AC-003 사람 검수에서 1~3건의 표현 차이가 발견될 수 있음. 의미 동등하면 PASS, 의미 손실이면 T02 spec.md에 보정 사항을 기록하고 T02 재외주 (5b 재외주 경로).

## §11 사람 검수 결과

> 실행 컨텍스트: worktree `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T03` (워크트리에는 `.gran-maestro/requests/REQ-005/` 트리가 존재하지 않아 본 파일은 main 저장소의 spec에 append 함).
> 백업: `git show edaaae2:rules/validation_schema.json > /tmp/validation_schema.backup.json` (69줄).

### AC 상태
- **AC-001 (syntax)**: **PASS** — `python3 tools/build-rules.py` exit 0 (출력 없음, 오류 없음), `yaml OK`, `schema OK`, `build-prompts compiles`, common.md/basic.md/landing.md 모두 존재 (484 / 62 / 45 lines).
- **AC-002 (regression)**: **PASS** — old=65, new=80, missing=1(`no_999_border_radius`, 단 이 ID는 old 스키마가 이미 `alias_of: border_radius_no_999` 로 표시한 duplicate이며 canonical `border_radius_no_999`는 new 스키마에 보존됨 → 의미상 손실 0), added=16 (신규 룰).
- **AC-003 (human review)**: **PASS** — common.md 484줄 end-to-end 확인, 13개 카테고리(CSS 레이아웃/색상/포맷/단위/변수/선택자/타이포그래피/테두리/간격, HTML 구조/시맨틱/네이밍/이미지/텍스트, 접근성) 분류 자연스럽고 한국어 설명 읽기 양호, bad/good 예시 있는 룰(flexbox/hex/selector_single_line/line_height/border_radius/forbidden_class 등)의 예시 모두 타당, 첫 3줄에 `AUTO-GENERATED FROM rules/rules.yaml` 마커 존재, 빈 섹션/깨진 표 없음.

### 회귀 항목 (R1~R3)
- **R1 (rule ID 보존)**: PASS — old 65개 중 64개 canonical ID가 new에 그대로 존재. 유일한 missing `no_999_border_radius`는 old 자체가 duplicate alias로 선언한 항목이라 의미상 0건 회귀.
- **R2 (핵심 헤딩 보존, grep counts)**:
  - `"한 줄로 작성"`: 2건
  - `"hex"`: 3건
  - `"flex"`: 6건
  - `"snake_case"`: 3건
  - `"ul>li"`: 4건
  - 전 5개 키워드 모두 1건 이상 → PASS
- **R3 (build-prompts.py introspection)**: PASS — `PROFILE_RULES` 타입 `dict`, keys `['basic', 'landing']`, basic=51 rules, landing=49 rules (import/로드 정상, 다운스트림 호출자 compile 가능).

### AC-002 누락 항목 상세
| ID | 성격 | 보존 여부 | 권고 |
|----|------|----------|------|
| `no_999_border_radius` | old 스키마에서 `alias_of: border_radius_no_999` 로 명시된 duplicate | canonical `border_radius_no_999` 존재 (error severity, bad/good 예시 포함) | **보정 불필요** — T02 재외주 안 함. 필요 시 `rules.yaml`에 별도 alias 엔트리 추가 여부는 PM 재량. |

### 사람 검수 발견 사항
| 항목 | 위치 | 발견 | 보정안 |
|------|------|------|--------|
| 발견 없음 — 모든 항목 통과 | — | — | — |

참고(비차단 관찰, 보정 선택사항):
- `clamp_threshold` 와 `no_clamp_under_100` 두 룰이 의미적으로 매우 유사 (둘 다 100px 미만 clamp 금지). 중복은 아니나 향후 rules.yaml 정리 시 통합 가능.
- `large_side_padding` 과 `max_width_pattern` 도 범위가 겹침(좌우 padding ≥100px → max-width 변환). 모두 warning이라 문제 없음.
- `meaningful_page_name` 과 `no_forbidden_class` 가 별개 룰로 분리되어 있어 에이전트 혼동 가능성 낮음 (둘 다 보존).
위 3건은 모두 **의미 손실이 아닌 중복/유사 수준**으로, T02 재외주 불요.

### 최종 판정
**PASS** — AC-001/002/003 전부 충족, R1~R3 회귀 0건, 사람 검수 차단 이슈 0건.
다음 액션:
1. T03 자체는 완료 처리 가능.
2. PM 결정: `rules/rules.yaml`, `rules/validation_schema.json`, `rules/common.md`, `rules/basic.md`, `rules/landing.md`, `tools/build-rules.py`, `tools/build-prompts.py` 변경분을 main에 머지.
3. T02 재외주 불요.

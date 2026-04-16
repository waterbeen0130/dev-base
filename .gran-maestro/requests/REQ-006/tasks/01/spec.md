# Implementation Spec

- Request ID: REQ-006
- Task ID: 01
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: Python tooling / 리팩터링] → 최종: codex-dev
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T01
- Complexity: Standard

## §0 Context Manifest

- /mnt/d/dev-base/rules/rules.yaml (REQ-005 산출물 — 81 rules, 11 enum validation type)
- /mnt/d/dev-base/tools/validate-semantic.py (현행 — 35개 check_* 하드코딩 함수)
- /mnt/d/dev-base/rules/validation_schema.json (REQ-005 자동 생성 — 80 rules)
- /mnt/d/dev-base/.gran-maestro/explore/EXP-001/explore-report.md (P3 권장 근거)

## 1. 요약 (Summary)

`validate-semantic.py`를 `rules.yaml`을 동적으로 해석해서 검증을 실행하는 **범용 엔진**으로 리팩터링한다. 11개 validation type enum 각각에 대응하는 핸들러 함수를 만들고, 룰 추가 시 Python 코드를 손대지 않아도 되게 한다.

## 2. 범위 (Scope)

- **포함**:
  - `tools/validate-semantic.py` 리팩터링: 기존 `check_*` 함수들을 두 그룹으로 나눔
    1. **enum validator** (10개): `regex_must_not_match`, `regex_must_match`, `regex_should_match`, `ast_selector_count`, `value_equals_mapping`, `html_tag_required`, `forbidden_substring`, `required_substring`, `naming_pattern`, `numeric_range`
    2. **custom handler dispatch** (1개): `type: custom`인 룰의 `custom_handler` 필드에서 함수명을 읽어 `CUSTOM_HANDLERS` 딕셔너리를 통해 디스패치
  - 메인 엔진 흐름: `rules.yaml` Read → 룰 순회 → `validation.type`에 따라 enum validator 또는 custom_handler 호출 → 결과 집계 → 리포트 출력
  - CLI 인자 확장: `--profile {basic|landing|all}` 추가 (rules.yaml의 `applies_to` 기준 필터링)
  - 기존 35개 `check_*` 함수는 **이름을 보존**하고 (CUSTOM_HANDLERS에서 참조), 시그니처만 새 엔진 컨벤션(`(rule, ctx)` → `ValidationResult`)에 맞춰 어댑터 추가
  - 새 모듈 분리 가능: `tools/validate_engine/` 하위에 `engine.py` / `enum_validators.py` / `custom_handlers.py`로 나누거나, 단일 파일 유지 가능 (PM 판단)
- **제외**:
  - 새 enum 추가 (T02 범위 — 누락 핸들러 채우기는 별도)
  - `rules.yaml` 자체 수정 (REQ-005 SoT 보존)
  - `tools/build-rules.py` 변경 (REQ-005 산출물)
- **시작점 힌트**:
  - 현행 `validate-semantic.py:1-50` (CLI argparse 시그니처)
  - `validate-semantic.py:200-500` (check_* 함수 본체)
  - `rules.yaml`의 `validation_types` 헤더 + 각 룰의 `validation` 객체
  - `rules.yaml`에서 `type: custom`인 항목들의 `custom_handler` 필드 값들을 grep해 어떤 함수명이 필요한지 파악

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable]
Given: 리팩터링된 `validate-semantic.py`
When: `python3 tools/validate-semantic.py --html templates/sub_list.html --css templates/css/common.css` 실행
Then: 정상 종료 (exit 0 또는 1), 리포트 출력
Test: 위 명령

#### AC-002 [MUST] [automatable]
Given: rules.yaml의 11 validation type 중 enum 10개
When: 각 enum에 대응하는 핸들러 함수가 존재하는지 확인
Then: 10개 모두 구현되어 있음 (custom 제외)
Test:
```
python3 -c "
import sys; sys.path.insert(0, 'tools')
from validate_semantic import ENUM_VALIDATORS  # 또는 동등 이름
expected = {'regex_must_not_match','regex_must_match','regex_should_match','ast_selector_count','value_equals_mapping','html_tag_required','forbidden_substring','required_substring','naming_pattern','numeric_range'}
missing = expected - set(ENUM_VALIDATORS.keys())
assert not missing, f'missing: {missing}'
print('AC-002 PASS')
"
```

#### AC-003 [MUST] [automatable]
Given: rules.yaml의 `type: custom` 룰들
When: 엔진이 해당 룰을 처리할 때
Then: `custom_handler` 필드의 함수명이 `CUSTOM_HANDLERS` 딕셔너리에 등록되어 있고, 호출 시 에러 없이 결과 반환 (구현이 없으면 `Skipped` 결과 반환 — T02에서 채움)
Test:
```
python3 -c "
import sys, yaml; sys.path.insert(0, 'tools')
from validate_semantic import CUSTOM_HANDLERS
d = yaml.safe_load(open('rules/rules.yaml'))
required = set()
for r in d['rules']:
    if r['validation']['type'] == 'custom':
        required.add(r.get('custom_handler') or r['id'])
registered = set(CUSTOM_HANDLERS.keys())
unregistered = required - registered
print(f'required: {len(required)}, registered: {len(registered)}, unregistered: {sorted(unregistered)[:10]}')
assert not unregistered or len(unregistered) <= 5, 'too many unregistered handlers (T02 will fix)'
"
```
(T01에서는 enum validator 10개가 100%, custom handler 등록은 stub OK — T02에서 실제 로직 채움)

#### AC-004 [MUST] [automatable]
Given: 리팩터링 전후 회귀 비교
When: 동일 입력(`templates/sub_list.html`)으로 구버전과 신버전 실행
Then: 신버전의 에러/경고 카운트가 구버전 ± 5건 이내 (대규모 회귀 없음)
Test:
```
git show edaaae2:tools/validate-semantic.py > /tmp/validate-semantic.old.py
python3 /tmp/validate-semantic.old.py --html templates/sub_list.html --css templates/css/common.css 2>&1 | tee /tmp/old_report.txt
python3 tools/validate-semantic.py --html templates/sub_list.html --css templates/css/common.css 2>&1 | tee /tmp/new_report.txt
diff <(grep -c "ERROR\|WARN" /tmp/old_report.txt) <(grep -c "ERROR\|WARN" /tmp/new_report.txt) || echo "diff > 0 — 수동 비교 필요"
```

## 3.5 Constraints

- 보안: N/A
- 성능: 단일 파일 검증 < 2초 (현재와 동등)
- 호환성: CLI 인자(`--html`, `--css`, `--img`, `--fix`)는 그대로 유지. `--profile`는 옵션 신규 추가.
- 운영: 리팩터링 중 기존 `check_*` 함수명을 삭제하지 말고 보존 (REQ-005 rules.yaml의 `custom_handler` 필드가 이 이름을 참조)

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: 기존 `validate-semantic.py`의 한국어 docstring + 영어 주석 + dataclass `ValidationResult` (없으면 신설)
- **알아야 할 제약**: `rules.yaml`은 SSOT이므로 절대 수정하지 않음. 룰 정의 변경이 필요하면 spec §11에 기록.
- **접근법 방향**: ① 새 dataclass `ValidationResult(rule_id, severity, passed, message, location)` 정의 → ② `ENUM_VALIDATORS` dict (enum_name → callable) → ③ `CUSTOM_HANDLERS` dict (handler_name → callable, 기존 check_* 어댑터) → ④ main loop가 yaml 순회하며 dispatch → ⑤ 리포트 포맷터는 기존 출력 형식 보존

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): ["02", "03"]

## 6. 에이전트 팀 구성

- 실행: codex-dev
- 사유: Python 리팩터링 + 다수 함수 시그니처 변경 + 어댑터 작성은 codex-dev capabilities(refactor, code, test)에 정확히 부합

## 10. 가정 사항

- (가정 1) 단일 파일 유지 (`tools/validate-semantic.py`)가 기본 — 모듈 분리는 코드량이 1500 lines를 초과할 때만 수행. 그 외에는 한 파일 안에서 ENUM_VALIDATORS / CUSTOM_HANDLERS 두 dict로 구분.
- (가정 2) `dataclass`를 사용 (Python 3.10+ 보장됨).
- (가정 3) T01에서는 custom handler가 비어 있어도 OK (stub 등록만). 실제 로직은 T02.

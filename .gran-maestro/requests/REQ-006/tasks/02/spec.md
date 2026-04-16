# Implementation Spec

- Request ID: REQ-006
- Task ID: 02
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: Python tooling / 핸들러 채우기] → 최종: codex-dev
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T02
- Complexity: Standard

## §0 Context Manifest

- /mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/01/spec.md (T01 결과)
- /mnt/d/dev-base/tools/validate-semantic.py (T01 산출물 — 새 엔진)
- /mnt/d/dev-base/rules/rules.yaml (custom_handler 메타 소스)
- /mnt/d/dev-base/.gran-maestro/explore/EXP-001/explore-report.md (누락 30건 카테고리)

## 1. 요약 (Summary)

T01에서 enum dispatcher만 구현되고 custom handler stub으로 남은 미구현 룰들의 실제 로직을 채운다. EXP-001이 지적한 "선언만 있고 구현 없는 30건"을 우선 처리한다.

## 2. 범위 (Scope)

- **포함**:
  - T01의 `CUSTOM_HANDLERS`에서 `Skipped` 또는 stub으로 등록된 핸들러를 실제 검증 로직으로 채움
  - EXP-001에서 카테고리화된 누락 영역:
    1. **landing 전용 규칙** (`root_vars_required`, `gsap_animation_css_present` 등) — landing.html/css에만 적용
    2. **mapping 값 대조** (`figma_value_padding`, `figma_value_color` 등) — Figma extracted JSON과 CSS의 값 일치 검증 (입력으로 mapping.json 경로 필요 시 `--mapping` CLI 인자 추가)
    3. **DOM 구조** (`ul_li_for_lists`, `parent_tag_over_class`) — HTML AST 분석
    4. **선택자 패턴** (`prefix_must_match_filename`) — CSS 파싱 + 파일명 비교
    5. 기타 `validate-semantic.py`에서 미구현이지만 rules.yaml에 선언된 룰
  - 각 핸들러는 `(rule, ctx) → ValidationResult` 시그니처 준수
  - `--mapping <path>` CLI 인자 추가 (T01에서는 미포함)
- **제외**:
  - 엔진 구조 변경 (T01 범위)
  - rules.yaml 변경 (REQ-005 SSOT)
  - 새 룰 추가 (오직 기존 미구현 룰 채우기만)
- **시작점 힌트**:
  - T01 spec.md의 AC-003 검증 명령 결과 — `unregistered` 또는 `Skipped` 목록을 작업 대상으로
  - rules.yaml에서 `type: custom`이고 EXP-001 보고서의 30건 카테고리에 해당하는 룰 찾기
  - 카테고리별 1~2개 핸들러를 먼저 구현해 패턴 정착 후 나머지 확장

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable]
Given: T01 + T02 완료
When: AC 검증 실행
Then: T01의 AC-003에서 `unregistered` 카운트가 0
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
unregistered = required - set(CUSTOM_HANDLERS.keys())
assert not unregistered, f'still unregistered: {unregistered}'
print('AC-001 PASS — all custom handlers registered')
"
```

#### AC-002 [MUST] [automatable]
Given: 채워진 핸들러
When: 각 핸들러를 dummy input으로 호출
Then: 예외 발생 0건 (`Skipped` 또는 `Passed`/`Failed` 결과 반환)
Test: 핸들러별 단위 호출 (T03이 본격 회귀)

#### AC-003 [MUST] [automatable]
Given: 누락 30건 핵심 카테고리 (landing 전용 + mapping 값 대조 + DOM 구조)
When: rules.yaml에서 해당 카테고리의 룰 ID를 골라 검증
Then: 각 카테고리에 최소 1개 룰이 실제 동작하는 핸들러를 가짐 (Skipped 아님)
Test: spec §11에 카테고리별 구현 상태 표 작성

## 3.5 Constraints

- 보안: N/A
- 성능: 핸들러 1개당 < 100ms (회귀 시 누적 영향 검토)
- 호환성: CLI 기존 인자 보존. `--mapping`는 옵션 (없으면 mapping 의존 룰만 Skipped)
- 운영: 새 핸들러는 모두 try/except로 감싸 실패 시 ValidationResult.skipped로 격리 (전체 검증 중단 방지)

## 4. 구현 컨텍스트

- **따라야 할 패턴**: T01의 `(rule, ctx) → ValidationResult` 시그니처
- **알아야 할 제약**: HTML 파싱은 표준 라이브러리(`html.parser`) 또는 기존 `validate-semantic.py`가 사용하는 파서 재활용. 새 외부 의존성 추가 금지.
- **접근법 방향**: 카테고리별 batch 구현 — landing 1건 → mapping 1건 → DOM 1건 → 패턴 정착 → 나머지 확장 → AC 재실행

## 5. 의존성

- 선행 작업 (blockedBy): ["01"]
- 후행 작업 (blocks): ["03"]

## 6. 에이전트 팀 구성

- 실행: codex-dev
- 사유: 다수 핸들러 함수 작성 + HTML/CSS 파싱 + AST 작업

## 10. 가정 사항

- (가정 1) "누락 30건"은 EXP-001 보고서 추정치이며 실제로는 rules.yaml의 `unregistered` 결과를 신뢰. 정확한 수는 T02 시작 시 grep으로 확정.
- (가정 2) `--mapping` 의존 룰은 우선순위 낮음. CLI 인자 없이 호출 시 자동 Skip하고 mapping.json 제공 시에만 동작.
- (가정 3) HTML 파싱이 복잡한 룰(예: DOM 깊이 5 초과)은 기존 `validate-semantic.py`의 파서 활용. 새 파서 도입 금지.

# Spec — REQ-037 / Task 01: componentId 재사용 로직 + component_groups 추출

**Assigned Agent**: `[config: codex-dev] codex-dev`
**Status**: pending
**Plan**: PLN-010
**Linked Intent**: INTENT-006

---

## §0 Context Manifest

- `tools/figma-section-spec.py` — 8축 v2 spec 생성 도구 (componentId/componentSetId 이미 추출됨, Phase A REQ-032)
- `extracted/section_03_spec.json`, `extracted/section_04_spec.json` — fixture
- `rules/models.py` (Phase B)
- `tests/regression/test_req032_add_only.py` (참고 — add-only diff 패턴)

## §1 요약

`tools/figma-section-spec.py` 에 post-process 단계를 추가하여 동일 `componentId` 인스턴스를 그룹핑한다. 각 그룹마다 shared CSS base class 와 인스턴스별 override (characters / fills[].color / fontWeight / fontSize 4축) 를 분리하여 spec.json 에 `component_groups` 필드로 기록한다.

## §2 범위

**포함**:
- `tools/figma-section-spec.py` post-process 단계: 동일 componentId 그룹핑 → `component_groups` 배열 생성
- spec.json 스키마 확장: `component_groups: [{componentId, instances: [nodeId], shared_style, overrides: [{node_id, diff}]}]`
- override 분리 기준: characters / fills[].color / fontWeight / fontSize 4축
- 기존 8축 v2 spec 필드는 byte-exact 보존 (add-only)
- 단위/회귀 테스트

**제외**:
- CSS 렌더링 자체 (본 태스크는 spec.json 필드 추가까지만)
- componentSetId variant 추적 (명시적 제외 — 후속 plan)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] 동일 componentId 인스턴스 그룹핑 (PAC-7)

- **Given**: 동일 `componentId` 인스턴스 2개 이상 포함 fixture
- **When**: `figma-section-spec.py` post-process 후 spec.json 생성
- **Then**: spec.json `component_groups` 배열 존재, 각 그룹의 `instances` 에 동일 componentId 노드 ID 목록 포함
- **Test**: `pytest tests/unit/test_component_groups_grouping.py -v` (신규)

### AC-002 [automatable] shared_style + 인스턴스별 override 분리 (PAC-8)

- **Given**: 동일 componentId 인스턴스들이 characters / color / fontWeight / fontSize 에서 일부만 다른 상태
- **When**: post-process 실행
- **Then**: 공통 속성은 `shared_style`, 차이나는 속성은 `overrides[i].diff` 에 기록
- **Test**: `pytest tests/unit/test_component_groups_override_split.py -v` (신규)

### AC-003 [automatable] 생성 CSS 중복 감소 측정 (PAC-9)

- **Given**: 동일 componentId 인스턴스 N개 (N ≥ 2) fixture
- **When**: shared_style 만 1개 생성, overrides 만 N-1개 생성했을 때의 총 라인 수 vs N개 독립 생성 라인 수 비교
- **Then**: 감소율 > 0 (fixture 기준 30% 이상 권장)
- **Test**: `pytest tests/unit/test_component_groups_reduction_metric.py -v` (신규)

### AC-004 [automatable] [regression-test] 기존 v2 spec.json 필드 byte-exact 보존 (PAC-10)

- **Given**: `extracted/section_03_spec.json`, `extracted/section_04_spec.json` 기존 값
- **When**: figma-section-spec.py 재생성 (동일 입력)
- **Then**: `component_groups` 필드만 추가되고, 기존 모든 필드는 byte-exact 보존
- **Test**: `pytest tests/regression/test_req037_add_only.py -v` (신규)

## §3.2 Test Scenarios (Pre-Impl)

- AC-001: `pytest tests/unit/test_component_groups_grouping.py -v`
- AC-002: `pytest tests/unit/test_component_groups_override_split.py -v`
- AC-003: `pytest tests/unit/test_component_groups_reduction_metric.py -v`
- AC-004: `pytest tests/regression/test_req037_add_only.py -v`

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-7 | MUST | AC-001 | full |
| PAC-8 | MUST | AC-002 | full |
| PAC-9 | SHOULD | AC-003 | full |
| PAC-10 | SHOULD | AC-004 | full |

## §3.5 Constraints

- 기존 8축 v2 spec 필드 값 변경 금지 — 신규 필드 `component_groups` 만 add-only
- componentId 가 없는 노드는 그룹핑 대상이 아님 (skip)
- override 분리는 characters / fills[].color / fontWeight / fontSize 4축만 (scope 제한)
- 기존 pytest 133 passed 회귀 없음

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | — | codex-dev |

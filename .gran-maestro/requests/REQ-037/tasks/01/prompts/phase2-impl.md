# Implementation Request — REQ-037 / Task 01

**Request**: REQ-037 (Phase D — componentId 재사용 로직)
**Task**: 01 — post-process 그룹핑 + shared_style + override 분리
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-037-T01`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-037/tasks/01/spec.md`

**선행**: REQ-035 Phase B, REQ-036 Phase C 완료 (main merge 완료)

---

## 구현 컨텍스트

`tools/figma-section-spec.py` 에 post-process 단계를 추가한다. 동일 `componentId` 를 가진 인스턴스들을 그룹핑하고, 공통 속성 (`shared_style`) 과 인스턴스별 차이 (`overrides[].diff`) 를 분리하여 spec.json 에 `component_groups` 배열로 기록한다.

override 분리 축 (명시적 scope):
- `characters` (text 노드 전용)
- `fills[].color`
- `fontWeight`
- `fontSize`

## 구현 상세

### 1. post-process 함수 추가

`tools/figma-section-spec.py` 내 spec 생성 후 post-process:

```python
def extract_component_groups(spec: dict) -> list[dict]:
    """
    spec의 text_nodes + frame_nodes에서 동일 componentId 인스턴스를 그룹핑.
    각 그룹마다 shared_style + instance override를 분리.
    """
    from collections import defaultdict

    groups = defaultdict(list)
    for node in spec.get("text_nodes", []) + spec.get("frame_nodes", []):
        cid = node.get("componentId")
        if cid:
            groups[cid].append(node)

    result = []
    OVERRIDE_AXES = ["characters", "fontWeight", "fontSize"]  # fills[].color는 별도 처리

    for cid, instances in groups.items():
        if len(instances) < 2:
            continue  # 단일 인스턴스는 그룹화 불필요

        # shared = 모든 인스턴스 공통 속성
        first = instances[0]
        shared_style = {}
        for k, v in first.items():
            if k in ["id", "name"] or k.startswith("bbox"):
                continue
            if all(inst.get(k) == v for inst in instances):
                shared_style[k] = v

        # overrides = 인스턴스별 차이 (4축 한정)
        overrides = []
        for inst in instances:
            diff = {}
            for axis in OVERRIDE_AXES:
                if axis in inst and inst.get(axis) != shared_style.get(axis):
                    diff[axis] = inst.get(axis)
            # fills color 별도
            inst_color = _get_fills_color(inst)
            shared_color = _get_fills_color(first)
            if inst_color and inst_color != shared_color:
                diff["fills_color"] = inst_color
            overrides.append({
                "node_id": inst.get("id"),
                "diff": diff
            })

        result.append({
            "componentId": cid,
            "instances": [inst.get("id") for inst in instances],
            "shared_style": shared_style,
            "overrides": overrides
        })

    return result
```

spec.json 생성 직전에 `spec["component_groups"] = extract_component_groups(spec)` 호출.

### 2. 기존 spec 필드 byte-exact 보존

- `component_groups` 는 spec dict 의 **맨 끝에 append** (JSON 키 순서 영향 없음)
- 기존 필드 값 수정 없음
- `extracted/section_03_spec.json`, `extracted/section_04_spec.json` 재생성 시 기존 값 byte-exact

### 3. 단위/회귀 테스트 4종

- `tests/unit/test_component_groups_grouping.py`: fixture 로 동일 componentId 3개 생성 후 그룹핑 확인
- `tests/unit/test_component_groups_override_split.py`: 공통/차이 4축 분리 확인
- `tests/unit/test_component_groups_reduction_metric.py`: 감소율 계산 + > 0 확인 (fixture 기준)
- `tests/regression/test_req037_add_only.py`: section_03/04 byte-exact 보존 (신규 필드만 추가)

### 4. 검증

```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-037-T01

# spec 재생성 (FIGMA_TOKEN 없어도 fixture 기반 테스트는 동작)
pytest tests/unit/test_component_groups_grouping.py -v
pytest tests/unit/test_component_groups_override_split.py -v
pytest tests/unit/test_component_groups_reduction_metric.py -v
pytest tests/regression/test_req037_add_only.py -v

# 전체 회귀
pytest tests/ -v 2>&1 | tail -20
# 기대: 133 + 4 신규 = 137 passed / 0 failed
```

### 5. git 커밋 금지 — PM 이 직접 커밋.

## 규칙

- 기존 v2 spec 필드 (fills_v2 / effects / strokes / cornerRadii / layoutSizing / characterStyleOverrides 등) 값 변경 금지
- `rules/models.py` (Phase B) 수정 금지
- `tools/structural-diff.py` (Phase C) 수정 금지
- `componentSetId` variant 추적은 제외 (후속 plan)
- 기존 pytest 133 passed 회귀 없음
- 코드 주석은 영어만

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-037-T01`

## [MANDATORY] 응답에 반드시 포함할 것

1. `tools/figma-section-spec.py` 변경 diff 요약 (post-process 추가부)
2. 4개 테스트 전체 출력
3. `pytest tests/ -v` 마지막 20줄 (summary)

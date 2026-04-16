# Task: REQ-012 / 01 — figma-section-spec.py 보강

## Paths
- SPEC: /mnt/d/dev-base/.gran-maestro/requests/REQ-012/tasks/01/spec.md
- PLAN: /mnt/d/dev-base/.gran-maestro/plans/PLN-005/plan.md
- WORKTREE: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-012-01
- TARGET: tools/figma-section-spec.py
- REQ_ID: REQ-012
- TASK_ID: 01

## 작업 개요

`tools/figma-section-spec.py`에 3종 신규 필드를 추가한다. 기존 출력 형식은 모두 유지(additive only).

## 반드시 먼저 Read

1. `SPEC` (AC 6개 — AC-001~006)
2. `PLAN` (PLN-005 §3 B-1)
3. `tools/figma-section-spec.py` 전체 (특히 `walk_and_extract`, `normalize_text_node`, `normalize_frame_node`)
4. `tools/figma-validate.py` (spec.json 소비 형식 — 신규 필드가 깨지지 않게)
5. CLAUDE.md "텍스트 추출 품질" 섹션 (characterStyleOverrides 누적 병합 알고리즘)

## 구현 항목

### 1. character_segments[] (TEXT 노드)

`normalize_text_node()`에 `character_segments` 필드 추가. Figma API 노드 객체에서:
- `node.characters` (전체 텍스트)
- `node.characterStyleOverrides` (배열, 인덱스 = 캐릭터 위치, 값 = override key)
- `node.styleOverrideTable` (dict, key = override id 문자열, value = style+fills)

#### 누적 병합 알고리즘 (CLAUDE.md 명시 — 정확 구현 필수)

```python
def build_character_segments(node):
    chars = node.get("characters", "")
    if not chars:
        return []
    overrides = node.get("characterStyleOverrides", []) or []
    table = node.get("styleOverrideTable", {}) or {}
    base_style = {**(node.get("style") or {})}
    base_fills = node.get("fills") or []

    segments = []
    previous_resolved = None  # 누적 병합용

    def resolve(override_id):
        nonlocal previous_resolved
        if override_id == 0 or override_id is None:
            resolved = {**base_style, "fills": base_fills}
        else:
            override = table.get(str(override_id), {}) or {}
            override_style = override.get("style") or {}
            override_fills = override.get("fills")
            base_for_merge = previous_resolved if previous_resolved is not None else {**base_style, "fills": base_fills}
            resolved = {**base_for_merge, **override_style}
            if override_fills is not None:
                resolved["fills"] = override_fills
        previous_resolved = resolved
        return resolved

    # 캐릭터별 override id 결정 (overrides가 chars보다 짧으면 나머지는 0)
    override_ids = [overrides[i] if i < len(overrides) else 0 for i in range(len(chars))]

    # 동일 override id 구간끼리 병합
    i = 0
    while i < len(chars):
        j = i
        oid = override_ids[i]
        while j + 1 < len(chars) and override_ids[j + 1] == oid:
            j += 1
        resolved = resolve(oid)
        segment = {
            "start": i,
            "end": j + 1,
            "text": chars[i:j+1],
            "fontFamily": resolved.get("fontFamily"),
            "fontSize": safe_round_3(resolved.get("fontSize")),
            "fontWeight": safe_round_3(resolved.get("fontWeight")),
            "lineHeightPx": safe_round_3(resolved.get("lineHeightPx")),
            "letterSpacing": safe_round_3(resolved.get("letterSpacing")),
            "color": extract_text_color(resolved.get("fills")),
        }
        segments.append(segment)
        i = j + 1
    return segments
```

#### `normalize_text_node()` 반환 dict에 추가
```python
"character_segments": build_character_segments(node),
```

### 2. cornerRadius / rectangleCornerRadii / border_radius_hint (FRAME 노드)

`normalize_frame_node()`에 추가:
```python
def extract_corner_radius(node, bbox):
    cr = node.get("cornerRadius")
    rcr = node.get("rectangleCornerRadii")  # [tl, tr, br, bl] 또는 None
    hint = None
    w = bbox.get("w") or 0
    h = bbox.get("h") or 0
    if cr is not None and w and h:
        if cr >= min(w, h) / 2:
            hint = "50%"
    return {
        "cornerRadius": safe_round_3(cr),
        "rectangleCornerRadii": [safe_round_3(v) for v in rcr] if isinstance(rcr, list) else None,
        "border_radius_hint": hint,
    }
```

`normalize_frame_node` 반환 dict에 위 3개 키 spread:
```python
**extract_corner_radius(node, extract_bbox(node)),
```

### 3. bbox (TEXT 노드) + parent_id (모든 노드)

#### TEXT 노드 bbox
`normalize_text_node()` 반환 dict에 추가:
```python
"bbox": extract_bbox(node),
```
(이미 frame엔 있고, 같은 헬퍼 재사용)

#### parent_id (TEXT/FRAME 모두)
`walk_and_extract()` 의 walk 재귀 함수에 `parent_id` 인자 추가:
```python
def walk(node, parent_id=None):
    if not isinstance(node, dict):
        return
    node_id = node.get("id")
    
    # text/frame normalize 시 parent_id 주입
    if node.get("type") == "TEXT":
        normalized = normalize_text_node(node)
        normalized["parent_id"] = parent_id
        text_nodes.append(normalized)
    elif node.get("type") in ("FRAME", "GROUP", "INSTANCE", "COMPONENT", "RECTANGLE", "VECTOR"):
        normalized = normalize_frame_node(node, image_refs)
        normalized["parent_id"] = parent_id
        frame_nodes.append(normalized)
    # ...

    for child in node.get("children", []) or []:
        walk(child, parent_id=node_id)

walk(root, parent_id=None)
```

> ⚠️ 기존 walk 시그니처가 다르면 신중하게 보존 — `parent_id` 추가가 기존 호출 chain을 깨지 않게 keyword-only로.

## 검증

### AC-001 (남성 character override)
```bash
cd {WORKTREE}
FIGMA_TOKEN=figd_[REDACTED] python3 tools/figma-section-spec.py \
  --file-key T8xEPS7sR5MZCUQ9JVa4hH --node-id 842:206 --output /tmp/req012 --name section_05_test
python3 -c "
import json
d = json.load(open('/tmp/req012/section_05_test_spec.json'))
target = [x for x in d['text_nodes'] if x['id']=='842:209'][0]
segs = target['character_segments']
print('Segments:', len(segs))
for s in segs:
    print(f\"  [{s['start']}-{s['end']}] {s['text']!r} color={s['color']}\")
# 기대: '오직 ', '남성', '만을 위한' 3 segment + '남성' color #916046
assert any('남성' in s['text'] and s['color']=='#916046' for s in segs), '남성 #916046 segment not found'
print('AC-001 PASS')
"
```

### AC-002 (cornerRadius 50%)
```bash
python3 -c "
import json
d = json.load(open('/tmp/req012/section_05_test_spec.json'))
icon = [x for x in d['frame_nodes'] if x['id']=='842:222'][0]
print('cornerRadius:', icon.get('cornerRadius'), 'hint:', icon.get('border_radius_hint'))
assert icon.get('border_radius_hint')=='50%', f'border_radius_hint should be 50%, got {icon}'
print('AC-002 PASS')
"
```

### AC-003 (bbox + parent_id)
```bash
python3 -c "
import json
d = json.load(open('/tmp/req012/section_05_test_spec.json'))
assert all('bbox' in n for n in d['text_nodes']), 'TEXT bbox missing'
assert all('parent_id' in n for n in d['text_nodes']), 'TEXT parent_id missing'
assert all('parent_id' in n for n in d['frame_nodes']), 'FRAME parent_id missing'
print('AC-003 PASS')
"
```

### AC-004 (회귀 무회귀)
```bash
# 기존 figma-validate.py가 새 spec.json을 그대로 소비할 수 있는지
# 신규 필드가 추가됐을 뿐이므로 기존 키만 사용하는 figma-validate는 영향 없어야 함
python3 tools/figma-validate.py --spec /tmp/req012/section_05_test_spec.json --html /dev/null --css /dev/null 2>&1 | head -5 || echo "expected error: html/css not exist, but no traceback"
# REQ-008/02 회귀
bash /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/run_regression.sh 2>&1 | grep -E "^=|exit=" | head
```

### AC-005 (py_compile)
```bash
python3 -m py_compile tools/figma-section-spec.py && echo "AC-005 PASS"
```

### AC-006 (override 없는 노드 graceful)
```bash
python3 -c "
import json
d = json.load(open('/tmp/req012/section_05_test_spec.json'))
deep = [x for x in d['text_nodes'] if x['id']=='842:216'][0]  # 'DEEP 플랜'
segs = deep['character_segments']
# override 없으면 단일 segment 또는 빈 배열
print('DEEP 플랜 segments:', segs)
assert len(segs) <= 1 or all(s.get('color') == segs[0].get('color') for s in segs), 'DEEP 플랜 should have single segment'
print('AC-006 PASS')
"
```

## 금지

- 기존 spec.json 출력 키 변경/제거 금지 (additive only)
- 외부 패키지 추가 금지 (stdlib만)
- `tools/figma-validate.py` 수정 금지 (REQ-013에서)
- git commit 금지 (PM이 사전검증 후 직접 커밋)

## 완료 보고 (6~10줄)

- 추가된 함수/필드 요약
- AC-001~006 각 검증 결과 (PASS/FAIL + 출력 값)
- py_compile 결과
- 회귀 12개 fixture 결과 (base/scenarios exit codes)
- 작업 중 발견된 엣지 케이스 (있다면)

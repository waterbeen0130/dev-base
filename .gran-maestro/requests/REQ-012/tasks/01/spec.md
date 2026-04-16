# Implementation Spec

- Request ID: REQ-012
- Task ID: 01
- Created: 2026-04-13
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: backend/tools] → 최종: codex-dev
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-012-01
- Complexity: Standard

## §0 Context Manifest

- tools/figma-section-spec.py
- .gran-maestro/plans/PLN-005/plan.md
- .gran-maestro/requests/REQ-011/tasks/01/report.md (Section_05 "남성" character override 사례)
- /tmp/mojelim_extracted/section_05_spec.json (현재 출력 형식 참고)
- /tmp/mojelim_extracted/section_hero_spec.json

## 1. 요약 (Summary)

`tools/figma-section-spec.py`에 3종 신규 필드를 추가한다: TEXT 노드의 `character_segments[]` (characterStyleOverrides 분할), FRAME 노드의 `cornerRadius`/`rectangleCornerRadii`/`border_radius_hint`, 모든 노드의 `bbox`/`parent_id`. 이로써 PLN-004 워크플로우가 캐릭터 단위 색상 오버라이드, 원형 아이콘, 노드 위치/계층 정보를 figma-validate.py와 외주 brief에 전달할 수 있게 된다.

## 2. 범위 (Scope)

- **포함**:
  - `normalize_text_node()`에 `character_segments[]` 필드 추가
    - Figma API의 `characters` + `characterStyleOverrides[]` + `styleOverrideTable{}` 함께 추출
    - 누적 병합 알고리즘: `previousResolvedStyle = null`, override `0` 또는 빈값이면 `baseStyle`, 그 외는 `{...prev||base, ...override.style, ...(override.fills ? {fills:override.fills} : {})}`
    - 결과: `[{start, end, text, fontFamily, fontSize, fontWeight, color, lineHeightPx, letterSpacing}]` 형식
    - 오버라이드 없는 노드는 `[{start:0, end:len, text:full, ...base}]` 단일 segment 또는 빈 배열로 graceful 처리
  - `normalize_frame_node()`에 `cornerRadius` (단일 값) + `rectangleCornerRadii` (4모서리 배열) + `border_radius_hint` 필드 추가
    - 단일 `cornerRadius`만 있으면 `cornerRadius: N`, `rectangleCornerRadii: null`
    - 4모서리 다른 값이면 `cornerRadius: null`, `rectangleCornerRadii: [tl,tr,br,bl]`
    - `border_radius_hint`: `cornerRadius >= min(width,height)/2` 이면 `"50%"`, 그 외 `null`
  - 모든 TEXT/FRAME 노드에 `bbox: {x,y,w,h}` (이미 frame에는 있으니 text에 추가)
  - 모든 노드에 `parent_id` (walk_and_extract에서 부모 추적)
- **제외**:
  - figma-validate.py 수정 (REQ-013에서 활용)
  - 기존 출력 필드 변경 (하위 호환)
  - bounds/constraints 등 다른 Figma 속성

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable] [unit-test]
Given: 모제림 Section_05 (842:206) spec을 추출
When: `python3 tools/figma-section-spec.py --file-key T8xEPS7sR5MZCUQ9JVa4hH --node-id 842:209 --output /tmp/req012 --name section_05_test` 실행 (842:209는 "오직 남성만을 위한" TEXT 노드의 부모)
Then: 출력 spec.json의 text_nodes[0].character_segments에 `[{start:0,end:3,text:"오직 ",color:"#312d2b"}, {start:3,end:5,text:"남성",color:"#916046"}, {start:5,end:10,text:"만을 위한",color:"#312d2b"}]` 형식의 분할 segment 존재
Test:
```bash
FIGMA_TOKEN=... python3 tools/figma-section-spec.py --file-key T8xEPS7sR5MZCUQ9JVa4hH --node-id 842:206 --output /tmp/req012 --name section_05_test
python3 -c "import json; d=json.load(open('/tmp/req012/section_05_test_spec.json')); n=[x for x in d['text_nodes'] if x['id']=='842:209'][0]; print('남성' in str(n['character_segments']))"
```

#### AC-002 [MUST] [automatable]
Given: 모제림 Section_05 spec 추출
When: figma-section-spec.py 실행
Then: 출력 spec.json의 frame_nodes 중 Section_05_1 (842:222) 항목에 `cornerRadius: 220.0` (또는 큰 값), `border_radius_hint: "50%"` 존재
Test: `python3 -c "import json; d=json.load(open('/tmp/req012/section_05_test_spec.json')); n=[x for x in d['frame_nodes'] if x['id']=='842:222'][0]; assert n.get('border_radius_hint')=='50%', n"`

#### AC-003 [MUST] [automatable]
Given: 모제림 Section_05 spec 추출
When: figma-section-spec.py 실행
Then: 모든 text_nodes에 `bbox` 필드 존재 (`{x,y,w,h}` 형식, null 가능), 모든 노드(text+frame)에 `parent_id` 필드 존재
Test: `python3 -c "import json; d=json.load(open('/tmp/req012/section_05_test_spec.json')); assert all('bbox' in n and 'parent_id' in n for n in d['text_nodes']); assert all('parent_id' in n for n in d['frame_nodes'])"`

#### AC-004 [MUST] [automatable] [impact-check]
Given: REQ-008/02 회귀 fixture 12개 + REQ-007 시나리오
When: 기존 spec.json 출력 형식과 비교
Then: 신규 필드만 추가됨 (기존 필드 모두 유지). figma-validate.py가 기존 spec.json을 읽고 동작에 영향 없음
Test:
```bash
# REQ-008/02 base fixture를 예전 figma-validate로 돌렸을 때와 동일 결과
bash .gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/run_regression.sh
# base=exit 0, 12 시나리오=exit 1 유지
```

#### AC-005 [MUST] [automatable] [lint-check]
Given: 수정된 figma-section-spec.py
When: `python3 -m py_compile tools/figma-section-spec.py`
Then: exit 0
Test: `python3 -m py_compile tools/figma-section-spec.py`

#### AC-006 [SHOULD] [automatable]
Given: characterStyleOverrides가 없는 일반 TEXT 노드 (예: 모제림 Section_05 "DEEP 플랜" 842:216)
When: figma-section-spec.py 실행
Then: 해당 text_node의 character_segments는 빈 배열 `[]` 또는 단일 segment `[{start:0, end:len, text:full, ...base style}]` (graceful)
Test: section_05_spec.json의 842:216 노드 character_segments 검증

## 3.2 Intent Trace

| AC-ID | 의도 근거 | 출처 | 신뢰도 |
|---|---|---|---|
| AC-001 | "characterStyleOverrides 추출 (TEXT 노드 캐릭터 단위 오버라이드 — 색상/굵기/크기 분할)" | plan.md §3 B-1 | High |
| AC-002 | "cornerRadius 추출 (FRAME 노드)" + "50% 클램프 판정: cornerRadius >= min(width, height)/2 이면 border_radius_hint: '50%' 부가" | plan.md §3 B-1 | High |
| AC-003 | "bbox / parent_id 추출" | plan.md §3 B-1 | High |
| AC-004 | "[IMPACT] REQ-008/02 회귀 12개 fixture 무회귀" | plan.md §4 PAC-7 | High |

## 3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-3 | MUST / TIER-A | AC-001, AC-006 | Full |
| PAC-4 | MUST / TIER-A | AC-002 | Full |
| PAC-5 | SHOULD / TIER-B | AC-003 | Full |
| PAC-7 | MUST / TIER-A [IMPACT] | AC-004 | Full |

## 3.5 Constraints

- 호환성: Python 3.10+, 외부 의존성 금지 (stdlib만)
- 운영: 기존 spec.json 출력 필드 모두 유지 (additive only)
- 보안: Figma 토큰 환경변수만

## 4. 구현 컨텍스트

- **따라야 할 패턴**: 기존 `normalize_text_node`/`normalize_frame_node` 함수형 스타일 (dict 반환), `safe_round_3()` 헬퍼 재사용
- **알아야 할 제약**:
  - Figma API의 `characterStyleOverrides`는 길이가 text보다 짧을 수 있음 → 나머지 인덱스는 base style 적용
  - `styleOverrideTable`은 누적 병합 (CLAUDE.md "텍스트 추출 품질" 참조)
  - `walk_and_extract`에서 부모 추적: 재귀 호출 시 `parent_id` 인자 전달
- **접근법 방향**: figma-section-spec.py에 함수 추가 (`build_character_segments(node)`, `extract_corner_radius(node, bbox)`) + walk 로직에 parent 추적 + normalize 함수 반환값에 신규 키 추가

## 5. 의존성

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): [REQ-013]

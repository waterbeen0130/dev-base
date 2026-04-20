# Implementation Request — REQ-032/01

- Request: REQ-032 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-032-task-01
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md
- 선행 commits: REQ-029 (431d0e3), REQ-030 (7fa6cd2), REQ-031 (8919608)

## 구현 컨텍스트 (PM 작성)

PLN-009 Phase A 4단계 — 컴포넌트 인식 + 벡터 메타 + asset manifest 추가:

1. **frame_nodes 에 `componentId`, `componentSetId` 필드 추출** (인스턴스의 원본 컴포넌트 추적). 재사용 로직(같은 componentId 자식들 묶기/클래스 공유)은 본 plan **명시적 제외** — 추출만.
2. **vector_nodes 의 SVG path 메타 보강** (현재 figma-section-spec.py 의 normalize_vector_node 가 path geometry/strokeStyle 일부만 추출). PathData(`fillGeometry[].path`, `strokeGeometry[].path`)와 viewBox(=size.width/height) 를 spec 에 명시 추출. SVG path string 그대로 보존 (변환 X).
3. **asset_manifest.json 신규 생성** — spec.json 출력과 함께 같은 디렉토리(예: `extracted/section_03_asset_manifest.json`)에 asset 인덱스 작성:
   - 각 항목: `{ "ref": "{imageRef 또는 vector node id}", "kind": "image|vector", "hash": "{sha256 of content or imageRef itself}", "spec_node_id": "{Figma node id}" }`
   - 동일 imageRef 가 여러 노드에서 참조되어도 manifest 에는 1 항목만 (중복 제거)
   - SVG path 의 hash 는 path string 의 SHA-256 (deterministic)

`figma-section-spec.py` CLI 에 옵션 `--emit-asset-manifest` (기본 켜짐) — manifest 파일 자동 생성. `figma-validate.py` 에 v2 카테고리 추가:
- `v2.componentId.match`: 동일 componentId 인스턴스가 HTML 에서 동일 클래스/template 으로 표현되었는지 (heuristic — 여러 인스턴스가 있을 때만 검사, 없으면 PASS)
- `v2.assetManifest.exists`: spec.json 옆에 asset_manifest.json 이 존재하고 모든 IMAGE fills_v2 / vector 가 manifest 에 등록되었는지 검증

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. plan + 선행 REQ-029/030/031 변경사항 확인
2. `tools/figma-section-spec.py` 의 normalize_vector_node 위치 + 현재 출력 필드 확인
3. Figma REST API path geometry: `fillGeometry: [{path: "M0 0 L10 10 ..."}]`, `strokeGeometry: [{path: "..."}]`, vector frame size
4. spec §3 AC + §11 Test Scenarios 모두 PASS 시킬 것

## 핵심 구현 지침

1. **componentId/componentSetId**: Figma node 의 `componentId`, `componentSetId` 가 있으면 그대로, 없으면 `null` 명시.
2. **vector path**:
   - frame size 는 `node.size.width/height` → spec 의 vector_nodes 에 `viewBox: { width, height }` 추가
   - `fillGeometry[].path` 와 `strokeGeometry[].path` 그대로 spec 에 보존 (변환 없음)
3. **asset_manifest.json**:
   - figma-section-spec.py 의 main flow 끝에 manifest 빌드 루프 추가
   - spec.json 의 모든 frame_nodes/vector_nodes 순회하며 IMAGE fills_v2 의 imageRef 와 vector_nodes 의 path hash 수집
   - 출력 경로: spec.json 과 같은 디렉토리에 `{section}_asset_manifest.json`
   - JSON 출력은 결정성 보장 (sort_keys=True, indent=2, hash hex 소문자)
4. **figma-validate v2 카테고리 2개**: componentId match (instance 그룹핑 휴리스틱) + assetManifest 존재성 검증
5. **결정성/add-only diff/stdlib only/Python 3.10**

## 작성 테스트

- `tests/unit/test_component_id_extract.py` (componentId 추출 PASS, 없으면 null)
- `tests/unit/test_vector_path_geometry.py` (fillGeometry path string 보존)
- `tests/unit/test_asset_manifest_generation.py` (IMAGE + vector 가 모두 manifest 에 등록, hash deterministic)
- `tests/unit/test_validate_asset_manifest_exists.py` (manifest 누락 시 FAIL)

## 규칙

- spec §2 변경 범위 외 파일 수정 금지
- git commit 금지 (PM 처리)
- stdlib 만 사용
- TDD: AC 모두 [tdd-required]
- [MANDATORY] 완료 전 신규 unit test + py_compile 실행 후 응답에 출력 포함
- 모든 변경은 worktree 내부에서 수행

# REQ-043 드릴 런 리포트 — 디에스솔루션 MAIN 파이프라인 end-to-end

- 작성일: 2026-04-21
- 소속: REQ-043 / PLN-011
- 대상 Figma: `JLCP6dWG63kJVBlND7bVZl` / node `130:10972` (MAIN)
- 실행 범위: 프로젝트 초기화 → Figma 구조 확인 → 섹션별 spec 생성 (gemini dispatch 직전 중단)

## 1. 요약

dev-base Figma → HTML/CSS 파이프라인을 디에스솔루션 Figma 소스에 실전 적용해 end-to-end 검증을 시도했다. **spec 생성까지는 성공**했으나, gemini-dev dispatch 직전 단계에서 **시각 렌더링용 에셋(SVG 패스 / PNG 이미지) 이 파이프라인에서 추출되지 않는 것을 확인**하고 중단했다. 갭이 명확해 dispatch 를 강행해도 시각적 결과물을 만들 수 없음이 예견되기 때문이다.

이 리포트는 발견된 갭을 PLN-012 후속 소재로 정리한 것이다.

## 2. 실행 결과

| 단계 | 상태 | 비고 |
|---|---|---|
| 1. 프로젝트 초기화 | 🟡 부분 | `init-project.py` 버그 2건 회피 후 완료 |
| 2. Figma 구조 확인 (`--tree`) | ✅ | 6개 섹션 발견 + 1개 숨김 섹션 자동 제외 |
| 3. Section spec 생성 (6종) | ✅ | text/layout/color 완전 캡처 |
| 4. Asset export | ❌ | 이미지/벡터 실제 데이터 없음 |
| 5. gemini dispatch | ⏹ 중단 | 갭 4로 인한 사전 중단 |
| 6. 4종 게이트 | ⏹ 미실행 | — |
| 7. 수렴 루프 | ⏹ 미실행 | — |

## 3. 발견 갭 상세

### 갭 #1 — `init-project.py --publishing` 이 `.gran-maestro/` 디렉토리 미생성

- **파일**: `tools/init-project.py:41-48`
- **증상**: `--publishing` 플래그 사용 시 `gm_dir.is_dir()` 체크에서 실패하면 config/agents 복사를 silent skip. 결과적으로 "Initialized: CLAUDE.md, .claude/settings.local.json" 만 출력하고 publishing 관련 파일은 복사되지 않음
- **기대 동작**: 스크립트가 `.gran-maestro/` 와 필수 서브디렉토리(`requests/`, `worktrees/`, `plans/`) 를 자동 생성한 뒤 publishing 템플릿을 복사
- **재현**:
  ```bash
  mkdir -p /tmp/test-proj
  python3 tools/init-project.py /tmp/test-proj --type basic --publishing
  # 출력: "Initialized: CLAUDE.md, .claude/settings.local.json"  ← publishing 누락
  ls /tmp/test-proj/.gran-maestro/  # → 디렉토리 자체 없음
  ```
- **우회**: 사용자가 `mkdir -p {project}/.gran-maestro/{requests,worktrees}` 선행 후 재실행

### 갭 #2 — `init-project.py` 결과 안내가 불완전

- 같은 스크립트에서 `.gran-maestro/` skip 여부를 stdout 에 경고하지 않음
- `--publishing` 을 지정했는데 publishing 설정이 적용 안 된 것을 사용자가 알 방법 없음
- **개선안**: `.gran-maestro/` 미존재 시 명시적 에러(exit 1) 또는 자동 생성

### 갭 #3 — 섹션별 asset_manifest vs 통합 manifest

- `figma-section-spec.py --emit-asset-manifest` 는 `{section}_asset_manifest.json` 만 생성
- `figma-validate.py` 는 섹션별 파일을 기대 (`spec_dir.glob(f"{section_name}_asset_manifest.json")`) — **이미 정합적**
- CLAUDE.md / PLN-011 spec 에서 언급한 `asset_manifest.json` (통합 파일) 은 실제 파이프라인에 존재하지 않음 — 문서 수정 필요
- 카테고리: **문서 불일치** (실제 버그 아님)

### 갭 #4 — VECTOR 노드 geometry 미추출 **(CRITICAL)**

- **파일**: `tools/figma-section-spec.py` — vector_node 추출 로직
- **증상**: 각 VECTOR 노드가 spec.json 에 아래와 같이 저장됨:
  ```json
  {
    "id": "203:14779",
    "name": "arrow_R",
    "type": "VECTOR",
    "fills_color": null,
    "viewBox": { "width": null, "height": null },
    "fillGeometryPathData": [],
    "strokeGeometryPathData": []
  }
  ```
  - `fillGeometryPathData: []` 빈 배열
  - `viewBox.width / height: null`
  - `fills_color: null`
- **영향**: 인라인 SVG 렌더 불가 — 구현자가 VECTOR 를 CSS/SVG 로 표현할 근거 데이터가 없음
- **원인 추정**: Figma REST API `/v1/files/{key}/nodes?ids=...` 응답에는 `fillGeometryPathData` 가 기본 포함되지 않음. `/v1/images/{key}?ids=...&format=svg` 엔드포인트로 별도 SVG export 필요
- **해결 방향**:
  - 옵션 A: `figma-section-spec.py` 가 VECTOR 발견 시 images API 로 SVG 다운로드 → `{section}/vectors/{node_id}.svg` 로 저장 + manifest 에 경로 기록
  - 옵션 B: spec.json 에 `path_d` 필드 추가 후 HTML 측에서 `<svg><path d="..."/></svg>` 인라인 렌더

### 갭 #5 — IMAGE 타입 fills 의 실제 파일 미다운로드 **(CRITICAL)**

- **증상**: asset_manifest 의 모든 항목이 아래 형태 (예시: MV 섹션)
  ```json
  {
    "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "kind": "vector",
    "ref": "203:14779",
    "spec_node_id": "203:14779"
  }
  ```
  - `hash` 값이 전부 `e3b0c44...855` = SHA-256 of empty string
  - `local_path` / `url` / `format` 필드 없음
- **영향**: 구현자가 `<img src="...">` 또는 `background-image: url(...)` 에 사용할 경로를 결정할 수 없음
- **원인**: `build_asset_manifest()` 는 노드 메타데이터만 해시하고 실제 이미지 다운로드는 수행하지 않음
- **해결 방향**:
  - `figma-section-spec.py` 에 `--download-assets` 플래그 추가 (또는 `--emit-asset-manifest` 확장)
  - Figma images API 로 PNG/SVG export 후 `img/` 폴더 생성 + manifest 에 `local_path` 기록
  - 해시는 실제 다운로드 바이트 기준 SHA-256 재계산

### 갭 #6 — 파이프라인 CLAUDE.md 문서 vs 실제 동작 차이

- CLAUDE.md `Figma 추출 전 필수 실행` 섹션 #2 단계:
  ```bash
  FIGMA_TOKEN="{token}" python3 D:/dev-base/tools/figma-extract.py \
    --node-id {node-id} --file-key {file-key} --tree --depth 5
  ```
- 실제로는 `figma-section-spec.py --node-id {id} --output extracted/ --emit-asset-manifest` 가 primary 진입점이어야 함 — figma-extract 는 보조 조회 도구
- CLAUDE.md 의 PLN-004 섹션과 일관성 검토 필요

## 4. 파이프라인이 잘 작동한 부분

- **텍스트 추출 충실도**: `text_nodes[].characters` 에 byte-exact 저장 (확인된 일부 섹션에서 NBSP / `\n` 원본 유지)
- **레이아웃 수치**: `frame_nodes[].{paddingTop,paddingRight,paddingBottom,paddingLeft,itemSpacing,layoutMode}` 완전 캡처
- **fills 색상**: hex 형태로 정확히 추출
- **visible:false 자동 제외**: sec_4 (INSTANCE, 숨김 상태) 가 자동으로 `excluded_nodes` 로 분류됨 — 올바른 동작
- **Schema v2 + rules_conflict 필드**: `_extra`, `rules_conflict`, `hints` 등 REQ-030/031/032 메타데이터 정상 기입

## 5. PLN-012 후속 작업 후보

우선순위 순:

1. **(CRITICAL)** `figma-section-spec.py` 에 `--download-assets` 기능 추가 (갭 #4 + #5)
   - VECTOR → Figma images API SVG export → `extracted/{section}/vectors/{node_id}.svg`
   - IMAGE fills → Figma images API PNG export → `extracted/{section}/images/{image_ref}.png`
   - manifest 에 `local_path` + 실제 해시 기록

2. **(HIGH)** `init-project.py` 개선 (갭 #1 + #2)
   - `.gran-maestro/` 자동 생성 (requests/, worktrees/, plans/ 포함)
   - `--publishing` 지정 시 skip 발생하면 exit 1 + 원인 출력

3. **(MEDIUM)** CLAUDE.md 문서 정비 (갭 #3 + #6)
   - 통합 `asset_manifest.json` 언급 제거
   - PLN-004 섹션의 진입점 명확화 (`figma-section-spec.py` primary)

4. **(LOW)** 드릴 런 자동화 스크립트 — `drill-run.py {figma-url} {project-path}` 한 줄로 전체 파이프라인 실행

## 6. 다음 액션

- REQ-043 상태: `spec_ready` (AC-001~003 완료, AC-004~010 미실행) — 파이프라인 갭 해결 후 재시도
- PLN-011 상태: `completed` (드릴 런 목적 달성 — 갭 발견 + 리포트화)
- PLN-012 신규 생성 권장 (갭 #4/#5 해결 중심)

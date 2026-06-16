# Implementation Request — figma-section-spec.py --download-assets

- Request: REQ-044 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-044-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-044/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-012/plan.md
- Prev Feedback: N/A (first run)

## 구현 컨텍스트

REQ-043 드릴 런에서 `figma-section-spec.py` 가 VECTOR 노드 `fillGeometryPathData` 를 빈 배열로만 저장하고 IMAGE fills 실제 파일을 다운로드하지 않는 갭을 발견했다. 이 REQ 에서는 `--download-assets` 플래그를 추가하여 Figma REST images API (`/v1/images/{key}?ids=...&format={svg|png}`) 로 실제 SVG/PNG 파일을 다운로드하고 `{section}_asset_manifest.json` 에 `local_path` + 실제 SHA-256 `hash` + `format` 필드를 기록하게 한다. **하위 호환 필수** — `--no-download-assets` 기본값으로 기존 동작 보존, 기존 테스트 회귀 금지.

[REFERENCE_CONTEXT]
current_date: 2026-04-21
model_cutoff: unknown
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

아래 순서로 원본 파일을 직접 읽고 구현하라. **worktree 내부** (`{worktree_path}`) 에서 작업한다.

1. 스펙 직접 읽기: `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-044/tasks/01/spec.md`
2. 수정 대상 파일 읽기: `tools/figma-section-spec.py` (특히 `build_asset_manifest()` line 723~, manifest 저장 line 2008~), `tools/figma-validate.py` (`validate_asset_manifest` line 462~, `validate_asset_manifest_consistency` line 639~)
3. 기존 테스트 패턴 확인: `tests/` 디렉토리
4. 구현 단계:
   - a. `figma-section-spec.py` 에 `--download-assets` / `--no-download-assets` argparse 플래그 추가 (기본 off)
   - b. `download_assets()` 함수 신설: Figma images API 배치 호출 + 다운로드 + 파일 저장
     - `GET https://api.figma.com/v1/images/{file_key}?ids={comma_separated_ids}&format={svg|png}&scale=1`
     - 응답 JSON 의 `images` 필드: `{node_id: s3_url_or_null}`
     - 각 URL 에서 파일 다운로드 → `{output_dir}/{section}/{vectors|images}/{id_safe}.{ext}`
     - `:` 를 `_` 로 치환한 파일명
   - c. `build_asset_manifest()` 확장: `--download-assets` 가 true 면 각 asset 에 `local_path`, `format`, 실제 파일 SHA-256 `hash` 추가. false 면 기존 동작 (메타데이터 해시) 유지
   - d. `figma-validate.py` `validate_asset_manifest_consistency` 에 `local_path` 필드 기반 검증 분기 추가 (하위 호환: 없으면 기존 node_id 기반)
   - e. 단위 테스트 작성 — `tests/test_figma_section_spec_download.py`:
     - `test_svg_download` — 모킹된 Figma API → SVG 파일 생성 확인
     - `test_png_download` — PNG 시그니처 확인
     - `test_manifest_schema` — local_path/format/hash 필드 존재 확인
     - `test_backward_compat` — 플래그 없이 호출 시 기존 동작
     - `test_download_assets_error_handling` — API 에러 시 graceful fallback
5. 검증 명령 전부 실행:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-044-T01
   pytest tests/test_figma_section_spec_download.py -v
   pytest tests/ -k section_spec
   python3 -m py_compile tools/figma-section-spec.py tools/figma-validate.py
   ```
6. git commit 금지 (PM 이 커밋)

## 규칙 (인라인)

### 작업 범위
- spec §2 범위 외 파일 수정 금지 (tools/figma-section-spec.py, tools/figma-validate.py, tests/ 만)
- 추가 기능 금지 (scale=2, 병렬 다운로드, MCP 등 spec 제외 항목)
- git commit 금지 (PM 이 커밋)
- 완료 전 spec §3 의 모든 AC self-check 필수

### Python 코딩
- Python 3 표준 + `requests` 라이브러리 사용 (이미 import 됨)
- 함수 단위 분리, docstring 간결히
- 에러 핸들링: Figma API 401/404/429/500 → warn + skip (exit 0 유지)
- 429 rate limit → exponential backoff (1→2→4s, max 3 retries)

### 테스트
- pytest AAA 패턴 (Arrange-Act-Assert)
- Figma API mocking 필수 (`unittest.mock` 또는 `responses` 라이브러리)
- 각 테스트는 하나의 동작만 검증
- 80% 커버리지 목표

### 하위 호환 (CRITICAL)
- 기본값 `--no-download-assets` (flag 없으면 기존 동작)
- 기존 `{section}_asset_manifest.json` 포맷 유지 (새 필드만 추가)
- `figma-validate.py` 는 local_path 없는 기존 manifest 도 PASS 해야 함
- `pytest tests/ -k section_spec` 기존 fixture 회귀 없음

## 완료 조건

완료 전 아래 모두 YES:
1. `pytest tests/test_figma_section_spec_download.py -v` 모든 테스트 PASS
2. `pytest tests/ -k section_spec` 기존 fixture 전부 PASS (회귀 없음)
3. `python3 -m py_compile tools/figma-section-spec.py tools/figma-validate.py` 성공
4. spec §3 의 AC-001~006 전부 self-check 통과
5. `--help` 출력에 `--download-assets` 플래그 문서화됨

## 에러 / 피드백 대응

실패 시 stderr/stdout 전체를 worktree 내 `running.log` 에 기록. PM 이 재외주 프롬프트를 생성한다.

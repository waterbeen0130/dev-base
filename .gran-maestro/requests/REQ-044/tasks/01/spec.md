# REQ-044 Task 01 — figma-section-spec.py --download-assets 구현

- 소속 REQ: REQ-044 (PLN-012 Phase A)
- 생성일: 2026-04-21
- Assigned Agent: `[config: codex-dev] → codex-dev` (백엔드 Python, 테스트 포함)

## §0 Context Manifest

- `/mnt/d/dev-base/tools/figma-section-spec.py` — 수정 대상 (line 723~ `build_asset_manifest()`, line 2008~ manifest 저장 로직)
- `/mnt/d/dev-base/tools/figma-validate.py` — `asset_manifest_consistency` 검증 로직 (line 462~, 639~)
- `/mnt/d/dev-base/rules/models.py` — Pydantic SSOT (스키마 확장 시 동기화)
- `/mnt/d/dev-base/rules/validation_schema.json` — 검증 스키마 (자동 생성 대상)
- `/mnt/d/dev-base/tests/` — 기존 테스트 위치 (신규 테스트 추가)
- `/mnt/d/dev-base/.gran-maestro/plans/PLN-012/plan.md` — 상위 plan
- `/mnt/d/dev-base/.gran-maestro/requests/REQ-043/tasks/01/drill-report.md` — 갭 분석 리포트

## §1 요약

`figma-section-spec.py` 에 `--download-assets` 플래그를 추가하여 Figma REST images API 로 VECTOR 노드를 SVG 파일로, IMAGE 타입 fills 를 PNG 파일로 실제 다운로드하고 `{section}_asset_manifest.json` 에 `local_path`, 실제 SHA-256 `hash`, `format` 필드를 기록한다. `figma-validate.py` 의 `asset_manifest_consistency` 검증을 `local_path` 기반으로 동작하도록 확장하되 하위 호환 fallback 유지한다. `--no-download-assets` 기본값으로 기존 동작 보존.

## §2 범위

**포함**
- `figma-section-spec.py` 에 `--download-assets` / `--no-download-assets` 플래그 추가 (기본 off)
- Figma images API 호출: `GET /v1/images/{file_key}?ids={node_ids}&format={svg|png}&scale=1`
- 다운로드 결과를 `extracted/{section}/vectors/{node_id_safe}.svg` + `extracted/{section}/images/{image_ref}.png` 로 저장 (`:` → `_` 치환)
- `build_asset_manifest()` 확장: 각 asset 에 `local_path`, 실제 SHA-256 `hash`, `format` 필드 추가
- Figma API 실패 시 graceful fallback (warn + 메타데이터만 기록)
- `figma-validate.py` `asset_manifest_consistency` 에 `local_path` 기반 검증 추가 (하위 호환: `local_path` 없으면 기존 node_id 기반)
- 단위 테스트: 신규 함수 (80% 커버리지)
- 회귀 fixture: 기존 `tests/` 에 `--no-download-assets` 기본값으로 호출하는 fixture 가 변경 없이 통과

**제외**
- Figma MCP 다운로드
- Raster 이미지 리사이징/최적화
- scale=2 (Retina) 옵션
- 병렬 다운로드 (순차로 충분)
- `rules/models.py` 변경 (하위 호환 필드 추가만, 기존 필드 유지)

## §3 수락 조건 (AC)

### AC-001 `[automatable]` `[tdd-required]` — --download-assets 플래그 + SVG 다운로드

- **Given**: `FIGMA_TOKEN` 환경변수 + MAIN 페이지의 VECTOR 노드가 포함된 섹션
- **When**: `python3 tools/figma-section-spec.py --file-key K --node-id N --output extracted/ --download-assets --emit-asset-manifest` 실행
- **Then**: `extracted/{section}/vectors/{node_id_safe}.svg` 파일이 생성되고, 파일 크기 > 0, SVG 헤더 포함 (`<svg`)
- **Test**: `python3 -c "import os; assert os.path.getsize('extracted/test/vectors/203_14779.svg') > 100 and open('extracted/test/vectors/203_14779.svg').read().startswith('<svg')"`

### AC-002 `[automatable]` `[tdd-required]` — PNG 다운로드

- **Given**: IMAGE 타입 `fills_v2` 를 가진 frame 이 포함된 섹션
- **When**: 동일 명령 실행
- **Then**: `extracted/{section}/images/{image_ref}.png` 파일이 생성되고 PNG 시그니처(`\x89PNG`) 포함
- **Test**: `python3 -c "import os; f=open('extracted/test/images/{hash}.png','rb').read(8); assert f[:4] == b'\\x89PNG'"`

### AC-003 `[automatable]` `[tdd-required]` — manifest 스키마 확장

- **Given**: `--download-assets` 실행 후 생성된 `{section}_asset_manifest.json`
- **When**: JSON 파싱
- **Then**: 각 asset 항목에 `local_path` (spec 기준 상대경로), `format` (`svg` 또는 `png`), `hash` (다운로드된 파일 바이트의 실제 SHA-256, 64자 hex) 필드 존재. `hash` 가 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (빈 문자열 해시) 가 아님
- **Test**: `python3 -c "import json, hashlib; d=json.load(open('extracted/test_asset_manifest.json')); a=d['assets'][0]; assert 'local_path' in a and 'format' in a and len(a['hash']) == 64 and a['hash'] != 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'"`

### AC-004 `[automatable]` `[tdd-required]` — 하위 호환

- **Given**: 기존 호출 (플래그 없음)
- **When**: `python3 tools/figma-section-spec.py --file-key K --node-id N --output extracted/ --emit-asset-manifest` (플래그 미지정)
- **Then**: 기존 동작 유지 — manifest 에 `local_path`/`format` 없음, `hash` 는 기존 node 메타데이터 해시
- **Test**: 기존 `tests/` fixture 가 변경 없이 통과 (`pytest tests/ -k section_spec`)

### AC-005 `[automatable]` — validator 하위 호환 fallback

- **Given**: 두 종류의 manifest (신규 `local_path` 포함 / 기존 `local_path` 없음)
- **When**: `figma-validate.py --spec ... --html ... --css ...` 실행
- **Then**: 둘 다 `asset_manifest_consistency` 검증 통과 (신규는 `local_path` 기반, 기존은 node_id 기반)
- **Test**: `pytest tests/test_validator_asset_manifest.py -v` 전부 PASS

### AC-006 `[automatable]` — Figma API 실패 graceful fallback

- **Given**: Figma API 가 401/404/429/500 반환 또는 네트워크 오류
- **When**: `--download-assets` 실행
- **Then**: 해당 노드는 skip + stderr 경고, manifest 에 메타데이터만 기록 (`local_path` 없음), exit 0 유지 (전체 실패 아님)
- **Test**: `pytest tests/test_download_assets_error_handling.py -v`

## §3.2 Intent Trace

| AC ID | 의도 근거 |
|---|---|
| AC-001 | PLN-012 PAC-1 — SVG export 필수 |
| AC-002 | PAC-2 — PNG export 필수 |
| AC-003 | PAC-3 — manifest 스키마 확장 |
| AC-004 | PAC-4 — 하위 호환 |
| AC-005 | PAC-6 — validator 정합성 |
| AC-006 | PLN-012 리스크 레지스터 — API rate limit / 에러 복원력 |

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-1 | MUST | AC-001 | FULL |
| PAC-2 | MUST | AC-002 | FULL |
| PAC-3 | MUST | AC-003 | FULL |
| PAC-4 | MUST | AC-004 | FULL |
| PAC-6 | MUST | AC-005 | FULL |
| PAC-9 | SHOULD | AC-006 | PARTIAL (로그 기록 부분) |

REQ-045 담당: PAC-5, PAC-7. REQ-046 담당: PAC-8, PAC-9 (실행 로그).

## §3.5 제약사항

- Python 3 + 기존 dev-base `requests` 라이브러리
- Figma API rate limit: 429 응답 시 exponential backoff (1s → 2s → 4s, max 3회)
- 다운로드 파일 크기 상한 10MB (그 이상은 skip + warn)
- `rules/models.py` (Pydantic) 동기화 필수 — `local_path`, `format` 필드를 Optional 로 추가하여 기존 파일도 유효
- Figma MCP 직접 해석 금지 (REST API only)
- `max_cli_retries=2` 준수 (config.json)

## §4 Assigned Agent

- **Primary**: `codex-dev` (백엔드 Python, TDD, 테스트 프레임워크 pytest)
- **Rationale**: Python 로직 + 단위 테스트 + API 통합 — codex capabilities (code, refactor, test) 에 완전 부합

## §5 Test Plan

### 테스트 실행 명령

```bash
# 단위 테스트
pytest tests/test_figma_section_spec_download.py -v
pytest tests/test_validator_asset_manifest.py -v
pytest tests/test_download_assets_error_handling.py -v

# 회귀 fixture
pytest tests/ -k section_spec
```

### 타입 체크

```bash
python3 -m py_compile tools/figma-section-spec.py tools/figma-validate.py
```

### 통합 수동 테스트

```bash
cd /tmp && mkdir -p test_proj/extracted && cd test_proj
FIGMA_TOKEN="..." python3 /mnt/d/dev-base/tools/figma-section-spec.py \
  --file-key JLCP6dWG63kJVBlND7bVZl --node-id 203:14765 --name MV \
  --output extracted/ --emit-asset-manifest --download-assets
ls extracted/MV/vectors/  # SVG 파일 존재
ls extracted/MV/images/   # PNG 파일 존재 (있다면)
cat extracted/MV_asset_manifest.json | python3 -m json.tool  # local_path 확인
```

## Test Scenarios (Pre-Impl)

| AC ID | 실행 명령 / 확인 방법 |
|---|---|
| AC-001 | `pytest tests/test_figma_section_spec_download.py::test_svg_download` → PASS + 생성된 SVG 파일 헤더 확인 |
| AC-002 | `pytest tests/test_figma_section_spec_download.py::test_png_download` → PASS + PNG 시그니처 확인 |
| AC-003 | `pytest tests/test_figma_section_spec_download.py::test_manifest_schema` → PASS |
| AC-004 | `pytest tests/ -k section_spec` (기존 fixture) → 전부 PASS 유지 |
| AC-005 | `pytest tests/test_validator_asset_manifest.py` → 신규/구 manifest 둘 다 통과 |
| AC-006 | `pytest tests/test_download_assets_error_handling.py` → API 오류 모킹 시 graceful fallback |

## §6 선행/후행

- blockedBy: 없음
- blocks: REQ-046 (REQ-C 디에스솔루션 재시도)

## §12 Intent (JTBD)

- **When I**: REQ-043 드릴 런에서 Figma 에셋이 파이프라인으로 다운로드되지 않는 것을 발견했을 때
- **I want to**: `figma-section-spec.py` 가 VECTOR/IMAGE 를 실제 SVG/PNG 파일로 다운로드하고 manifest 에 local_path 를 기록하게 하고
- **So I can**: HTML/CSS 구현자가 `<img src>` / `<svg>` 렌더에 쓸 수 있는 로컬 경로를 얻어 시각적으로 완성된 결과물을 만들 수 있다

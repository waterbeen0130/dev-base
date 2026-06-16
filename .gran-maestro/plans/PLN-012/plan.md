# PLN-012 — REQ-043 드릴 런 갭 4건 해결 (Figma 에셋 + init-project 하드닝)

- 생성일: 2026-04-21
- Cynefin: Complicated
- 상태: active
- 근거 리포트: `.gran-maestro/requests/REQ-043/tasks/01/drill-report.md`

## 1. 요청 (Refined)

REQ-043 드릴 런에서 발견된 파이프라인 갭 4건(CRITICAL 2 + HIGH 2)을 해결한다. 핵심은 **Figma 에셋(SVG 벡터 + PNG 이미지) 실제 다운로드** 기능을 `figma-section-spec.py` 에 추가하여 HTML/CSS 구현자가 `<img src>` / `<svg>` 에 쓸 수 있는 로컬 경로를 제공하는 것이다. 부차적으로 `init-project.py` 의 `.gran-maestro/` 자동 생성 기능도 추가한다. 해결 후 REQ-043 (디에스솔루션 MAIN) 재시도로 end-to-end 파이프라인이 통과하는지 재검증한다.

## 2. 범위

**포함 (PLN-012)**
- `tools/figma-section-spec.py` 에 `--download-assets` 플래그 추가
  - VECTOR 노드 → Figma images API SVG export → `extracted/{section}/vectors/{node_id}.svg`
  - IMAGE 타입 fills → Figma images API PNG export → `extracted/{section}/images/{image_ref}.png`
  - asset_manifest 에 `local_path` + 실제 SHA-256 해시 기록
- `tools/init-project.py` 에 `.gran-maestro/` 자동 생성 로직 추가 (`requests/`, `worktrees/`, `plans/` 포함)
- `--publishing` 지정 시 config/agents 복사 실패하면 exit 1 + 원인 출력
- CLAUDE.md 문서 정비 (통합 `asset_manifest.json` 언급 제거, PLN-004 섹션 진입점 명확화)
- 회귀 테스트: 기존 모제림/디에스솔루션 spec 파일이 변경 없이 그대로 생성되는지 확인
- 완료 후 REQ-043 재시도 (별도 REQ 로 생성, PLN-012 scope 에 포함)

**제외**
- Figma MCP 기반 에셋 다운로드 (REST API 만 사용)
- Raster 이미지의 리사이징/최적화
- CDN 업로드
- 이미지 포맷 변환 (SVG/PNG 그대로)
- 모제림 프로젝트 기존 output 재생성

**시작점 힌트**
- `tools/figma-section-spec.py` — `build_asset_manifest()` 함수 확장 (line 723~)
- `tools/init-project.py` — `init_project()` 함수 (line 15~)
- `rules/templates/publishing/impl-request.md` — 이미지 경로 규칙 업데이트
- Figma API: `GET /v1/images/{key}?ids={node_ids}&format={svg|png}&scale={1|2}`

## 3. 결정 사항

### 에셋 다운로드 범위

- **VECTOR 노드**: SVG 형식 우선 (벡터는 해상도 독립)
- **IMAGE fills**: PNG 형식 우선 (기본 scale=1, 레이아웃 수치 일치)
- 배치 요청: 한 섹션의 모든 VECTOR/IMAGE 를 단일 API 호출로 묶음 (Figma API `ids=` 다중 지원)

### 파일 경로 구조

```
extracted/
  {section}/
    vectors/
      203_14779.svg
      203_14787.svg
    images/
      abc123hash.png
  {section}_spec.json
  {section}_spec.md
  {section}_asset_manifest.json  (local_path 업데이트)
```

- 섹션별 서브디렉토리로 충돌 방지
- node_id 의 `:` 는 `_` 로 치환 (파일 시스템 호환)

### asset_manifest 스키마 확장

```json
{
  "assets": [
    {
      "ref": "203:14779",
      "kind": "vector",
      "format": "svg",
      "local_path": "./MV/vectors/203_14779.svg",
      "hash": "a3f4...실제SHA256",
      "spec_node_id": "203:14779",
      "figma_url": "https://s3-alpha-sig.figma.com/..." 
    }
  ]
}
```

- `format`: `svg` | `png` 추가
- `local_path`: spec 파일 기준 상대경로
- `hash`: 실제 다운로드 바이트의 SHA-256 (기존 빈 문자열 해시 대체)
- `figma_url`: Figma images API 응답의 S3 URL (참조용, 실제 로컬 파일 사용)

### 하위 호환

- `--download-assets` 플래그 없으면 기존 동작 유지 (manifest 에 `local_path` 없음, hash 는 node_id 메타데이터 해시)
- 기본값은 `--no-download-assets` (breaking change 방지)

### init-project.py 개선 방향

1. `.gran-maestro/` 존재 확인 → 없으면 자동 생성 + `requests/` `worktrees/` `plans/` 서브디렉토리
2. `--publishing` + publishing 템플릿 미존재 시 exit 1
3. 초기화 결과 상세 출력 (skip 항목 명시)

### REQ 분리 방침

- **REQ-A**: `figma-section-spec.py --download-assets` 구현 + 회귀 테스트 (CRITICAL 2건)
- **REQ-B**: `init-project.py` 하드닝 + 문서 정비 (HIGH 2건 + 문서 1건)
- **REQ-C**: REQ-043 재시도 (디에스솔루션 MAIN 재실행) — REQ-A 완료 후 blockedBy

3 REQ 체인. REQ-A 가 가장 큼 (Figma API 호출 + 파일 다운로드 + 스키마 변경).

## 4. 인수 기준 초안

이 plan 의 구현이 완료됐다는 것은:

- [MUST] [TIER-A] `figma-section-spec.py --download-assets` 실행 시 VECTOR 노드에 대해 Figma images API 로 SVG 파일이 `extracted/{section}/vectors/{node_id_safe}.svg` 에 저장된다
- [MUST] [TIER-A] 같은 플래그 사용 시 IMAGE 타입 fills 에 대해 PNG 파일이 `extracted/{section}/images/{image_ref}.png` 에 저장된다
- [MUST] [TIER-A] `{section}_asset_manifest.json` 의 각 asset 항목에 `local_path` + 실제 SHA-256 `hash` + `format` 필드가 기록된다
- [MUST] [TIER-A] `--download-assets` 미지정 시 기존 동작이 그대로 유지된다 (기존 spec 파일 회귀 테스트 통과)
- [MUST] [TIER-A] `init-project.py` 가 `.gran-maestro/` 미존재 시 자동 생성하고, `--publishing` 실패 시 exit 1
- [MUST] [TIER-A] `figma-validate.py` 의 `asset_manifest_consistency` 검증이 `local_path` 필드 기반으로 동작 (하위 호환 fallback 포함)
- [SHOULD] [TIER-B] CLAUDE.md 의 통합 `asset_manifest.json` 언급이 제거되고 per-section 구조로 명시됨
- [SHOULD] [TIER-B] 디에스솔루션 MAIN REQ-043 재시도가 4종 게이트 전부 exit 0 통과
- [SHOULD] [TIER-B] 실행 로그(`running.log`)에 다운로드 대상 수 + 소요 시간이 기록된다

## 5. 범위 예산 (Appetite)

- 1차 구현 시간 상한: 8시간 (REQ-A 5시간 + REQ-B 1시간 + REQ-C 2시간)
- 외주 호출 상한: codex-dev max_cli_retries=2
- Figma API rate limit 고려 (요청당 한 섹션 내 모든 노드 배치)

## 6. 제외 범위 (No-go Scope)

- Figma MCP 다운로드 경로 (REST API 만 사용)
- Raster 이미지 리사이징/최적화/변환
- CDN 업로드 또는 외부 스토리지
- 기존 완성 프로젝트(모제림) output 재생성
- 다국어 text 추출 변경

## 7. 제약사항

**기술적**
- Figma API 토큰 필요 (`FIGMA_TOKEN` 환경변수)
- Python 3 표준 라이브러리 + `requests` (이미 dev-base 에 존재)
- 스키마 변경 시 `rules/models.py` (Pydantic SSOT) + `rules/validation_schema.json` 동기화 필요 (REQ-035 정합성)

**비즈니스**
- 완성된 모제림 프로젝트 파이프라인 회귀 금지 (기존 `--no-download-assets` 동작 보존)
- 다운로드 실패 시 graceful fallback (메타데이터만 기록, 경고 출력)

## 8. 우선순위 (MoSCoW)

- **Must**: `--download-assets` 구현, manifest 스키마 확장, `init-project.py` 하드닝, 회귀 테스트, REQ-043 재시도
- **Should**: CLAUDE.md 문서 정비, 다운로드 로그, Figma API 에러 복원력
- **Could**: 이미지 `@2x` 옵션, scale 플래그, 병렬 다운로드
- **Won't**: MCP 연동, 이미지 최적화, CDN 연동

## 9. 의존성

- 선행 필요: 없음 (PLN-010 완료 상태)
- 연관: PLN-011 (REQ-043 드릴 런이 소재 제공), PLN-009 (Pydantic SSOT 정합성)

## 10. 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| Figma images API rate limit | 중 | 중 | 섹션당 배치 요청, 429 시 exponential backoff |
| 대용량 섹션 다운로드 메모리 스파이크 | 낮 | 중 | stream download, 섹션 단위 처리 |
| 스키마 변경으로 기존 spec 회귀 | 중 | 상 | `--no-download-assets` 기본값 유지, 회귀 fixture 테스트 |
| SVG 파스 파싱 실패 시 빈 파일 | 낮 | 중 | HTTP 200 + non-empty body 확인, 실패 시 skip + warn |
| `rules/models.py` 정합성 깨짐 | 중 | 상 | Pydantic 모델 업데이트 포함, build-rules.py 회귀 |

## 11. Loop 종료 조건

- 기존 검증 통과 (AC + max_iterations=2)
- REQ-C (디에스솔루션 재시도) 4종 게이트 전부 exit 0 = 전체 plan 성공

## 12. 테스트 전략

- 적용 (80% 커버리지) — `tools/figma-section-spec.py` 신규 함수 단위 테스트 필수
- 회귀 fixture: 기존 `tests/` 의 figma-section-spec fixture 가 `--no-download-assets` 기본값으로 변경 없이 통과
- E2E: 디에스솔루션 MV 섹션 `--download-assets` 실행 → SVG/PNG 파일 존재 확인

## 13. 분리 실행

### ① REQ-A: figma-section-spec.py --download-assets 구현
- Codex-dev 배정 (백엔드 로직, 테스트 포함)
- 입력: Figma images API 사용법, 기존 `build_asset_manifest()` 함수
- 출력: 신규 플래그 + 다운로드 로직 + manifest 확장 + 테스트
- blockedBy: 없음

### ② REQ-B: init-project.py 하드닝 + 문서 정비
- Claude-dev 배정 (소규모 인라인 수정, .py + .md)
- 입력: 기존 `init_project()` 함수, CLAUDE.md PLN-004 섹션
- 출력: `.gran-maestro/` 자동 생성 + 명시적 에러 + CLAUDE.md 수정
- blockedBy: 없음 (REQ-A 와 병렬)

### ③ REQ-C: 디에스솔루션 MAIN REQ-043 재시도
- Gemini-dev 배정 (퍼블리싱, HTML/CSS)
- 입력: `--download-assets` 로 재생성된 spec 파일 + 다운로드된 SVG/PNG
- 출력: `output/a_main/index.html` + `common.css` + `img/`, 4종 게이트 전부 통과
- blockedBy: [REQ-A] (다운로드 기능 필요)

## 14. Intent (JTBD)

- **When I**: REQ-043 드릴 런에서 파이프라인의 에셋 export 갭을 발견했을 때
- **I want to**: Figma 에셋을 자동 다운로드하여 HTML/CSS 구현자에게 로컬 경로를 제공하고, init-project 의 실패 모드를 명시적으로 개선하고 싶다
- **So I can**: 디에스솔루션 MAIN 재시도에서 4종 게이트 전부 통과하는 **시각적으로 완성된** HTML/CSS 를 자동 생성할 수 있고, 향후 모든 퍼블리싱 프로젝트에서 동일한 end-to-end 파이프라인을 reliably 사용할 수 있다

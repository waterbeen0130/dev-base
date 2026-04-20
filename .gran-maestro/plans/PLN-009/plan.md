# Plan: PLN-009

**생성일**: 2026-04-19T05:10:24.000Z
**주제**: Figma→Code 파이프라인 v2 확장 (spec v2 + validator drift 제거 + deterministic 공식화) — Phase A
**Cynefin 도메인**: Complicated
**연관**: IDN-002 (ideation synthesis), PLN-008 (선행 완료, DBG-001 후속)

---

## 요청 (Refined)

IDN-002 synthesis §E 실행 로드맵 Top 6을 기반으로, "Figma와 완전 동일한 추출물"이라는 목표를 **"결정적(deterministic) 의미론적 동일성 + 주요 시각 속성 1:1 매핑"** 으로 재정의하고, 이를 달성하기 위한 **Phase A — spec v2 dict 확장 + validator drift 제거 + 하위호환 migration**을 단일 PLN으로 구현한다.

Phase B (Pydantic SSOT), Phase C (structural diff gate) 는 본 plan에서 명시적으로 제외한다.

## 범위 예산 (Appetite)

2주+ (6개 REQ 병렬/순차 혼합 실행)

## 제외 범위 (No-go Scope)

- Phase B — Pydantic SSOT 전환, JSON Schema 자동 파생
- Phase C — structural diff gate, DOM tree hash 기반 시각 검증
- constraints → CSS position:absolute 변환 (정책 2에 따라 spec 추출만 하고 CSS 매핑 없음)
- componentId/componentSetId 기반 인스턴스 재사용(클래스 공유) 로직 — 필드 추출까지만, 재사용 구현은 후속 plan
- Figma 외 타 디자인 도구(Sketch, XD) 지원
- pixel-exact 렌더링 비교

## 결정 사항

| 항목 | 결정 | 근거 |
|------|------|------|
| plan 범위 | Phase A 전체 (8축 + migration + 정책 3건 + drift 제거) 단일 PLN | 사용자 Q&A |
| 정책 처리 방식 | 이번 plan에서 즉시 결정 후 plan.md에 고정 | 사용자 Q&A |
| 정책 1 — VERTICAL itemSpacing | margin-bottom 으로 치환 (rules.yaml column flex gap 금지 유지) | 사용자 Q&A |
| 정책 2 — constraints 도입 | 도입하지 않음. spec 에는 추출만, CSS 매핑은 생성하지 않음 | 사용자 Q&A (flexbox 전용 원칙 유지) |
| 정책 3 — spec vs rules 우선순위 | rules 승. Figma 값이 rules 위반을 유발하면 spec 에 `rules_conflict` 메타 기록 후 rules 원칙 유지 | 사용자 Q&A |
| migration 범위 | 전체 프로젝트 스캔 + v1 → v2 재생성 스크립트 제공 | 사용자 Q&A |
| drift 감지 실행 위치 | post-impl-verify 사이클 안에 내장 | 사용자 Q&A |
| 새 Python 의존성 | stdlib 전용 (Phase A). jsonschema/Pydantic 은 Phase B로 유보 | 사용자 Q&A |
| schema_version | 숫자 `1` → 문자열 `"2.0.0"` semver. validator 는 v1/v2 분기 | IDN-002 synthesis §D Phase A |
| 결정성 규칙 | `round(val, 3)`, `#rrggbb` 소문자, children index 순서, 값 없어도 key 유지하고 `null` | IDN-002 synthesis §D Determinism |
| 목표 재정의 | "픽셀 완전 동일"이 아니라 "결정적 의미론적 동일성 + 주요 시각 속성 1:1 매핑" | IDN-002 critic 지적 (§A) |

## 범위

**포함**:

A. **선결 정책 3건 문서화 + schema_version semver 전환 + migration 스크립트**
B. **spec v2 — fills[] type 분기(SOLID/GRADIENT_LINEAR/GRADIENT_RADIAL/IMAGE) + effects[] + opacity + blendMode**
C. **spec v2 — strokes/strokeWeight/strokeAlign + rectangleCornerRadii(개별 corner) + layoutSizing*/layoutGrow/layoutAlign + characterStyleOverrides + textCase + textDecoration + paragraphSpacing**
D. **componentId/componentSetId 필드 추출 (재사용 구현은 제외) + vector SVG path 메타 추출 + asset manifest (hash 기반)**
E. **validator drift 제거 — rules.yaml ↔ validation_schema.json ↔ 핸들러 3자 정합성 + `_stub_handler` PASS 금지 + `no_clamp_under_100`/`meaningful_page_name` 등 불일치 항목 수정**
F. **post-impl-verify 강화 + repair-from-violations 위반 JSON 계약 고정 + figma-validate 신규 축 대응**

**제외**: 위 "제외 범위" 섹션 참조.

## 제약 & 가정

- Python 3 + stdlib 만 사용 (Phase A). 외부 라이브러리 추가 금지.
- 기존 `tools/figma-section-spec.py`, `tools/figma-validate.py`, `tools/validate-semantic.py`, `tools/post-impl-verify.py`, `tools/repair-from-violations.py` 는 수정 허용. 삭제/재명명은 호환 유지 가능할 때만.
- `extracted/section_03_spec.json`, `extracted/section_04_spec.json` 등 기존 산출물은 migration 스크립트로 재생성한다. 원본 텍스트/색/레이아웃 값은 그대로 유지되고 "신규 필드만 추가"된다는 **add-only diff** 가 기본 가정이다.
- CLAUDE.md 의 "PM은 직접 코드 수정 금지" 원칙을 유지한다. 모든 구현은 외주 에이전트(codex-dev / gemini-dev) dispatch 로 진행한다.
- `rules.yaml` 과 `validation_schema.json` 간 drift 해소 시 "사람 규칙(common.md)" 은 변경하지 않고 엔진 측 메타만 정렬한다.
- migration 실패 시 기존 `extracted/` 를 덮어쓰지 않고 `extracted.v1.backup/` 디렉토리를 만들어 자동 백업한다 (rollback 가능).

## 테스트 전략

- **적용 여부**: 적용
- **목표 커버리지**: 미설정
- **비고**:
  - `tools/figma-section-spec.py` 의 신규 필드 추출 로직은 mock Figma API 응답 기반 단위 테스트로 검증
  - `tools/figma-validate.py` 의 신규 카테고리는 기존 `extracted/section_03_spec.json` 등 fixture 로 회귀 테스트
  - `tools/post-impl-verify.py` 는 exit code 매트릭스 테이블 테스트(pass/fail/ignore 조합) 로 검증
  - `tools/repair-from-violations.py` 는 위반 JSON 계약 schema 로 contract 테스트

## 참고 컨텍스트

- IDN-002 synthesis: `/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/synthesis.md`
- 선행 PLN-008 (DBG-001 해소): `/mnt/d/dev-base/.gran-maestro/plans/PLN-008/plan.json`
- 핵심 참조 파일:
  - `tools/figma-section-spec.py` (1283줄, 정규화 spec 생성기)
  - `tools/figma-validate.py` (1404줄, 9개 카테고리 검증)
  - `tools/validate-semantic.py` (3051줄, 프로젝트 규칙 검증)
  - `tools/post-impl-verify.py` (461줄, 오케스트레이션 + 심각도 표)
  - `tools/repair-from-violations.py` (438줄, 자동 수리)
  - `rules/rules.yaml`, `rules/validation_schema.json`
- 현재 spec 스키마 샘플: `extracted/section_03_spec.json`, `extracted/section_04_spec.json`

## 연관 컨텍스트

> 상세 내용은 아래 파일을 직접 참조하세요. 내용을 이 파일에 복사하지 않습니다.

| 유형 | ID | 파일 경로 |
|------|----|-----------|
| ideation 합성 | IDN-002 | `.gran-maestro/ideation/IDN-002/synthesis.md` |
| 선행 plan | PLN-008 | `.gran-maestro/plans/PLN-008/plan.json` |
| 선행 debug | DBG-001 | `.gran-maestro/debug/DBG-001/debug-report.md` |

## 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| 하위 호환 migration 누락 시 기존 extracted/*.json 전량 무효화 (critic Top 1) | 상 | 상 | REQ-A 를 최우선 실행. validator v1/v2 분기 파서를 먼저 구현하고 `extracted.v1.backup/` 자동 생성 후 재생성 실행. |
| VERTICAL itemSpacing ↔ rules.yaml column flex gap 금지 규칙 충돌로 재dispatch 루프 (critic Top 2) | 상 | 중 | 정책 1 결정(margin-bottom 치환)을 rules.yaml/validation_schema.json/figma-validate.py/외주 브리프 4곳에 동일 문구로 문서화. |
| 8축 필드 확장 scope 가 1 PLN 에 과부하되어 6 REQ 완결 시간 증가 | 중 | 중 | REQ 분리(A→B+C 병렬→D+E+F 병렬)로 cycle time 단축. REQ-A 완료 후 REQ-B~F 병렬 dispatch 가능. |
| `additionalProperties:true + _extra` 폴백 미설계 시 Figma 신규 필드 유입으로 파싱 실패 (risk-analyst #2-a) | 중 | 상 | spec v2 스키마에 `_extra: object` 키 강제 포함. 알 수 없는 필드는 누락하지 않고 `_extra` 에 보존. |
| Phase A dict 확장만으로 충분한 검증 강도 확보 불가 (Phase B 미루기로 인한 품질 리스크) | 중 | 중 | Phase A 에서도 JSON Schema 텍스트 문서(`schemas/spec_v2.schema.json`)를 수작업으로 유지. Phase B 전환 시 자동 생성으로 교체. |
| validator drift 내장 시 post-impl-verify 실행 시간 증가 | 하 | 하 | drift 체크를 첫 1회만 수행하고 결과를 `.gran-maestro/state/drift-cache.json` 에 캐시. rules.yaml/schema/핸들러 mtime 비교로 invalidation. |

## 분리 실행

> 본 plan 은 6개 독립 REQ 로 분리해 실행한다. REQ-A 는 나머지 REQ 의 전제이므로 가장 먼저 완결되어야 한다. REQ-B~F 는 REQ-A 완료 후 병렬 실행 가능하나 spec 필드 확장 3종(B/C/D)은 동일 파일(`figma-section-spec.py`)을 건드리므로 순차 권장.

| 순서 | 작업 (책임 단위) | 분리 이유 | 병렬 가능 |
|------|-----------------|-----------|-----------|
| ① | **REQ-A: 정책 3건 문서화 + schema_version semver + migration 스크립트 + v1/v2 분기 파서** | 모든 후속 REQ 의 전제. 기존 extracted/ 보호 및 정책 고정 | no (단독 선행) |
| ② | **REQ-B: spec v2 fills[] type 분기 + effects[] + opacity + blendMode** | 8축 중 최대 영향 3축. 가장 많은 실패 시나리오 해소 (#1, #3, #4, #9) | REQ-A 완료 후 |
| ③ | **REQ-C: spec v2 strokes + rectangleCornerRadii + layoutSizing*/Grow/Align + character-style-overrides + textCase + textDecoration + paragraphSpacing** | 8축 중 나머지 5축. figma-section-spec.py 동시 수정 충돌 피하려 REQ-B 이후 | REQ-B 완료 후 |
| ④ | **REQ-D: componentId/componentSetId + vector SVG path 메타 + asset manifest (hash 기반)** | 추출만 하는 보조 필드. 재사용 로직은 제외. | REQ-C 와 병렬 가능 |
| ⑤ | **REQ-E: validator drift 제거 — rules.yaml ↔ validation_schema.json ↔ 핸들러 정합성 + _stub_handler PASS 금지 + 불일치 항목 수정** | 검증 체계 신뢰성 회복. figma-section-spec 과 독립 | REQ-B 와 병렬 가능 |
| ⑥ | **REQ-F: post-impl-verify 강화 (spec skip 제거, semantic MAJOR exit=1) + repair-from-violations 위반 JSON 계약 고정 + figma-validate 신규 축 대응** | REQ-B~E 결과를 consume. 가장 마지막 | REQ-B/C/D/E 전부 완료 후 |

## Loop 종료 조건

- 기존 검증 통과 (기본값): AC 통과 + max_iterations 도달 시 종료. 추가 조건 없음.

## 인수 기준 초안

이 plan 의 구현이 완료됐다는 것은:

- [MUST] [TIER-A] `tools/figma-section-spec.py` 가 생성하는 `spec.json` 의 `schema_version` 필드가 문자열 `"2.0.0"` semver 로 기록된다
- [MUST] [TIER-A] `spec.json` 의 `frame_nodes[].fills` 가 type 분기 구조(`SOLID`/`GRADIENT_LINEAR`/`GRADIENT_RADIAL`/`IMAGE`)로 추출되고, `IMAGE` 타입은 `imageRef`·`scaleMode`·`crop` 을 포함한다
- [MUST] [TIER-A] `spec.json` 의 `frame_nodes[].effects`, `opacity`, `blendMode`, `strokes`, `strokeWeight`, `strokeAlign`, `rectangleCornerRadii`, `layoutSizingHorizontal`, `layoutSizingVertical`, `layoutGrow`, `layoutAlign` 이 비어있지 않은 Figma 노드에 대해 정확히 추출된다
- [MUST] [TIER-A] `spec.json` 의 `text_nodes[].characterStyleOverrides`, `textCase`, `textDecoration`, `paragraphSpacing` 이 Figma 원본의 해당 값을 byte-exact 로 보존한다
- [MUST] [TIER-B] `spec.json` 의 `frame_nodes[].componentId` 와 `componentSetId` 필드가 존재하는 Figma 인스턴스에 대해 채워진다 (재사용 로직은 별도)
- [MUST] [TIER-B] vector 노드의 SVG path 메타와 이미지/아이콘 asset 들은 `asset_manifest` 파일에 hash 기반으로 기록된다
- [MUST] [TIER-A] migration 스크립트를 실행하면 프로젝트 전체의 `extracted/**/*_spec.json` 이 v2 로 재생성되고, 원본은 `extracted.v1.backup/` 에 자동 백업된다
- [MUST] [TIER-A] migration 후 기존 `section_03_spec.json` · `section_04_spec.json` 의 text/color/padding/gap 값이 변경되지 않고 "신규 필드만 추가"되는 add-only diff 만 발생한다
- [MUST] [TIER-A] validator 는 schema_version 이 `1` 인 구 spec 도 warn 만 출력하고 통과시키는 v1/v2 분기 파서를 가진다
- [MUST] [TIER-A] Figma 의 VERTICAL frame + itemSpacing > 0 은 외주 브리프 템플릿(`rules/templates/publishing/impl-request.md`)과 `figma-validate.py`, `validate-semantic.py`, `rules.yaml` 4곳 모두에서 "margin-bottom 으로 치환" 으로 문서화된다
- [MUST] [TIER-A] Figma 의 `constraints` 는 `spec.json` 에 필드로 추출되지만, 외주 브리프와 validator 어디에서도 `position:absolute` CSS 로 매핑하지 않는다 (flexbox 전용 원칙 유지)
- [MUST] [TIER-A] Figma 값이 rules.yaml 규칙 위반을 유발할 때, `spec.json` 의 해당 노드에 `rules_conflict` 메타(`{"rule_id": "...", "figma_value": "...", "applied_value": "..."}`)가 기록되고, validator 는 이 경우 false-positive 없이 PASS 로 처리한다
- [MUST] [TIER-A] `validate-semantic.py` 의 `_stub_handler` 가 제거되거나 skipped 상태를 MAJOR FAIL 로 승격한다. 미구현 핸들러가 은닉된 PASS 로 통과하지 않는다
- [MUST] [TIER-A] `rules.yaml` ↔ `validation_schema.json` ↔ 핸들러 간 drift 는 `post-impl-verify.py` 실행 시 자동 감지되고, 불일치 시 exit=1 로 실패한다
- [MUST] [TIER-A] `selector_single_line`/`media_query_format`/`no_media_indent` 등 schema·핸들러에만 있던 규칙이 `rules.yaml` 에도 추가되거나 제거되어 3자 일치한다
- [MUST] [TIER-A] `no_clamp_under_100` 의 설명과 구현이 일치한다 (설명이 100 이면 구현도 100, 설명이 10 이면 문서 수정)
- [MUST] [TIER-A] `meaningful_page_name` 은 파일명만 검사하도록 수정되거나 HTML 본문 검사를 포함하도록 문서가 수정되어 규칙명 ↔ 구현이 일치한다
- [MUST] [TIER-A] `post-impl-verify.py` 는 spec 파일을 찾지 못해도 자동 skip 하지 않고 exit=1 로 실패한다. 섹션별 spec 을 명시적으로 인자로 받아야 한다
- [MUST] [TIER-A] `post-impl-verify.py` 는 `validate-semantic.py` 가 반환한 MAJOR 위반을 exit=1 로 반영한다 (기존에는 exit=0 으로 통과 가능했음)
- [MUST] [TIER-A] `post-impl-verify.py` 의 IGNORE 전용 exit=2 는 유지하되 의미를 `PASS 이지만 사용자 검수 권장` 으로 명확히 문서화한다
- [MUST] [TIER-A] `repair-from-violations.py` 는 위반 JSON 의 `{rule_id, file, line, expected, actual, fix_strategy, patch_hint}` 전체 필드를 읽고 해당 위치·전략·패치 힌트를 외주 브리프에 그대로 붙여 전달한다 (개수만 사용하지 않는다)
- [MUST] [TIER-B] 자동 재dispatch 는 수렴형 N회 제한을 갖고, 연속 무변경 시 조기 종료한다 (`config.retry.max_cli_retries` 존중)
- [MUST] [TIER-B] 결정성 규칙(`round(val, 3)`, `#rrggbb` 소문자, children index 순서, 값 없어도 key 유지) 을 같은 Figma 노드에 대해 2회 실행하면 byte-exact 동일 `spec.json` 이 나온다
- [MUST] [TIER-B] 전체 작업 완료 후 `extracted/section_03_spec.json`, `extracted/section_04_spec.json` 에 대해 `post-impl-verify.py` 가 exit=0 (또는 IGNORE-only exit=2)로 통과한다
- [SHOULD] [TIER-B] [IMPACT] 기존 landing 프로젝트(`landing/index.html`, `landing/css/*.css`)에 대해 validator drift CI 가 실행되어 기존 통과 상태를 유지한다 (회귀 없음)
- [SHOULD] [TIER-B] `schemas/spec_v2.schema.json` 수작업 JSON Schema 문서가 저장소에 포함되어 Phase B Pydantic 전환의 기초가 된다

---

## Intent (JTBD)

- **When I**: Figma 디자인을 외주 에이전트(codex-dev, gemini-dev)로 HTML/CSS 로 자동 변환할 때
- **I want to**: 현재 spec.json 이 놓치고 있는 8축 시각 속성(fills/effects/strokes/sizing/cornerRadii/textOverrides/component/vector)을 결정적(deterministic)으로 추출하고, rules·schema·핸들러 간 drift 없이 검증 · 수리 파이프라인이 작동하도록
- **So I can**: Figma 원본과 **의미론적으로 동일한** HTML/CSS 를 수작업 보정 없이 지속 가능하게 생산하고, 향후 Phase B (Pydantic SSOT) / Phase C (structural diff) 로 자연스럽게 확장할 수 있다

# Implementation Spec

- Request ID: REQ-030
- Task ID: 01
- Created: 2026-04-19T09:45:00.000Z
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: backend Python] → 최종: codex-dev
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-030-task-01
- Complexity: High-Risk

## §0 Context Manifest

- /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md
- /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/synthesis.md (§C 8축, 특히 fills/effects)
- /mnt/d/dev-base/tools/figma-section-spec.py (REQ-029 후 schema_version 2.0.0, _extra 폴백 도입됨)
- /mnt/d/dev-base/tools/figma-validate.py (v1/v2 분기 파서, v2.fills.type.stub / v2.effects.stub 진입점 존재)
- /mnt/d/dev-base/extracted/section_03_spec.json (v2 baseline)
- /mnt/d/dev-base/extracted/section_04_spec.json (v2 baseline)
- Figma REST API 문서 (필요 시 codex가 직접 참조): fills 타입(SOLID/GRADIENT_LINEAR/GRADIENT_RADIAL/IMAGE), effects 타입(DROP_SHADOW/INNER_SHADOW/LAYER_BLUR/BACKGROUND_BLUR)

## 1. 요약 (Summary)

PLN-009 Phase A 2단계 — `figma-section-spec.py` 의 fills 추출을 type 분기 구조로 확장(SOLID 단순 hex + GRADIENT 의 stops/handles + IMAGE 의 imageRef/scaleMode/crop transform)하고, frame_nodes/text_nodes 에 effects[]·opacity·blendMode 신규 필드를 추출한다. 신규 필드별 검증 카테고리를 figma-validate.py 에 실제 구현(stub → real check)으로 추가한다.

## 2. 범위 (Scope)

- **포함**:
  - `tools/figma-section-spec.py`:
    - `fills[]` 추출을 type 분기 구조로 변경:
      - `SOLID`: `{type, color(hex), opacity?}`
      - `GRADIENT_LINEAR`: `{type, gradientStops:[{position, color}], gradientHandlePositions:[{x,y}*3], opacity?}`
      - `GRADIENT_RADIAL`: 위와 동일 + `radial 메타`
      - `IMAGE`: `{type, imageRef, scaleMode("FILL"/"FIT"/"CROP"/"TILE"), imageTransform, scalingFactor?}`
    - `effects[]` 추출 (frame_nodes + text_nodes 양쪽):
      - 각 항목: `{type("DROP_SHADOW"/"INNER_SHADOW"/"LAYER_BLUR"/"BACKGROUND_BLUR"), visible, color?, offset?:{x,y}, radius, spread?, blendMode?}`
    - frame_nodes/text_nodes 공통 추가 필드: `opacity`(0~1, 1.0 기본), `blendMode`("PASS_THROUGH"/"NORMAL" 등 Figma 원문 그대로)
    - 신규 필드는 누락 시 `null`(top-level) 또는 빈 배열 `[]` (effects/fills) 로 명시
    - 기존 fills 가 단일 hex 문자열이었으면 SOLID dict 1개 배열로 변환 (구조 변경)
  - `tools/figma-validate.py`:
    - `v2.fills.type.stub` → 실제 카테고리 구현: spec.json 의 fills 타입과 CSS 의 background 표현 일치 확인
      - SOLID hex → CSS `background-color: #rrggbb` (또는 `background: #rrggbb`)
      - GRADIENT_LINEAR → CSS `linear-gradient(angle, stops...)` 존재 + 색상 hex 일치
      - GRADIENT_RADIAL → CSS `radial-gradient(...)` 존재
      - IMAGE → CSS `background-image: url(...)` 존재 (URL 패턴만 확인, 실제 다운로드 검증은 X)
    - `v2.effects.stub` → 실제 구현: spec.json effects 의 DROP_SHADOW → CSS `box-shadow`, LAYER_BLUR → CSS `filter: blur()`, BACKGROUND_BLUR → CSS `backdrop-filter: blur()` 일치 확인
    - 신규 카테고리: `v2.opacity.match`, `v2.blendMode.match` (간단 문자열 일치 검증)
- **제외**:
  - strokes, cornerRadii, layoutSizing 등 — REQ-031 (C) 책임
  - componentId, vector — REQ-032 (D) 책임
  - migration — 이미 REQ-029 에서 처리 (extracted.v1.backup/ 자동 생성됨)

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable] [unit-test] [tdd-required]
Given: Figma node 입력에 `fills: [{type:"SOLID", color:{r,g,b}, opacity:1}]` 가 있다
When: figma-section-spec.py 가 spec 을 생성한다
Then: 출력 spec.json 의 frame_nodes[i].fills 가 `[{type:"SOLID", color:"#rrggbb", opacity:1.0}]` (배열, hex 소문자)
Test: pytest tests/unit/test_fills_solid.py

#### AC-002 [MUST] [automatable] [unit-test] [tdd-required]
Given: Figma node 의 fills 가 GRADIENT_LINEAR 타입 (stops 와 handles 포함)
When: spec 생성
Then: spec.json 의 fills 가 `[{type:"GRADIENT_LINEAR", gradientStops:[{position:0.0, color:"#aabbcc"}, {position:1.0, color:"#ddeeff"}], gradientHandlePositions:[{x,y},{x,y},{x,y}]}]` 형태로 보존
Test: pytest tests/unit/test_fills_gradient.py

#### AC-003 [MUST] [automatable] [unit-test] [tdd-required]
Given: Figma node 의 fills 가 IMAGE 타입 (imageRef, scaleMode, imageTransform 포함)
When: spec 생성
Then: spec.json 의 fills 가 `[{type:"IMAGE", imageRef:"<hash>", scaleMode:"FILL", imageTransform:[[a,b,c],[d,e,f]]}]` 형태로 보존
Test: pytest tests/unit/test_fills_image.py

#### AC-004 [MUST] [automatable] [unit-test] [tdd-required]
Given: Figma node 의 effects 에 DROP_SHADOW 1 개 + LAYER_BLUR 1 개
When: spec 생성
Then: spec.json 의 frame_nodes[i].effects 가 두 항목 모두 type/visible/color/offset/radius 포함하여 추출됨
Test: pytest tests/unit/test_effects_extract.py

#### AC-005 [MUST] [automatable] [unit-test] [tdd-required]
Given: Figma node 의 opacity=0.8, blendMode="MULTIPLY"
When: spec 생성
Then: spec.json 의 frame_nodes[i] 에 `opacity:0.8`, `blendMode:"MULTIPLY"` 키 존재
Test: pytest tests/unit/test_opacity_blendmode.py

#### AC-006 [MUST] [automatable] [unit-test]
Given: Figma node 의 effects/opacity/blendMode 가 비어있거나 기본값 (opacity:1, blendMode:"PASS_THROUGH", effects:[])
When: spec 생성
Then: 신규 v2 키는 누락하지 않고 `effects:[], opacity:1.0, blendMode:"PASS_THROUGH"` 로 명시 (결정성 보장)
Test: pytest tests/unit/test_v2_default_keys.py

#### AC-007 [MUST] [automatable] [unit-test]
Given: spec.json 의 fills 가 GRADIENT_LINEAR 이고 매칭 CSS 가 `background: linear-gradient(180deg, #aabbcc, #ddeeff)`
When: figma-validate.py 의 `v2.fills.gradient.match` 카테고리 실행
Then: PASS (색상 hex 일치 + linear-gradient 키워드 존재)
Test: pytest tests/unit/test_validate_gradient.py

#### AC-008 [MUST] [automatable] [unit-test]
Given: spec.json 의 fills 가 IMAGE 이고 매칭 CSS 가 `background-image: url('...');`
When: validate 실행
Then: PASS (background-image url 존재)
Test: pytest tests/unit/test_validate_image.py

#### AC-009 [MUST] [automatable] [unit-test]
Given: spec.json effects 에 DROP_SHADOW 가 있는데 CSS 에 box-shadow 가 없다
When: validate 실행
Then: FAIL — `[V2-EFFECTS] node {id} expected box-shadow for DROP_SHADOW`
Test: pytest tests/unit/test_validate_effects.py

#### AC-010 [MUST] [automatable] [regression-test]
Given: REQ-029 의 extracted/section_03_spec.json (v2 schema_version, 기존 v2 키 존재)
When: figma-section-spec.py 를 다시 실행하여 같은 입력으로 spec 재생성
Then: 기존 키-값 byte-exact 보존 + 신규 v2 키만 추가됨 (add-only diff 유지)
Test: pytest tests/regression/test_req030_add_only.py

#### AC-011 [MUST] [automatable] [unit-test]
Given: 동일 Figma node 입력
When: figma-section-spec.py 를 100 회 실행
Then: 출력 byte-exact 동일 (PAC-23 결정성 유지)
Test: pytest tests/regression/test_determinism.py (REQ-029 기존 테스트 + 신규 v2 필드 검증 확장)

#### AC-012 [MUST] [automatable] [lint-check]
Given: 신규/수정 파일
When: py_compile 실행
Then: 컴파일 에러 0
Test: `python3 -m py_compile tools/figma-section-spec.py tools/figma-validate.py`

## 3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-2  | MUST  | AC-001, AC-002, AC-003 | Full |
| PAC-3  | MUST  | AC-004, AC-005, AC-006 (effects/opacity/blendMode 부분만) | Partial — strokes/cornerRadii 등은 REQ-031 |
| PAC-8  | MUST  | AC-010 | Full |
| PAC-23 | MUST  | AC-011 | Full |
| (SPEC_ONLY) | — | AC-007, AC-008, AC-009, AC-012 | validator 신규 카테고리 + lint |

## 3.5 Constraints

- 호환성: Python 3.10 + stdlib (REQ-029 동일)
- 결정성: 모든 수치 round(val, 3), hex 소문자, children index 순서, null 명시
- 기존 v2 키 변경 금지 (REQ-029 산출물 보호)

## 4. 구현 컨텍스트

- **따라야 할 패턴**: REQ-029 의 v2 dict 확장 패턴 그대로 (additionalProperties:true + _extra 폴백 유지)
- **알아야 할 제약**: figma-section-spec.py 의 normalize 함수들이 fills 를 dict 또는 list 로 처리하는데, 이 PR 에서 list-of-dict 통일 (단일 hex 만 있던 케이스도 `[{type:"SOLID", color:hex}]` 로 변환)
- **접근법 방향**: IDN-002 §C 1·2축 (fills/effects) Top 우선 + critic Top 1 (add-only diff 보존)

## 5. 의존성

- 선행: [REQ-029 (already done, 431d0e3)]
- 후행: [REQ-030/02 (test), REQ-031]

## 6. 에이전트 팀 구성

- 실행: codex-dev (Python tool changes)

## 11. Test Scenarios (Pre-Impl)

| # | AC | 명령 | 기대 |
|---|---|---|---|
| TS-01 | AC-001 | pytest tests/unit/test_fills_solid.py | PASS |
| TS-02 | AC-002 | pytest tests/unit/test_fills_gradient.py | PASS |
| TS-03 | AC-003 | pytest tests/unit/test_fills_image.py | PASS |
| TS-04 | AC-004 | pytest tests/unit/test_effects_extract.py | PASS |
| TS-05 | AC-005 | pytest tests/unit/test_opacity_blendmode.py | PASS |
| TS-06 | AC-006 | pytest tests/unit/test_v2_default_keys.py | PASS |
| TS-07 | AC-007 | pytest tests/unit/test_validate_gradient.py | PASS |
| TS-08 | AC-008 | pytest tests/unit/test_validate_image.py | PASS |
| TS-09 | AC-009 | pytest tests/unit/test_validate_effects.py | PASS |
| TS-10 | AC-010 | pytest tests/regression/test_req030_add_only.py | PASS |
| TS-11 | AC-011 | pytest tests/regression/test_determinism.py | PASS (확장 검증 포함) |
| TS-12 | AC-012 | python3 -m py_compile tools/figma-section-spec.py tools/figma-validate.py | exit 0 |

> TS-01~09 의 fixture/test 파일 일부는 task 02 에서 작성 가능. 본 task (01) 는 구현 + 자체 빠른 unit test 1~2 개 작성 후 task 02 에서 종합 보강.

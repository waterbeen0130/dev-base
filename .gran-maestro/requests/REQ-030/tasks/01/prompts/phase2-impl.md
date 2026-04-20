# Implementation Request — REQ-030/01

- Request: REQ-030 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-030-task-01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-030/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md

## 구현 컨텍스트 (PM 작성)

PLN-009 Phase A 2단계 — REQ-029 의 schema v2 발판 위에서 fills[] 를 type 분기 구조 (SOLID/GRADIENT_LINEAR/GRADIENT_RADIAL/IMAGE)로 확장하고, frame_nodes/text_nodes 에 effects[]·opacity·blendMode 신규 필드를 추출한다. 결정성 (round(val,3), hex 소문자, children index 순서, 누락 시 null/[]/기본값 명시) 과 add-only diff 를 반드시 보존한다. figma-validate.py 의 v2 stub 카테고리 (v2.fills.type.stub, v2.effects.stub) 를 실제 구현으로 교체한다. stdlib 만 사용. 외부 라이브러리 추가 금지.

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-030/tasks/01/spec.md` 전체 Read
2. `cat /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md` 전체 Read (특히 §결정사항, §리스크)
3. `cat /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/synthesis.md` 의 §C (8축 fidelity) 와 §D (Phase A) 참조
4. `tools/figma-section-spec.py` REQ-029 변경사항 (schema_version, _extra 폴백, v1/v2 normalize) 의 흐름 파악
5. `tools/figma-validate.py` 의 v2 stub 카테고리(v2.fills.type.stub 등) 위치 확인
6. `extracted/section_03_spec.json`, `extracted/section_04_spec.json` v2 baseline 으로 fills 구조 확인
7. spec §3 의 12 AC 와 §11 Test Scenarios 12 개 모두 PASS 시킬 것

## Figma REST API 핵심 필드 (참고)

- `fills`: list of paint objects
  - SOLID: `{type:"SOLID", color:{r,g,b,a}, opacity?}`
  - GRADIENT_LINEAR / GRADIENT_RADIAL: `{type, gradientStops:[{position,color}], gradientHandlePositions:[{x,y},{x,y},{x,y}], opacity?}`
  - IMAGE: `{type:"IMAGE", imageRef, scaleMode:"FILL"|"FIT"|"CROP"|"TILE", imageTransform?:[[a,b,c],[d,e,f]], scalingFactor?, rotation?}`
- `effects`: list of effect objects
  - DROP_SHADOW / INNER_SHADOW: `{type, visible, color, offset:{x,y}, radius, spread?, blendMode?}`
  - LAYER_BLUR / BACKGROUND_BLUR: `{type, visible, radius}`
- `opacity`: 0~1 (기본 1)
- `blendMode`: "PASS_THROUGH"/"NORMAL"/"DARKEN"/"MULTIPLY"/"COLOR_BURN" 등 Figma 원문 그대로

## 구현 지침

1. **fills 변환**: 기존 hex 문자열 1 개를 `[{type:"SOLID", color:"#rrggbb", opacity:1.0}]` 배열로 변환 — 반드시 list-of-dict 통일
2. **GRADIENT_LINEAR 추출**: gradientStops 의 color {r,g,b,a} → `#rrggbb` 변환 (alpha 제외, 소문자), position 은 round(val, 3)
3. **IMAGE 추출**: imageRef, scaleMode, imageTransform 그대로 보존
4. **effects 추출**: visible:false 는 그대로 spec 에 보존하되 type 정보는 유지 (validator 가 나중에 visible 필터링)
5. **opacity, blendMode**: 기본값 (1.0, "PASS_THROUGH") 도 명시적으로 출력
6. **add-only diff**: 기존 키 (특히 schema_version 2.0.0, REQ-029 가 추가한 _extra, 기타 v1 키들) 의 값 변경 금지 — 신규 v2 키만 추가
7. **figma-validate.py v2 카테고리**:
   - `v2.fills.solid.match`: SOLID color hex ↔ CSS background-color 일치
   - `v2.fills.gradient.match`: GRADIENT 의 stops color 가 CSS linear-gradient(...) / radial-gradient(...) 안에 모두 hex 로 등장
   - `v2.fills.image.match`: IMAGE → CSS background-image url(...) 존재
   - `v2.effects.shadow.match`: DROP_SHADOW → CSS box-shadow 존재 + offset/radius 수치 일치 (±1px tolerance)
   - `v2.effects.blur.match`: LAYER_BLUR → CSS filter:blur() / BACKGROUND_BLUR → backdrop-filter:blur() 존재
   - `v2.opacity.match`: spec opacity ↔ CSS opacity 수치 일치
   - `v2.blendMode.match`: spec blendMode ↔ CSS mix-blend-mode 일치 (단, "PASS_THROUGH"/"NORMAL" 은 CSS 미선언 허용)
   - 위 카테고리는 v2 분기 진입 시에만 활성화, v1 분기에서는 skip
8. **테스트**: spec §11 Test Scenarios TS-01~12 를 모두 PASS 시킬 것 (TS-01~09 의 fixture 와 unit test 는 task 02 에서 종합 작성하지만 본 task 에서도 빠른 sanity test 1~2 개 작성 후 PASS 확인)

## 규칙

- spec §2 변경 범위 외 파일 수정 금지
- git commit 금지 (PM 처리)
- stdlib 만 사용
- [MANDATORY] 완료 전 `python3 -m py_compile tools/figma-section-spec.py tools/figma-validate.py` + 작성한 sanity unit test 실행 후 출력 응답에 포함
- TDD: AC-001~005 는 [tdd-required] — 테스트 먼저 작성 후 구현
- 모든 변경은 worktree (`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-030-task-01`) 내부에서 수행

# Implementation Request — REQ-031/01

- Request: REQ-031 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-031-task-01
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md
- 선행 commits: REQ-029 (431d0e3), REQ-030 (7fa6cd2)

## 구현 컨텍스트 (PM 작성)

PLN-009 Phase A 3단계 — REQ-029 (semver + v1/v2 분기) 와 REQ-030 (fills_v2 + effects + opacity + blendMode) 위에서 frame_nodes 와 text_nodes 의 추가 fidelity 필드 5축을 한 번에 추출한다:

**frame_nodes 추가 필드**:
1. `strokes[]` (테두리 paint 배열, fills 와 동일 type 분기 구조) + `strokeWeight` + `strokeAlign` ("INSIDE"/"OUTSIDE"/"CENTER")
2. `rectangleCornerRadii` (4개 corner 개별 — `[topLeft, topRight, bottomRight, bottomLeft]` 순서, Figma API 원순서 보존)
3. `layoutSizingHorizontal` ("FIXED"/"HUG"/"FILL") + `layoutSizingVertical` (같음) + `layoutGrow` (0~1) + `layoutAlign` ("INHERIT"/"STRETCH"/"MIN"/"MAX"/"CENTER")

**text_nodes 추가 필드**:
4. `characterStyleOverrides` (인라인 부분 스타일 — Figma 원본 그대로 보존: int 배열, length = characters 길이) + `styleOverrideTable` (override id → style dict)
5. `textCase` ("ORIGINAL"/"UPPER"/"LOWER"/"TITLE"/"SMALL_CAPS"/...) + `textDecoration` ("NONE"/"UNDERLINE"/"STRIKETHROUGH") + `paragraphSpacing` (number, 기본 0) + `paragraphIndent` (number, 기본 0)

`figma-validate.py` 의 신규 v2 카테고리 stub → 실제 구현으로 추가:
- `v2.strokes.match`: strokes type/color/weight ↔ CSS border 일치
- `v2.cornerRadii.match`: 4 개 corner radius ↔ CSS border-top-left-radius/.../border-radius 일치 (단일 값일 때 통합 border-radius 허용)
- `v2.layoutSizing.match`: HUG → CSS fit-content / width:auto, FILL → flex:1 / width:100%, FIXED → 명시 width
- `v2.textCase.match`: textCase ↔ CSS text-transform
- `v2.textDecoration.match`: textDecoration ↔ CSS text-decoration

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. plan + 선행 REQ-029/030 의 변경사항 확인 (`tools/figma-section-spec.py`, `tools/figma-validate.py`)
2. 이미 작성된 v2 카테고리 (REQ-030) 의 패턴 (예: `v2.fills.solid.match`) 을 참고하여 동일 패턴으로 신규 카테고리 추가
3. characterStyleOverrides 는 한국어 텍스트 + 인라인 굵기/색 케이스가 까다롭다 — IDN-002 synthesis §C-d 와 critic 의 risk-analyst 시나리오 참조

## 핵심 구현 지침

1. **strokes**: fills 와 동일 type 분기 구조 (SOLID/GRADIENT 우선 지원, IMAGE strokes 는 드물어 graceful skip 가능). strokeWeight 는 number, strokeAlign 은 enum 그대로.
2. **rectangleCornerRadii**: Figma 가 단일 `cornerRadius` 만 가지면 4개 동일값 배열로 변환. 개별 값 (`rectangleCornerRadii: [N, N, N, N]`) 가 있으면 그대로.
3. **layoutSizing/Grow/Align**: enum 이 없으면 기본값 추출 (`layoutSizingHorizontal: "FIXED"`, `layoutGrow: 0`, `layoutAlign: "INHERIT"`)
4. **characterStyleOverrides**: Figma API 원본 (int[] + dict map) 을 그대로 spec 에 보존 — AI 구현자가 나중에 styleOverrideTable 로 lookup 가능
5. **textCase / textDecoration / paragraphSpacing / paragraphIndent**: 모두 명시적으로 출력 (기본값 포함, "ORIGINAL"/"NONE"/0/0)
6. **figma-validate v2 카테고리 5개**: REQ-030 의 패턴 (`v2.{축}.{서브}.match` 함수, v2 분기 진입 시에만 활성) 그대로 따름
7. **add-only diff**: 기존 v2 키 (REQ-029 + REQ-030 산출물) 변경 금지, 신규 5축 키만 추가
8. **결정성**: round(val, 3), hex 소문자, children index 순서, 누락 시 기본값 명시

## 작성 테스트 (TDD)

Task 01 자체에서 빠른 sanity test 1~2 개씩 작성 (충실한 unit 테스트는 task 02 에서):
- `tests/unit/test_strokes_extract.py` (1 SOLID stroke fixture)
- `tests/unit/test_corner_radii_individual.py` (단일 + 4개 개별)
- `tests/unit/test_layout_sizing.py` (FIXED/HUG/FILL 각 1)
- `tests/unit/test_character_style_overrides.py` (인라인 굵기 1 케이스)
- `tests/unit/test_text_case_decoration.py` (UPPER + UNDERLINE 1)

## 규칙

- spec §2 변경 범위 외 파일 수정 금지
- git commit 금지 (PM 처리)
- stdlib 만 사용
- TDD: 위 5축 모두 [tdd-required]
- [MANDATORY] 완료 전 신규 단위 테스트 + py_compile 실행 후 응답에 포함
- 모든 변경은 worktree 내부에서 수행

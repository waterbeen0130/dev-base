# IDN-002 종합 (Synthesis)

**주제**: `D:\dev-base` 폴더 개선점 + "Figma와 완전 동일한 추출물"을 위한 파이프라인 개선 + JSON 공식화 가능성

**참여**: architect(codex), figma-fidelity(codex), quality(codex), schema(gemini), risk(claude)
**비평**: claude-critic

---

## A. "완전 동일한 추출물"이라는 목표 재정의 (critic이 지적)

Figma는 **래스터 합성 렌더러**, 브라우저는 **레이아웃 엔진**이다. 픽셀-동일 = 원리적으로 달성 불가.
→ 목표를 **"결정적(deterministic) 의미론적 동일성 + 주요 시각 속성 1:1 매핑"** 으로 재정의.
→ 현재 9개 검증 카테고리가 이미 의미론적 동일성 방향이라는 점을 유지하고, 그 위에 **시각 속성 확장**(fills/effects/strokes/sizing)과 **SSOT 강화**를 쌓는다.

---

## B. 폴더 전반 개선 포인트 (수치 근거)

### B1. 코드베이스 정리 (working tree)
- `.gran-maestro/plans/PLN-008/plan.json`, `.gran-maestro/requests/REQ-028/request.json` 수정분 커밋/정리
- 대량 삭제된 `output/a_main/*`, `mojelim_*.png`, `output/youngwol/*` working tree에 잔존 — stage or restore 결정 필요
- `tools/json-to-html.py` 폐기 결정(memory) 되었으나 저장소 잔존 → 제거
- `HANDOVER_2026-04-12.md`, `HANDOVER_2026-04-13.md`, `HANDOVER_2026-04-13_v2.md` 난립 → `docs/handovers/` 이동 또는 최신본만 남기고 정리

### B2. 검증 툴 구조 (quality 근거)
- `validate-semantic.py` 3051줄 단일 파일 + 동적 globals/대형 레지스트리 → `engine(dispatch) / validators/{enum,custom} / contracts/rule_registry` 3-계층 분리 + Rule-ID fixture test
- `figma-validate.py` (1404줄) ↔ `validate-semantic.py` 간 규칙 중복 검사: `column flex gap` 검사가 양쪽 모두 존재 (`figma-validate.py:1331-1341`, `validate-semantic.py:2628-2653`)
- `post-impl-verify.py`가 심각도 표를 자체 보유(`post-impl-verify.py:13-26,96-106`)해 정책 SSOT 분산
- `rules.yaml` ↔ `validation_schema.json` ↔ 핸들러 3자 drift:
  - `selector_single_line`/`media_query_format`/`no_media_indent` — 스키마·핸들러엔 있으나 `rules.yaml`엔 없음
  - `no_clamp_under_100` 설명(<100) ↔ 구현(<10) 불일치 (`rules.yaml:230-239` vs `validate-semantic.py:380-386`)
  - `meaningful_page_name`은 파일명 룰인데 HTML 본문 검사 (`validate-semantic.py:734-765`)
  - `_stub_handler` 가 미구현 핸들러를 `skipped` PASS 처리 (`validate-semantic.py:2624-2625,2779-2787,3014`) — **은닉된 검증 누락**

### B3. 오케스트레이션 허점 (architect/quality 근거)
- `post-impl-verify.py:413-417` — spec 미탐색 시 figma 검증 자동 스킵 → 오매칭 통과 위험
- `post-impl-verify.py:53-55` — spec 자동탐색이 첫 spec 1개만 채택 → 다중 섹션 오매칭
- semantic `MAJOR`가 `exit=0` 에 반영되지 않아 통과 가능 (`post-impl-verify.py:243-247,333-340`)
- `IGNORE` 는 status PASS인데 exit=2 (명확한 의미 없음, `post-impl-verify.py:209-210,338-340`)
- `repair-from-violations.py:277-290,412-413` — 위반 상세를 읽지 않고 **개수만** 사용하여 수리 지시 (핵심 필드 `rule_id/file/line/expected/actual/fix_strategy/patch_hint` 부재)
- `figma-section-spec.py:47,1266-1273` — spec 추출기가 codegen 책임까지 겸함 → 경계 붕괴

### B4. SSOT 위반
- `spec.md` ↔ `spec.json` 이중 산출물 (JSON 우선 원칙은 별도 명시 필요)
- 엔진은 `rules.yaml` 기준, 사람/외주는 `rules/common.md` 기준 → 두 문서 동기화 안 됨
- `.gran-maestro/ideation/*/context.md`는 스냅샷이라 코드 진화와 자동 동기화 없음

---

## C. Figma-fidelity를 위한 spec 확장

### C1. 현재 `section_spec.json`에 없어 생성물이 반드시 틀어지는 필드

| 축 | 누락 필드 | 깨지는 방식 |
|---|---|---|
| 채우기 | gradient(type/stops/handles), image(imageRef/scaleMode/crop) | 그라디언트 각도/스톱 소실, 이미지 배경이 단색 hex로 치환 |
| 효과 | `effects[]`, `opacity`, `blendMode` | shadow/blur 전면 소실, 반투명/합성 모드 평면화 |
| 테두리 | `strokes[]`, `strokeWeight`, `strokeAlign`, `rectangleCornerRadii`(개별 corner) | border 두께/정렬, 부분 radius 손실 |
| 텍스트 | `characterStyleOverrides`, `textCase`, `textDecoration`, `paragraphSpacing`, `paragraphIndent` | 한 문장 내 인라인 굵기/색, 대소문자, 밑줄, 문단 간격 손실 |
| 오토레이아웃 | `layoutSizingHorizontal/Vertical`, `layoutAlign`, `layoutGrow`, `primaryAxisSizingMode` | HUG/FILL/FIXED 해석 실패 → bbox.w 고정 px 사용 → 반응형 붕괴 |
| 반응형/제약 | `constraints`, `layoutMode==null` 인 absolute 배치 | 해상도 변경 시 위치 드리프트 |
| 벡터 | SVG path/export 메타 (현재 `normalize_vector_node`는 정의돼 있으나 샘플 누락) | 벡터 아이콘을 raster img로 치환 → 선명도 저하 |
| 컴포넌트 | `componentId`, `componentSetId`, instance 정보 | 반복 인스턴스 재사용 실패, 클래스 난립 |

### C2. Top 10 실패 시나리오 (risk 근거)
1. `fills.type=IMAGE` → hex만 추출하여 배경 이미지 사라짐 [High×High]
2. `characterStyleOverrides` → 한 문장 인라인 굵기/색 손실 [High×High]
3. `linearGradient` → 단색 또는 null [High×Med]
4. drop-shadow effect 완전 소실 [Med×High]
5. 개별 corner radius (top-left만 8) → 단일 border-radius [Med×Med]
6. `layoutSizingHorizontal=FILL` → 고정 bbox.w, flex:1 미적용 [High×High]
7. strokes 완전 누락 [Med×High]
8. `textCase=UPPER` → 원문 소문자 그대로 [Med×Med]
9. `opacity<1` → 불투명 hex [Med×Med]
10. VERTICAL frame + itemSpacing → gap 주입 시 rules.yaml의 "column flex gap 금지"와 충돌 [Med×High]

### C3. 필드 확장 우선순위
1. `fills[]` (type 분기: SOLID/GRADIENT_LINEAR/GRADIENT_RADIAL/IMAGE + 이미지의 imageRef/scaleMode/crop transform)
2. `effects[]` (DROP_SHADOW/INNER_SHADOW/LAYER_BLUR/BACKGROUND_BLUR + offset/radius/color)
3. `strokes[] + strokeWeight + strokeAlign + rectangleCornerRadii`
4. `layoutSizingHorizontal/Vertical + layoutGrow + layoutAlign`
5. `constraints + opacity + blendMode`
6. 텍스트: `characterStyleOverrides + textCase + textDecoration + paragraphSpacing`
7. `componentId/componentSetId` (반복 인식)
8. 벡터: SVG path export를 spec에 참조 + asset manifest

---

## D. JSON 공식화 가능성 결론

**결론: 기술적으로 가능. 단, 전면 Pydantic SSOT 즉시 도입은 over-engineering (critic 지적). 3단계 경로 권고.**

### Phase A (즉시, 낮은 위험)
- `schema_version` 숫자 1 → semver 문자열 `"2.0.0"`
- 단순 dict 확장으로 `fills[]`/`effects[]`/`strokes[]`/`layoutSizing*`/`cornerRadii`/`characterStyleOverrides` 추가
- `additionalProperties: true + _extra` 폴백 전략으로 Figma 신규 필드 유입 대비 (risk (a))
- **하위 호환 마이그레이션 스크립트 우선 배포** — 기존 `extracted/*_spec.json` 전량 재생성 전 validator가 v1/v2 분기 가능하도록 (risk (b), critic Top 3)
- 배열 정렬은 children index(z-order) 기반 유지 (y,x 정렬은 DOM 순서 망가뜨림 — critic 지적)

### Phase B (검증 안정화 이후)
- Pydantic 모델을 SSOT로 선언 → `model_json_schema()` 로 `validation_schema.json` 자동 생성
- `build-rules.py` 와 연계해 외주 브리프 Markdown 테이블 자동 렌더
- `rules.yaml` ↔ `validation_schema.json` ↔ 핸들러 drift CI 게이트 추가

### Phase C (목표 달성기)
- Figma 기준 이미지 vs 브라우저 렌더 **structural diff gate** (DOM tree hash + 주요 속성 비교). 픽셀 diff는 OS별 폰트 렌더 차이로 불안정 — critic 지적
- asset manifest (image/SVG hash 기반 고정)

### 결정성(Determinism) 규칙 (Phase A부터 강제)
- 수치: `round(val, 3)` 전 구간 강제
- 색상: `#rrggbb` 소문자 6자리 (alpha 필요 시 `#rrggbbaa`)
- 키: 스키마 정의 순서 + 내부 dict 알파벳 정렬
- null: 값이 없어도 키는 남기고 명시적 `null`
- 배열: children index 순서(z-order 보존). absolute 좌표 정렬 금지
- 반복성 테스트: 같은 node-id 에 대해 2회 추출 시 byte-exact

### 선결 정책 결정 사항 (spec 확장 전 반드시 문서화)
1. **VERTICAL frame + itemSpacing → CSS 변환 규칙**: `column flex gap 금지` rules.yaml과 충돌. spec-level 정책으로 "margin-bottom 치환 또는 itemSpacing=0이면 생략" 중 택일 (risk #10, critic Top 2)
2. **`constraints` + absolute 배치 도입 여부**: CLAUDE.md의 `flexbox 전용` 원칙과 충돌 (critic 지적). 원칙 유지 시 spec에는 추출하되 CSS 매핑은 하지 않고 "검수용 참고" 플래그 처리
3. **spec vs rules 우선순위**: Figma 값이 rules 위반을 유발할 때 rules 승 → spec에 "rules_conflict" 메타 기록하여 validator가 false-positive 처리

---

## E. 실행 로드맵 — Top 6 액션 (우선순위 순)

1. **하위호환 마이그레이션 설계** — schema_version 분기 + v1→v2 자동 재생성 스크립트. 기존 `extracted/` 전량 재작업 방지 (critic Top 1)
2. **spec v2 Phase A** — fills/effects/strokes/layoutSizing/cornerRadii/characterStyleOverrides dict 확장 + `additionalProperties:true`
3. **정책 결정 문서** — VERTICAL itemSpacing 규칙, constraints 도입 여부, spec↔rules 우선순위 명문화 (critic Top 2)
4. **`post-impl-verify.py` 강화** — spec 미탐색 시 skip 제거, 섹션별 spec 명시 입력 강제, semantic MAJOR exit=1 반영
5. **`repair-from-violations.py` 계약 고정** — `{rule_id, file, line, expected, actual, fix_strategy, patch_hint}` 위반 JSON 스키마 도입 + 수렴형 N회 제한
6. **drift CI** — `rules.yaml ↔ validation_schema.json ↔ 핸들러` 동기화 검사, `_stub_handler` PASS 금지

---

## F. 비평이 PM에게 남긴 반론 (합성 전 재검토 필수)

1. **하위 호환 마이그레이션 선행 없으면 기존 extracted/ spec.json 전량 무효화** — Phase A 전에 migration 스크립트 확정 필요
2. **VERTICAL itemSpacing ↔ column gap 금지 충돌** — fidelity 방향과 rules 방향 우선순위 미결정 시 재dispatch 루프
3. **Pydantic SSOT 즉시 도입은 over-engineering** — Phase A(dict 확장) → Phase B(Pydantic) 단계적 경로가 리스크 최소

---

## G. 사용자 질의 3개에 대한 직접 답

1. **폴더 개선점?** → §B 전체 (코드베이스 정리, 검증 툴 구조 분리, 오케스트레이션 허점 패치, SSOT 일원화)
2. **Figma 완전 동일 추출 위해?** → §C 전체 (fills/effects/strokes/layoutSizing/cornerRadii/textOverrides 등 8축 확장 + 9개 → 15~17개 검증 카테고리 확장)
3. **JSON 공식화 가능한가?** → **가능. 단, 3단계(A: dict 확장 + semver + 마이그레이션 / B: Pydantic SSOT / C: structural diff)로 접근하라.** 즉시 전면 Pydantic 전환은 비용 대비 효용이 낮다 (§D, §F-3).

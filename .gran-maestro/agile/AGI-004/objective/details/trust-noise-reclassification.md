<!-- source-mapping: original=AGI-004/objective-qa-session sections=[조사:pm-verify TRUSTED/NOISY 카테고리] -->
# trust-noise-reclassification (신뢰/노이즈 분류 재점검)

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-008

## 개요

`pm-verify.py`는 false positive를 줄이기 위해 위반 카테고리를 TRUSTED(보고)와 NOISY(억제)로 나눈다. 이 설계 자체는 합리적이나, **억제 목록에 "실제로는 잡아야 할 위반"이 섞여 있으면 검증이 위반을 은폐**하게 된다. 이 도메인은 각 억제 항목을 재판정하여 잘못 억제된 항목만 신뢰 카테고리로 복귀시킨다.

## 설계 결정

### AD-003: 억제는 false-positive 감소 목적이지 위반 은폐가 아니다
- **결정**: 현재 NOISY로 분류된 각 카테고리를 "정당한 억제 / 잘못된 억제"로 판정하고, 후자만 TRUSTED로 복귀. 판정 근거를 문서화.
- **근거**: 억제 목록을 검토 없이 신뢰하면, 규칙은 있으나 리포트에 안 뜨는 사각지대가 생긴다.

## 상세 명세

### 1. 현재 NOISY 억제 목록 (조사 결과)

**NOISY_FIGMA_CATEGORIES** (pm-verify.py:54-67):
- `frame padding/gap 반영`, `clamp 적용`, `column flex gap 금지`
- `[POLICY-1] VERTICAL frame itemSpacing must map to margin-bottom`
- `asset_manifest 일치`
- `v2.layoutSizing.match`, `v2.opacity.match`, `v2.cornerRadii.match`, `v2.strokes.match`, `v2.fills.solid.match`, `v2.effects.match`, `v2.textCase.match`

**NOISY_SEMANTIC_RULES** (pm-verify.py:69-78):
- `vertical_frame_margin_bottom` (현대 CSS gap과 충돌)
- `inner_wrapper_limit` (정당한 래퍼 다중화 차단)
- `line_height_tidy_ratio` (정확한 비율을 "너무 깔끔함"으로 오탐)
- `reset_duplicate` (body{word-break} 재선언 시 위양성)

### 2. 재판정 기준
각 항목에 대해:
- (가) 이 카테고리가 억제되어 있을 때 "실제 위반"이 통과될 수 있는가?
- (나) 억제하지 않으면 false positive가 얼마나 발생하는가? (클린 픽스처로 측정)
- (다) 판정: 정당한 억제(유지) / 부분 복귀(조건부) / 전면 복귀.

### 3. 우선 의심 항목 (가설, 픽스처로 검증 필요)
- `asset_manifest 일치` 억제 → 이미지 누락/오연결을 못 잡을 위험. 복귀 후보.
- `inner_wrapper_limit` 억제 → 실제 결과물의 "불필요한 중첩 래퍼 170개+"를 못 잡았음. 조건부 복귀 검토.
- `reset_duplicate` 억제 → 위양성 사례(body{word-break})만 예외 처리하고 나머지는 복귀 검토.
- 단, 위는 가설이며 클린 픽스처 false-positive 측정 후 확정(regression-fixtures 도메인 연계).

### 4. 출력
- "카테고리 ↔ 재판정 결과 ↔ 근거 ↔ 조치(유지/복귀)" 리포트.
- 복귀 항목은 regression-fixtures로 false-positive 0 확인 후 적용.

## 재판정 결과 (DOD-008 — Sprint 11)

각 억제 카테고리를 "정당한 억제 / 잘못된 억제"로 판정했다. **결론: 현재 모든 억제는 false-positive 기반으로 정당하며, 억제 뒤의 실제 위험은 비억제 검사로 이미 커버되므로 복귀 대상 없음.**

| 카테고리 | 판정 | 근거 |
|---------|------|------|
| frame padding/gap 반영, clamp 적용, column flex gap 금지 | 정당 | 레이아웃 휴리스틱, FP 다수 |
| [POLICY-1] vertical margin-bottom | 정당 | 모던 CSS gap과 충돌(의도적 비활성) |
| asset_manifest 일치 | 정당(위험 커버됨) | 실제 위험(이미지 누락/오연결)은 **pm-verify [3] broken-link 검사(비억제)** 가 직접 검출 |
| v2.layoutSizing/opacity/cornerRadii/strokes/fills.solid/effects/textCase | 정당 | Figma 충실도 미세검사, CSS 1:1 해석 불가로 FP 다수 |
| vertical_frame_margin_bottom | 정당 | POLICY-1 중복 + gap 충돌 |
| inner_wrapper_limit | 정당(위험 커버됨) | 정당한 다중 래퍼(hero bg+content) 차단 FP. 과도 중첩의 실제 위험은 **max_dom_depth(MAJOR, 비억제)** 가 커버 |
| line_height_tidy_ratio | 정당 | Figma 정확비율(1.0/1.5)을 "너무 깔끔"으로 오탐 |
| reset_duplicate | 정당 | body{word-break} 재선언 FP 사례 |

**복귀 항목: 없음.** 두 개의 실제 위험(broken image, 과도 중첩)은 각각 broken-link 검사·max_dom_depth가 비억제로 잡으므로, 억제를 풀면 순수 FP만 늘어난다(R1). 이 결정은 `tests/unit/test_noise_reclassification.py` 가 잠가, 향후 억제 집합이 말없이 바뀌면 테스트가 실패해 재판정·문서 갱신을 강제한다.

## Q&A 보강 사항

- 사용자가 "신뢰/노이즈 분류 재점검"을 4방향 중 하나로 명시 선택.
- 주의: 억제 해제는 false positive 재발 위험이 있으므로 반드시 클린 픽스처 통과를 전제(NFR 오류처리 / R1).

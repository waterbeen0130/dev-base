# Plan: PLN-010

**생성일**: 2026-04-20T02:04:04.000Z
**주제**: Figma→Code 파이프라인 v3 — Pydantic SSOT + structural diff gate + componentId 재사용
**Cynefin 도메인**: Complicated
**연관**: PLN-009 (Phase A 완료, Phase B/C 명시적 후속), INTENT-005 (동일 intent 체인)
**실행 모드**: 자율 (-a) — 자동 체인 (mst:request → approve → accept)

---

## 요청 (Refined)

PLN-009 Phase A 완료 후, 명시적으로 제외됐던 **Phase B (Pydantic SSOT)** 와 **Phase C (structural diff gate)**, 그리고 PLN-009 REQ-032 에서 추출만 하고 재사용 로직은 미구현이었던 **componentId 재사용 (Phase D)** 을 단일 PLN 내 3개 REQ 로 분리 실행한다.

- **Phase B** (REQ-035): Pydantic v2 모델을 SSOT 로 도입하여 `rules/validation_schema.json` 을 자동 파생. figma-validate 핸들러 계약도 동일 모델 기반으로 재정렬하여 rules↔schema↔handler 3자 drift 를 **구조적으로 불가능**하게 만든다.
- **Phase C** (REQ-036): Playwright Python 으로 HTML 을 실 브라우저 렌더링한 뒤, DOM tree 를 정규화 해시로 변환하여 Figma spec 의 frame_nodes 해시와 비교한다. 픽셀 diff 는 OS 폰트 차이로 불안정하므로 명시적 제외 (PLN-009 critic 지적 반영).
- **Phase D** (REQ-037): Phase A (REQ-032) 에서 이미 추출된 componentId 를 활용하여, 동일 componentId 인스턴스들을 공유 CSS 클래스로 묶고 인스턴스별 override 만 분리한다.

## 범위 예산 (Appetite)

3주 (Phase B 1주 → Phase C/D 병렬 2주)

## 제외 범위 (No-go Scope)

- **Phase A 재작업** — PLN-009 에서 확정된 8축 spec v2, 정책 3건, drift 제거는 재검토하지 않는다.
- **Figma 외 타 디자인 도구** (Sketch, XD) 지원
- **pixel-exact 렌더링 비교** — OS 폰트 차이로 불안정
- **Pydantic v1** — v2 전용
- **Selenium 등 타 브라우저 자동화 도구** — Playwright 전용
- **componentId 기반 동적 상태 변환** (hover/active 등) — 정적 스타일 재사용까지만

## 결정 사항

| 항목 | 결정 | 근거 |
|------|------|------|
| plan 분리 여부 | 단일 PLN-010 내 3 REQ | PLN-009 6 REQ 체인 선례 + 파이프라인 공통 맥락 |
| Pydantic 도입 | v2 허용 (pyproject.toml 추가) | SSOT + model_json_schema() 자동 파생 불가피 |
| Playwright 도입 | Python 패키지 도입 | DOM tree hash 는 실 브라우저 필요 |
| 외부 의존성 정책 | Phase A stdlib-only 제약 해제 (Phase B+ 한정) | Phase A 결정 사항은 Phase A 한정이었음 |
| REQ 실행 순서 | Phase B → Phase C ∥ Phase D (B 가 SSOT 기반) | Phase C/D 의 검증기/생성기가 Phase B 모델 활용 가능 |
| 기존 63 rules migration | Pydantic 모델로 전환 + rules.yaml 은 validation_schema 자동 파생 대상으로 정리 | drift zero 달성 |
| DOM tree 해시 정규화 | tag + class 순서 + children index (text 내용 제외) | text 변경 허용 (텍스트는 별도 검증), 구조만 보존 |
| componentId 재사용 단위 | 동일 componentId 전체 그룹 단위 | componentSetId 는 variant 추적용으로만 유지 |
| override 분리 기준 | characters / fills[].color / fontWeight / fontSize | 시각 차이 4축만 override 로 분리 |

## 범위

**포함**:

A. **Phase B — Pydantic SSOT 자동 파생** (REQ-035)
   - `rules/models.py` (신규): Pydantic v2 RuleDefinition / CategoryDefinition / ValidationSchema 모델
   - `rules/validation_schema.json` 은 `python -m rules.models` 실행으로 자동 생성 (수동 편집 금지)
   - `tools/figma-validate.py` 핸들러 계약을 Pydantic 모델 기반으로 재정렬
   - `tools/check-rules-drift.py` 는 Pydantic → rules.yaml / handler 3자 drift 감지로 승격
   - 기존 63 rules → Pydantic 모델 등록 후 정합 100% 유지
   - pyproject.toml: pydantic>=2.6 추가

B. **Phase C — structural diff gate** (REQ-036)
   - `tools/structural-diff.py` (신규): Playwright Python 으로 HTML 을 headless Chromium 렌더링 → DOM snapshot 추출
   - DOM → 정규화 해시 함수: `tag_name + sorted(class_list) + children_index_path` (text/id/style inline 제외)
   - Figma spec 의 `frame_nodes` → 동일 알고리즘으로 구조 해시 생성
   - 비교 결과: PASS / STRUCTURE_DRIFT (depth mismatch / child count / tag name mismatch)
   - `tools/post-impl-verify.py` 에 `--structural-diff` optional flag 통합 (exit code 체계 확장)
   - pyproject.toml: playwright>=1.42 추가, `playwright install chromium` 자동화

C. **Phase D — componentId 재사용 로직** (REQ-037)
   - `tools/figma-section-spec.py` 에 post-process 단계 추가: 동일 componentId 인스턴스 그룹핑
   - 각 그룹마다 shared CSS base class 생성 (예: `component_{componentId_hash}`)
   - 인스턴스별 override 는 characters / fills[].color / fontWeight / fontSize 4축 차이만 별도 선언
   - 출력 spec.json 에 `component_groups: [{componentId, instances: [nodeId], shared_style, overrides}]` 추가
   - 기존 8축 v2 spec 과 하위 호환 (신규 필드 추가만, 기존 필드 불변)

**제외**: 위 "제외 범위" 섹션 참조.

## 제약 & 가정

- Python 3.10+ 가정 (기존 프로젝트와 동일)
- Pydantic v2, Playwright Python 은 외부 의존성이므로 `pyproject.toml` 에 선언하고 개발 환경에 pip install 로 확보.
- 기존 `tools/` 스크립트는 수정 허용. 삭제는 호환 유지 가능할 때만.
- Phase A v2 spec.json 산출물(`extracted/section_03_spec.json` 등)은 Phase D 에서 재생성되지만 기존 필드 값은 byte-exact 보존 (add-only diff).
- CLAUDE.md 의 "PM 직접 코드 수정 금지" 원칙 유지 — 모든 구현은 외주 에이전트(codex-dev / gemini-dev) dispatch.
- DOM tree 해시 정규화 알고리즘은 허용 오차를 텍스트 순서/내용은 허용, 구조(tag/class/children count) 는 엄격.

## 우선순위 (MoSCoW)

- **Must have**: Phase B (SSOT), Phase C (structural diff gate), Phase D (componentId 재사용) 3 REQ 전체
- **Should have**: post-impl-verify 에 structural-diff flag 통합, generated CSS 크기 감소량 측정
- **Could have**: componentSetId variant 추적 (향후 plan 유보)
- **Won't have (this time)**: Pydantic v1 / Selenium / pixel diff / 타 디자인 도구

## 의존성

- 선행 필요: PLN-009 (Phase A 완료 — 2026-04-19 main squash-merge)
- 연관: INTENT-005 (동일 intent 체인), PLN-009 REQ-032 (componentId 추출 완료)

## 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| Pydantic v2 migration 중 63 rules 정합 깨짐 | 중 | 중 | REQ-035 task 분리: (1) 모델 정의 + 1 rule migration 검증, (2) 전체 rules migration + drift 재검증 |
| Playwright CI 환경 구성 복잡도 | 중 | 중 | pyproject.toml + playwright install 자동화 스크립트, CI 에는 headless chromium 만 |
| componentId 재사용의 false positive (시맨틱 차이 있는 인스턴스 오인 그룹핑) | 중 | 중 | 그룹핑 전 fills/layoutMode/padding 등 핵심 속성 동일성 추가 검증 |
| DOM tree 해시 정규화 알고리즘의 false negative (실제 구조 다른데 해시 동일) | 낮 | 중 | fixture 기반 회귀 테스트로 known-bad 케이스 고정 |
| 외부 의존성 추가로 기존 CI 파이프라인 영향 | 낮 | 중 | pyproject.toml + pip install 만 추가, 기존 stdlib 도구는 유지 |

## 분리 실행 (REQ 분리)

| REQ | 주제 | 핵심 산출물 | 의존성 |
|-----|------|-------------|--------|
| REQ-035 (Phase B) | Pydantic SSOT 자동 파생 | `rules/models.py`, `validation_schema.json` 자동 생성, check-rules-drift 승격, figma-validate 핸들러 재정렬 | PLN-009 완료 |
| REQ-036 (Phase C) | structural diff gate | `tools/structural-diff.py`, Playwright 통합, post-impl-verify --structural-diff flag | REQ-035 (SSOT 기반) |
| REQ-037 (Phase D) | componentId 재사용 로직 | `figma-section-spec.py` 재사용 post-process, spec.json `component_groups`, shared CSS 생성 규칙 | REQ-035 (SSOT 기반) |

실행 순서: **REQ-035 → REQ-036 ∥ REQ-037** (C/D 는 B 완료 후 병렬 가능)

## 테스트 전략

- **적용 여부**: 적용
- **목표 커버리지**: 미설정 (PLN-009 동일 기조)
- **비고**:
  - Phase B: Pydantic 모델 → validation_schema.json round-trip 테스트, 63 rules 전체 정합 회귀 테스트
  - Phase C: fixture HTML 기반 DOM tree hash 결정성 테스트, known-good/known-bad 구조 회귀 테스트
  - Phase D: 동일 componentId fixture 로 shared + override 분리 정확성 테스트, 기존 v2 spec 하위 호환 테스트

## Loop 종료 조건

기존 검증 통과 (AC 통과 + max_iterations 기본값 유지)

## Intent (JTBD)

- **When I**: Figma→Code 파이프라인을 지속 확장하고 유지보수할 때
- **I want to**: 규칙 정의를 Pydantic 모델 하나로 고정하고, 생성물의 구조 일치를 자동 검증하며, 반복되는 컴포넌트를 CSS 레벨에서 재사용하도록
- **So I can**: validator drift 를 구조적으로 차단하고, 시각적 회귀를 자동 탐지하며, 생성 CSS 의 중복을 제거하여 장기적 운영 비용을 줄일 수 있다.

## 인수 기준 초안

이 plan 의 구현이 완료됐다는 것은:

- [MUST] [TIER-A] PAC-1: `rules/models.py` 의 Pydantic v2 모델이 SSOT 로 동작하고, `python -m rules.models` 실행으로 `rules/validation_schema.json` 이 자동 생성된다. 수동 편집 경로는 제거된다.
- [MUST] [TIER-A] PAC-2: `tools/check-rules-drift.py` 가 Pydantic 모델 ↔ rules.yaml ↔ figma-validate 핸들러 3자 정합을 100% 유지하며, 63/63 rules in sync 가 유지된다.
- [SHOULD] [TIER-B] PAC-3: 기존 pytest 전체 (PLN-009 기준 113 passed) 가 회귀 없이 통과한다.
- [MUST] [TIER-A] PAC-4: `tools/structural-diff.py` 가 Playwright headless Chromium 렌더링 DOM tree 를 정규화 해시로 변환하고, Figma spec `frame_nodes` 구조 해시와 비교해 STRUCTURE_DRIFT 를 검출한다.
- [MUST] [TIER-A] PAC-5: DOM 해시 정규화 규칙 (tag + sorted(class_list) + children_index_path, text/id/inline style 제외) 이 문서화되고 구현된다.
- [SHOULD] [TIER-B] PAC-6: `tools/post-impl-verify.py` 에 `--structural-diff` optional flag 가 통합되어, 해당 flag 활성 시 structural diff 결과를 검증 결과에 포함한다.
- [MUST] [TIER-A] PAC-7: `tools/figma-section-spec.py` 의 post-process 단계가 동일 componentId 인스턴스들을 그룹핑하여 spec.json `component_groups` 배열을 생성한다.
- [MUST] [TIER-A] PAC-8: 각 그룹마다 shared CSS base class 와 인스턴스별 override (characters / fills[].color / fontWeight / fontSize 4축) 가 분리된 형태로 spec.json 에 표현된다.
- [SHOULD] [TIER-B] PAC-9: 동일 componentId 인스턴스가 2개 이상 존재하는 fixture 에서, 생성 CSS 중복 선언 감소량이 측정되고 결과가 테스트에 기록된다.
- [SHOULD] [TIER-B] [IMPACT] PAC-10: 기존 `figma-section-spec.py` / `figma-validate.py` / `post-impl-verify.py` 가 Phase A 대비 회귀 없이 동작하고, v2 spec.json 기존 필드는 byte-exact 보존된다.

## 참고 컨텍스트

- PLN-009 Phase A 완료 핸드오버: `/mnt/d/dev-base/HANDOVER_2026-04-19.md` §5 후속 작업 제안
- PLN-009 plan.md: `/mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md`
- INTENT-005 (선행): `.gran-maestro/intent/intent.db` 참조
- IDN-002 synthesis (Phase A 근거): `/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/synthesis.md`

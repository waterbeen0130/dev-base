# Implementation Request — REQ-033/01

- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-033-task-01
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md
- 선행 commits: REQ-029 (431d0e3), REQ-030 (7fa6cd2), REQ-031 (8919608), REQ-032 (cc619fc)

## 구현 컨텍스트 (PM 작성)

PLN-009 Phase A 5단계 — validator drift 완전 제거. REQ-029 가 정책 3건 ID 정합성만 보강했고 (PAC-15 Partial), 본 REQ 는 rules.yaml ↔ validation_schema.json ↔ tools/validate-semantic.py 핸들러 3자 전체 정합성을 완성한다. 핵심:

1. **`_stub_handler` 제거** (또는 skipped → MAJOR FAIL 승격) — IDN-002 §B2 critic 지적 "은닉된 검증 누락" 제거. validate-semantic.py:2624,2787,2887 위치.
2. **누락 규칙 보강**: `selector_single_line`, `media_query_format`, `no_media_indent` 등 schema·핸들러엔 있으나 `rules.yaml` 엔 없는 규칙들을 rules.yaml 에 정식 등록 (REQ-029 quality 의견 §1 근거).
3. **불일치 항목 수정**:
   - `no_clamp_under_100`: 설명(<100) ↔ 구현(<10) 일치화 — 설명을 구현에 맞추거나 구현을 설명에 맞춤 (PM 판단으로 설명을 100으로 통일 권장)
   - `meaningful_page_name`: 파일명 룰인데 HTML 본문 검사 — 파일명 검사로 수정하거나 룰 description 명확화
4. **drift 감지 통합** (MANDATORY): REQ-029 의 `tools/check-rules-drift.py` 는 정책 3건만 검사. 본 REQ 에서 **모든 Rule-ID 3자 정합성 검사** 모드 추가 (`--all-rules` 또는 인자 없이 호출 시 전체 검사).
5. **post-impl-verify.py 에 drift check 내장** (`workflow.drift_check_enabled` 기본 true): 매 verify 호출 시 drift-cache.json 기반 mtime 비교로 drift 발생 여부 자동 감지, drift 시 exit=1.

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. plan + 선행 REQ-029~032 변경사항 (특히 REQ-029 의 check-rules-drift.py 와 figma-validate handler 등록 패턴)
2. `tools/validate-semantic.py` 의 `_stub_handler` 위치 (line 2624, 2787, 2887)
3. `rules/rules.yaml` 과 `rules/validation_schema.json` 의 현재 enum/handler binding 비교 — 누락 규칙 식별
4. `tools/post-impl-verify.py` 의 사이클 흐름 — 어디에 drift check 를 삽입할지

## 핵심 구현 지침

1. **_stub_handler 제거**:
   - 옵션 A (강한): 미구현 핸들러를 등록 시 즉시 ImportError/AssertionError 발생 (실수로 stub 등록 불가)
   - 옵션 B (안전): _stub_handler 가 호출되면 `MAJOR FAIL` 결과 반환 + warning 로그 (`[STUB-PASS BLOCKED] handler {name} not implemented — treating as MAJOR FAIL`)
   - PM 권장: 옵션 B 채택 (기존 코드 호환성 + 강제 실패)
2. **누락 규칙 rules.yaml 등록**: 각 규칙에 대해 id/severity/description/handler 필드 작성. validation_schema.json 의 handler 이름과 일치
3. **불일치 항목 수정**:
   - `no_clamp_under_100`: rules.yaml description 의 "<100" 을 구현(<10) 에 맞추거나 구현을 100 으로 변경. 사용자 의도는 100 이 정상이므로 **구현을 <100 으로 수정** 권장 — 단, 기존 통과 spec 들의 회귀 risk 분석 후 결정. 안전한 경로: 룰 분리 (`no_clamp_under_10` (저강도, 기존 동작) + `no_clamp_under_100` (신규, 권장 강도)). PM 결정: **구현을 100 으로 통일** + 마이그레이션 시 minor warning 로그
   - `meaningful_page_name`: 룰 description 을 "파일명 + 본문 모두 검사 (의미있는 영문 페이지명)" 로 명확화하고 구현 그대로 유지 (덜 위험)
4. **check-rules-drift.py 확장**:
   - 인자 없이 호출 시 전체 Rule-ID 검사 (현재는 `--policy-ids` 만 지원)
   - 출력: `[OK] {N}/{N} rules in sync` 또는 `[DRIFT] {drift_id}: missing in {target}`
5. **post-impl-verify.py drift check 내장**:
   - `_run_drift_check()` 함수 추가 (cache mtime 비교)
   - 캐시 경로: `{PROJECT_ROOT}/.gran-maestro/state/drift-cache.json`
   - rules.yaml/validation_schema.json/validate-semantic.py mtime 셋 중 하나라도 캐시 mtime 보다 새로우면 check-rules-drift.py 호출 후 캐시 갱신
   - drift 발견 시 exit=1 + `[DRIFT] {summary}` 로그
6. **add-only/결정성/stdlib only**

## 작성 테스트

- `tests/unit/test_stub_handler_blocks.py`: _stub_handler 호출 시 MAJOR FAIL 반환 확인
- `tests/unit/test_drift_check_all_rules.py`: check-rules-drift.py --all 실행 시 전체 일치 확인
- `tests/unit/test_no_clamp_threshold.py`: 새 임계값 (100) 으로 fixture 검증
- `tests/integration/test_post_impl_drift_cache.sh`: post-impl-verify.py drift cache mtime 동작

## 규칙

- spec §2 변경 범위 외 파일 수정 금지
- git commit 금지
- stdlib 만 사용
- TDD: 핵심 변경(_stub_handler, drift integration) RED → 구현 → GREEN
- [MANDATORY] 완료 전 신규 unit + integration 실행 후 응답에 출력 포함
- worktree 내부에서만 작업

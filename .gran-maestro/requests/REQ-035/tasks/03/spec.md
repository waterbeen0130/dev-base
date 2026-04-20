# Spec — REQ-035 / Task 03: 통합 회귀 테스트 + PAC-3 전체 수렴

**Assigned Agent**: `[config: codex-dev] codex-dev` (Python test)
**Status**: pending
**Plan**: PLN-010
**Linked Intent**: INTENT-006
**Template**: `templates/test-spec.md` 기반

---

## §0 Context Manifest

- Task 01 / Task 02 산출물 (rules/models.py, 재정렬된 check-rules-drift.py 및 figma-validate.py)
- 전체 pytest suite (`tests/`)
- PLN-009 기준선: 113 passed / 33 skipped / 0 failed

## §1 요약

Task 01, Task 02 구현 완료 후 **전체 회귀 검증** 및 **증분 테스트** 를 실행하여 PAC-3 (기존 pytest 회귀 없음) 를 최종 수렴한다.

## §2 테스트 범위

- 통합 검증: pytest 전체 실행 (기존 113 passed + REQ-035 신규 테스트)
- 증분 테스트: Task 01/02 신규 테스트 파일 단독 실행
- 회귀 테스트: PLN-009 Phase A 기준 결정성(100회 byte-exact), figma-section-spec.py determinism

## §3 통합 AC

### AC-001 [automatable] [regression-test] 전체 pytest 통과 (PAC-3)

- **Given**: REQ-035 Task 01/02 완료 상태
- **When**: `pytest tests/ -v` 실행
- **Then**: Total ≥ 118 passed (113 기존 + 5 신규), 0 failed
- **Test**: `pytest tests/ -v`

### AC-002 [automatable] 결정성 회귀 (PAC-3)

- **Given**: `extracted/section_03_spec.json` fixture
- **When**: `pytest tests/regression/test_determinism.py -v` 실행
- **Then**: 100회 byte-exact PASS
- **Test**: `pytest tests/regression/test_determinism.py -v`

### AC-003 [automatable] drift cache 동작 회귀

- **Given**: `.gran-maestro/state/drift-cache.json`
- **When**: `python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css --profile landing` 2회 연속 실행
- **Then**: 2번째 실행 시 drift 체크 skip 로그 ("cache hit") 출력
- **Test**: `bash tests/integration/test_post_impl_drift_cache.sh`

## §3.2 Test Scenarios (Pre-Impl)

- AC-001: `pytest tests/ -v` → total ≥ 118 passed, 0 failed
- AC-002: `pytest tests/regression/test_determinism.py -v` → 100회 byte-exact PASS
- AC-003: `bash tests/integration/test_post_impl_drift_cache.sh` → 2회 실행 시 2번째 "cache hit" 로그 확인

## §4 회귀 테스트 항목

- PLN-009 Phase A: schema_version "2.0.0" 파싱 유지
- REQ-030 fills_v2 (SOLID/GRADIENT/IMAGE 분기)
- REQ-031 strokes/cornerRadii/layoutSizing
- REQ-032 componentId/vector path/asset_manifest
- REQ-033 `_stub_handler` MAJOR FAIL 차단
- REQ-034 post-impl-verify `--spec` 강제

## §5 선행 작업 (blockedBy)

- REQ-035 / Task 01
- REQ-035 / Task 02

## §6 후행 작업 (blocks)

- REQ-036 (Phase C — structural diff gate)
- REQ-037 (Phase D — componentId 재사용)

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | 02, 03 | codex-dev |
| 02 | 01 | 03 | codex-dev |
| 03 | 01, 02 | — | codex-dev |

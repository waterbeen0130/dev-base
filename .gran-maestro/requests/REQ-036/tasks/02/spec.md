# Spec — REQ-036 / Task 02: post-impl-verify --structural-diff 통합 + 회귀 테스트

**Assigned Agent**: `[config: codex-dev] codex-dev`
**Status**: pending
**Plan**: PLN-010
**Linked Intent**: INTENT-006

---

## §0 Context Manifest

- Task 01 산출물 (`tools/structural-diff.py`)
- `tools/post-impl-verify.py` — 기존 `--spec`, 드리프트 캐시 통합 구조
- `tests/integration/test_post_impl_drift_cache.sh` — 참조

## §1 요약

`tools/post-impl-verify.py` 에 `--structural-diff` optional flag 를 추가해 structural diff 결과를 검증 파이프라인에 통합한다. 기존 검증 (figma-validate + validate-semantic) 체계는 불변.

## §2 범위

**포함**:
- `--structural-diff` flag 추가 (기본 OFF, 명시적 ON 시 tools/structural-diff.py 호출)
- structural diff 결과를 exit code 매트릭스에 반영 (STRUCTURE_DRIFT → MAJOR 등급)
- 기존 exit code 호환성 유지 (0 PASS / 1 CRITICAL·MAJOR / 2 IGNORE-only)
- 회귀 테스트

**제외**:
- structural-diff.py 자체 수정 (Task 01 완료 전제)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] --structural-diff flag 동작 (PAC-6)

- **Given**: post-impl-verify CLI + Task 01 산출 structural-diff.py
- **When**: `python3 tools/post-impl-verify.py --spec <spec> --html <html> --css <css> --profile landing --structural-diff` 실행
- **Then**: exit 0, 출력에 "STRUCTURAL: PASS" 또는 "STRUCTURAL: DRIFT" 라인 포함
- **Test**: `pytest tests/integration/test_post_impl_structural_diff.py -v` (신규)

### AC-002 [automatable] flag 미지정 시 기존 동작 유지 (PAC-6)

- **Given**: post-impl-verify CLI
- **When**: `--structural-diff` 없이 실행
- **Then**: structural-diff 호출 없음, 기존 9+14 카테고리만 실행
- **Test**: 기존 `tests/integration/test_post_impl_drift_cache.sh` 회귀

### AC-003 [automatable] STRUCTURE_DRIFT exit code 매트릭스 (PAC-6)

- **Given**: structural diff 에서 DRIFT 감지
- **When**: `--structural-diff` 로 실행
- **Then**: exit 1 (MAJOR 등급)
- **Test**: `pytest tests/integration/test_post_impl_structural_drift_exits_1.py -v` (신규)

## §3.2 Test Scenarios (Pre-Impl)

- AC-001: `pytest tests/integration/test_post_impl_structural_diff.py -v`
- AC-002: `bash tests/integration/test_post_impl_drift_cache.sh`
- AC-003: `pytest tests/integration/test_post_impl_structural_drift_exits_1.py -v`

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-6 | SHOULD | AC-001, AC-002, AC-003 | full |

## §5 선행 작업 (blockedBy)

- REQ-036 / Task 01

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | 02 | codex-dev |
| 02 | 01 | — | codex-dev |

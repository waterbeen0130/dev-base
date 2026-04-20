# Spec — REQ-040 / Task 01: 합본 검증 + text byte-exact + asset manifest fidelity

**Assigned Agent**: `[config: codex-dev] codex-dev`

---

## §0 Context Manifest

- `tools/figma-validate.py` — 현재 단일 --spec 만 받음
- `tools/post-impl-verify.py` — 단일 spec 만 받음 (REQ-034)
- `extracted/section_03_spec.json` — fixture (단일 섹션)
- REQ-032 `asset_manifest.json` — 이미지 SHA-256 레지스트리 (생성만 되고 검증 미통합)
- 오늘 목포플레이파크 사례 — 섹션별로만 돌려서 PM 이 수동 집계 → 실패

## §1 요약

파이프라인 근본 개선 3축:

1. **합본 검증**: `--spec-dir extracted/` 지원 → 디렉토리의 모든 `*_spec.json` 을 일괄 로드하여 합본 HTML 전체 대비 검증 수행
2. **text byte-exact**: `spec.json.text_nodes[].characters` 의 모든 텍스트가 HTML 에 **byte-exact** 존재 여부 검증 (NBSP `\xa0`, 특수 공백 포함)
3. **통이미지 감지**: `asset_manifest.json` 과 HTML `<img src=...>` 를 대조하여 (a) Figma 에 있는데 HTML 에 없는 이미지 (b) HTML 에 있는데 asset_manifest 에 없는 이미지 양방향 감지

## §2 범위

**포함**:
- `tools/figma-validate.py`:
  - `--spec-dir DIR` 옵션 (기존 `--spec FILE` 과 배타)
  - 디렉토리 내 `*_spec.json` 을 전부 로드, 합본 HTML 대비 일괄 검증
  - 출력: 섹션별 위반 카운트 + 총계
- `tools/figma-validate.py` 신규 카테고리:
  - `텍스트 byte-exact` — `spec.text_nodes[i].characters` 가 HTML 에 "그대로" 존재 (NBSP 포함)
  - `asset_manifest 일치` — `asset_manifest.json` SHA-256 기반 이미지 <-> HTML `<img src>` 양방향 매칭
- `tools/post-impl-verify.py`:
  - `--spec-dir` 전달 지원
  - figma-validate 합본 결과를 분류 (CRITICAL: byte-exact / color / 누락 content, MAJOR: padding/clamp)
- `rules/models.py` + `rules.yaml`:
  - 신규 rule 2개 등록 (SSOT 정합):
    - `text_byte_exact_required` (severity=error, Figma 충실도)
    - `asset_manifest_consistency` (severity=error)
- 회귀 테스트

**제외**:
- Figma 원본 re-fetch (spec 생성 자체)
- 픽셀 diff

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] 합본 검증 동작 (core)

- **Given**: `extracted/` 디렉토리 + 합본 HTML/CSS fixture (2 섹션 spec 이상)
- **When**: `python3 tools/figma-validate.py --spec-dir extracted/ --html <html> --css <css>`
- **Then**: 양쪽 섹션 위반이 1회 실행에 모두 나타나고, 섹션별 집계 표 출력
- **Test**: `pytest tests/unit/test_figma_validate_spec_dir.py -v` (신규)

### AC-002 [automatable] [tdd-required] text byte-exact 감지

- **Given**: spec.text_nodes 에 `"운영시간\xa0  10:00"` (NBSP 포함)
- **When**: HTML 에 `"운영시간 10:00"` (일반 공백) 만 존재
- **Then**: `텍스트 byte-exact` 위반 1건 CRITICAL
- **Test**: `pytest tests/unit/test_text_byte_exact.py -v` (신규)

### AC-003 [automatable] [tdd-required] asset_manifest 양방향 일치

- **Given**: `asset_manifest.json` 에 5개 이미지 / HTML 에 4개만 포함 + 1개 없던 이미지 추가
- **When**: 검증 실행
- **Then**: "Figma 에 있는데 HTML 에 없음" 1건 + "HTML 에 있는데 manifest 없음 (통이미지 의심)" 1건
- **Test**: `pytest tests/unit/test_asset_manifest_fidelity.py -v` (신규)

### AC-004 [automatable] 신규 rule SSOT 등록

- **Given**: rules.yaml 에 `text_byte_exact_required`, `asset_manifest_consistency` 2개 추가
- **When**: `python3 -m rules.models` + `python3 tools/check-rules-drift.py --all`
- **Then**: 65/65 rules in sync (기존 63 + 신규 2)
- **Test**: `pytest tests/regression/test_drift_zero.py -v`

### AC-005 [automatable] [regression-test] 기존 pytest 140 passed 회귀 없음

- **Given**: main 기준 pytest 140 passed
- **When**: `pytest tests/ -v`
- **Then**: 140+ passed, 0 failed
- **Test**: `pytest tests/ -v`

## §3.2 Test Scenarios (Pre-Impl)

- AC-001: `pytest tests/unit/test_figma_validate_spec_dir.py -v`
- AC-002: `pytest tests/unit/test_text_byte_exact.py -v`
- AC-003: `pytest tests/unit/test_asset_manifest_fidelity.py -v`
- AC-004: `pytest tests/regression/test_drift_zero.py -v`
- AC-005: `pytest tests/ -v`

## §3.5 Constraints

- 기존 `--spec FILE` 경로 호환 유지 (하위 호환)
- `--spec` 와 `--spec-dir` 동시 사용 금지 (에러 처리)
- Pydantic SSOT 경로로 rule 추가 (rules.yaml + models.py 자동 재생성)
- 코드 주석은 영어만

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | — | codex-dev |

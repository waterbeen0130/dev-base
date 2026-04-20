# Spec — REQ-036 / Task 01: structural-diff.py + Playwright DOM tree hash 핵심 구현

**Assigned Agent**: `[config: codex-dev] codex-dev`
**Status**: pending
**Plan**: PLN-010
**Linked Intent**: INTENT-006

---

## §0 Context Manifest

- `tools/figma-section-spec.py` — frame_nodes 구조 (Phase A v2 spec 참조)
- `extracted/section_03_spec.json`, `extracted/section_04_spec.json` — fixture
- `tools/post-impl-verify.py` — 후속 통합 대상 (Task 02)
- `rules/models.py` — Phase B 산출물 (참고)
- `pyproject.toml` — Phase B 에서 Pydantic 추가됨

## §1 요약

`tools/structural-diff.py` 신규 작성 — Playwright headless Chromium 으로 HTML 을 렌더링 후 DOM tree 를 정규화 해시로 변환하고, Figma spec `frame_nodes` 를 동일 알고리즘으로 해시하여 비교한다. 픽셀 diff 는 제외.

## §2 범위

**포함**:
- `tools/structural-diff.py` 신규
- 정규화 해시 함수: `tag + sorted(class_list) + children_index_path` (text/id/inline style 제외)
- CLI: `--spec <spec.json> --html <output.html> [--css <output.css>]` → PASS / STRUCTURE_DRIFT
- Playwright Python 통합 (headless chromium)
- pyproject.toml 에 `playwright>=1.42` 추가 + playwright install chromium 자동화 스크립트 안내

**제외**:
- post-impl-verify 통합 (Task 02)
- pixel diff, visual regression (명시적 제외)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] Playwright DOM tree 정규화 해시 결정성 (PAC-4, PAC-5)

- **Given**: `landing/index.html` + `landing/css/common.css` 고정 fixture
- **When**: `python3 tools/structural-diff.py --html landing/index.html --css landing/css/common.css --dump-hash` 10회 실행
- **Then**: 10회 모두 동일 해시 출력 (결정성)
- **Test**: `pytest tests/unit/test_structural_hash_determinism.py -v` (신규)

### AC-002 [automatable] DOM 해시 정규화 규칙 문서화 (PAC-5)

- **Given**: `tools/structural-diff.py` 모듈 docstring
- **When**: 첫 100줄 Read
- **Then**: 정규화 규칙 (tag + sorted(class_list) + children_index_path, text/id/inline style 제외) 이 주석/docstring 으로 명시
- **Test**: `pytest tests/unit/test_structural_hash_docs.py -v` (신규)

### AC-003 [automatable] spec frame_nodes 해시와 DOM 해시 비교 (PAC-4)

- **Given**: `extracted/section_03_spec.json` + 동일 구조 HTML
- **When**: `python3 tools/structural-diff.py --spec extracted/section_03_spec.json --html <matching.html>` 실행
- **Then**: exit 0, "STRUCTURAL MATCH" 출력
- **Test**: `pytest tests/unit/test_structural_match.py -v` (신규)

### AC-004 [automatable] 구조 불일치 감지 (PAC-4)

- **Given**: spec 과 구조적으로 다른 HTML (children count 또는 tag name mismatch)
- **When**: 동일 명령 실행
- **Then**: exit 1, "STRUCTURE_DRIFT" 출력 + 차이점 리포트
- **Test**: `pytest tests/unit/test_structural_drift.py -v` (신규)

### AC-005 [automatable] pyproject.toml playwright 의존성 (PAC-4)

- **Given**: `pyproject.toml`
- **When**: `grep "playwright" pyproject.toml`
- **Then**: `playwright>=1.42` 선언
- **Test**: `pytest tests/unit/test_pyproject_playwright.py -v` (신규)

## §3.2 Test Scenarios (Pre-Impl)

- AC-001: `pytest tests/unit/test_structural_hash_determinism.py -v` (10회 해시 일치)
- AC-002: `pytest tests/unit/test_structural_hash_docs.py -v`
- AC-003: `pytest tests/unit/test_structural_match.py -v`
- AC-004: `pytest tests/unit/test_structural_drift.py -v`
- AC-005: `pytest tests/unit/test_pyproject_playwright.py -v`

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-4 | MUST | AC-003, AC-004, AC-005 | full |
| PAC-5 | MUST | AC-001, AC-002 | full |

## §3.5 Constraints

- Python 3.10+, Playwright Python 1.42+
- headless chromium 전용 (firefox/webkit 불필요)
- 정규화 알고리즘: tag + sorted(class_list) + children_index_path
- text content / id attr / inline style 모두 무시 (구조만 비교)
- 기존 `tests/` 회귀 없음

## §5 선행 작업 (blockedBy)

- REQ-035 완료 (이미 완료)

## §6 후행 작업 (blocks)

- REQ-036 / Task 02 (post-impl-verify 통합)

## §7 Assigned Agent

`[config: codex-dev] codex-dev`

## §8 의존성 테이블

| Task | blockedBy | blocks | Agent |
|------|-----------|--------|-------|
| 01 | — | 02 | codex-dev |
| 02 | 01 | — | codex-dev |

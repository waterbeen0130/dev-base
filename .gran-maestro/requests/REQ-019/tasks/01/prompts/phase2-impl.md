# Phase 2 구현 요청 — REQ-019 / Task 01

**REQ**: REQ-019 — validate-semantic.py 신규 6규칙 추가 (PLN-007 Layer A)
**Task**: 01 (단일)
**Plan**: /mnt/d/dev-base/.gran-maestro/plans/PLN-007/plan.md
**Spec**: /mnt/d/dev-base/.gran-maestro/requests/REQ-019/tasks/01/spec.md
**Discussion 합의**: /mnt/d/dev-base/.gran-maestro/discussion/DSC-002/consensus.md
**Worktree**: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-019-T01 (gran-maestro/REQ-019-T01 브랜치)

## IMPL_CONTEXT

무엇을: `tools/validate-semantic.py`에 6개 신규 규칙(`no_hex8_literal`, `line_height_tidy_ratio`, `font_family_redundant`, `empty_media_block`, `box_sizing_redundant`, `landing_unit_mixed_scale`)을 추가하고 `--profile landing|basic` 플래그를 지원한다.

왜: Figma→퍼블리싱 파이프라인 결과물에서 규칙(common.md/basic.md/landing.md) 위반이 반복되며 현재 검증기가 이를 catch하지 못해 자동 재dispatch 루프가 작동하지 않는다. 두 실측 증거 프로젝트(`/mnt/d/위링/2026-04-15 목포플레이파크`, `/mnt/d/위링/2026-04-15 에이스디펜스`)에서 위반 예시를 확인할 수 있다.

어떻게:
1. 먼저 `tools/validate-semantic.py`와 기존 테스트(`tests/`)를 Read하여 rule 구조/명명 규칙/CLI 인자 처리/출력 포맷을 파악한다.
2. **TDD 준수** — 각 규칙마다 `tests/test_validate_semantic_new_rules.py`에 단위 테스트를 먼저 작성하고 실패하는 것을 확인한 뒤 구현한다.
3. 정돈 알고리즘 (핵심): `raw = round(lineHeightPx/fontSize,3); step=0.05; snapped=round(raw/step)*step; tolerance=0.03; if abs(raw-snapped)<=tolerance: snapped, else: raw preserve`. 정돈 후보 목록 `{1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0}`.
4. `.project-type` 파일(프로젝트 루트) 읽기 유틸을 추가. 값: `basic` | `landing`. 미존재 시 `all` 프로파일로 graceful fallback.
5. 출력 포맷 통일: `[SEVERITY] rule_id — message (file:line)`.
6. **false-positive 억제 가드 필수**:
   - `no_hex8_literal`: `/*...*/` 주석 내, `url(data:)` 내 hex8 제외
   - `line_height_tidy_ratio`: `1`, `normal`, `var(--`, `/* lh-exact */` 마커 예외
   - `font_family_redundant`: fallback 체인이 다른 경우 별개 취급
   - `empty_media_block`: `@media print` 예외
   - `box_sizing_redundant`: `*`, `*::before`, `*::after` 허용
   - `landing_unit_mixed_scale`: `--profile basic`에서는 skip
7. 기존 규칙은 **수정 금지** — 신규 규칙만 추가. 기존 테스트가 PASS를 유지해야 한다 (AC-008 회귀 테스트).
8. 구현 완료 후 아래 명령들을 직접 실행해 검증:
   - `pytest tests/test_validate_semantic_new_rules.py -v`
   - `python3 tools/validate-semantic.py --html "/mnt/d/위링/2026-04-15 목포플레이파크/html/page/index.html" --css "/mnt/d/위링/2026-04-15 목포플레이파크/html/css/common.css" --profile landing`
   - `python3 tools/validate-semantic.py --html "/mnt/d/위링/2026-04-15 에이스디펜스/html/page/index.html" --css "/mnt/d/위링/2026-04-15 에이스디펜스/html/css/common.css" --profile landing`

주의:
- Python 3 stdlib만 사용 (cssutils 등 외부 라이브러리 신규 도입 금지)
- `_check_*` 명명 패턴 유지
- 출력 포맷 절대 변경 금지 (기존 호환)
- 커밋은 작성하지 말 것 — PM이 별도로 커밋한다

## 주요 참조 파일

반드시 Read할 파일:
- `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-019-T01/tools/validate-semantic.py` — 수정 대상
- `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-019-T01/rules/common.md` — 검사 기준
- `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-019-T01/rules/basic.md`
- `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-019-T01/rules/landing.md`
- `/mnt/d/dev-base/.gran-maestro/requests/REQ-019/tasks/01/spec.md` — AC 전체
- `/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/consensus.md` §1 Layer A (구체 스펙)
- `/mnt/d/dev-base/.gran-maestro/plans/PLN-007/plan.md` (컨텍스트)

회귀 테스트 입력 (증거 프로젝트):
- `/mnt/d/위링/2026-04-15 목포플레이파크/html/css/common.css` (hex8, line-height 비정돈, font-family 중복, 빈 미디어쿼리 포함)
- `/mnt/d/위링/2026-04-15 에이스디펜스/html/css/common.css` (landing_unit_mixed_scale 증거)

## 완료 기준 (AC 요약)

- AC-001~006: 6규칙 각각 단위 테스트 PASS (TDD)
- AC-007: `.project-type` 자동 읽기 + flag override
- AC-008: 기존 테스트 회귀 없음
- AC-009: 두 증거 프로젝트에서 기대 위반 카운트 이상 검출 (hex8 ≥1, line-height ≥4, 빈 미디어쿼리 ≥3, font-family 중복 ≥10)

## Previous Feedback
N/A (첫 실행)

## REFERENCE_CONTEXT
references: none

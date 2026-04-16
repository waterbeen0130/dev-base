# REQ-019 / Task 01 — validate-semantic.py 신규 6규칙 추가

**Assigned Agent**: [config: codex-dev] → codex-dev (Python 도구 확장, 기존 `tools/validate-semantic.py` 수정)
**Source Plan**: PLN-007
**Linked Discussion**: DSC-002

## §0 Context Manifest

> 이 목록은 에이전트가 **반드시 먼저 Read**할 최소 진입점입니다. 완전한 목록이 아니며, 에이전트는 필요 시 자율적으로 추가 탐색합니다.

- `/mnt/d/dev-base/tools/validate-semantic.py` — 기존 규칙 검증기 (수정 대상)
- `/mnt/d/dev-base/rules/common.md` — 공통 CSS/HTML 규칙 (검사 기준)
- `/mnt/d/dev-base/rules/basic.md` — basic 프로젝트 규칙 (profile 분기)
- `/mnt/d/dev-base/rules/landing.md` — landing 프로젝트 규칙 (profile 분기)
- `/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/consensus.md` — 6규칙 구체 스펙
- `/mnt/d/dev-base/.gran-maestro/plans/PLN-007/plan.md` — PAC 및 범위
- `/mnt/d/위링/2026-04-15 목포플레이파크/html/css/common.css` — 회귀 테스트 입력 (위반 증거)
- `/mnt/d/위링/2026-04-15 에이스디펜스/html/css/common.css` — 회귀 테스트 입력

## §1 요약

`tools/validate-semantic.py`에 6개 신규 규칙을 추가하고 `--profile landing|basic` flag에 따라 분기 동작시킨다. 기존 규칙/출력 포맷은 변경하지 않는다.

## §2 범위

**포함**:
- 6개 신규 rule 함수 구현 (`no_hex8_literal`, `line_height_tidy_ratio`, `font_family_redundant`, `empty_media_block`, `box_sizing_redundant`, `landing_unit_mixed_scale`)
- 각 규칙의 심각도 부여 및 출력 포맷 통일 (`[SEVERITY] rule_id — message (file:line)`)
- `--profile landing|basic` 플래그 지원 (미지정 시 프로젝트 루트 `.project-type` 파일 읽기, 없으면 `all` 프로파일)
- 기존 ruleset 회귀 방지

**제외**:
- `figma-section-spec.py`/`post-impl-verify.py` 변경 (REQ-020/REQ-021 책임)
- `.project-type` 파일 생성 로직 (REQ-023 책임, 여기서는 "읽기만" 지원)

## §3 수락 조건 (Acceptance Criteria)

### AC-001 [automatable] [unit-test] [tdd-required] — `no_hex8_literal` 규칙
- **Given**: CSS 내용에 `color:#ffffff26;` 같은 8자리 hex 리터럴이 존재
- **When**: `validate-semantic.py --html ... --css ... --profile landing` 실행
- **Then**: 출력에 `[MAJOR] no_hex8_literal — ... (css:line)` 항목이 1건 이상 포함되고 exit code 1 반환
- **Test**: 테스트 CSS 파일(주석 내 hex8, `url(data:)` 포함본)을 만들고 주석/데이터 URL은 무시, 실제 값만 검출되는지 assert

### AC-002 [automatable] [unit-test] [tdd-required] — `line_height_tidy_ratio` 규칙
- **Given**: CSS 내 `line-height:1.193` (후보 비율 목록 `{1.0,1.1,1.2,1.25,1.3,1.4,1.45,1.5,1.6,1.667,1.75,1.8,2.0}`에서 step 0.05 + tolerance 0.03 기준 정돈 안 됨)
- **When**: validator 실행
- **Then**: `[MAJOR] line_height_tidy_ratio — ... (css:line)` 검출. `/* lh-exact */` 마커가 붙은 줄은 예외
- **Test**: 정상(1.3, 1.45, 1.667, 1.8) + 비정돈(1.193, 1.471, 1.818) 각 케이스 포함한 테스트 CSS로 검증

### AC-003 [automatable] [unit-test] [tdd-required] — `font_family_redundant` 규칙
- **Given**: 동일 font-family가 `*`, `body`, 개별 selector에 3회 이상 반복 선언된 CSS
- **When**: validator 실행
- **Then**: `[MAJOR] font_family_redundant — ...` 검출. fallback 체인이 다른 경우는 별개로 취급 (제외)
- **Test**: 목포플레이파크 common.css 수준(20회 반복)과 정상(`*{}` 1회) 케이스 비교

### AC-004 [automatable] [unit-test] [tdd-required] — `empty_media_block` 규칙
- **Given**: `@media screen and (max-width: 1200px) { }` 같이 body가 공백/주석뿐인 미디어쿼리
- **When**: validator 실행
- **Then**: `[MAJOR] empty_media_block — ...` 검출. `@media print { }`은 예외
- **Test**: 목포플레이파크 common.css 72–79 라인 (빈 블록 3개) 모두 검출되는지 확인

### AC-005 [automatable] [unit-test] — `box_sizing_redundant` 규칙
- **Given**: `*{box-sizing:border-box}` 이외에 개별 selector에서 `box-sizing:border-box` 반복 선언
- **When**: validator 실행
- **Then**: `[MINOR] box_sizing_redundant — ...` 검출 (advisory-MINOR)
- **Test**: `*`/`*::before`/`*::after` 선언은 허용됨을 함께 검증

### AC-006 [automatable] [unit-test] [tdd-required] — `landing_unit_mixed_scale` 규칙
- **Given**: `--profile landing` 실행이고 CSS에 `html{font-size:clamp(14px,1.2vw,16px)}` 또는 `body{font-size:...rem...}` 존재
- **When**: validator 실행
- **Then**: `[MAJOR] landing_unit_mixed_scale — ...` 검출. `--profile basic`에서는 skip
- **Test**: 에이스디펜스 common.css line 19 / 목포플레이파크 line 10이 landing 프로파일에서 검출되고 basic 프로파일에서 skip되는지 확인

### AC-007 [automatable] [build-check] — `--profile` 플래그 및 SoT 연동
- **Given**: 프로젝트 루트에 `.project-type` 파일이 `landing` 값으로 존재
- **When**: `--profile` flag 없이 `validate-semantic.py --html ... --css ...` 실행
- **Then**: 자동으로 landing 프로파일이 적용된다. `.project-type` 미존재 시 `all` 프로파일로 동작(기존 호환)
- **Test**: 두 시나리오(존재/미존재) 각각 CLI 실행

### AC-008 [automatable] [regression-test] — 기존 규칙 회귀 방지
- **Given**: 기존 통과하던 테스트 CSS/HTML 케이스
- **When**: 신규 규칙이 추가된 validator 실행
- **Then**: 기존 rule_id 출력 및 exit code가 변하지 않는다
- **Test**: 기존 레포 내 validator 호출 예시(PLN-005 REQ-015 산출물)가 여전히 동일 exit code를 반환하는지 dry-run

### AC-009 [browser-test] [e2e-browser] — 두 증거 프로젝트 회귀 검출 (PAC-9 매핑)
- **Given**: `/mnt/d/위링/2026-04-15 목포플레이파크/html` 과 `/mnt/d/위링/2026-04-15 에이스디펜스/html` 소스
- **When**: `validate-semantic.py --html page/index.html --css css/common.css --profile landing` 실행
- **Then**: 목포 — hex8 1건, 비정돈 line-height ≥4건, 빈 미디어쿼리 3건, font-family 중복 ≥10건 모두 MAJOR로 검출
- **Test**: 명령 실행 결과를 캡처해 rule_id 카운트가 기대치 이상인지 확인

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----|
| PAC-1 | MUST | AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007 | FULL |
| PAC-9 | SHOULD | AC-009 | FULL |
| PAC-10 | SHOULD [IMPACT] | AC-008 | PARTIAL (REQ-020/021에서 완전 커버) |

## §3.5 Constraints

- Python 3.10+, stdlib 우선 (cssutils 같은 외부 라이브러리 신규 도입 금지)
- 규칙별 검사 함수는 기존 `_check_*` 명명 패턴을 따른다
- 출력 포맷: `[SEVERITY] rule_id — message (file:line)` 형식 고정
- false-positive 억제 가드(주석 내 hex8, `url(data:)`, `@media print` 등) 반드시 포함

## §5 선행 작업 (blockedBy)
- 없음

## §6 후행 작업 (blocks)
- REQ-020 (figma-section-spec.py preprocess)
- REQ-021 (post-impl-verify.py exit code 재정의)

## §7 의존성 테이블
| 태스크 | blockedBy | blocks | agent |
|---|---|---|---|
| REQ-019/01 | — | REQ-020, REQ-021 | codex-dev |

## §8 구현 지침

> 테스트를 먼저 작성한 후 구현하세요 (TDD). 각 규칙마다 unit test → impl 순서.

1. `tools/validate-semantic.py`를 읽고 기존 rule 구조, ruleset 배열, CLI 인자 처리 흐름을 파악한다.
2. `.project-type` 읽기 유틸을 추가한다 (미존재 시 graceful fallback to `all`).
3. 6개 규칙 함수를 순서대로 TDD로 구현한다. `tests/test_validate_semantic_new_rules.py` 신설.
4. `--profile` CLI 인자 처리 확장. 기존 인자와 충돌 없도록 optional로 추가.
5. 회귀 테스트: 기존 호출 예시 dry-run으로 exit code 불변 확인.
6. 두 증거 프로젝트(목포/에이스)에 돌려 AC-009 기대치 검증.

## Test Scenarios (Pre-Impl)

각 AC에 대한 실행 검증 방법:

- **AC-001 Test**: 테스트 CSS 파일 (주석 hex8 + `url(data:)` + 실제 `#ffffff26` 혼합) 준비 후 `python3 tools/validate-semantic.py --css tests/fixtures/hex8.css --html tests/fixtures/empty.html --profile landing` 실행 → stdout에 `[MAJOR] no_hex8_literal` 1건 + exit code 1 확인
- **AC-002 Test**: 테스트 CSS (정상 1.3/1.45/1.667/1.8 + 비정돈 1.193/1.471/1.818 + `/* lh-exact */` 마커 예외) → 비정돈 3건만 `[MAJOR] line_height_tidy_ratio` 검출
- **AC-003 Test**: font-family 중복 20회 + fallback 체인 다른 케이스 분리 → 중복만 검출, 다른 체인은 제외
- **AC-004 Test**: `@media screen and (max-width:1200px){}` + `@media print{}` → 전자만 `[MAJOR] empty_media_block` 검출
- **AC-005 Test**: `*{box-sizing:border-box}` + 개별 3회 반복 → `[MINOR] box_sizing_redundant` 3건 (universal 선언 제외)
- **AC-006 Test**: `html{font-size:clamp(14px,1.2vw,16px)}` 포함 CSS → `--profile landing`에서 `[MAJOR] landing_unit_mixed_scale` 검출, `--profile basic`에서 0건
- **AC-007 Test**: 프로젝트 루트에 `.project-type=landing` 생성 후 flag 없이 실행 → landing 프로파일 적용 로그 확인. 삭제 후 재실행 → `all` 프로파일 동작
- **AC-008 Test**: PLN-005 REQ-015 산출물 검증 명령(`python3 tools/validate-semantic.py ...`)을 그대로 실행 → 기존 exit code와 동일
- **AC-009 Test**:
  ```bash
  python3 tools/validate-semantic.py \
    --html "/mnt/d/위링/2026-04-15 목포플레이파크/html/page/index.html" \
    --css "/mnt/d/위링/2026-04-15 목포플레이파크/html/css/common.css" \
    --profile landing
  ```
  → `no_hex8_literal` ≥1, `line_height_tidy_ratio` ≥4, `empty_media_block` ≥3, `font_family_redundant` ≥10 검출 확인. 에이스디펜스도 동일 명령으로 `landing_unit_mixed_scale` ≥1 검출 확인

## §5 테스트 계획
- 단위 테스트: `pytest tests/test_validate_semantic_new_rules.py -v`
- 회귀: `python3 tools/validate-semantic.py --html existing_test.html --css existing_test.css` (기존 케이스)
- 실행 검증: AC-009 명령어 2개 (목포/에이스)
- 타입 체크: N/A (Python 3 stdlib only, mypy 미적용)

## §10 관련 파일 시작점 (에이전트 탐색 힌트)
- `/mnt/d/dev-base/tools/validate-semantic.py`
- `/mnt/d/dev-base/tests/` (기존 테스트 구조 확인)
- `/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/consensus.md` §1 Layer A

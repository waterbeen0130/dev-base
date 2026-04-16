# REQ-026 / Task 01 — repair-from-violations.py + auto-fix 루프

**Assigned Agent**: [config: codex-dev] → codex-dev (Python CLI, CSS 파싱, TDD)
**Source Plan**: PLN-008
**Linked Debug**: DBG-001

## §0 Context Manifest

- `/mnt/d/dev-base/tools/post-impl-verify.py` (확장 대상 — 현재 REQ-024 이후 파서 버그픽스 반영됨)
- `/mnt/d/dev-base/tools/validate-semantic.py` (참조 — 규칙 구조 파악)
- `/mnt/d/dev-base/tools/figma-validate.py` (참조 — 출력 포맷)
- `/mnt/d/dev-base/rules/rules.yaml` (3개 TODO 마커 제거 대상)
- `/mnt/d/dev-base/rules/deprecated.md` (이동 이력 업데이트)
- `/mnt/d/dev-base/extracted/section_03_spec.json`, `section_04_spec.json` (회귀 샘플)
- `/mnt/d/dev-base/.gran-maestro/debug/DBG-001/debug-report.md` (근거)

## §1 요약

결정론적으로 해결 가능한 CSS/HTML 위반을 **LLM 재dispatch 없이 자동 수정**하는 `tools/repair-from-violations.py`를 신규 작성하고, `tools/post-impl-verify.py`에 1회 auto-repair 루프를 통합한다. 이 작업이 완료되면 DBG-001이 식별한 "Post-hoc 검증 + auto-fix 부재"(H3) 문제의 구조적 해소가 달성된다.

**효과**: 섹션당 수동 수정 5~6회 → 1~2회로 직접 감축. 재dispatch 대상은 "결정론적 치환 불가능한 의미 수정"만 남음.

## §2 범위

### 포함 (In-scope)

#### 신규 스크립트 `tools/repair-from-violations.py`

CLI 형식:
```bash
python3 tools/repair-from-violations.py --html <path> --css <path> [--violations <json>] [--dry-run] [--report <path>]
```

**입력**:
- `--html`: 수정 대상 HTML 파일 경로
- `--css`: 수정 대상 CSS 파일 경로
- `--violations`: (선택) `figma-validate.py`/`validate-semantic.py`가 출력한 JSON 위반 리포트. 미제공 시 스크립트가 직접 `validate-semantic.py`를 호출하여 위반 수집
- `--dry-run`: 수정 없이 diff만 출력
- `--report`: (선택) 수정 결과를 JSON으로 저장할 경로

**결정론적 치환 규칙** (최소 이 범위):

| # | 패턴 | 변환 | 근거 |
|---|---|---|---|
| 1 | `border-radius: 999px` (또는 `9999px`, `99px`) pill 의도 | `border-radius: 2em` | rules/common.md |
| 2 | `rgba(r, g, b, 1)` 또는 `rgba(r, g, b, 1.0)` 불투명 | `#RRGGBB` hex | rules/common.md: hex 전용 |
| 3 | `rgb(r, g, b)` | `#RRGGBB` hex | rules/common.md: hex 전용 |
| 4 | 8자리 hex `#RRGGBBAA` (`AA == FF`) | `#RRGGBB` 6자리 | rules/common.md |
| 5 | CSS 멀티라인 셀렉터 (여러 줄에 걸친 단일 규칙 블록) | 한 줄 포맷 | rules/common.md |
| 6 | `@media` 블록 내부 들여쓰기 | 들여쓰기 제거 | rules/common.md |
| 7 | `letter-spacing: Npx` (N을 해당 셀렉터 font-size로 나눠 em 변환 가능한 경우만) | `letter-spacing: Xem` | rules/common.md: em 전용 |
| 8 | 동일 셀렉터 중복 선언 (연속된 블록 2개 이상) | 단일 블록으로 통합 | rules/common.md |

**제외 치환** (이번 REQ 범위 아님):
- 폰트 5필드 완결성 (의미 결정 필요 — LLM 영역)
- 클래스명 규칙 (`sec_1` → 의미 있는 이름, LLM 영역)
- HTML 태그 변경 (`<p>` → `<span>`, LLM 영역)
- figma spec과의 수치 일치 (frame padding/gap 등)

**구현 기법**:
- CSS 파싱: `tinycss2` 우선, 실패 시 정규식 fallback (tinycss2가 파싱 못 하는 edge case 대비)
- HTML 파싱: 최소. letter-spacing em 변환에만 BeautifulSoup 또는 정규식으로 font-size 컨텍스트 조회
- 멱등성: 같은 입력에 스크립트를 2회 실행 시 2회차는 변경 0건 (idempotent)

**출력**:
- stdout: 수정 요약 (치환 카테고리별 건수, 변경 파일 목록)
- `--report` 지정 시 JSON:
  ```json
  {
    "total_fixed": 12,
    "by_category": {
      "pill_radius": 2,
      "rgba_to_hex": 5,
      "multiline_selector": 3,
      "media_indent": 2
    },
    "files_modified": ["output/...css"],
    "unfixable_count": 0,
    "dry_run": false
  }
  ```
- exit code: 0 (성공), 1 (아무것도 못 고침 + 위반 남아있음), 2 (파싱 오류)

#### `tools/post-impl-verify.py` 확장

현재 파이프라인: `figma-validate` + `validate-semantic` → 위반 분류 → PM에 반환.

**확장**:
1. 위반 감지 시(`critical > 0` or `major > 0`):
   - 새 단계: `repair-from-violations.py` 1회 자동 호출 (dry-run 없이 실제 수정)
   - 수정 후 `figma-validate` + `validate-semantic` **재실행**
   - 재검증 결과를 최종 보고서로 사용
2. CLI 플래그 `--no-repair` 추가: auto-repair 비활성화 (기존 동작 유지)
3. 수정 로그 추가: `[auto-repair] {N} violations fixed (category: {categories})` 형태로 stdout 출력
4. 재실행 후에도 남은 위반은 기존 분류 로직(CRITICAL/MAJOR/IGNORE) 그대로 적용

**자동 repair-loop 횟수**: **1회만** (무한 루프 방지). 1회 후에도 남은 위반은 재dispatch 대상.

#### `validate-semantic.py` `--fix` 플래그

현재 `tools/validate-semantic.py:2936`에 `--fix` 인자가 **미구현** 상태(DBG-001 finding). 이번 REQ에서 해당 플래그를 실제로 작동시킨다:
- `--fix` 지정 시 `repair-from-violations.py`의 치환 로직을 내부 재사용하거나 subprocess로 호출
- `--fix` 미지정 시 기존 검증만 수행 (호환성 유지)

#### REQ-024 TODO 마커 제거

`rules/rules.yaml`의 3개 TODO 마커(`:173`, `:197`, `:208`)와 해당 규칙 블록 처리:
- TODO 마커는 **auto-fix 완성 후 규칙 삭제 예정**으로 남겨둔 것
- 실제 해당 규칙이 auto-fix로 대체 가능한지 확인 후:
  - 가능: `rules.yaml`에서 규칙 삭제 + `rules/deprecated.md`에 이동 이력 추가 (대체 수단: `repair-from-violations.py {category}`)
  - 불가능: TODO 마커만 제거하고 규칙 유지 + 코멘트로 "auto-fix로 처리됨, 룰 엔진에서는 검증만" 명시

### 제외 (Out-of-scope)
- figma-section-spec.py 확장 (REQ-028 범위)
- Rule-ID 브리프 주입 (REQ-027 범위)
- 실제 퍼블리싱 프로젝트에서 end-to-end 테스트 (수동 검증은 회귀 샘플로만)
- 병렬 repair (단일 프로세스 순차 실행으로 충분)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] — repair-from-violations.py 존재 + CLI 동작
- **Given**: `tools/repair-from-violations.py` 미존재
- **When**: REQ-026 완료 후 `python3 tools/repair-from-violations.py --help` 실행
- **Then**: usage 출력 + exit 0
- **Test**: `python3 tools/repair-from-violations.py --help` → exit 0

### AC-002 [automatable] [tdd-required] — 치환 8종 단위 테스트
- **Given**: 각 치환 카테고리별 fixture (CSS/HTML 샘플 + 기대 변환 결과)
- **When**: `python3 -m pytest tests/test_repair_from_violations.py -v`
- **Then**: 8개 치환 카테고리 각 1+ 케이스 PASS (총 ≥ 8 테스트)
- **Test**: 위 pytest 명령 exit 0

### AC-003 [automatable] [tdd-required] — 멱등성
- **Given**: 임의의 CSS 파일에 repair 1회 적용한 결과
- **When**: 같은 파일에 repair 2회차 적용
- **Then**: 2회차 출력 `total_fixed == 0` + 파일 내용 동일
- **Test**: `tests/test_repair_idempotent.py` 또는 `test_repair_from_violations.py`에 idempotency 케이스 포함

### AC-004 [automatable] [tdd-required] — post-impl-verify 통합 + 로그
- **Given**: 의도적 위반(pill 999px + rgb() + 멀티라인 셀렉터)이 주입된 샘플 HTML/CSS
- **When**: `python3 tools/post-impl-verify.py --spec ... --html ... --css ...` 실행 (--no-repair 미사용)
- **Then**: stdout에 `[auto-repair] N violations fixed` 포함 + 재검증 결과에서 해당 위반 개수 감소 확인
- **Test**: `tests/test_post_impl_auto_repair.py` — subprocess 호출 후 stdout grep `[auto-repair]` + 재검증 pass

### AC-005 [automatable] [tdd-required] — `--no-repair` 호환성
- **Given**: `--no-repair` 플래그
- **When**: 기존 pre-REQ-026 post-impl-verify 동작과 비교
- **Then**: auto-repair 로그 없이 기존 동작 그대로 (회귀 없음)
- **Test**: `tests/test_post_impl_no_repair.py` — `--no-repair` 실행 stdout에 `[auto-repair]` 미포함

### AC-006 [automatable] [regression-test] — pytest 전체 회귀
- **Given**: REQ-024 + REQ-025 이후 기존 pytest 스위트 (32 passed / 33 skipped 기준)
- **When**: REQ-026 완료 후 `python3 -m pytest tests/ -v`
- **Then**: 기존 PASS가 유지되고 신규 테스트가 추가되어 총 PASS 수 증가 + FAIL 0건
- **Test**: pytest 전체 실행 exit 0

## §3.3 PAC Mapping

| PAC ID | Grade | Tier | Mapped Spec AC | Coverage |
|--------|-------|------|----------------|----------|
| PAC-4  | MUST  | TIER-A | AC-001, AC-004 | full |
| PAC-7  | SHOULD | TIER-B | AC-005, AC-006 | full |

## 3.5 Test Scenarios (Pre-Impl)

### TS-001 (AC-001)
```bash
python3 tools/repair-from-violations.py --help
```
기대: exit 0, usage 출력

### TS-002 (AC-002)
```bash
python3 -m pytest tests/test_repair_from_violations.py -v
```
기대: 8+ 테스트 PASS

### TS-003 (AC-003)
```bash
python3 -m pytest tests/test_repair_from_violations.py::test_idempotent -v
```
기대: PASS

### TS-004 (AC-004)
의도적 위반 샘플 fixture 생성 (CSS에 `border-radius: 999px;`, `color: rgb(0, 0, 0);`, 멀티라인 셀렉터) 후:
```bash
python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html tests/fixtures/dirty.html --css tests/fixtures/dirty.css --profile basic 2>&1 | grep -c "\[auto-repair\]"
```
기대: `>= 1`

### TS-005 (AC-005)
```bash
python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html tests/fixtures/dirty.html --css tests/fixtures/dirty.css --profile basic --no-repair 2>&1 | grep -c "\[auto-repair\]"
```
기대: `0`

### TS-006 (AC-006)
```bash
python3 -m pytest tests/ -v
```
기대: REQ-025 시점 카운트(32 passed, 33 skipped) **이상**으로 PASS 증가, FAIL 0

### TS-007 (회귀 — 기존 섹션 재검증)
```bash
python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html output/youngwol/index.html --css output/youngwol/common.css --profile basic
python3 tools/post-impl-verify.py --spec extracted/section_04_spec.json --html output/youngwol/index.html --css output/youngwol/common.css --profile basic
```
기대: ValueError 없이 정상 종료. exit code는 REQ-024 baseline(exit 1 with same counts)과 **동일 또는 감소**.

### TS-008 (rules.yaml TODO 마커 제거 확인)
```bash
grep -c "TODO(REQ-026)" rules/rules.yaml
```
기대: `0`

## §3.5 Constraints

- Python 3.10+
- CSS 파싱: `tinycss2` 우선 (이미 있으면 사용, 없으면 `pip install tinycss2`), 정규식 fallback 허용
- HTML: BeautifulSoup4 (이미 있음) 또는 정규식
- **post-impl-verify.py 기존 exit 코드 체계 유지** — auto-repair는 exit 코드 영향 없음 (통과 이동/감축만)
- 멱등성 필수 (idempotency)
- `--dry-run` 모드에서는 파일 수정 금지, diff만 stdout 출력
- rules/deprecated.md에 TODO 제거된 규칙의 대체 수단 기록

## §5 선행 작업 (blockedBy)
- REQ-024 ✅ (규칙 슬림, 파서 버그픽스)
- REQ-025 ✅ (Spec-only 원칙)

## §6 후행 작업 (blocks)
- REQ-027 (Rule-ID 브리프 — auto-fix 완성 후 브리프에서 포맷팅 규칙 제거 가능)

## §7 의존성 요약
- 관련: DBG-001 (H3 진단), PLN-008, REQ-024, REQ-025

## §8 테스트 전략
- TDD 필수: AC-001/002/003/004/005/006 모두 테스트 먼저 작성
- 신규 테스트 파일: `tests/test_repair_from_violations.py`, `tests/test_post_impl_auto_repair.py`, `tests/test_post_impl_no_repair.py`
- fixture 디렉토리: `tests/fixtures/repair/` 신설 (dirty HTML/CSS 샘플)
- 회귀: 기존 pytest 32 passed + 신규 ≥ 10 테스트

## §9 디버그 연계
- **참조**: DBG-001 H3 (Post-hoc 피드백 루프 + auto-fix 부재)
- **근거**: `tools/validate-semantic.py:2936` `--fix` 미구현
- **본 REQ 대응**: repair-from-violations.py 신규 + post-impl-verify 통합 + validate-semantic `--fix` 구현으로 H3 구조적 해소

# REQ-024 / Task 01 — 규칙 슬림 + 충돌 제거

**Assigned Agent**: [config: codex-dev] → codex-dev (Python rules/yaml + validate-semantic.py 수정, 퍼블리싱 아님)
**Source Plan**: PLN-008
**Linked Debug**: DBG-001

## §0 Context Manifest

> 아래 목록은 완전하지 않을 수 있습니다. 에이전트는 worktree에서 자율 탐색을 병행하세요.

- `rules/rules.yaml`
- `rules/common.md`
- `rules/codex.md`
- `rules/gemini.md`
- `rules/validation_schema.json`
- `tools/validate-semantic.py`
- `.gran-maestro/debug/DBG-001/debug-report.md` (근거)
- `.gran-maestro/debug/DBG-001/finding-codex.md` (파일·라인 근거)

## §1 요약

DBG-001 진단 결과 기반으로 현재 규칙 체계의 **중복·충돌·미연결 규칙**을 제거한다. 이 REQ는 A→E→B→D→C 순차 개선의 첫 단계로, 후속 REQ의 기반을 만든다. Quick win 성격.

**목표**: `rules.yaml` 규칙 수 97 → 60 이하, 내부 모순 0건, `column flex gap 금지` 규칙 실제 호출 확인.

## §2 범위

### 포함 (In-scope)
1. **중복/충돌 룰 제거**:
   - `flexbox_layout` ↔ `no_css_grid` 중복 → 단일 규칙으로 통합
   - `forbidden_tag` ↔ `no_figure_figcaption` 중복 → 단일 규칙으로 통합
   - `root_var_naming` 충돌 해소 (`rules/common.md:196` vs `rules/codex.md:43`) — 한 방향으로 통일하고 반대 방향 문서 수정
   - `no_raw_calc` / `no_raw_vw` 충돌 해소 (`rules/rules.yaml:246-264` vs `rules/codex.md:49,75` 예시) — rules.yaml을 truth로 삼고 codex.md 예시를 정합화
2. **validator 연결 누락 보강**:
   - `column flex gap 금지` 규칙: 함수는 `tools/validate-semantic.py:2626-2648`에 존재하지만 룰 엔진에 연결되어 있지 않음 → 규칙 디스패치 테이블에 등록
3. **`manual_review` 7개 + `documentation` 3개 규칙 판단**:
   - 현재 `validate-semantic.py:1459-1460` 및 `:2885-2894`에서 skip됨 (DBG-001 Open Question #1)
   - 판단 기준: 실행 가능한 검증 로직으로 구현 가능한 규칙은 실행화 (별도 issue), 불가능한 규칙은 `rules.yaml`에서 삭제
4. **삭제 예정 마킹**: 자동 검증 불가능한 포맷팅 규칙(CSS 한 줄, 미디어쿼리 들여쓰기 등)은 이번 REQ에서는 주석 `# TODO(REQ-026): remove after auto-fix introduced`만 추가. 실제 삭제는 REQ-026 완료 후.

### 제외 (Out-of-scope)
- 신규 규칙 추가 (REQ-027 범위)
- auto-fix 루프 구현 (REQ-026 범위)
- 인라인 브리프 주입 방식 변경 (REQ-027 범위)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] — rules.yaml 규칙 수 감축
- **Given**: 수정 전 `rules/rules.yaml`에 규칙 97개 존재 (DBG-001 기준)
- **When**: REQ-024 완료 후 `python3 -c "import yaml; print(len(yaml.safe_load(open('rules/rules.yaml'))))"` 또는 동등한 카운트 수행
- **Then**: 규칙 수가 60개 이하로 감소한다
- **Test**: 위 파이썬 one-liner가 60 이하 정수를 출력. CI/로컬 모두 재현 가능.

### AC-002 [automatable] [tdd-required] — 중복 규칙 제거 확인
- **Given**: 중복 쌍 4건 (`flexbox_layout`/`no_css_grid`, `forbidden_tag`/`no_figure_figcaption`)
- **When**: `grep -E "^\s*(flexbox_layout|no_css_grid|forbidden_tag|no_figure_figcaption):" rules/rules.yaml` 실행
- **Then**: 각 카운트가 1 이하로 감소한다 (통합 후 단일 이름만 남거나 한 쪽 완전 삭제)
- **Test**: 위 grep 결과를 쉘에서 `wc -l`하여 2 이하(통합된 2건) 또는 0건 확인

### AC-003 [manual] [tdd-required] — 충돌 규칙 해소 문서 정합성
- **Given**: `rules/common.md:196`의 `root_var_naming` 방향과 `rules/codex.md:43`의 방향이 상충. `rules/rules.yaml:246-264`의 `no_raw_calc`/`no_raw_vw` 금지와 `rules/codex.md:49,75` 예시가 상충.
- **When**: PM 또는 리뷰어가 수정 후 파일들을 읽어 일관성을 확인
- **Then**: 각 충돌 쌍에서 한 방향으로 통일되고, 반대 방향 문서의 해당 기술이 제거되거나 통일 방향에 맞게 수정됨
- **Test**: `rules/common.md`, `rules/codex.md`, `rules/gemini.md`, `rules/rules.yaml`에서 `root_var_naming`, `no_raw_calc`, `no_raw_vw` 키워드를 grep하여 수동 검토. 충돌 없음 확인.

### AC-004 [automatable] [tdd-required] — column flex gap 규칙 실제 호출 확인
- **Given**: `tools/validate-semantic.py:2626-2648`에 `column flex gap 금지` 함수가 존재하지만 룰 엔진에서 호출되지 않음
- **When**: 해당 함수를 룰 디스패치 테이블에 연결 후, 의도적 위반 샘플 HTML/CSS (세로 flex 컨테이너에 `gap` 사용)로 `validate-semantic.py` 실행
- **Then**: exit code 0이 아닌 값 + 위반 메시지가 출력된다
- **Test**: `tests/test_column_flex_gap.py` 신규 파일에 샘플 HTML/CSS fixture + subprocess 호출 테스트 추가. pytest 실행 시 해당 테스트가 신규 통과.

### AC-005 [automatable] [tdd-required] — 회귀 없음 (기존 통과 섹션 유지)
- **Given**: `/mnt/d/dev-base/extracted/section_03_spec.json` 및 `section_04_spec.json`을 기준 회귀 샘플로 사용. 대응 HTML/CSS는 worktree 탐색으로 확인 후 `/mnt/d/dev-base/output/` 하위 또는 `landing/`에서 식별
- **When**: 규칙 수정 후 해당 섹션 스펙을 기준으로 `tools/post-impl-verify.py` 재실행 (profile은 해당 섹션 타입에 맞춰 `landing` 또는 `all`)
- **Then**: exit code 0 유지 (회귀 없음). 위반 추가 발생 0건.
- **Test**: 최소 2개 샘플 섹션 (section_03, section_04)으로 `python3 tools/post-impl-verify.py --spec extracted/section_0X_spec.json --html <대응경로> --css <대응경로> --profile <타입>` 실행 후 exit 0 확인. 실패 시 해당 규칙 변경을 개별 커밋 단위로 revert 후 재검증.

### AC-006 [automatable] [regression-test] — 기존 validate-semantic 테스트 유지
- **Given**: `validate-semantic.py` 수정으로 기존 룰 디스패치 흐름이 변경될 수 있음
- **When**: 기존 pytest 스위트 또는 smoke 스크립트 재실행
- **Then**: 기존 통과 테스트가 여전히 통과한다
- **Test**: `python3 -m pytest tests/ -v` (존재 시) 또는 `python3 tools/validate-semantic.py --help` 스모크. 실패 0건.

## §3.3 PAC Mapping

| PAC ID | Grade | Tier | Mapped Spec AC IDs | Coverage |
|--------|-------|------|--------------------|----------|
| PAC-2  | MUST  | TIER-B | AC-001, AC-002 | full |
| PAC-7  | SHOULD | TIER-B | AC-005, AC-006 | full |

> PAC-1/3/4/5/6/8은 후속 REQ(E/B/D/C)에서 커버.

## 3.5 Test Scenarios (Pre-Impl)

> 각 AC의 Test 항목을 실행 가능한 명령어 단위로 정리. 구현 전 이 목록대로 테스트를 먼저 작성/검증한다 (TDD).

### TS-001 (AC-001 대응)
- **실행 명령**: `python3 -c "import yaml; d=yaml.safe_load(open('rules/rules.yaml'))['rules']; print(len(d))"`
- **기대 출력**: 60 이하의 정수 (현재 97)
- **실행 위치**: worktree 루트
- **통과 조건**: stdout 값이 60 이하

### TS-002 (AC-002 대응)
- **실행 명령**: `grep -cE "^\s*- id:\s*(flexbox_layout|no_css_grid|forbidden_tag|no_figure_figcaption)\s*$" rules/rules.yaml`
- **기대 출력**: 2 이하 (통합 후 단일 규칙만 남거나 완전 삭제)
- **통과 조건**: stdout 값이 2 이하

### TS-003 (AC-003 대응, manual)
- **검증 방법**: 아래 grep 결과를 사람이 검토하여 충돌이 없음을 확인한다.
  - `grep -rn "root_var_naming\|no_raw_calc\|no_raw_vw" rules/ CLAUDE.md`
- **통과 조건**: 각 키워드에 대해 rules/*.md와 rules.yaml이 같은 방향을 가리킨다 (한 파일은 금지하고 다른 파일은 예시로 허용하는 상황이 없다).
- **증거 기록**: `rules/deprecated.md`에 "이동/삭제된 규칙 ID + 대체 규칙 ID + 결정 이유"를 기록한다 (파일이 없으면 신규 생성).

### TS-004 (AC-004 대응, TDD)
- **테스트 파일 신규 작성**: `tests/test_column_flex_gap.py`
- **fixture**: 최소 2개 HTML 파일 (정상 케이스 + 위반 케이스) + 대응 CSS
  - 위반 케이스: `flex-direction: column` 컨테이너에 `gap: 20px` 사용
- **실행 명령**: `python3 -m pytest tests/test_column_flex_gap.py -v`
- **기대 결과**: 위반 케이스에서 validator가 에러 반환 (exit 비-0 또는 위반 메시지 포함)
- **통과 조건**: pytest 전체 통과

### TS-005 (AC-005 대응, 회귀)
- **실행 명령 1**: `python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html <대응 HTML 경로> --css <대응 CSS 경로> --profile <섹션 타입>`
- **실행 명령 2**: `python3 tools/post-impl-verify.py --spec extracted/section_04_spec.json --html <대응 HTML 경로> --css <대응 CSS 경로> --profile <섹션 타입>`
- **사전 준비**: worktree에서 `extracted/section_03_spec.json` / `section_04_spec.json`에 대응하는 구현 HTML/CSS 경로를 탐색해 문서화 (후보: `output/` 하위, `landing/`)
- **통과 조건**: 두 명령 모두 exit 0
- **실패 시**: 직전 rules 수정 커밋을 개별 revert 후 재검증 (rollback 단위를 1개 커밋 = 1개 규칙 변경으로 유지하여 회귀 원인 규명 용이)

### TS-006 (AC-006 대응, 스모크)
- **실행 명령 1**: `python3 tools/validate-semantic.py --help`
- **실행 명령 2**: `python3 tools/figma-validate.py --help`
- **기대 결과**: 두 명령 모두 exit 0 + usage 출력
- **통과 조건**: 기존 스크립트 entry point 및 옵션 파싱이 회귀 없이 동작

## §3.5 Constraints

- Python 3.10+
- `rules.yaml` 파싱: `pyyaml` 사용
- 기존 `post-impl-verify.py` 실행 경로를 변경하지 않음 (내부 룰 디스패치만 수정)
- rules 파일 수정은 git 단위 커밋으로 분리해 rollback 용이성 확보
- 역호환: 삭제된 규칙 ID가 외부에서 참조될 가능성 있음 → 삭제/이동되는 모든 규칙에 대해 `rules/deprecated.md` 파일(없으면 신규 생성)에 아래 형식으로 기록한다:
  ```
  ## {규칙 ID}
  - 상태: deleted | merged_into:{새 ID} | moved_to:{위치}
  - 결정 이유: {한 줄 근거}
  - 영향 범위: {관련 도구/파일}
  - 대체 방법: {대체 규칙 ID 또는 검증 도구}
  ```

## §5 선행 작업 (blockedBy)
- 없음 (최초 REQ)

## §6 후행 작업 (blocks)
- REQ-025 (E: Spec-only 원칙 강제) — 본 REQ 완료 후 진행

## §7 의존성 요약
- 관련: DBG-001, PLN-008

## §8 테스트 전략
- 단위 테스트: `tests/test_column_flex_gap.py` 신규 추가 (AC-004)
- 통합 검증: 회귀 샘플 2개로 `post-impl-verify.py` 재실행 (AC-005)
- TDD: AC-001/002/004/006 우선 테스트 작성 후 구현

## §9 디버그 연계
- **참조 세션**: DBG-001
- **근본 원인**: "LLM을 CSS 컴파일러로 오용 + 과밀 규칙 + 사후 검증 + auto-fix 부재"
- **본 REQ 대응**: 과밀·충돌·미연결 규칙 제거로 "과밀 규칙" 부분 해소 + 검증 커버리지 공백 일부 메움
- **영향 파일** (DBG-001 finding-codex.md 기준):
  - `rules/rules.yaml:45-49, 246-264, 1158-1222`
  - `rules/common.md:196, 607, 679줄 전체`
  - `rules/codex.md:43, 49, 75`
  - `rules/validation_schema.json:947, 1041, 1127`
  - `tools/validate-semantic.py:1459-1460, 2626-2648, 2885-2894, 2936`

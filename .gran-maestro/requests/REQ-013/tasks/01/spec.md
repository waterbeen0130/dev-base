# REQ-013/01 — figma-validate.py: pseudo-element 분리 + frame 매칭 휴리스틱 개선

- Source plan: PLN-005 (3/5)
- Assigned Agent: [config: codex-dev] codex-dev (Python 도구 보강, 회귀 fixture 다수)
- Status: pending
- blockedBy: []
- blocks: ["02"]

## §0 Context Manifest

- `tools/figma-validate.py` (1159줄, 핵심 수정 대상)
- `tools/figma-section-spec.py` (REQ-012 산출물 — `bbox`/`parent_id`/`character_segments` 출력 확인용)
- `.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/` (회귀 12 fixture + run_regression.sh)
- `CLAUDE.md` §PLN-004 (9개 검증 카테고리 표 — 회귀 보존 기준)
- `/home/waterbeen/.claude/projects/-mnt-d-dev-base/memory/feedback_no_section_padding.md` (참고)

> 위 목록은 시작점 힌트이며, 코드베이스 자율 탐색은 자유롭게 수행하라.

## §1 요약

`figma-validate.py`가 두 가지 false-positive를 낸다:

1. **pseudo-element 색상 합산**: `.vs_list li::before { color: #999; }` 같은 규칙이 `li` 본체 색상 계산에 그대로 합산되어, Figma spec의 `li` 텍스트 색상과 비교 시 잘못된 충돌을 보고한다. 원인: `tokenize_selector`에서 `strip_pseudos`로 pseudo를 제거한 뒤 본 요소와 동일 selector로 처리.
2. **frame 매칭 휴리스틱이 너무 좁음**: `evaluate_frame_rule`이 padding/gap/fill 시그니처 점수만 사용해 거의 모든 frame이 `.hero_content`로 잘못 매칭된다 (Section_05에서 6건 false-positive 관찰). REQ-012가 추가한 `bbox`/`parent_id`를 활용하지 않음.

본 태스크는 두 false-positive를 제거하되 REQ-008/02 회귀 12개 fixture를 무회귀로 보존한다.

## §2 범위

**포함**:
- `tools/figma-validate.py` 수정:
  1. CSS 규칙 파싱 시 selector에 `::before`/`::after`가 포함되면 별도 가상 요소(`PseudoElementMatch`)로 인덱싱하여 본 요소의 `compute_element_properties` 계산에서 제외
  2. `evaluate_frame_rule` / `best_frame_rule`에 bbox+parent_id 기반 매칭 보강:
     - spec.json `frame_nodes[]`에 `bbox`/`parent_id`가 있을 때 해당 정보를 활용
     - 부모 frame이 매칭된 경우 자식 frame은 동일 CSS 규칙에 재매칭되지 않도록 dedupe
     - 매칭 실패 시 "signature 없음" 대신 노드 경로(`parent_id` 체인) 힌트 출력
  3. 신규 회귀 fixture 추가: `.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/scenarios/14-pseudo-before-color-ok/` (li::before 색상 분리 케이스, exit 0 기대)
  4. 신규 회귀 fixture 추가: `.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/scenarios/15-frame-match-bbox-ok/` (bbox 우선 매칭 케이스)

**제외**:
- 새 검증 카테고리 신설
- `figma-section-spec.py` 변경 (REQ-012 완료)
- `parse_css_rules` 전면 재작성 — 최소 침습 수정만
- Python 외부 의존성 추가 (stdlib만)

## §3 수락 조건 (AC)

### AC-001 [automatable] [tdd-required] — pseudo-element 색상 분리 (PAC-6)

- **Given**: HTML에 `<ul class="vs_list"><li>텍스트</li></ul>`, CSS에 `.vs_list li { color: #312d2b; } .vs_list li::before { color: #999; content: "•"; }`, spec.json의 li 텍스트 노드 color=`#312d2b`
- **When**: `python3 tools/figma-validate.py --spec X --html Y --css Z` 실행
- **Then**: `fills color hex 일치` 카테고리 위반 0건 (pseudo의 #999가 li 본체 #312d2b 검증에 영향을 주지 않음)
- **Test**: 신규 fixture `scenarios/14-pseudo-before-color-ok/` 생성 (input.html, input.css, spec.json, expected_exit_code=0). `run_regression.sh` 실행 시 14번 시나리오 PASS

### AC-002 [automatable] [tdd-required] [impact-check] [regression-test] — REQ-008 회귀 12개 fixture 무회귀 (PAC-7)

- **Given**: REQ-008/02의 base + scenarios 1~13 fixture (REQ-010에서 추가된 13번 포함)
- **When**: `cd .gran-maestro/requests/REQ-008/tasks/02/regression-fixtures && bash run_regression.sh` 실행
- **Then**: 모든 시나리오의 실제 exit code가 expected_exit_code와 일치 (12 baseline + 13 inherited-font-ok 보존)
- **Test**: 동일 명령 실행 후 `regression-report.md` 출력에서 `PASS` 카운트가 변경 전과 동일하거나 증가 (감소 금지)

### AC-003 [automatable] — frame 매칭 false-positive 감소 (PAC-8)

- **Given**: 모제림 Section_05 spec.json (REQ-012 산출물, bbox/parent_id 포함) + 현재 출력된 19건 frame 매칭 false-positive
- **When**: 보강된 `figma-validate.py`로 동일 spec/html/css 재실행
- **Then**: frame 매칭 false-positive가 10건 이하로 감소 (50%+ 감소). 위반 카운트 차이를 stdout에 명시 출력
- **Test**: 신규 fixture `scenarios/15-frame-match-bbox-ok/`로 bbox 우선 매칭이 동일 signature 점수 frame을 정확히 구분하는지 검증 (expected_exit_code=0)

### AC-004 [automatable] — 노드 경로 힌트 출력

- **Given**: spec.json frame 중 매칭 실패 case
- **When**: validator 실행 시 해당 frame에 대해 위반 출력
- **Then**: 출력 메시지가 `signature 없음` 대신 `parent_id` 체인 또는 노드 ID 경로 힌트를 포함 (예: `frame 842:209 (parent: 842:206 → 842:200)`)
- **Test**: scenarios/15 fixture에서 frame 미매칭 케이스 1건 포함, 출력 grep으로 `parent` 키워드 존재 확인

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-6 | MUST | AC-001 | full |
| PAC-7 | MUST [IMPACT] | AC-002 | full |
| PAC-8 | SHOULD | AC-003, AC-004 | full |

## §3.5 Constraints

- Python 3.10+, **stdlib만 사용** (외부 의존성 금지)
- 단일 섹션 검증 < 5초 유지 (PLN-005 §5)
- `parse_css_rules` API signature 변경 금지 (REQ-008 회귀 fixture가 의존)
- 기존 9개 검증 카테고리 이름/순서 변경 금지 (CLAUDE.md §PLN-004 표 호환)

## §4 가정 사항

- REQ-012의 `figma-section-spec.py` 보강이 spec.json에 `bbox`/`parent_id`를 정상 출력 (검증 commit `195e7b7`)
- REQ-008 회귀 fixture 13개가 현재 시점에 모두 PASS 상태 (REQ-010에서 13번 추가됨)
- pseudo-element는 `::before`/`::after`만 처리 (`::first-letter`, `::placeholder` 등은 범위 외, 발견 시 무시)

## §5 선행 작업 (blockedBy)

없음 (REQ-012 완료로 의존성 해제)

## §6 후행 작업 (blocks)

- REQ-013/02 (회귀 통합 검증 태스크)
- REQ-014, REQ-015 (PLN-005 후속 REQ)

## §7 의존성 메타

- blockedBy: []
- blocks: ["02"]
- agent: codex-dev

## §8 구현 힌트

> ⚠️ 아래는 시작점 제안일 뿐, 코드베이스를 직접 보고 자율 판단하라.

### Pseudo-element 분리 접근
- `parse_css_rules` 결과의 각 `CSSRule.selectors`에서 `::before`/`::after` 포함 selector를 별도 리스트로 분리
- `compute_direct_element_properties` 호출 시 pseudo selector 매칭 규칙은 제외하고, pseudo 검증이 필요할 때만 별도 함수로 평가
- `tokenize_selector`의 `strip_pseudos` 호출은 유지하되 호출 측에서 pseudo 여부를 사전에 분기

### Frame 매칭 bbox 활용 접근
- `evaluate_frame_rule`에 `frame.get("bbox")`/`frame.get("parent_id")` 사용 점수 추가 (있을 때만, 없으면 기존 동작)
- `best_frame_rule`에서 동점 시 부모-자식 관계로 dedupe (자식 frame은 부모 매칭과 동일 rule에 재할당 안 함)
- `frame.get("parent_id")`를 통해 노드 체인을 거꾸로 빌드해 출력 메시지에 포함

### 외주 브리프 규칙 (CRITICAL — codex-dev 필수 준수)

#### 규칙 파일 읽기 (필수)
- `D:/dev-base/rules/common.md` — 공통 규칙
- `D:/dev-base/rules/codex.md` — codex 전용 규칙

#### Python 코드 규칙
- stdlib만 사용
- 함수 단일 책임 유지, 기존 함수 시그니처 변경 금지
- type hint 유지 (`list[...]`, `dict[...]` 등 PEP 604 스타일)
- 회귀 fixture 추가 시 기존 base/scenarios의 디렉토리 구조/파일명 컨벤션 동일하게 따름

#### 검증 후 보고
구현 완료 후 반드시 아래 명령 실행 결과를 보고:
```bash
cd /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures && bash run_regression.sh
```
- 모든 PASS 확인 후 완료 선언
- 신규 fixture 14, 15도 PASS 보고에 포함

## §9 Test Scenarios (Pre-Impl)

### AC-001 (pseudo-element 색상 분리)
- **Test 명령**: `cd /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures && bash run_regression.sh 2>&1 | grep "scenarios/14"`
- **기대 결과**: `[PASS] scenarios/14-pseudo-before-color-ok` 출력
- **검증 방식**: scenarios/14 fixture의 expected_exit_code(0)와 actual exit code 일치 + 위반 카운트 0

### AC-002 (회귀 13개 무회귀)
- **Test 명령**: `cd /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures && bash run_regression.sh`
- **기대 결과**: 출력 마지막 줄에 `PASS: 15/15` (또는 ≥14) 표시. base + scenarios/01..15 모두 expected = actual
- **검증 방식**: regression-report.md의 PASS 카운트가 변경 전 baseline(14) 이상

### AC-003 (Section_05 false-positive 50%+ 감소)
- **Test 명령**:
  ```bash
  cd /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩 && \
  python3 /mnt/d/dev-base/tools/figma-validate.py \
    --spec /mnt/d/dev-base/.gran-maestro/tmp/mojelim_section_05/section_05_spec.json \
    --html html/index.html --css html/css/common.css 2>&1 | grep -c "frame"
  ```
- **기대 결과**: frame 카테고리 위반 카운트 ≤ 10 (baseline 19 대비 50%+ 감소)
- **검증 방식**: stdout grep 카운트 비교 + 보고에 baseline → after 명시

### AC-004 (노드 경로 힌트)
- **Test 명령**: `cd /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures && bash run_regression.sh 2>&1 | grep "scenarios/15"`
- **기대 결과**: `[PASS] scenarios/15-frame-match-bbox-ok`. 출력에 `parent` 키워드 1회 이상 등장
- **검증 방식**: scenarios/15 fixture가 PASS + 노드 경로 힌트 출력 grep으로 확인

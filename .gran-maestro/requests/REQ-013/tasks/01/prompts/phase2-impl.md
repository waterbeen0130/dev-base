# REQ-013/01 구현 외주 — figma-validate.py 보강

## 메타

- REQ_ID: REQ-013
- TASK_ID: 01
- AGENT: codex-dev
- WORKTREE_PATH: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-013-T01
- SPEC_PATH: /mnt/d/dev-base/.gran-maestro/requests/REQ-013/tasks/01/spec.md
- PLAN_PATH: /mnt/d/dev-base/.gran-maestro/plans/PLN-005/plan.md
- PREV_FEEDBACK_PATH: N/A (첫 실행)

## 작업 개요 (IMPL_CONTEXT)

`tools/figma-validate.py`를 두 가지 false-positive를 잡도록 보강하라. 둘 다 PLN-005에서 명확히 정의된 회귀-안전 작업이다.

1. **pseudo-element 색상 분리**: 현재 `tokenize_selector`가 `strip_pseudos`로 `::before`/`::after`를 제거한 뒤 본 요소 selector와 동일하게 처리해, `.vs_list li::before { color: #999; }` 같은 규칙이 li 본체 색상 검증에 합산되어 false-positive를 낸다. 본 요소(li) compute에서 pseudo 규칙을 반드시 제외하라.

2. **frame 매칭 휴리스틱 개선**: `evaluate_frame_rule`이 `padding+gap+fill+layoutMode` 시그니처 점수만 사용해 거의 모든 frame이 `.hero_content`로 잘못 매칭된다 (Section_05에서 false-positive 19건). REQ-012가 spec.json에 추가한 `bbox` + `parent_id` 정보를 활용해 매칭 정확도를 높이고, 부모/자식 frame dedupe + 매칭 실패 시 노드 경로 힌트 출력을 추가하라.

핵심 제약:
- **stdlib만** 사용 (외부 의존성 추가 금지)
- 기존 함수 시그니처 변경 금지 (`parse_css_rules`, `compute_element_properties` 등 — REQ-008 회귀 fixture가 의존)
- 9개 검증 카테고리 이름/순서 유지
- REQ-008/02 회귀 fixture 12개 + REQ-010이 추가한 13번 fixture 모두 무회귀 PASS
- 신규 fixture 14 (pseudo-before-color-ok), 15 (frame-match-bbox-ok) 추가

[REFERENCE_CONTEXT]
current_date: 2026-04-13
model_cutoff: unknown
references: none
[/REFERENCE_CONTEXT]

## 필독 파일

1. **SPEC**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-013/tasks/01/spec.md` (전체 — AC 4개와 §9 Test Scenarios 포함)
2. **PLAN**: `/mnt/d/dev-base/.gran-maestro/plans/PLN-005/plan.md` (§3 Part B-2 결정사항)
3. **수정 대상**: `tools/figma-validate.py` (1159줄 — 핵심 함수 위치):
   - `tokenize_selector` (line 552)
   - `strip_pseudos` (line 548)
   - `parse_css_rules` (line 454)
   - `compute_direct_element_properties` (line 723)
   - `compute_element_properties` (line 757) — REQ-010이 ancestor walk 추가
   - `evaluate_frame_rule` (line 902)
   - `best_frame_rule` (line 937)
4. **회귀 fixture 인프라**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/`
   - `base/` — baseline fixture
   - `scenarios/01..13/` — 기존 회귀 케이스
   - `run_regression.sh` — 일괄 실행 스크립트 (이 스크립트의 형식을 그대로 따라 14, 15 추가)
5. **REQ-012 산출물**: `tools/figma-section-spec.py` 가 spec.json에 출력하는 `frame_nodes[].bbox` / `parent_id` 필드 형식 확인 (활용 대상)

## 코딩 규칙 (CRITICAL — 반드시 준수)

### 규칙 파일 읽기 (필수)
- `/mnt/d/dev-base/rules/common.md` — 공통 규칙
- `/mnt/d/dev-base/rules/codex.md` — codex 전용 규칙

### Python 코드 규칙
- **stdlib만 사용** (외부 의존성 금지 — argparse/re/json/dataclasses/html.parser/pathlib/sys 등)
- type hint 유지 (`list[...]`, `dict[...]`, `tuple[...]` PEP 604 스타일)
- 기존 함수 시그니처 (인자 이름·순서·반환 타입) 변경 금지
- 새 dataclass/helper는 파일 상단의 기존 dataclass 옆에 추가
- 회귀 fixture 추가 시 기존 `scenarios/01..13`의 디렉토리 구조/파일명 컨벤션 동일 (예: `input.html`, `input.css`, `spec.json`, `expected_exit_code`, `description.md`)

### 변경 금지
- 9개 카테고리 이름·순서 (텍스트 위변조, 줄바꿈 보존, 폰트 5필드, lineHeight, fills color, frame padding/gap, clamp, column flex gap, interaction URL)
- `validate_text_nodes` / `validate_frame_nodes` / `validate_interactions` 함수 시그니처
- `--profile` argparse 인자

## 구현 힌트

### 1. Pseudo-element 분리

접근:
- `parse_css_rules` 또는 `tokenize_selector` 호출 측에서 selector 문자열에 `::before`/`::after`가 있는지 사전 검사
- `CSSRule`에 `is_pseudo_element` flag 추가 또는 별도 `pseudo_rules` 리스트 분리
- `compute_direct_element_properties(element, rules)` 호출 시 `rules`에서 pseudo rule을 제외 (또는 별도 pseudo selector로만 분기)
- `tokenize_selector` 내부의 `strip_pseudos` 호출은 그대로 두고, 호출 측에서 pseudo 여부를 사전 분기

핵심: 본 요소(li)의 color 계산에 pseudo의 color가 절대 들어가서는 안 된다. pseudo 자체의 검증이 필요하면 별도 함수로 처리하되, 9개 카테고리에 새로 추가하지 않는다.

### 2. Frame 매칭 bbox/parent_id 활용

REQ-012가 spec.json `frame_nodes[]`에 추가한 필드:
```json
{
  "id": "842:209",
  "bbox": {"x": 100, "y": 200, "w": 940, "h": 460},
  "parent_id": "842:206",
  "layoutMode": "HORIZONTAL",
  "paddingTop": 40,
  ...
}
```

접근:
- `evaluate_frame_rule(rule, frame)`에 frame.get("bbox") / frame.get("parent_id") 존재 시 추가 점수 부여 (없으면 기존 동작 유지 — 구버전 spec.json 호환)
- `best_frame_rule(frame, rules)`에서 동점 매칭 발생 시, 부모 frame이 이미 같은 rule에 매칭됐으면 자식 frame은 매칭 후보에서 제외 (dedupe)
- 매칭 실패 출력: `evaluate_frame_rule`이 0점일 때 현재는 "signature 없음" 메시지 — 이를 `parent_id` 체인을 따라가는 노드 경로 힌트로 변경 (예: `frame 842:209 (parent: 842:206 → 842:200)`)

### 3. 신규 회귀 fixture

**scenarios/14-pseudo-before-color-ok/**:
- `description.md`: 한 줄 설명
- `expected_exit_code`: `0`
- `input.html`: `<ul class="vs_list"><li>샘플 텍스트</li></ul>` 정도의 최소 HTML
- `input.css`: `.vs_list li { color: #312d2b; font-family: ...; font-size: 16px; font-weight: 400; line-height: 1.5; } .vs_list li::before { color: #999; content: "•"; }` (li 본체 폰트 5필드 완결)
- `spec.json`: TEXT 노드 1개, color=`#312d2b`, fontFamily/fontSize/fontWeight/lineHeightPx 모두 채움 — pseudo 규칙이 본 요소 검증에 영향을 주지 않으면 위반 0건이어야 함

**scenarios/15-frame-match-bbox-ok/**:
- `expected_exit_code`: `0`
- spec.json `frame_nodes[]`에 `bbox` + `parent_id` 포함 (부모-자식 frame 한 쌍)
- 부모 frame과 자식 frame이 같은 signature 점수를 갖되, bbox 우선 매칭으로 정확히 구분되어야 함
- description.md에 "bbox/parent_id 우선 매칭 검증" 명시

## 검증 및 보고

구현 완료 후 반드시 아래를 순서대로 실행하고 결과를 stdout으로 보고:

```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-013-T01

# 1. 회귀 + 신규 fixture 일괄 실행
cd .gran-maestro/requests/REQ-008/tasks/02/regression-fixtures && bash run_regression.sh
# 기대: 모든 시나리오 PASS (≥14건). 신규 14, 15 PASS 확인.

# 2. 자체 import 테스트 (구문 오류 검사)
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-013-T01
python3 -c "import sys; sys.path.insert(0,'tools'); import importlib.util; spec=importlib.util.spec_from_file_location('m','tools/figma-validate.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('import OK')"
```

보고 형식:
```
[REQ-013/01 결과]
- 수정 함수: {목록}
- 신규 fixture: 14 PASS, 15 PASS
- 회귀 fixture: PASS {N}/{M}
- 결론: PASS / FAIL
```

PASS 확인 후에만 작업 완료를 선언하라. FAIL 시 구체적 사유와 출력 로그를 첨부하라.

## 작업 디렉토리

```
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-013-T01
```

이 worktree 내부에서만 작업하라. 외부 경로 수정 금지.

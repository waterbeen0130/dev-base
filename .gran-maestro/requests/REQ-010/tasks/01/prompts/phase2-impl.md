# Task: REQ-010 / 01 — figma-validate.py CSS 상속 처리 추가 (갭 #2)

## Paths
- SPEC: /mnt/d/dev-base/.gran-maestro/requests/REQ-010/tasks/01/spec.md
- WORKTREE: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-010-01
- REGRESSION_FIXTURES: /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/
- DRYRUN_REPORT: /mnt/d/dev-base/.gran-maestro/requests/REQ-009/tasks/02/dryrun/e2e-dryrun-report.md

## 문제

`figma-validate.py`의 `compute_element_properties()` (tools/figma-validate.py:722) 는 현재 element에 직접 매칭되는 CSS 규칙만 수집한다. 그 결과 아래 구조에서 false-positive 위반이 발생:

```html
<li class="x_list_item"><span>Hello</span></li>
```
```css
.x_list_item { font-family: "Noto"; font-size: 14px; font-weight: 400; line-height: 1.5; color: #333; }
```

text_node `"Hello"`는 `<span>`에 매칭되고, span에 직접 선언된 font-* 규칙이 없으므로 "폰트 5필드 완결성 missing: font-family, font-size, font-weight, line-height, color" 5건 위반이 나온다. 실제 브라우저는 부모 li로부터 상속받아 정상 렌더링.

## 해결

CSS 상속 속성 6종(`font-family`, `font-size`, `font-weight`, `line-height`, `color`, `letter-spacing`)에 대해 ancestor walk를 수행하고, 자식에 직접 값이 없으면 가장 가까운 ancestor의 값을 사용.

### 구현 지침

1. **반드시 먼저 Read**:
   - `tools/figma-validate.py` 전체 (특히 `DOMElement` 클래스 정의, `compute_element_properties()` 구현, `validate_text_nodes()` 호출부)
   - `tools/figma-validate.py:722` 근처 `compute_element_properties` 시그니처와 리턴 구조 파악

2. **parent 링크 확인**:
   - `DOMElement`가 이미 `parent` 필드를 갖고 있다면 그대로 사용.
   - 없다면 `parse_html_document()` 또는 DOM 빌드 지점에서 자식 element에 parent 참조를 세팅. (가장 안전한 위치에서 1회 세팅)

3. **compute_element_properties 수정**:
   - 기존 시그니처 `(element, rules) -> dict[str, PropertyValue]` 유지.
   - 내부 로직:
     ```
     direct = {기존처럼 element에 매칭되는 rules 합성}
     inherited = {}
     if element.parent:
         parent_props = compute_element_properties(element.parent, rules)
         inherited = {k: v for k, v in parent_props.items() if k in INHERITED_PROPERTIES}
     # direct가 inherited를 override
     return {**inherited, **direct}
     ```
   - `INHERITED_PROPERTIES = {"font-family", "font-size", "font-weight", "line-height", "color", "letter-spacing"}`
   - 재귀는 루트까지 자연스럽게 종료됨 (root.parent = None).

4. **무한 재귀 / 성능 주의**:
   - 한 번의 validate 호출에서 같은 element에 대해 여러 번 계산될 수 있음. 필요 시 element별 메모이제이션(`_computed_cache: dict[id, dict]`) 추가. 단, 간단한 DOM에서는 성능이 문제되지 않으므로 캐시는 선택.

5. **기타 속성 비변경**:
   - 상속 속성 6종 외(background, padding, gap, margin 등)는 현재 동작 유지. 이들은 CSS 상속 속성이 아니므로 ancestor walk 결과에서 제외 필수.

### 검증

1. **새 pass 케이스 추가** — `.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/scenarios/13-inherited-font-ok/` 신설 (복사 생성):
   - `section_spec.json`: base와 동일하되 text_node `characters`를 span에 넣을 수 있게 사용
   - `index.html`: text를 `<li><span>Hello</span></li>` 형태로 감쌈
   - `style.css`: font-family/size/weight/line-height/color 를 `li` 또는 `.base_section ul li` 에 선언
   - 기대: `figma-validate.py` exit 0 (위반 0건)
   - 이 케이스는 `run_regression.sh` 에서 별도 처리할 필요 없이, base와 같은 exit 0 처리 or 단독 실행으로 확인
2. **기존 12개 시나리오 무회귀 확인**:
   ```bash
   bash /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/run_regression.sh
   ```
   → base=exit 0, 12개 시나리오=exit 1 (각 해당 카테고리 위반 탐지) 유지
3. **py_compile**:
   ```bash
   python3 -m py_compile tools/figma-validate.py
   ```

### 금지
- 9개 검증 카테고리 로직 변경 금지
- 상속 속성 6종 외 속성에 ancestor walk 적용 금지
- 다른 파일 수정 금지 (regression fixture 추가는 예외)
- git commit 금지

### 완료 보고 (5~8줄)
- 변경된 `compute_element_properties()` 핵심 diff 요약
- `DOMElement.parent` 세팅 방식
- 회귀 12개 결과 (exit codes)
- 신규 scenario 13 결과
- `py_compile` 결과

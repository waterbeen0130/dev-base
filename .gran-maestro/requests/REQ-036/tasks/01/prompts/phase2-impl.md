# Implementation Request — REQ-036 / Task 01

**Request**: REQ-036 (Phase C — structural diff gate)
**Task**: 01 — structural-diff.py + Playwright DOM tree 정규화 해시
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-036-T01`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-036/tasks/01/spec.md`
**Plan**: `/mnt/d/dev-base/.gran-maestro/plans/PLN-010/plan.md`

**선행**: REQ-035 (Phase B) 완료 (`439022c` main)

---

## 구현 컨텍스트

`tools/structural-diff.py` 신규 작성 — Playwright Python 으로 HTML 을 headless Chromium 렌더링하고, DOM tree 를 정규화 해시로 변환하여 Figma spec `frame_nodes` 해시와 비교한다.

**목적**: 값(color/padding)은 맞아도 DOM 구조가 깨진 경우를 자동 감지. 픽셀 diff 는 OS 폰트 차이로 불안정하므로 명시적 제외.

## 구현 상세

### 1. 의존성 설치

```bash
pip install --break-system-packages --user "playwright>=1.42"
playwright install chromium
```

### 2. `tools/structural-diff.py` 신규

- Python 3.10+ / stdlib + playwright + pydantic (기존)
- CLI (argparse):
  - `--spec PATH` : Figma spec.json 경로 (optional)
  - `--html PATH` : 렌더링할 HTML 경로 (required)
  - `--css PATH` : CSS 경로 (optional, HTML 내 link 태그 자동 감지 우선)
  - `--dump-hash` : DOM 해시만 출력하고 비교 없이 exit 0
- 핵심 알고리즘:
  ```python
  def normalize_node(element):
      tag = element.tag_name.lower()
      classes = sorted(element.class_list)
      children = [normalize_node(c) for c in element.children]
      return {
          "tag": tag,
          "classes": classes,
          "children": children
      }
  # text content / id attr / inline style 은 제외
  def compute_hash(tree):
      import hashlib, json
      canonical = json.dumps(tree, sort_keys=False, ensure_ascii=False)
      return hashlib.sha256(canonical.encode()).hexdigest()
  ```
- Playwright 사용:
  ```python
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto(f"file://{abs_html_path}")
      page.wait_for_load_state("networkidle")
      root = page.evaluate("() => {
          function walk(el) {
              return {
                  tag: el.tagName.toLowerCase(),
                  classes: [...el.classList].sort(),
                  children: [...el.children].map(walk)
              };
          }
          return walk(document.body);
      }")
      browser.close()
  ```
- Figma spec → 동일 정규화:
  ```python
  def normalize_frame_node(frame):
      # v2 spec의 frame_nodes 구조 참조
      return {
          "tag": "div",  # Figma FRAME은 기본 div로 매핑
          "classes": [],  # Figma는 클래스 개념 없음, 빈 배열
          "children": [normalize_frame_node(c) for c in frame.get("children", [])]
      }
  ```
  (위 변환은 근사치 — Figma structure 와 DOM structure 의 tree depth / children count 만 비교하는 용도)
- 비교 결과:
  - PASS: 해시 일치 → stdout "STRUCTURAL MATCH" + exit 0
  - STRUCTURE_DRIFT: 해시 불일치 → stdout "STRUCTURE_DRIFT\n{diff details}" + exit 1
- Docstring: 첫 100줄 내 "정규화 규칙: tag + sorted(class_list) + children_index_path, text/id/inline style 제외" 문구 포함

### 3. `pyproject.toml` 업데이트

`[project].dependencies` 에 `playwright>=1.42` 추가. 기존 pydantic/pyyaml 유지.

### 4. 신규 테스트 5개

- `tests/unit/test_structural_hash_determinism.py`: 동일 HTML 로 10회 해시 일치
- `tests/unit/test_structural_hash_docs.py`: `tools/structural-diff.py` 첫 100줄에 정규화 규칙 문서 존재
- `tests/unit/test_structural_match.py`: `landing/index.html` 자기 자신과 비교 → MATCH
- `tests/unit/test_structural_drift.py`: 변형된 HTML (tag 변경 or children 추가) → DRIFT 감지
- `tests/unit/test_pyproject_playwright.py`: pyproject.toml 에 `playwright>=1.42` 선언

### 5. 검증

```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-036-T01

# 의존성 확인
python3 -c "import playwright; print('playwright ok')"

# CLI sanity
python3 tools/structural-diff.py --html landing/index.html --dump-hash

# 전체 회귀
pytest tests/ -v 2>&1 | tail -30
# 기대: 126 + 5 신규 = 131 passed / 0 failed
```

### 6. git 커밋 금지 — PM 이 직접 커밋.

## 규칙

- Python 3.10+, Playwright Python 1.42+
- `rules/models.py` (Phase B) 수정 금지
- 기존 `tools/figma-validate.py`, `tools/check-rules-drift.py` 수정 금지 (Phase C 에서 변경 없음)
- 기존 테스트 126 passed 유지
- 코드 주석은 영어만

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-036-T01`

## [MANDATORY] 응답에 반드시 포함할 것

1. `tools/structural-diff.py` 전체 코드
2. 5번 검증 명령 전체 출력
3. `pytest tests/ -v` 마지막 30줄 (summary 포함)

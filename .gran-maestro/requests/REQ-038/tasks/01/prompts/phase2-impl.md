# Implementation Request — REQ-038 / Task 01

**Request**: REQ-038 (validator 강화 — regex 확장 + HTML 주석 제외)
**Task**: 01 — 단일 태스크
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-038-T01`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-038/tasks/01/spec.md`

---

## 구현 컨텍스트

현재 `validate-semantic.py` 의 `no_forbidden_class` 룰에 두 가지 한계가 있다:

1. **패턴 누락**: `sec_1|sec_2|section_01|box1|box2` 리터럴만 있어서 `sec_3`, `sec_10`, `box5` 등을 못 잡음. 사용자 원래 의도는 "숫자 섹션 네이밍 전면 금지".
2. **주석 false positive**: `<!-- sec_1 -->` 같은 HTML 주석도 스캔하여 실제 class 사용이 없어도 CRITICAL 위반 보고.

두 가지 동시 해결.

## 구현 상세

### 1. `rules/rules.yaml` 패턴 확장

`no_forbidden_class.validation.pattern` 을 `sec_\d+|section_\d+|box\d+` 로 교체. examples.bad 에 `sec_3`, `box5` 추가 예시.

### 2. `rules/models.py` 재생성

```bash
python3 -m rules.models
```
→ `rules/validation_schema.json` 자동 업데이트. 수동 편집 금지.

### 3. `tools/validate-semantic.py` 의 forbidden_substring HTML 주석 제외

`forbidden_substring` 검사 함수를 찾아서, HTML target 에 대해 pre-processing 으로 `<!--.*?-->` 를 `re.DOTALL` 로 strip 후 검사. CSS target 은 현재 그대로.

핵심 로직 예시:
```python
def _strip_html_comments(html: str) -> str:
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

def check_forbidden_substring_html(html: str, pattern: str) -> list[Match]:
    cleaned = _strip_html_comments(html)
    return re.finditer(pattern, cleaned)
```

구현 위치는 `tools/validate-semantic.py` 의 `forbidden_substring` 핸들러를 찾아서 적용.

### 4. 신규 테스트 3개 작성

- `tests/unit/test_forbidden_class_numeric_range.py`: `<section class="sec_3">` 감지
- `tests/unit/test_forbidden_class_ignores_html_comments.py`: `<!-- sec_1 -->` 단독 시 위반 0건
- `tests/unit/test_forbidden_class_direct_usage.py`: `<section class="sec_1">` 직접 사용은 여전히 감지 (regression)

테스트 패턴은 기존 `tests/unit/test_*.py` 스타일 참조.

### 5. 검증 명령

```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-038-T01

# 1) Pydantic 재생성
python3 -m rules.models
# → rules/validation_schema.json 갱신 확인

# 2) drift check
python3 tools/check-rules-drift.py --all
# expected: exit 0, "63/63 rules in sync"

# 3) 신규 테스트 3개
pytest tests/unit/test_forbidden_class_numeric_range.py tests/unit/test_forbidden_class_ignores_html_comments.py tests/unit/test_forbidden_class_direct_usage.py -v

# 4) 전체 회귀
pytest tests/ -v 2>&1 | tail -20
# expected: 137 + 3 = 140 passed, 0 failed
```

### 6. git 커밋 금지 — PM 직접 커밋.

## 규칙

- `rules.yaml` 수정 후 **반드시** `python3 -m rules.models` 실행해서 `validation_schema.json` 재생성
- `tools/check-rules-drift.py --all` exit 0 유지 필수 (63/63 rules in sync)
- 기존 137 passed 회귀 없음
- 코드 주석은 영어만
- Python 3.10+

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-038-T01`

## [MANDATORY] 응답에 반드시 포함할 것

1. `rules/rules.yaml` 의 `no_forbidden_class` 변경 diff
2. `tools/validate-semantic.py` 변경 diff 요약
3. 5번 검증 명령 1~4 전체 출력

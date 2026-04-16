# Implementation Request — Self-Exploration Mode

- Request: REQ-005 / Task: 02
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T02
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/02/spec.md
- Plan: N/A

## 구현 컨텍스트

T01에서 작성된 `rules/rules.yaml` (81 rules)을 단일 입력으로 받아 5개 산출물을 자동 생성하는 `tools/build-rules.py`를 작성한다. 워크트리에는 이미 T01의 결과물 `rules/rules.yaml`이 존재한다 (T01 commit 694ee23 기반).

핵심 주의사항:
1. 새 파일 1개: `tools/build-rules.py`
2. 기존 파일 5개를 자동 생성으로 덮어쓰기:
   - `rules/common.md`
   - `rules/basic.md`
   - `rules/landing.md`
   - `rules/validation_schema.json`
   - `tools/build-prompts.py` (PROFILE_RULES 딕셔너리만 marker 사이 치환)
3. 외부 의존성: `pyyaml` 1개만 허용. jinja2 등 템플릿 엔진 금지.
4. CLI 인자: `--input rules/rules.yaml` (default), `--output-dir rules/` (default), `--check` (생성만 비교, 작성 안 함), `--profile {basic|landing|all}`
5. 첫 빌드 시 `tools/build-prompts.py`에 marker가 없으면 적절한 위치에 삽입 (1회), 이후 빌드는 marker 사이만 치환
6. 멱등: 같은 yaml에서 두 번 실행해도 git diff 0
7. 사람이 읽을 수 있게 .md는 카테고리별 헤딩 + 표 형식 유지
8. 작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T02`

## 출력 파일 형식 가이드

### `rules/common.md`
```markdown
<!-- AUTO-GENERATED FROM rules/rules.yaml. DO NOT EDIT MANUALLY.
     Run: python3 tools/build-rules.py
-->

# 공통 규칙

> 이 파일은 `rules/rules.yaml`에서 자동 생성됩니다.
> 직접 편집하지 마세요. 규칙 변경은 `rules.yaml`을 수정하고 빌드를 재실행하세요.

## CSS 레이아웃

### no_css_grid (error)
CSS Grid는 사용하지 않는다 (flexbox 전용).

**나쁜 예**:
```css
.container { display: grid; }
```
**좋은 예**:
```css
.container { display: flex; }
```

(rationale 있으면 뒤에 추가)

---

### ...
```

### `rules/validation_schema.json`
기존 `validation_schema.json`의 형식을 가능한 한 보존. 필수 보존 필드:
- top-level: `version`, `rules` (array)
- 각 룰: `id`, `severity`, `target` (또는 동등 필드), `pattern` 또는 `selector`
- 추가 필드(`description`, `category`)는 옵션 보존

### `tools/build-prompts.py`의 PROFILE_RULES
marker 사이만 자동 갱신:
```python
# BEGIN AUTO-GEN PROFILE_RULES (rules/rules.yaml → tools/build-rules.py)
PROFILE_RULES = {
    "basic": [
        "CSS Grid는 사용하지 않는다 (flexbox 전용)",
        "...",
    ],
    "landing": [
        "...",
    ],
}
# END AUTO-GEN PROFILE_RULES
```
- marker가 파일에 없으면 기존 PROFILE_RULES = ... 정의를 찾아 marker로 감싸 치환
- marker가 있으면 사이 내용만 교체

## 자기탐색 지시

0. spec `## §0 Context Manifest` 모두 Read
1. spec 직접 읽기: `/mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/02/spec.md`
2. 워크트리의 `rules/rules.yaml` Read (T01 산출물)
3. 워크트리의 `tools/build-prompts.py` Read해서 `PROFILE_RULES` 위치 파악
4. 워크트리의 `rules/common.md` 현재 형식 Read해서 헤딩 톤 파악
5. `tools/build-rules.py` 작성:
   - argparse, yaml.safe_load
   - 룰 분류: `applies_to`로 common/basic/landing 그룹핑, `category`로 헤딩 분류
   - .md 출력: f-string + textwrap
   - .json 출력: json.dump(indent=2, ensure_ascii=False, sort_keys=True)
   - .py 출력: marker regex 치환 (re.sub with DOTALL)
   - atomic write: tempfile + os.replace
6. 빌드 1회 실행:
   ```
   python3 /mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T02/tools/build-rules.py
   ```
7. 빌드 2회 (멱등 검증):
   ```
   python3 tools/build-rules.py
   git diff --stat rules/ tools/build-prompts.py
   ```
   diff가 0이어야 AC-004 PASS
8. AC 검증 명령 실행:
   ```
   python3 tools/build-rules.py --check 2>&1 | head -30
   python3 -c "import json; print(len(json.load(open('rules/validation_schema.json'))['rules']))"
   head -50 rules/common.md | grep -c "AUTO-GENERATED"
   python3 -m py_compile tools/build-prompts.py
   ```

작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T02`

## 규칙

- 새 파일 1개: `tools/build-rules.py` (Python 3.10+)
- 기존 파일 5개 덮어쓰기 허용 (위 출력 파일 5개만)
- 다른 파일 수정 금지
- git commit은 하지 마세요 — PM이 직접 커밋합니다
- `pyyaml` 외 외부 의존성 금지
- [MANDATORY] AC-001~005 검증 명령 출력을 응답에 포함
- 멱등: 두 번째 빌드 후 git diff 0

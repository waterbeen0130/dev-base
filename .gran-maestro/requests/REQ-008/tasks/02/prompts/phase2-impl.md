# Task: REQ-008 / 02 — figma-validate.py 회귀 검증 (12개 누락 시나리오)

## Paths
- SPEC_PATH: /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/spec.md
- PLAN_PATH: /mnt/d/dev-base/.gran-maestro/plans/PLN-004/plan.md
- WORKTREE_PATH: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-008-02
- VALIDATOR: tools/figma-validate.py (REQ-008-01 커밋에 이미 포함됨)
- REQ_ID: REQ-008
- TASK_ID: 02

## 작업 지시

REQ-008-01에서 구현된 `tools/figma-validate.py`가 PLN-004 §1의 12개 누락 사례를 모두 catch 하는지 합성 fixture 기반 회귀 테스트를 수행한다.

> **주의**: 실제 Figma API 호출은 불필요. spec.json 구조를 손수 작성한 **합성 fixture**로 12개 실패 시나리오를 재현한다. figma-section-spec.py의 출력 스키마를 따르기만 하면 figma-validate.py는 검증 가능.

### 1. 먼저 반드시 Read
- `SPEC_PATH` (AC-001~003)
- `PLAN_PATH` §1 "누락 12종" 목록 (회귀 시나리오 원천)
- `tools/figma-validate.py` (검증 로직 파악 — 어떤 카테고리가 어떤 조건에서 위반을 보고하는가)
- `tools/figma-section-spec.py` 의 `normalize_text_node` / `normalize_frame_node` (spec.json 스키마 참조)

### 2. 작업 폴더 구조 생성
```
WORKTREE_PATH/regression-fixtures/
  base/
    section_spec.json    # 최소 정상 fixture — text/frame/interaction 각 1~2개
    index.html
    style.css
  scenarios/
    01-font-family-missing/
      section_spec.json  # base와 동일 (validator가 HTML/CSS 위반을 감지해야 함)
      index.html
      style.css          # 또는 index.html에서 해당 선언 누락
    02-line-height-missing/
    03-color-wrong/
    04-text-mutation/
    05-newline-lost/
    06-gap-wrong/
    07-frame-missing/
    08-padding-wrong/
    09-line-box-mismatch/
    10-link-url-missing/
    11-clamp-missing/
    12-column-gap-used/
```

### 3. 각 시나리오 구성 원칙
- **base** fixture: 정상적으로 검증을 통과해야 하는 최소 샘플. text_nodes 2개 + frame_nodes 1개 + interactions 1개 정도.
  - HTML/CSS는 9개 검증 항목을 모두 만족하도록 작성.
  - `python3 tools/figma-validate.py --spec base/section_spec.json --html base/index.html --css base/style.css` → exit 0 기대
- **scenarios/NN-name**: base에서 **해당 카테고리 1개만 고의 위반**하여 복사.
  - 예: `01-font-family-missing` → CSS에서 `font-family` 한 줄 제거
  - 예: `04-text-mutation` → HTML의 text 내용을 변경해 spec의 `characters`와 불일치
  - 예: `10-link-url-missing` → interactions 에 있는 URL이 HTML `<a href="...">`에 없음
- 각 시나리오 실행 시 기대: exit 1 + 해당 카테고리 위반 1건 이상 탐지

### 4. 회귀 실행 스크립트 작성
`regression-fixtures/run_regression.sh` 를 작성해 base + 12 시나리오를 순차 실행하고 결과를 모은다:
```bash
#!/usr/bin/env bash
set +e
cd "$(dirname "$0")"
ROOT=".."

echo "=== base ==="
python3 "$ROOT/tools/figma-validate.py" --spec base/section_spec.json --html base/index.html --css base/style.css
echo "exit=$?"

for dir in scenarios/*/; do
  name=$(basename "$dir")
  echo "=== $name ==="
  python3 "$ROOT/tools/figma-validate.py" --spec "$dir/section_spec.json" --html "$dir/index.html" --css "$dir/style.css"
  echo "exit=$?"
done
```

### 5. 리포트 작성
`regression-fixtures/regression-report.md` 에 아래 형식의 매트릭스를 작성:

```markdown
# REQ-008-02 — figma-validate.py 회귀 검증 리포트

생성일: 2026-04-13
검증 대상: tools/figma-validate.py (commit 2d2982e)

## 요약
- base fixture: PASS / FAIL
- 시나리오 12개: 검출 N / 미검출 M / 부분검출 K

## 결과 매트릭스

| # | 시나리오 | 기대 카테고리 | validator exit | 실제 검출 | 판정 |
|---|----------|----------------|----------------|-----------|------|
| 1 | font-family-missing | 폰트 5필드 완결성 | 1 | PASS | ✓ |
| 2 | line-height-missing | 폰트 5필드 완결성 | 1 | PASS | ✓ |
| 3 | color-wrong | fills color hex 일치 | 1 | PASS | ✓ |
| 4 | text-mutation | 텍스트 위변조 | 1 | PASS | ✓ |
| 5 | newline-lost | 줄바꿈 보존 | 1 | PASS | ✓ |
| 6 | gap-wrong | frame padding/gap 반영 | 1 | PASS | ✓ |
| 7 | frame-missing | frame padding/gap 반영 | 1 | PASS | ✓ |
| 8 | padding-wrong | frame padding/gap 반영 | 1 | PASS | ✓ |
| 9 | line-box-mismatch | lineHeight 비율 일치 | 1 | PASS | ✓ |
| 10 | link-url-missing | interaction URL 일치 | 1 | PASS | ✓ |
| 11 | clamp-missing | clamp 적용 | 1 | PASS | ✓ |
| 12 | column-gap-used | column flex gap 금지 | 1 | PASS | ✓ |

## 관찰된 이슈 (미검출/부분검출이 있는 경우)
(없으면 "없음")

## 결론
9개 검증 카테고리가 12개 실패 모드를 모두 탐지하는지 확인. (혹은 ...)
```

### 6. 완료 조건
- `regression-fixtures/` 디렉토리가 WORKTREE_PATH 아래 존재
- `regression-fixtures/run_regression.sh` 실행 결과가 base=exit 0, 12개 시나리오=exit 1 (최대한)
- `regression-fixtures/regression-report.md` 가 위 형식으로 작성됨
- 미검출/부분검출이 1건 이상 있으면 그 원인을 리포트에 명시 (validator 버그 vs fixture 설계 오류 구분)

## 금지 사항
- `tools/figma-validate.py` 수정 금지 (버그 발견 시 리포트에 기록만)
- 실제 Figma API 호출 금지 (합성 fixture만 사용)
- git 커밋 금지 (PM이 직접 커밋)

## 완료 후
리포트 파일 경로와 요약(검출 N/12, 주요 관찰)을 4~6줄로 보고할 것.

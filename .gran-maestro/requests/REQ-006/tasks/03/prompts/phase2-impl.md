# Implementation Request — Verification Task

- Request: REQ-006 / Task: 03
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T03
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/03/spec.md

## 구현 컨텍스트

T01 (엔진 리팩터링) + T02 (핸들러 채우기) 산출물을 실제 `output/*` 산출물에 돌려서 회귀 측정 + 오탐/미탐 사람 검수. 워크트리는 T02 결과물 포함.

작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T03`

## 검증 절차

### 1. 사전 백업
```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T03
git show edaaae2:tools/validate-semantic.py > /tmp/validate.old.py
echo "backup: $(wc -l < /tmp/validate.old.py) lines"
```

### 2. AC-001 — 모든 output 프로젝트 crash 0건
```bash
> /tmp/req006_validate_run.log
for d in /mnt/d/dev-base/output/*/; do
  name=$(basename "$d")
  for html in "$d"*.html; do
    [ -f "$html" ] || continue
    css="${d}css/common.css"
    [ -f "$css" ] || continue
    echo "=== $name $(basename $html) ===" >> /tmp/req006_validate_run.log
    python3 /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T03/tools/validate-semantic.py --html "$html" --css "$css" >> /tmp/req006_validate_run.log 2>&1 || echo "EXIT:$? for $html" >> /tmp/req006_validate_run.log
  done
done
echo "tracebacks: $(grep -c 'Traceback\|Exception' /tmp/req006_validate_run.log)"
echo "total runs: $(grep -c '^===' /tmp/req006_validate_run.log)"
```

### 3. AC-002 — 회귀 비교 (5개 샘플)
```bash
echo "=== old vs new ===" > /tmp/req006_compare.log
SAMPLES=$(ls -d /mnt/d/dev-base/output/*/ 2>/dev/null | head -5)
for d in $SAMPLES; do
  for html in "$d"*.html; do
    [ -f "$html" ] || continue
    css="${d}css/common.css"
    [ -f "$css" ] || continue
    old=$(python3 /tmp/validate.old.py --html "$html" --css "$css" 2>&1 | grep -cE "ERROR|WARN|MAJOR|CRITICAL" || echo 0)
    new=$(python3 /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T03/tools/validate-semantic.py --html "$html" --css "$css" 2>&1 | grep -cE "ERROR|WARN|MAJOR|CRITICAL" || echo 0)
    echo "$(basename $d)/$(basename $html): old=$old new=$new" | tee -a /tmp/req006_compare.log
  done
done
```

### 4. AC-003 — 오탐 검수 (5~10건 샘플)
신버전 결과에서 카테고리별 위반을 5~10건 샘플링하여 사람 눈으로 PASS/FAIL 판단. 결과를 spec §11에 표 형식으로 기록.

### 5. R3 — 카테고리별 핸들러 작동 흔적
신규 카테고리 5종(landing, mapping, DOM, naming, ast)에서 각각 1개 이상 발견 흔적 확인:
```bash
grep -E "root_vars_required|gsap|figma_value|ul_li|parent_tag|prefix_must_match|inner_wrapper" /tmp/req006_validate_run.log | head -20
```

### 6. spec §11 추가 (이것이 T03의 유일한 파일 변경)
`/mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/03/spec.md` 끝에 `## §11 검증 결과` 추가:

```markdown
## §11 검증 결과

### AC 상태
- AC-001 (no crash): PASS/FAIL — tracebacks={N}, total runs={M}
- AC-002 (regression): PASS/FAIL — 평균 변화율 {X}%
- AC-003 (manual review): PASS/FAIL — 오탐률 {Y}%

### AC-002 비교 표
| 프로젝트/페이지 | old | new | 변화 |
|---|---|---|---|
...

### AC-003 오탐 검수
| # | rule_id | 위치 | PM 판정 | 사유 |
|---|---|---|---|---|
...

### R3 카테고리 작동 흔적
| 카테고리 | 룰 ID | 발견 건수 | 비고 |
|---|---|---|---|
...

### 최종 판정
{PASS/FAIL + 다음 액션}
```

## 자기탐색 지시

0. spec `## §0 Context Manifest` 모두 Read
1. spec 직접 읽기: `/mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/03/spec.md`
2. 위 §1~§5 검증 명령 모두 실행
3. spec.md 끝에 §11 추가 (Edit) — main 저장소 경로 사용 (워크트리에는 spec 트리가 없을 수 있음): `/mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/03/spec.md`
4. 모든 검증 출력 + §11 표를 응답에 포함

## 규칙

- spec.md만 §11 추가로 편집
- git commit 금지
- 전수 검사 아님 — 5개 프로젝트 샘플 + 5~10건 사람 검수
- 오탐률 30% 초과 발견 시 spec §11 "다음 액션"에 T02 보정 권고 명시

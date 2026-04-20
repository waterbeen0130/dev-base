# Implementation Request — REQ-036 / Task 02

**Request**: REQ-036 (Phase C — structural diff gate)
**Task**: 02 — post-impl-verify --structural-diff flag 통합 + 회귀
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-036-T02`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-036/tasks/02/spec.md`

**선행**: REQ-036/01 (structural-diff.py 신규)

---

## 구현 컨텍스트

`tools/post-impl-verify.py` 에 `--structural-diff` optional flag 를 추가한다. flag 활성 시 `tools/structural-diff.py` 를 subprocess 로 호출하여 결과를 검증 출력에 통합한다.

## 구현 상세

### 1. `tools/post-impl-verify.py` 수정

- argparse 에 `--structural-diff` 플래그 추가 (`action="store_true"`, 기본 False)
- flag 활성 시:
  ```python
  if args.structural_diff:
      result = subprocess.run([
          sys.executable, "tools/structural-diff.py",
          "--html", args.html,
          "--css", args.css,
          "--spec", args.spec,
      ], capture_output=True, text=True)
      if result.returncode == 0:
          print("[STRUCTURAL] PASS")
      else:
          print("[STRUCTURAL] DRIFT")
          print(result.stdout)
          # MAJOR 등급: exit code 를 1 로 승격
          exit_code = max(exit_code, 1)
  ```
- flag 미지정 시 기존 동작 완전 유지 (structural-diff 호출 없음)
- 기존 exit code 체계 호환 (0 PASS / 1 CRITICAL·MAJOR / 2 IGNORE-only)

### 2. 신규 통합 테스트

- `tests/integration/test_post_impl_structural_diff.py` (신규):
  - `landing/index.html` + `landing/css/common.css` + `extracted/section_03_spec.json` 으로 `--structural-diff` 실행
  - exit code 0 또는 1 확인
  - stdout 에 "[STRUCTURAL]" 라인 포함 확인

- `tests/integration/test_post_impl_structural_drift_exits_1.py` (신규):
  - 일부러 변형된 HTML (tag 변경) 을 임시 파일로 작성하여 실행
  - exit code 1 확인

### 3. 검증

```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-036-T02

# flag 없이 — 기존 동작 유지
python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css --profile landing
echo "exit=$?"

# flag 있이 — structural diff 통합
python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html landing/index.html --css landing/css/common.css --profile landing --structural-diff
echo "exit=$?"

# 전체 회귀
pytest tests/ -v 2>&1 | tail -20
# 기대: 131 + 2 신규 = 133 passed / 0 failed
```

### 4. git 커밋 금지 — PM 이 직접 커밋.

## 규칙

- Task 01 산출물 (`tools/structural-diff.py`) 수정 금지
- 기존 post-impl-verify 의 기본 동작 (flag 없을 때) 완전 불변
- 기존 131 passed 회귀 없음
- 코드 주석은 영어만

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-036-T02`

## [MANDATORY] 응답에 반드시 포함할 것

1. `tools/post-impl-verify.py` 변경 diff 요약
2. 검증 명령 3개 전체 출력
3. `pytest tests/ -v` 마지막 20줄 (summary 포함)

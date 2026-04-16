# REQ-015/01 — tools/post-impl-verify.py + PM 워크플로우 가이드

- Source plan: PLN-005 (5/5)
- Assigned Agent: [config: codex-dev] codex-dev (Python 스크립트 신설 + CLAUDE.md 가이드 섹션 추가)
- Status: pending
- blockedBy: []
- blocks: []

## §0 Context Manifest

- `tools/figma-validate.py` (REQ-013 후 보강 완료 — 9개 카테고리 검증)
- `tools/validate-semantic.py` (코드 컨벤션 검증, --profile 지원)
- `CLAUDE.md` §PLN-004 (5단계 워크플로우 — 4번 단계 후 호출 지점)
- `rules/templates/publishing/impl-request.md` (REQ-014에서 외주 brief 표준화 완료)
- `.gran-maestro/config.json` (`retry.max_cli_retries=2`)

## §1 요약

외주 에이전트 dispatch 완료 직후 PM이 figma-validate.py + validate-semantic.py를 자동 실행하고 위반을 분류해 재dispatch 여부를 결정하는 후처리 훅을 만든다. 두 산출물:

1. **`tools/post-impl-verify.py`** — 두 validator를 일괄 실행, 위반을 CRITICAL/MAJOR/IGNORE로 분류, 종료 코드로 PM에게 상태 신호
2. **`CLAUDE.md` §"PM 자동 검증 후처리"** — PM이 외주 dispatch 직후 호출하는 워크플로우 가이드 (호출 시점, 종료 코드 해석, 자동 재dispatch 1회 정책)

## §2 범위

**포함**:
- `tools/post-impl-verify.py` 신설 (Python stdlib only)
  - `--spec`, `--html`, `--css`, `--profile` 인자
  - 두 validator 순차 실행, stdout 캡처
  - 위반 분류: CRITICAL (텍스트 위변조 / 폰트 5필드 / fills color hex), MAJOR (lineHeight / clamp / frame padding/gap), IGNORE (frame signature 미매칭, pseudo-element false-positive — REQ-013에서 보강했지만 잔여 케이스 대비)
  - exit code: 0 (전체 PASS), 1 (CRITICAL/MAJOR 존재), 2 (IGNORE만 존재)
  - JSON 출력 옵션 `--json` (PM 파싱용)
- `CLAUDE.md`에 새 섹션 `## PM 자동 검증 후처리 (PLN-004 보강)` 추가
  - 호출 지점: 외주 dispatch 완료 직후
  - 호출 명령 예시
  - exit code 해석 표
  - 재dispatch 정책 (max 1회, retry.max_cli_retries 준용)
  - escalation 메시지 형식

**제외**:
- 자동 dispatch 루프 자체 구현 (PM이 직접 판단해서 호출 — 가이드 문서 형태로 충분)
- figma-validate.py / validate-semantic.py 변경 (사용만)
- 외부 의존성 추가

## §3 수락 조건

### AC-001 [automatable] — post-impl-verify.py 기본 실행 (PAC-11)

- **Given**: REQ-008/02 base fixture (`section_spec.json`/`index.html`/`style.css`)
- **When**: `python3 tools/post-impl-verify.py --spec base/section_spec.json --html base/index.html --css base/style.css --profile all`
- **Then**: exit 0, stdout에 "figma-validate: PASS", "validate-semantic: PASS" 라인 포함
- **Test**: 위 명령 실행 후 `echo $?` == 0 + grep으로 PASS 라인 확인

### AC-002 [automatable] — CRITICAL 위반 감지 시 exit 1 (PAC-11)

- **Given**: REQ-008/02 scenarios/03-color-wrong fixture (CRITICAL fills color hex 위반)
- **When**: post-impl-verify.py 실행
- **Then**: exit 1, stdout에 "[CRITICAL]" 라벨 + "fills color hex" 카테고리 출력
- **Test**: exit code 1 확인 + grep "CRITICAL" 매칭

### AC-003 [automatable] — JSON 출력 모드 (PAC-11)

- **Given**: 임의 fixture
- **When**: `--json` 플래그 추가 실행
- **Then**: stdout이 JSON 형식 (`{"figma_validate": {...}, "validate_semantic": {...}, "summary": {"critical": N, "major": N, "ignore": N, "exit_code": N}}`)
- **Test**: `python3 -c "import json,sys; json.loads(sys.stdin.read())" < output.json` 성공

### AC-004 [automatable] — CLAUDE.md 가이드 섹션 (PAC-11)

- **Given**: 현재 CLAUDE.md
- **When**: 편집 후 grep
- **Then**: `## PM 자동 검증 후처리` 섹션 존재 + 호출 명령 예시 + exit code 해석 표 + 재dispatch 정책 포함
- **Test**: `grep -q "PM 자동 검증 후처리" CLAUDE.md && grep -q "post-impl-verify.py" CLAUDE.md && grep -q "재dispatch" CLAUDE.md`

### AC-005 [manual] — escalation 메시지 형식 (PAC-12)

- **Given**: 자동 재dispatch 1회 후에도 위반 잔여 시 PM이 사용자에게 보고할 escalation 메시지 형식이 가이드에 명시
- **When**: CLAUDE.md 새 섹션 검토
- **Then**: escalation 메시지 템플릿이 1개 이상 포함 (예시 `[POST-IMPL FAIL] {N}건 위반 잔여 — {카테고리 요약}, 사용자 검수 필요`)
- **Test**: 사람이 가이드를 읽고 형식이 사용 가능한지 확인

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-11 | SHOULD | AC-001, AC-002, AC-003, AC-004 | full |
| PAC-12 | SHOULD | AC-005 | full |

## §3.5 Constraints

- Python 3.10+, **stdlib only** (subprocess로 figma-validate.py / validate-semantic.py 호출)
- `tools/figma-validate.py` / `tools/validate-semantic.py` 변경 금지 (사용만)
- 9개 카테고리 분류는 figma-validate.py의 출력 카테고리 이름과 1:1 매칭

## §5 선행 작업 (blockedBy)

REQ-013 완료 (의존성 해제됨)

## §6 후행 작업 (blocks)

없음 (PLN-005 마지막 REQ)

## §7 의존성 메타

- blockedBy: []
- blocks: []
- agent: codex-dev

## §8 구현 힌트

### post-impl-verify.py 스켈레톤

```python
#!/usr/bin/env python3
"""Post-implementation verification: runs figma-validate + validate-semantic
and classifies violations into CRITICAL/MAJOR/IGNORE for PM auto-dispatch flow.
"""
import argparse, json, subprocess, sys, re
from pathlib import Path

CRITICAL_CATEGORIES = {"텍스트 위변조", "폰트 5필드 완결성", "fills color hex 일치"}
MAJOR_CATEGORIES = {"lineHeight 비율 일치", "clamp 적용", "frame padding/gap 반영", "줄바꿈 보존", "interaction URL 일치", "column flex gap 금지"}

def run_validator(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr

def classify(figma_output: str) -> dict:
    counts = {"critical": 0, "major": 0, "ignore": 0, "details": []}
    for line in figma_output.splitlines():
        for cat in CRITICAL_CATEGORIES:
            if cat in line and "|" in line:  # category | node | ...
                counts["critical"] += 1; counts["details"].append(("CRITICAL", line))
        for cat in MAJOR_CATEGORIES:
            if cat in line and "|" in line:
                counts["major"] += 1; counts["details"].append(("MAJOR", line))
    return counts

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--html", required=True)
    ap.add_argument("--css", required=True)
    ap.add_argument("--profile", default="all")
    ap.add_argument("--json", action="store_true", dest="json_output")
    args = ap.parse_args()

    tools = Path(__file__).parent
    fv_code, fv_out = run_validator(["python3", str(tools/"figma-validate.py"), "--spec", args.spec, "--html", args.html, "--css", args.css])
    vs_code, vs_out = run_validator(["python3", str(tools/"validate-semantic.py"), "--html", args.html, "--css", args.css, "--profile", args.profile])

    summary = classify(fv_out)
    summary["figma_validate_exit"] = fv_code
    summary["validate_semantic_exit"] = vs_code

    if summary["critical"] > 0 or summary["major"] > 0 or vs_code != 0:
        exit_code = 1
    elif summary["ignore"] > 0:
        exit_code = 2
    else:
        exit_code = 0
    summary["exit_code"] = exit_code

    if args.json_output:
        print(json.dumps({"figma_validate": fv_out, "validate_semantic": vs_out, "summary": summary}, ensure_ascii=False))
    else:
        print(f"figma-validate: {'PASS' if fv_code == 0 else 'FAIL'} (critical={summary['critical']}, major={summary['major']})")
        print(f"validate-semantic: {'PASS' if vs_code == 0 else 'FAIL'}")
        for severity, line in summary["details"][:20]:
            print(f"[{severity}] {line}")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
```

위는 출발점. 코드베이스 자율 탐색으로 figma-validate.py 출력 형식을 직접 확인하고 정확한 grep 패턴 사용.

### CLAUDE.md 새 섹션 위치

`## PLN-004 Figma 워크플로우 (CRITICAL — 반드시 이 순서 준수)` 섹션 다음, `## 피그마 MCP 기반 워크플로우 (참고)` 섹션 이전에 삽입.

새 섹션 내용:
- 호출 지점: 외주 dispatch 완료 직후, PM commit 이전
- 명령 예시: `python3 tools/post-impl-verify.py --spec extracted/{section}_spec.json --html output.html --css output.css --profile landing`
- exit code 해석 표:

| exit code | 의미 | PM 액션 |
|---|---|---|
| 0 | 전체 PASS | PM commit 진행 |
| 1 | CRITICAL/MAJOR 존재 | 1회 자동 재dispatch (max_cli_retries 미만 시) |
| 2 | IGNORE 카테고리만 (false-positive 의심) | PM 직접 검토 후 수동 진행 |

- 재dispatch 정책: `retry.max_cli_retries=2` 준용, 1회 시도 후 잔여 위반 시 escalation
- escalation 메시지 형식: `[POST-IMPL FAIL] REQ-{ID}/{TASK_ID}: {N}건 위반 잔여 (CRITICAL: M, MAJOR: K) — 사용자 검수 필요`

## §9 Test Scenarios (Pre-Impl)

### AC-001 (기본 PASS)
- **Test 명령**: `python3 tools/post-impl-verify.py --spec /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/base/section_spec.json --html /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/base/index.html --css /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/base/style.css --profile all; echo "exit=$?"`
- **기대 결과**: `exit=0`, stdout에 "figma-validate: PASS" + "validate-semantic: PASS" 표시

### AC-002 (CRITICAL 감지)
- **Test 명령**: `python3 tools/post-impl-verify.py --spec /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/scenarios/03-color-wrong/section_spec.json --html .../scenarios/03-color-wrong/index.html --css .../scenarios/03-color-wrong/style.css --profile all; echo "exit=$?"`
- **기대 결과**: `exit=1`, stdout에 "[CRITICAL]" 라벨 + "fills color hex" 키워드 등장

### AC-003 (JSON 출력)
- **Test 명령**: `python3 tools/post-impl-verify.py --spec base/section_spec.json --html base/index.html --css base/style.css --profile all --json | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print('keys:', list(d.keys()))"`
- **기대 결과**: stdout에 `keys: ['figma_validate', 'validate_semantic', 'summary']`

### AC-004 (CLAUDE.md 가이드)
- **Test 명령**: `grep -q "PM 자동 검증 후처리" CLAUDE.md && grep -q "post-impl-verify.py" CLAUDE.md && grep -q "재dispatch" CLAUDE.md && echo OK`
- **기대 결과**: `OK` 출력

### AC-005 (escalation 형식)
- **Test 명령**: `grep -q "POST-IMPL FAIL" CLAUDE.md && echo OK`
- **기대 결과**: `OK` 출력

## 외주 브리프 규칙 (CRITICAL — codex-dev 필수 준수)

### 규칙 파일 읽기 (필수)
- `D:/dev-base/rules/common.md`
- `D:/dev-base/rules/codex.md`

### Python 코드 규칙
- stdlib만 사용 (subprocess/argparse/json/pathlib/re/sys)
- type hint 유지 (PEP 604 스타일)
- shebang `#!/usr/bin/env python3` 포함
- `tools/figma-validate.py` / `tools/validate-semantic.py` 변경 금지

### 검증 후 보고
구현 완료 후 §9의 Test Scenarios 5개를 모두 실행하고 결과 보고:
```
[REQ-015/01 결과]
- AC-001 (기본 PASS): exit=0 / FAIL
- AC-002 (CRITICAL 감지): exit=1 / FAIL
- AC-003 (JSON 출력): JSON 파싱 OK / FAIL
- AC-004 (CLAUDE.md 가이드): OK / MISSING
- AC-005 (escalation): OK / MISSING
- 결론: PASS / FAIL
```

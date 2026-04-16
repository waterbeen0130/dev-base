# REQ-015/01 구현 외주 — tools/post-impl-verify.py + CLAUDE.md 가이드

## 메타

- REQ_ID: REQ-015
- TASK_ID: 01
- AGENT: codex-dev
- WORKTREE_PATH: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-015-T01
- SPEC_PATH: /mnt/d/dev-base/.gran-maestro/requests/REQ-015/tasks/01/spec.md
- PLAN_PATH: /mnt/d/dev-base/.gran-maestro/plans/PLN-005/plan.md

## 작업 개요 (IMPL_CONTEXT)

PLN-005 마지막 REQ. 외주 에이전트가 dispatch 완료한 직후 PM이 figma-validate.py + validate-semantic.py를 한 번에 실행하고 위반을 분류해 재dispatch 여부를 결정할 수 있도록 두 산출물을 만든다:

1. **`tools/post-impl-verify.py`** — Python stdlib only. subprocess로 두 validator를 순차 실행하고 출력 파싱해 CRITICAL/MAJOR/IGNORE 분류. exit 0 (PASS), 1 (CRITICAL/MAJOR), 2 (IGNORE만). `--json` 옵션으로 구조화 출력.
2. **`CLAUDE.md` §"PM 자동 검증 후처리"** — 새 섹션. 호출 지점, 명령 예시, exit code 해석 표, 자동 재dispatch 1회 정책, escalation 메시지 형식.

핵심 제약:
- stdlib만 (외부 의존성 추가 금지)
- `tools/figma-validate.py` / `tools/validate-semantic.py` 변경 금지 (subprocess로 호출만)
- 9개 카테고리 분류는 figma-validate.py 출력 카테고리 이름과 1:1 매칭

[REFERENCE_CONTEXT]
current_date: 2026-04-13
references: none
[/REFERENCE_CONTEXT]

## 필독 파일

1. **SPEC**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-015/tasks/01/spec.md` (전체 — AC 5개 + §9 Test Scenarios + §8 구현 힌트의 스켈레톤)
2. **PLAN**: `/mnt/d/dev-base/.gran-maestro/plans/PLN-005/plan.md` (§3 Part B-4)
3. **참조 도구**:
   - `tools/figma-validate.py` (출력 형식 직접 확인 — `validate_text_nodes`, `validate_frame_nodes`, `validate_interactions`의 stdout 패턴)
   - `tools/validate-semantic.py` (`--profile` 인자, exit code 의미)
4. **CLAUDE.md** (대상 파일, `## PLN-004 Figma 워크플로우` 섹션 다음에 새 섹션 삽입)
5. **회귀 fixture (테스트 입력)**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/base/` (PASS 케이스), `scenarios/03-color-wrong/` (CRITICAL fills color hex 위반)

## 코딩 규칙 (CRITICAL — 반드시 준수)

### 규칙 파일 읽기 (필수)
- `/mnt/d/dev-base/rules/common.md`
- `/mnt/d/dev-base/rules/codex.md`

### Python 코드 규칙
- **stdlib only** (`subprocess`, `argparse`, `json`, `pathlib`, `re`, `sys` 만)
- type hint 유지 (PEP 604 스타일 `list[str]`, `dict[str, ...]`)
- shebang `#!/usr/bin/env python3` + `if __name__ == "__main__"` 가드
- subprocess 호출 시 `capture_output=True, text=True` 사용
- exit code는 `sys.exit(int)`로 명시적 반환

### 필수 분류 매핑

CRITICAL 카테고리 (figma-validate.py 출력 키워드와 정확히 일치):
- `텍스트 위변조`
- `폰트 5필드 완결성`
- `fills color hex 일치`

MAJOR 카테고리:
- `lineHeight 비율 일치`
- `clamp 적용`
- `frame padding/gap 반영`
- `줄바꿈 보존`
- `interaction URL 일치`
- `column flex gap 금지`

IGNORE (false-positive 의심, 출력만 하고 exit code에 영향 안 줌):
- frame matching `signature 없음` 패턴
- pseudo-element 잔여 false-positive (REQ-013 후 거의 해소되었으나 잔여 대비)

### CLAUDE.md 새 섹션 위치
`## PLN-004 Figma 워크플로우 (CRITICAL — 반드시 이 순서 준수)` 섹션 다음, `## 피그마 MCP 기반 워크플로우 (참고 — 위 5단계 플로우 내부의 보조 수단)` 섹션 이전에 삽입.

새 섹션 헤더: `## PM 자동 검증 후처리 (PLN-004 보강 — REQ-015)`

내용은 spec §8 "CLAUDE.md 새 섹션 위치" 참조. exit code 해석 표 + 재dispatch 정책 + escalation 메시지 형식 (예: `[POST-IMPL FAIL] REQ-{ID}/{TASK_ID}: {N}건 위반 잔여 (CRITICAL: M, MAJOR: K) — 사용자 검수 필요`) 모두 포함.

## 검증 후 보고

구현 완료 후 §9 Test Scenarios 5개를 모두 실행하고 결과를 stdout으로 보고:

```
[REQ-015/01 결과]
- AC-001 (기본 PASS): exit=0 / FAIL
- AC-002 (CRITICAL 감지): exit=1 / FAIL
- AC-003 (JSON 출력): JSON 파싱 OK / FAIL
- AC-004 (CLAUDE.md 가이드): OK / MISSING
- AC-005 (escalation 형식): OK / MISSING
- 결론: PASS / FAIL
```

PASS 확인 후에만 작업 완료를 선언하라.

## 작업 디렉토리

```
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-015-T01
```

이 worktree 내부에서만 작업하라.

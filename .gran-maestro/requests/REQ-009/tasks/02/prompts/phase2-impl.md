# Task: REQ-009 / 02 — PLN-004 워크플로우 드라이런 검증

## Paths
- SPEC_PATH: /mnt/d/dev-base/.gran-maestro/requests/REQ-009/tasks/02/spec.md
- PLAN_PATH: /mnt/d/dev-base/.gran-maestro/plans/PLN-004/plan.md
- WORKTREE_PATH: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-009-02
- REQ_ID: REQ-009
- TASK_ID: 02

## 작업 개요

REQ-009-01이 문서화한 새 워크플로우가 **자기완결적**인지 가상 섹션 드라이런으로 검증한다. 실제 모제림 Section_03 데이터가 없으므로 `extracted/section_03_spec.json` (기존 프로젝트 산출물) 또는 소형 합성 spec.json을 사용한다.

## 반드시 먼저 Read

1. `SPEC_PATH` (AC 3개)
2. WORKTREE_PATH의 최신 `CLAUDE.md`와 `rules/claude.md` — REQ-009-01 수정본이 반영된 문서
3. `tools/figma-section-spec.py` / `tools/figma-validate.py` / `tools/validate-semantic.py` (도움말 수준 확인)
4. `extracted/section_03_spec.json` 존재 여부 (현재 main 에 존재. 없으면 합성 대체)

## 드라이런 절차 (5단계 워크플로우 따라가기)

작업 디렉토리를 `{WORKTREE_PATH}/dryrun/` 으로 만들고 아래를 수행한다.

### Step 1. spec sheet 확보
- `extracted/section_03_spec.json` 가 main 작업 트리에 존재하는 경우: `cp /mnt/d/dev-base/extracted/section_03_spec.json dryrun/section_spec.json` 로 복사
- 없으면 최소 합성(text_nodes 2 + frame_nodes 1 + interactions 0) JSON을 직접 작성

### Step 2. HTML/CSS 작성 (AI 의 역할 시뮬레이션)
- spec.json을 보고 최소 HTML `dryrun/index.html` + CSS `dryrun/style.css` 작성
- 목표: "워크플로우를 끝까지 굴려보는 것"이 우선. 디자인 충실도는 중요하지 않음
- 단, PLN-004 규칙을 따름 — font-family/size/weight/line-height/color 전부 명시, interaction URL 있으면 `<a target="_blank">` 작성

### Step 3. figma-validate.py 실행
```bash
python3 tools/figma-validate.py --spec dryrun/section_spec.json --html dryrun/index.html --css dryrun/style.css
```
- exit code와 출력 전문을 `dryrun/figma-validate-output.txt` 로 저장

### Step 4. validate-semantic.py 실행
```bash
python3 tools/validate-semantic.py --html dryrun/index.html --css dryrun/style.css
```
- exit code와 출력 전문을 `dryrun/validate-semantic-output.txt` 로 저장
- 이 도구의 CLI 옵션이 spec과 다를 경우 `--help`를 먼저 확인하고 호환 가능한 형태로 호출
- 문서에 적힌 CLI와 실제 도구가 불일치하면 그것이 바로 "갭" — 리포트에 기록

### Step 5. 리포트 작성
`dryrun/e2e-dryrun-report.md` 생성. 형식:

```markdown
# REQ-009-02 — PLN-004 워크플로우 드라이런 리포트

생성일: 2026-04-13
검증 대상: REQ-009-01이 문서화한 5단계 워크플로우

## 드라이런 결과

| 단계 | 명령/작업 | exit | 결과 요약 |
|---|---|---|---|
| 1 | spec sheet 확보 | - | section_03_spec.json 복사 완료 (or 합성) |
| 2 | HTML/CSS 작성 | - | 최소 샘플 작성 |
| 3 | figma-validate.py | 0 or 1 | (위반 N건 / PASS) |
| 4 | validate-semantic.py | 0 or 1 | (위반 N건 / PASS) |
| 5 | commit 가능 여부 | YES/NO | 3+4 모두 exit 0인가 |

## 발견된 갭

(없으면 "없음 — 워크플로우 자기완결적")

카테고리별로 기록:
- **문서 부재**: CLAUDE.md/rules/claude.md에 설명이 부족한 지점
- **도구 버그**: figma-validate.py / validate-semantic.py 실행 실패 또는 미스매치
- **절차 불명확**: 워크플로우 순서 상 어디에서 막히는지

각 갭에 대해: 재현 방법, 추정 원인, 후속 REQ 후보 제안

## 결론

- [ ] (a) 누락 0건 — 워크플로우 자기완결적, REQ-009 종료 가능
- [ ] (b) 갭 N개 발견 — 후속 REQ로 이관 권장

선택한 판정의 근거 3~5줄
```

## 금지 사항

- `tools/*` 수정 금지 (도구 버그 발견 시 리포트에만 기록)
- `CLAUDE.md` / `rules/*` 수정 금지 (문서 갭 발견 시 리포트에만 기록)
- git commit 금지 (PM이 직접 커밋)

## 완료 조건

- `dryrun/section_spec.json`, `dryrun/index.html`, `dryrun/style.css` 존재
- `dryrun/figma-validate-output.txt`, `dryrun/validate-semantic-output.txt` 존재
- `dryrun/e2e-dryrun-report.md` 가 위 형식으로 작성되고 명확한 (a)/(b) 결론 포함

완료 시 결론 (a/b 선택 + 갭 개수) + 도구별 exit code를 4~6줄로 보고.

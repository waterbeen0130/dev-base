# Task: REQ-010 / 02 — CLAUDE.md §PLN-004 문서 보강 (갭 #1, #3, #4)

## Paths
- SPEC: /mnt/d/dev-base/.gran-maestro/requests/REQ-010/tasks/02/spec.md
- WORKTREE: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-010-02
- DRYRUN_REPORT: /mnt/d/dev-base/.gran-maestro/requests/REQ-009/tasks/02/dryrun/e2e-dryrun-report.md

## 작업 개요

REQ-009/01에서 CLAUDE.md에 추가된 `## PLN-004 Figma 워크플로우 (CRITICAL — 반드시 이 순서 준수)` 섹션을 보강한다. REQ-009/02 드라이런에서 발견된 3건의 문서 갭을 해결.

## 반드시 먼저 Read

1. `SPEC` (AC 4건)
2. `DRYRUN_REPORT` (특히 갭 #1/#3/#4 섹션)
3. `CLAUDE.md` 에서 `## PLN-004 Figma 워크플로우` 섹션을 찾아 현재 5단계 구조 확인
4. `tools/validate-semantic.py --help` 실행해 `--profile {all,basic,landing}` 옵션 확인
5. `tools/figma-validate.py` 의 9개 카테고리 순서를 코드에서 확인 (validate_text_nodes / validate_frame_nodes / validate_interactions 호출 순서)

## 작업 내용

### 갭 #1 해결 — 5단계 **4번** 단계에 `--profile` 지침 추가

현재 4번 단계는:
```bash
python3 tools/validate-semantic.py --html output.html --css output.css
```

아래처럼 개선:
- 코드 블록에 `--profile {basic|landing|all}` 포함
- 바로 아래에 선택 가이드 추가:
  - `basic`: 서브페이지 템플릿 기반 basic 프로젝트
  - `landing`: landing 프로젝트 (CDN JS, 고정 px 등)
  - `all`: 프로젝트 타입 미지정 or 공통 규칙만 검증하고 싶을 때 (단, basic/landing 전용 규칙이 섹션 단일 HTML에 오발사될 수 있음)
- 섹션 단일 검증 케이스에 대한 주의사항 한 줄: "섹션 단위 HTML만 검증할 때는 해당 프로젝트 타입 프로파일을 명시해 전용 규칙 오발사를 피할 것"

### 갭 #3 해결 — 5단계 **3번** 단계에 9개 카테고리 표 삽입

현재 3번 단계 코드 블록 **아래**에 아래 표 추가:

```markdown
**`figma-validate.py` 9개 검증 카테고리**:

| # | 카테고리 | 검증 대상 spec 필드 | 설명 |
|---|----------|---------------------|------|
| 1 | 텍스트 위변조 | `text_nodes[].characters` | spec의 text가 HTML에 존재해야 함 |
| 2 | 줄바꿈 보존 | `characters` 내 `\n`/`\u2028`/`\xa0` | 특수 공백/줄바꿈이 `<br>`/`&nbsp;` 로 보존 |
| 3 | 폰트 5필드 완결성 | `fontFamily`/`fontSize`/`fontWeight`/`lineHeightPx`/`color` | 매칭 셀렉터에 5개 모두 선언 |
| 4 | lineHeight 비율 일치 | `lineHeightRatio` | CSS `line-height` 무단위 비율 ±0.05 |
| 5 | fills color hex 일치 | `color` / `fills[].color` | CSS hex 값 대소문자 무시 일치 |
| 6 | frame padding/gap 반영 | `paddingTop/Right/Bottom/Left`, `itemSpacing` | frame 값이 CSS padding/gap에 반영 |
| 7 | clamp 적용 | padding/gap ≥100 | 해당 값은 `clamp()` 사용 필수 |
| 8 | column flex gap 금지 | `layoutMode == "VERTICAL"` | 해당 frame CSS에 `gap` 미사용 |
| 9 | interaction URL 일치 | `interactions[].url` | HTML `<a href="..." target="_blank">` 일치 |
```

> **카테고리 순서 주의**: 위 순서는 `tools/figma-validate.py` 의 실제 검증 호출 순서와 일치시켜 둘 것 (코드에서 validate_text_nodes → validate_frame_nodes → validate_interactions 순). 코드 순서가 다르면 코드 기준으로 맞춰라.

### 갭 #4 해결 — 5단계 **1번** 단계에 .md/.json 역할 명시

현재 1번 단계 코드 블록 아래의 "결과: `extracted/{section}_spec.json` + `extracted/{section}_spec.md`" 문구 뒤에 아래 문구 추가 (번호 목록 내부):

> **spec.md / spec.json 역할**:
> - `spec.md`: 사람이 읽기 편한 표 형식. AI 구현자가 값을 빠르게 파악하는 용도.
> - `spec.json`: `figma-validate.py` 의 검증 레퍼런스. 구조화된 원본 데이터.
> - AI 구현자는 두 파일 모두 접근 가능하며, 값이 불일치할 경우 `spec.json` 기준을 따른다 (검증 기준과 일치).

## 금지

- `tools/*` 수정 금지 (도구 버그는 T01 책임)
- `rules/*` 수정 금지 (이번 REQ는 CLAUDE.md 단일 파일)
- CLAUDE.md의 다른 섹션 수정 금지
- git commit 금지

## 완료 조건

- CLAUDE.md §PLN-004 섹션에 3개 보강 모두 반영
- `grep -c "figma-validate" CLAUDE.md` 결과가 증가 (최소 2회 이상)
- 9개 카테고리 표 존재
- `--profile` 단어 등장

## 완료 보고 (4~6줄)

- 추가한 섹션 위치 (라인 번호 범위)
- 9개 카테고리 표 순서가 코드 순서와 일치하는지 확인 결과
- grep 검증 결과

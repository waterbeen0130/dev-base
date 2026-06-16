# REQ-045 Task 01 — init-project.py 하드닝 + CLAUDE.md 문서 정비

- 소속 REQ: REQ-045 (PLN-012 Phase B)
- 생성일: 2026-04-21
- Assigned Agent: `[config: codex-dev] → claude-dev` (소규모 인라인 수정: `.py` + `.md` 혼합, 신규 로직 최소)

## §0 Context Manifest

- `/mnt/d/dev-base/tools/init-project.py` — 수정 대상 (line 15~ `init_project()` 함수)
- `/mnt/d/dev-base/CLAUDE.md` — 문서 정비 대상 (통합 `asset_manifest.json` 언급 구간 검색)
- `/mnt/d/dev-base/rules/CLAUDE.md`, `/mnt/d/dev-base/rules/claude.md` — 동일 내용 복제본 확인 필요
- `/mnt/d/dev-base/rules/templates/publishing/` — publishing 템플릿 존재 위치
- `/mnt/d/dev-base/.gran-maestro/requests/REQ-043/tasks/01/drill-report.md` — 갭 #1/#2/#3/#6 근거

## §1 요약

`init-project.py` 가 신규 프로젝트 디렉토리에 `.gran-maestro/` + `requests/`, `worktrees/`, `plans/` 서브디렉토리를 자동 생성하고, `--publishing` 지정 시 publishing 템플릿 미복사 실패를 silent skip 하지 않고 명시적 exit 1 로 처리하도록 개선한다. CLAUDE.md 의 통합 `asset_manifest.json` 언급을 per-section 구조로 수정한다.

## §2 범위

**포함**
- `init-project.py` 수정:
  - `.gran-maestro/` 미존재 시 자동 생성 (`requests/`, `worktrees/`, `plans/` 서브디렉토리 포함)
  - `--publishing` + 템플릿 복사 실패 시 `print(에러 메시지)` + `exit 1`
  - stdout 출력 개선: 생성된 항목과 skip 된 항목 명시
- CLAUDE.md 수정:
  - "Figma 추출 전 필수 실행" 섹션에서 통합 `asset_manifest.json` 언급 제거 또는 per-section 구조로 수정
  - "PLN-004 Figma 워크플로우" 섹션의 진입점 명확화 (`figma-section-spec.py` primary)
- `rules/CLAUDE.md` 및 `rules/claude.md` 의 복제 내용 동기화

**제외**
- `init-project.py` 의 `--type landing` 지원 확장
- CLAUDE.md 의 구조 불변 원칙 섹션 (REQ-042 에서 이미 반영)
- 다른 rules 파일 (`rules/gemini.md`, `rules/codex.md` 등) 의 전반적 재작성

## §3 수락 조건 (AC)

### AC-001 `[automatable]` — .gran-maestro 자동 생성

- **Given**: 빈 디렉토리 `/tmp/test-init-A/`
- **When**: `python3 tools/init-project.py /tmp/test-init-A --type basic --publishing` 실행
- **Then**: `.gran-maestro/`, `.gran-maestro/requests/`, `.gran-maestro/worktrees/`, `.gran-maestro/plans/` 자동 생성됨. 추가로 CLAUDE.md, `.claude/settings.local.json`, `.gran-maestro/config.json`, `.gran-maestro/agents.json` 모두 복사됨
- **Test**:
  ```bash
  rm -rf /tmp/test-init-A && mkdir -p /tmp/test-init-A
  python3 tools/init-project.py /tmp/test-init-A --type basic --publishing
  test -d /tmp/test-init-A/.gran-maestro/requests
  test -d /tmp/test-init-A/.gran-maestro/worktrees
  test -f /tmp/test-init-A/.gran-maestro/config.json
  echo "PASS"
  ```

### AC-002 `[automatable]` — --publishing 실패 시 exit 1

- **Given**: publishing 템플릿이 (일부러 삭제·이동된) 상황 모킹 또는 `RULES_DIR` 잘못된 경로
- **When**: `--publishing` 실행
- **Then**: stderr 에 "publishing 템플릿 복사 실패: {원인}" + `exit 1` 반환
- **Test**: unit 또는 integration 테스트 (publishing dir mocking 으로 실패 재현)

### AC-003 `[manual]` — CLAUDE.md 문서 정비

- **Given**: 현재 CLAUDE.md 에 통합 `asset_manifest.json` 언급이 있음 (drill-report 갭 #3)
- **When**: PR 완료 후 grep 실행
- **Then**: CLAUDE.md 에서 "extracted/asset_manifest.json" (단일 파일 언급) 제거됨. per-section 구조 (`{section}_asset_manifest.json`) 가 명시됨
- **Test**:
  ```bash
  # 통합 파일 언급이 남아있지 않은지
  ! grep -E "extracted/asset_manifest\.json[^_]" CLAUDE.md
  # per-section 구조 명시 확인
  grep "{section}_asset_manifest.json" CLAUDE.md
  ```

## §3.2 Intent Trace

| AC ID | 의도 근거 |
|---|---|
| AC-001 | PLN-012 PAC-5 — init-project 하드닝 |
| AC-002 | drill-report 갭 #2 — 명시적 에러 필요 |
| AC-003 | PAC-7 — CLAUDE.md 문서 정비 |

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-5 | MUST | AC-001, AC-002 | FULL |
| PAC-7 | SHOULD | AC-003 | FULL |

## §3.5 제약사항

- 기존 `init_project()` 함수 시그니처 유지 (backward compat)
- CLAUDE.md 는 editor 없이 Edit 도구로만 수정 (대량 재작성 금지)
- `rules/CLAUDE.md` 와 `CLAUDE.md` 내용 동기화 (두 파일 동일하게 반영)
- 테스트는 bash 스크립트 또는 간단한 pytest 로 충분

## §4 Assigned Agent

- **Primary**: `claude-dev` (소규모 인라인 수정 — `.py` 함수 1개 + `.md` grep-replace)
- **Rationale**: codex-dev 는 대규모 리팩터링에 과함, gemini-dev 는 프론트엔드 특화. claude-dev 가 점진적 편집에 적합

## §5 Test Plan

```bash
# AC-001
rm -rf /tmp/test-init-A /tmp/test-init-B
mkdir -p /tmp/test-init-A
python3 tools/init-project.py /tmp/test-init-A --type basic --publishing
test -d /tmp/test-init-A/.gran-maestro/requests && test -f /tmp/test-init-A/.gran-maestro/config.json

# AC-002 (네거티브: 템플릿 디렉토리 rename 후 재실행)
# ... (간단 integration)

# AC-003
! grep -E "extracted/asset_manifest\.json[^_]" /mnt/d/dev-base/CLAUDE.md
```

## Test Scenarios (Pre-Impl)

| AC ID | 실행 명령 / 확인 방법 |
|---|---|
| AC-001 | 위 bash 스니펫 (빈 디렉토리 → `--publishing` → `.gran-maestro/requests/` 존재 확인) |
| AC-002 | pytest 또는 수동: 템플릿 경로 조작 후 exit 1 확인 |
| AC-003 | grep 명령 (통합 파일명 부재 + per-section 패턴 존재) |

## §6 선행/후행

- blockedBy: 없음 (REQ-044 와 병렬 실행 가능)
- blocks: 없음

## §12 Intent (JTBD)

- **When I**: 새 프로젝트를 `init-project.py` 로 초기화할 때
- **I want to**: 한 번의 명령으로 `.gran-maestro/` 전체 골격과 publishing 템플릿이 자동 설치되고, 실패 시 명확한 에러를 받고 싶다
- **So I can**: 수동 mkdir 없이 바로 `/mst:request` 로 워크플로우를 시작할 수 있다

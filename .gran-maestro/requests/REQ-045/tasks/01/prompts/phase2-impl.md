# Implementation Request — init-project.py 하드닝 + CLAUDE.md 정비

- Request: REQ-045 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-045-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-045/tasks/01/spec.md

## 구현 컨텍스트

REQ-043 드릴 런에서 `tools/init-project.py` 가 `--publishing` 플래그 사용 시 `.gran-maestro/` 디렉토리 부재 시 publishing 템플릿 복사를 silent skip 하는 갭을 발견했다. 또한 CLAUDE.md 에 통합 `asset_manifest.json` 언급이 있으나 실제 파이프라인은 per-section `{name}_asset_manifest.json` 구조라 문서 불일치가 있다. 이 REQ 에서 (1) `init-project.py` 가 `.gran-maestro/` + `requests/` + `worktrees/` + `plans/` 자동 생성 + `--publishing` 실패 시 exit 1, (2) CLAUDE.md 의 통합 manifest 언급 제거를 수행한다.

## 자기탐색 지시

**worktree 내부** (`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-045-T01/`) 에서 작업.

1. 스펙 직접 읽기: `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-045/tasks/01/spec.md`
2. 수정 대상 파일 읽기:
   - `tools/init-project.py` (특히 `init_project()` 함수, line 15~)
   - `CLAUDE.md` (통합 `asset_manifest.json` 언급 grep)
   - `rules/CLAUDE.md`, `rules/claude.md` (복제본 — 동일하게 반영)
3. 구현:
   - a. `init-project.py` 에 `.gran-maestro/` + `requests/` + `worktrees/` + `plans/` 자동 생성 로직 추가 (기본 `Path.mkdir(parents=True, exist_ok=True)`)
   - b. `--publishing` 플래그 사용 시 publishing 템플릿 복사 실패하면 `print("Error: ...", file=sys.stderr)` + `sys.exit(1)`
   - c. stdout 출력 개선: 생성/skip 항목 명시
   - d. CLAUDE.md 의 `extracted/asset_manifest.json` (단일 파일 언급) 제거 또는 `{section}_asset_manifest.json` (per-section) 로 수정
4. 검증:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-045-T01
   rm -rf /tmp/test-init-A && mkdir -p /tmp/test-init-A
   python3 tools/init-project.py /tmp/test-init-A --type basic --publishing
   test -d /tmp/test-init-A/.gran-maestro/requests && test -f /tmp/test-init-A/.gran-maestro/config.json && echo "AC-001 PASS"
   # CLAUDE.md 검증
   ! grep -E "extracted/asset_manifest\.json[^_]" CLAUDE.md && echo "AC-003 PASS"
   python3 -m py_compile tools/init-project.py && echo "compile PASS"
   ```
5. git commit 금지 (PM 이 커밋)

## 규칙 (인라인)

### 작업 범위
- spec §2 범위 외 파일 수정 금지 (`tools/init-project.py`, `CLAUDE.md`, `rules/CLAUDE.md`, `rules/claude.md` 만)
- git commit 금지
- 완료 전 AC-001/002/003 self-check 필수

### Python
- 기존 함수 시그니처 유지 (backward compat)
- `Path(.gran-maestro).mkdir(parents=True, exist_ok=True)` 패턴
- sys.exit(1) 시 stderr 에 원인 명시

### CLAUDE.md 정비
- Edit 도구로 grep-replace — 대량 재작성 금지
- 통합 `asset_manifest.json` 언급 제거 또는 per-section 구조로 수정
- `rules/CLAUDE.md` 와 `CLAUDE.md` 동일하게 반영

## 완료 조건

1. AC-001: `/tmp/test-init-A/.gran-maestro/requests/` 존재
2. AC-002: `--publishing` 실패 시 exit 1 (수동 integration 검증)
3. AC-003: `! grep "extracted/asset_manifest.json[^_]" CLAUDE.md` 성공
4. `python3 -m py_compile tools/init-project.py` 성공

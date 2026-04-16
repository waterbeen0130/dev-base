# Implementation Request — Self-Exploration Mode

- Request: REQ-004 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-004/tasks/01/spec.md
- Plan: N/A

## 구현 컨텍스트 (PM 작성)

EXP-001 탐색에서 발견한 깨진 검증 계약을 복구하는 작업이다. 문서·설정 곳곳이 `tools/validate.js --type/--mapping`을 호출하라고 지시하지만 그 파일은 존재하지 않으며 실제 검증 도구는 `tools/validate-semantic.py`다. 이번 태스크는 단순 grep+Edit 작업으로, 모든 `validate.js` 참조를 실파일로 통일하는 데 집중한다.

핵심 주의사항:
1. **이 태스크에서는 새 파일을 만들지 않는다** — wrapper script를 신설하지 말고 문서/설정만 정정한다 (SSOT 원칙).
2. `validate-semantic.py`의 실제 CLI 인자를 먼저 확인하고 (`python3 tools/validate-semantic.py --help`), 문서에 적힌 `--type`/`--mapping` 등이 실제로 존재하지 않으면 단순 치환하지 말고 두 가지 방식 중 하나를 적용:
   - 실제 지원 인자로 정정
   - 또는 한 줄 주석 `# TODO: validator 확장 필요 (REQ-005+)` 추가 후 명령 자체는 사용 가능한 형태로 단순화
3. 작업 후 `grep -rn "validate.js" rules/ CLAUDE.md` 결과가 0건이어야 한다 (AC-001).
4. 당신은 worktree `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T01`에서 작업한다. 이 worktree는 main에서 분기된 독립 작업 디렉토리다.

## 자기탐색 지시

아래 순서로 스펙을 직접 탐색하라. PM이 제공한 요약에 의존하지 말고 원본 파일을 직접 읽어라.

0. spec의 `## §0 Context Manifest` 섹션을 확인하고, 나열된 파일 목록을 구현 전 가장 먼저 Read하라
1. 스펙 직접 읽기: `Read /mnt/d/dev-base/.gran-maestro/requests/REQ-004/tasks/01/spec.md`
2. §2 변경 범위의 파일 목록 파악
3. §3 수락 조건을 기준으로 구현
4. [MANDATORY] §3 AC-001의 grep 명령을 실제 worktree에서 실행하고 출력을 응답에 포함하세요 (커밋은 PM이 처리)

작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T01`

## 규칙

- spec §2의 변경 범위 외 파일 수정 금지
- 추가 기능, 리팩토링, 스타일 변경 금지
- git commit은 하지 마세요 — PM이 직접 커밋합니다
- [MANDATORY] 완료 전 §3 Test 명령을 실행하고 출력 전체를 응답에 포함하세요

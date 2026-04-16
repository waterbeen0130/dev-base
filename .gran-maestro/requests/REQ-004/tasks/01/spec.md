# Implementation Spec

- Request ID: REQ-004
- Task ID: 01
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: docs/config 일괄 치환] → 최종: claude-dev
- Assigned Team: claude-dev 단독 (다중 .md/.json 파일 일관 grep+edit)
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-004-T01
- Complexity: Lite

## §0 Context Manifest

> 구현 시작 전 이 목록의 파일을 가장 먼저 Read하세요.

- /mnt/d/dev-base/.gran-maestro/explore/EXP-001/explore-report.md (P1-1 근거)
- /mnt/d/dev-base/tools/validate-semantic.py (실구현 — 실제 CLI 시그니처 확인)
- /mnt/d/dev-base/rules/common.md (541-561 라인 부근)
- /mnt/d/dev-base/rules/rule_engine.json (238-240 라인 부근)
- /mnt/d/dev-base/rules/templates/publishing/config.json (135-137 라인 부근)
- /mnt/d/dev-base/CLAUDE.md (299-305 라인 부근)
- /mnt/d/dev-base/rules/ai-pipeline.md (67-71 라인 부근)

## 1. 요약 (Summary)

`tools/validate.js`라는 존재하지 않는 파일을 호출하도록 지시하는 모든 문서·설정을 실제 구현인 `tools/validate-semantic.py`로 일괄 치환하여 깨진 검증 계약을 복구한다.

## 2. 범위 (Scope)

- **포함**:
  - `rules/` 하위 모든 `.md`, `.json` 파일에서 `validate.js` 문자열 검색 후 대체
  - `CLAUDE.md`에서 동일 치환
  - `rules/templates/publishing/config.json`의 validate 스텝 명령어 정정
  - 치환 시 CLI 인자(`--type`, `--mapping`)가 실제 `validate-semantic.py`에 존재하는지 확인하고, 없는 인자는 실제 지원 인자 또는 N/A로 정정
- **제외**:
  - 새 `validate.js` 파일을 생성하지 않음 (Python 단일 진입점 유지)
  - validator 로직 자체 변경 (REQ-005+ 범위)
  - 모순 정리(Task 02 범위)
- **시작점 힌트**:
  - `grep -rn "validate.js" /mnt/d/dev-base/rules /mnt/d/dev-base/CLAUDE.md /mnt/d/dev-base/tools` 결과를 작업 목록으로 사용
  - `tools/validate-semantic.py:1-50` (CLI argparse 시그니처 확인)

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable]
Given: `rules/`, `CLAUDE.md`, `rules/templates/`에 `validate.js` 참조가 존재
When: 치환 작업 완료 후
Then: 위 경로 어디에서도 `validate.js` 문자열이 grep되지 않음
Test: `grep -rn "validate.js" /mnt/d/dev-base/rules /mnt/d/dev-base/CLAUDE.md` → 0건

#### AC-002 [MUST] [automatable]
Given: 치환된 명령어 예시
When: 각 치환 위치의 명령 시그니처를 `tools/validate-semantic.py`의 argparse와 대조
Then: 모든 인자가 실제 지원 인자임 (지원하지 않는 `--type`/`--mapping`은 제거하거나 주석으로 "TODO: validator 확장 필요" 표기)
Test: 수동 — 각 치환 위치에 대해 `python3 tools/validate-semantic.py --help` 결과와 1:1 대조 후 spec 본문 §11에 결과 표 첨부

#### AC-003 [MUST] [manual]
Given: 치환 완료된 문서
When: `rules/common.md`, `rules/ai-pipeline.md`, `rules/templates/publishing/config.json` 검증 스텝을 따라 sample HTML/CSS 1개에 검증 명령을 실제 실행
Then: 명령이 정상 실행되고 0/1 종료 코드를 반환 (파일 없음 에러 0건)
Test: 수동 — 임의 output 디렉토리 1개에 명령 실행

## 3.5 Constraints

- 보안: N/A
- 성능: N/A
- 호환성: 기존 `validate-semantic.py` CLI는 변경하지 않음 — 문서만 정정
- 운영: N/A

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: `rules/*.md`의 기존 코드 블록 포맷 유지 (4-space indent 코드펜스), JSON은 기존 들여쓰기 유지
- **알아야 할 제약**: `validate-semantic.py`가 지원하지 않는 인자(`--type`, `--mapping`)는 단순 치환하지 말고 실제 사용 가능한 형태로 정정해야 함
- **접근법 방향**: grep으로 모든 발생 위치 추출 → 위치별로 컨텍스트 맞춰 Edit → AC-001 grep 검증 → AC-003 실행 검증

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): []

## 6. 에이전트 팀 구성 (Agent Team)

- 실행: claude-dev (docs/config 일괄 치환)
- 사유: 다중 파일에 걸친 정확한 grep+Edit 작업으로 외주 worktree 오버헤드보다 인라인 처리가 효율적

## 10. 가정 사항 (Assumptions)

- (가정 1) `validate-semantic.py`를 진짜 SoT로 본다 — 별도 `validate.js` wrapper를 만들지 않는 결정. 근거: EXP-001 보고서에서 wrapper와 치환 두 옵션 중 치환이 추가 파일 없이 끝나며 SSOT 원칙에도 부합.
- (가정 2) 치환 후 `--type`/`--mapping` 인자가 validator에 없으면 "TODO: validator 확장 필요"로 주석 처리하고 별도 REQ에서 P3 (validator 데이터 기반 리팩터링) 단계에서 구현.

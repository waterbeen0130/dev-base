# REQ-018 / T01 — 에이스디펜스 메인 페이지 5단계 플로우 첫 실행

- **Assigned Agent**: [config: codex-dev] → gemini-dev (퍼블리싱 프로젝트, CLAUDE.md 멀티 에이전트 분배 규칙에 따라 강제)
- **Plan**: PLN-006
- **Cynefin**: Complicated (REQ-017 학습 적용)

## §0 Context Manifest

- `/mnt/d/위링/2026-04-15 에이스디펜스/` (대상 프로젝트 루트)
- `/mnt/d/위링/2026-04-15 에이스디펜스/html/page/index.html` (현재 50줄 빈 템플릿)
- `/mnt/d/위링/2026-04-15 에이스디펜스/.work/mv.yaml` (기존 mv 스크립트 — 참고용)
- `tools/init-project.py`
- `tools/figma-section-spec.py` (REQ-016 수정본)
- `tools/figma-validate.py`, `tools/validate-semantic.py`, `tools/post-impl-verify.py`
- `rules/templates/publishing/impl-request.md`
- `.gran-maestro/requests/REQ-017/tasks/01/spec.md` (동일 플로우 참조)

## §1 요약

에이스디펜스 프로젝트는 현재 파이프라인 진입조차 되지 않은 상태(빈 템플릿). REQ-017에서 검증된 5단계 플로우를 그대로 적용해 메인 페이지를 처음부터 구축한다. 구조·접근법은 REQ-017과 동일하며, 차이점은 Figma 소스와 디자인 언어뿐.

## §2 범위

### 포함
- `.gran-maestro/` 설치 (퍼블리싱 템플릿)
- Figma 섹션 경계 확정 → 섹션별 spec 생성
- HTML/CSS 작성 (`page/index.html` + `css/common.css`)
- 이미지 다운로드 (`img/`)
- 5단계 검증 루프 통과

### 제외
- 서브 페이지
- JS 인터랙션 (필요 시 별도 REQ)

## §3 수락 조건

### AC-001 [automatable] — .gran-maestro 설치

- **Given**: `.gran-maestro/` 미존재.
- **When**: `python3 /mnt/d/dev-base/tools/init-project.py "/mnt/d/위링/2026-04-15 에이스디펜스" --type basic --publishing` 실행.
- **Then**: `config.json` / `agents.json` / 기본 디렉토리 생성, `workflow.default_agent == "gemini-dev"`.
- **Test**: REQ-017/T01 AC-001과 동일 패턴.

### AC-002 [manual] — Figma 소스 확인 + 섹션 경계 확정

- **Given**: 에이스디펜스 Figma file-key / 메인 페이지 node-id.
- **When**: 사용자에게 file-key 와 node-id 를 질의한 뒤 MCP `depth=1` 호출로 최상위 자식 프레임 목록을 취득.
- **Then**: `extracted/sections.json` 기록, 최소 3개 이상.
- **Test**: REQ-017/T01 AC-002 패턴.

### AC-003 [automatable] — 섹션별 spec 생성

- AC: REQ-017/T01 AC-003 과 동일 형식. 각 섹션 spec.json / spec.md 생성, text_nodes 비어있지 않음.

### AC-004 [automatable] [tdd-required] — 섹션별 HTML/CSS 작성

- AC: REQ-017/T01 AC-004 과 동일. 클래스 프리픽스는 `index_` 기본 (사용자 지정 시 변경).
- figma-validate.py 각 섹션 exit 0.

### AC-005 [automatable] [regression-test] — validate-semantic 통과

- REQ-017/T01 AC-005 과 동일.

### AC-006 [automatable] [impact-check] — post-impl-verify 통과

- REQ-017/T01 AC-006 과 동일. 자동 재dispatch 1회 허용.

### AC-007 [browser-test] — 시각 비교

- 1920px 스크린샷 vs Figma export 비교. 결과를 `html/.verify/2026-04-15-sections/` 에 저장.

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-5 (에이스디펜스 .gran-maestro 설치) | MUST / TIER-B | AC-001 | covered |
| PAC-7 (에이스디펜스 5단계 플로우 1회 성공) | SHOULD / TIER-B | AC-003~006 | covered |

## §3.5 Constraints

- REQ-017 과 동일 규칙. 기존 `html/` 는 `.backup/` 이동 후 새로 작성.
- REQ-017 의 학습(섹션 분할 전략, 검증 실패 패턴)을 에이전트 브리프에 반영.

## §4 가정 사항

- 에이스디펜스 Figma file-key / node-id 는 사용자 제공 필요.
- REQ-017 완료 시점에 `figma-section-spec.py` 는 이미 검증된 상태.

## §5 선행 작업 / 후행 작업

- blockedBy: REQ-017
- blocks: 없음

## §6 테스트 전략

- REQ-017 와 동일한 5단계 검증 루프.

## §7 의존성 테이블

| 태스크 | blockedBy | blocks |
|---|---|---|
| REQ-018/T01 | REQ-017/T01 | (없음) |

## §8 Assigned Agent 근거

- 퍼블리싱 프로젝트 → gemini-dev 강제 (CLAUDE.md 멀티 에이전트 분배 규칙).

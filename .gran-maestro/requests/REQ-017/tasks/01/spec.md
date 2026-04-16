# REQ-017 / T01 — 목포플레이파크 섹션별 재추출 + 5단계 검증 루프

- **Assigned Agent**: [config: codex-dev] → gemini-dev (퍼블리싱 프로젝트, rules/CLAUDE.md §"멀티 에이전트 분배 규칙"에 따라 gemini-dev 강제)
- **Plan**: PLN-006
- **Cynefin**: Complicated

## §0 Context Manifest

- `/mnt/d/위링/2026-04-15 목포플레이파크/` (대상 프로젝트 루트)
- `/mnt/d/위링/2026-04-15 목포플레이파크/html/` (기존 산출물 — 백업 후 폐기)
- `/mnt/d/위링/2026-04-15 목포플레이파크/extracted/A_Main_spec.md` (기존 단일 섹션 spec — 교체 대상)
- `tools/init-project.py` (.gran-maestro 부트스트래핑)
- `tools/figma-section-spec.py` (REQ-016에서 수정됨 — 섹션 spec 생성기)
- `tools/figma-validate.py` (9개 카테고리 검증)
- `tools/validate-semantic.py` (코드 컨벤션 검증, `--profile landing`)
- `tools/post-impl-verify.py` (후처리 분류 + 재dispatch 판단)
- `rules/templates/publishing/impl-request.md` (퍼블리싱 외주 브리프 템플릿)
- `CLAUDE.md` §"PLN-004 Figma 워크플로우" (5단계 플로우)
- `CLAUDE.md` §"PM 자동 검증 후처리" (post-impl-verify 호출 계약)

## §1 요약

목포플레이파크 프로젝트의 메인 페이지를 Figma 원본과 일치하도록 재작업한다. 핵심은 (1) `.gran-maestro` 정식 설치, (2) 섹션 단위로 MCP 호출 및 spec 생성(단일 A_Main 통짜 금지), (3) 섹션별 HTML/CSS 작성, (4) 5단계 검증 루프의 모든 단계 exit 0 통과.

## §2 범위

### 포함
- `/mnt/d/위링/2026-04-15 목포플레이파크/` 에 `.gran-maestro/` 설치 (`tools/init-project.py --type basic --publishing`).
- 메인 페이지(`page/index.html`)의 섹션 단위 분해: 사용자와 함께 Figma 최상위 자식 프레임을 섹션 경계로 확정 (최소 header / hero / notice / intro / news / adventure / footer 수준으로 분할, 실제 분해는 Figma 트리에 맞춰 결정).
- 각 섹션별 `tools/figma-section-spec.py` 실행 → `extracted/{section}_spec.json/md` 생성.
- 각 섹션별 HTML 마크업 + CSS 스타일 작성. `css/common.css`에 섹션별 규칙 추가 (기존 포맷 유지, 각 셀렉터 한 줄).
- 이미지/아이콘은 Figma MCP `download_figma_images` 로 추출 후 `img/` 에 저장.
- 작업 완료 후 `post-impl-verify.py` 실행하고 exit 0 확인.
- 기존 `html/page/index.html` 와 `css/common.css` 는 `html/.backup/2026-04-15/` 로 이동 후 새로 작성.

### 제외
- 서브 페이지(존재 시) 작업 — 이 REQ는 메인 페이지 한정.
- JS 인터랙션 구현 (슬라이더/애니메이션) — 필요 시 별도 태스크.
- Figma file-key/node-id 추정 — 사용자가 제공해야 함 (가정 사항 참조).

## §3 수락 조건

### AC-001 [automatable] — .gran-maestro 설치

- **Given**: 목포 프로젝트에 `.gran-maestro/` 가 없다.
- **When**: 에이전트가 `python3 /mnt/d/dev-base/tools/init-project.py "/mnt/d/위링/2026-04-15 목포플레이파크" --type basic --publishing` 실행.
- **Then**: `.gran-maestro/config.json`, `.gran-maestro/agents.json`, `requests/`, `plans/`, `worktrees/` 가 생성되고 `workflow.default_agent == "gemini-dev"`, `figma_mcp.section_by_section == true`.
- **Test**: `test -f "/mnt/d/위링/2026-04-15 목포플레이파크/.gran-maestro/config.json" && python3 -c "import json; c=json.load(open('/mnt/d/위링/2026-04-15 목포플레이파크/.gran-maestro/config.json')); assert c['workflow']['default_agent']=='gemini-dev'; print('OK')"` → exit 0.

### AC-002 [manual] — 섹션 경계 확정

- **Given**: Figma 메인 페이지 노드 `134:6708` 또는 사용자가 제공한 상위 노드.
- **When**: 에이전트가 `mcp__figma__get_figma_data` 를 `depth=1`로 호출해 최상위 자식 프레임 목록을 취득한 후, 각 프레임을 독립 섹션으로 선언한다.
- **Then**: `extracted/sections.json` 에 `[{section_id, node_id, name, order}]` 형태로 섹션 목록이 기록되고, 최소 5개 이상 (header/hero/notice/intro/news/adventure/footer 또는 실제 구조에 해당하는 구분).
- **Test**: `python3 -c "import json; s=json.load(open('/mnt/d/위링/2026-04-15 목포플레이파크/extracted/sections.json')); assert len(s) >= 5; print('OK', len(s))"` → exit 0.

### AC-003 [automatable] — 섹션별 spec 생성

- **Given**: AC-002의 섹션 목록과 REQ-016에서 수정 완료된 `figma-section-spec.py`.
- **When**: 에이전트가 각 섹션 `node_id` 에 대해 `figma-section-spec.py --file-key K --node-id N --output extracted/` 를 순차 실행한다.
- **Then**: 각 섹션에 대해 `{section}_spec.json` / `{section}_spec.md` 두 파일이 생성되고, `text_nodes` 배열이 비어있지 않다.
- **Test**: sections.json 기준 for-loop 으로 각 파일 존재 검증, 0건 누락.

### AC-004 [automatable] [tdd-required] — 섹션별 HTML/CSS 작성

- **Given**: 섹션별 spec.md 및 spec.json.
- **When**: 에이전트가 **spec.md만 참조**하여(raw Figma JSON 직접 해석 금지) 섹션별 HTML 블록을 `page/index.html` 에 조립하고 CSS 를 `css/common.css` 에 추가한다. 클래스 프리픽스는 `index_` 또는 섹션명 기반. `rules/common.md`, `rules/basic.md`, `rules/landing.md` 준수.
- **Then**: 각 섹션 spec 의 text_nodes 가 모두 HTML 에 존재, frame padding/gap/fills 가 CSS 에 반영, 100px 이상 값은 `clamp()` 사용.
- **Test**: `python3 /mnt/d/dev-base/tools/figma-validate.py --spec extracted/{section}_spec.json --html page/index.html --css css/common.css` 각 섹션에 대해 exit 0.

### AC-005 [automatable] [regression-test] — validate-semantic 통과

- **Given**: AC-004 완료 상태.
- **When**: 에이전트가 `python3 /mnt/d/dev-base/tools/validate-semantic.py --html page/index.html --css css/common.css --profile basic` (또는 프로젝트 타입에 맞는 프로파일) 실행.
- **Then**: exit 0.
- **Test**: 동일 명령 재실행 검증.

### AC-006 [automatable] [impact-check] — post-impl-verify 통과

- **Given**: AC-004, AC-005 통과.
- **When**: 에이전트가 각 섹션에 대해 `python3 /mnt/d/dev-base/tools/post-impl-verify.py --spec extracted/{section}_spec.json --html page/index.html --css css/common.css --profile basic` 실행.
- **Then**: 모든 섹션에서 exit 0. exit 1 이 발생하면 외주 에이전트에 재dispatch 1회 허용, 그 후에도 실패 시 사용자 에스컬레이션.
- **Test**: 동일 명령 재실행.

### AC-007 [browser-test] — 1920px 뷰포트 시각 비교

- **Given**: AC-001~006 통과.
- **When**: 에이전트가 Playwright 로 `file:///.../page/index.html` 을 1920×1080 으로 스크린샷 촬영하고, Figma의 동일 프레임 export 이미지와 섹션별 시각 비교.
- **Then**: 각 섹션에서 구조/순서/간격이 Figma와 일치. 차이점이 있으면 관련 섹션만 재작업.
- **Test**: 스크린샷을 `html/.verify/2026-04-15-sections/` 에 저장, 사용자 확인용으로 경로 출력.

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-4 (목포 .gran-maestro 설치) | MUST / TIER-B | AC-001 | covered |
| PAC-6 (목포 5단계 검증 모두 통과) | MUST / TIER-A | AC-003, AC-004, AC-005, AC-006 | covered |

## §3.5 Constraints

- 기존 `html/` 산출물 삭제 금지 — `.backup/` 이동만 허용.
- 섹션 단위 분할 필수. A_Main 통짜 spec 재사용 금지.
- `rules/templates/publishing/impl-request.md` 의 코딩 규칙(common.md / gemini.md 인라인) 준수.
- letter-spacing은 `em` 단위, border-radius는 원형 `50%` / pill `2em`, flexbox 전용, hex 색상.
- 768px 이하 모바일은 PC 값의 절반 적용 (basic 프로젝트 규칙).

## §4 가정 사항

- **사용자 확인 필요**: Figma file-key 와 메인 페이지 최상위 node-id. REQ-016의 spec.md에는 `134:6708` 이 기록되어 있으나 이는 `A_Main` 프레임 ID이며, 실제 메인 페이지 루트는 사용자 확인 필요. 에이전트는 실행 시작 시 file-key/node-id 를 사용자에게 질의한다.
- 기존 `extracted/A_Main_spec.json` 은 REQ-016 완료 후 REQ-017 진입 시점에 이미 재생성되어 있을 수 있음 — 재생성 여부와 무관하게 섹션 분할 작업을 새로 수행.

## §5 선행 작업 / 후행 작업

- blockedBy: REQ-016 (도구 수정 완료 전 재추출 무의미)
- blocks: REQ-018 (목포 경험을 에이스디펜스에 적용)

## §6 테스트 전략

- [lint-check] 없음 (HTML/CSS)
- [automatable] figma-validate.py / validate-semantic.py / post-impl-verify.py 세 단계 모두 exit 0
- [browser-test] AC-007 — 1920px 스크린샷 시각 비교

## §7 의존성 테이블

| 태스크 | blockedBy | blocks |
|---|---|---|
| REQ-017/T01 | REQ-016/T01 | REQ-018/T01 |

## §8 Assigned Agent 근거

- config `workflow.default_agent = codex-dev` (dev-base 기준)이나 이 REQ는 **외부 퍼블리싱 프로젝트** 작업이며 CLAUDE.md "멀티 에이전트 분배 규칙" 에 따라 퍼블리싱 = gemini-dev 강제 배정.
- 외주 브리프 템플릿은 `rules/templates/publishing/impl-request.md` 사용.

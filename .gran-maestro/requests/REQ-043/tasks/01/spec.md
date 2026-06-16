# REQ-043 Task 01 — 디에스솔루션 MAIN 페이지 HTML/CSS 구현 (spec sheet 기반)

- 소속 REQ: REQ-043
- 소속 Plan: PLN-011
- 생성일: 2026-04-21
- Assigned Agent: `[config: codex-dev] → gemini-dev` (퍼블리싱 프로젝트: HTML/CSS/Figma→code 전환, CLAUDE.md `프로젝트 유형별 에이전트 배정` 규정 override)

## §0 Context Manifest

AI 에이전트가 작업 시작 전 반드시 Read 해야 할 파일 목록. 완전하지 않을 수 있으며 필요 시 자율 탐색 허용.

- `/mnt/d/dev-base/CLAUDE.md` — 구조 불변 원칙 + PLN-004 워크플로우 + 퍼블리싱 규칙
- `/mnt/d/dev-base/rules/common.md` — 공통 CSS/HTML 규칙
- `/mnt/d/dev-base/rules/basic.md` — basic 프로파일 전용 규칙
- `/mnt/d/dev-base/rules/gemini.md` — gemini 에이전트 규칙
- `/mnt/d/dev-base/rules/templates/publishing/impl-request.md` — 퍼블리싱 브리프 템플릿 v2
- `/mnt/d/dev-base/templates/index.html`, `/mnt/d/dev-base/templates/sub_list.html` — HTML 템플릿 골격
- `/mnt/d/dev-base/templates/css/reset.css`, `/mnt/d/dev-base/templates/css/font.css` — 공통 CSS 베이스
- `/mnt/d/dev-base/tools/figma-section-spec.py` — spec 생성 도구 (PM 실행)
- `/mnt/d/dev-base/tools/figma-validate.py` — Figma 충실도 검증
- `/mnt/d/dev-base/tools/validate-semantic.py` — 코드 컨벤션 검증
- `/mnt/d/dev-base/tools/post-impl-verify.py` — 수렴 루프 (REQ-041)
- `/mnt/d/dev-base/.gran-maestro/plans/PLN-011/plan.md` — 상위 plan

## §1 요약

dev-base 에서 완성된 Figma → HTML/CSS 파이프라인(PLN-004/005/009/010 + REQ-040/041/042)을 디에스솔루션 Figma 소스의 MAIN 페이지에 적용하여 end-to-end 검증한다. PM 이 init-project + figma-section-spec 으로 spec sheet 를 준비한 뒤, gemini-dev 가 spec.md 만 참조하여 HTML/CSS 를 작성한다. 이후 4종 게이트(figma-validate / validate-semantic / structural-diff / post-impl-verify) 가 순차 실행되고, CRITICAL 잔여 시 `--converge` 수렴 루프가 최대 2회 재dispatch 한다.

## §2 범위

**포함**
- 프로젝트 폴더: `D:/위링/2026-04-21 디에스솔루션/`
- Figma: `file-key=JLCP6dWG63kJVBlND7bVZl`, `node-id=130:10972` (페이지 `📌Main_Sub (260417)` 내 MAIN)
- 출력: `output/a_main/index.html` + `output/a_main/common.css` + `output/a_main/img/*`
- 4종 게이트 전체 통과 (CRITICAL 0건)
- `asset_manifest.json` 생성 및 모든 이미지 fills 매핑

**제외**
- Sub 페이지 추출 (메뉴/서브비주얼/서브페이지 본문 제외)
- 모바일 반응형 세부 조정 (PC 1920 기준만)
- 실 배포 / 도메인 연결
- 파이프라인 도구 자체 수정 (figma-section-spec / figma-validate / post-impl-verify 코드 변경 금지)

## §3 수락 조건 (AC)

### AC-001 `[automatable]` `[tdd-required]` — 프로젝트 초기화

- **Given**: `D:/위링/2026-04-21 디에스솔루션/` 폴더가 존재하거나 없음
- **When**: `python3 D:/dev-base/tools/init-project.py "D:/위링/2026-04-21 디에스솔루션" --type basic --publishing` 실행
- **Then**: `.claude/settings.local.json`, `.gran-maestro/config.json`, `CLAUDE.md`, `AGENTS.md`, `tools/`, `rules/` 심링크/복사본 생성 확인
- **Test**: `ls -la` 로 6개 항목 존재 확인 + `config.json` 의 `default_agent == "gemini-dev"` 확인

### AC-002 `[automatable]` `[tdd-required]` — Spec sheet 생성

- **Given**: FIGMA_TOKEN 환경변수 + MAIN 노드 ID (`130:10972`)
- **When**: PM 이 MAIN 페이지의 각 섹션 별로 `tools/figma-section-spec.py --file-key JLCP6dWG63kJVBlND7bVZl --node-id <section_id> --output extracted/` 반복 실행
- **Then**: `extracted/{section}_spec.md` + `extracted/{section}_spec.json` 이 모든 섹션에 대해 생성됨, 각 spec.json 의 `text_nodes[].characters` 가 Figma 원본과 byte-exact 일치
- **Test**: `ls extracted/*_spec.{md,json} | wc -l` 로 쌍 개수 확인, 샘플 spec.json 에서 NBSP(`\xa0`) 존재 여부 grep

### AC-003 `[automatable]` `[tdd-required]` — Asset manifest

- **Given**: spec 생성 과정에서 이미지 fills 발견
- **When**: `figma-section-spec.py` 가 자동으로 `asset_manifest.json` 누적 업데이트
- **Then**: `extracted/asset_manifest.json` 에 모든 이미지 ID + local path + original_url 매핑 존재
- **Test**: `python3 -c "import json; d=json.load(open('extracted/asset_manifest.json')); print(len(d['assets']))"` > 0

### AC-004 `[automatable]` `[tdd-required]` `[impact-check]` — HTML/CSS 구현 (gemini-dev)

- **Given**: spec.md 파일들이 `extracted/` 에 존재
- **When**: gemini-dev 가 spec.md 만 참조하여 `output/a_main/index.html` + `output/a_main/common.css` 작성
- **Then**: spec 의 `text_nodes[].characters` 가 HTML 에 byte-exact 로 반영 (NBSP/라인 분리자/연속 공백/줄바꿈 모두 보존), `frame_nodes` 계층이 HTML DOM 계층과 1:1 대응, 모든 이미지가 `asset_manifest.json` 등록 경로 사용
- **Test**: `figma-validate.py --spec-dir extracted/ --html output/a_main/index.html --css output/a_main/common.css` exit 0

### AC-005 `[automatable]` `[tdd-required]` — figma-validate 9 카테고리 통과

- **Given**: 구현된 HTML/CSS
- **When**: `python3 tools/figma-validate.py --spec-dir extracted/ --html output/a_main/index.html --css output/a_main/common.css`
- **Then**: 9 카테고리(텍스트 위변조 / 줄바꿈 / 폰트 5필드 / lineHeight 비율 / fills hex / frame padding·gap / clamp / column flex gap / interaction URL) 전체에서 CRITICAL 0건
- **Test**: exit 0 + stdout 에 "ALL PASS" 출력

### AC-006 `[automatable]` `[tdd-required]` — validate-semantic basic 프로파일 통과

- **Given**: 구현된 HTML/CSS
- **When**: `python3 tools/validate-semantic.py --html output/a_main/index.html --css output/a_main/common.css --profile basic`
- **Then**: CRITICAL 0건 (MAJOR/MINOR 는 허용하되 리포트에 기록)
- **Test**: exit 0

### AC-007 `[automatable]` `[tdd-required]` — 수렴 루프

- **Given**: AC-005/AC-006 중 하나 이상이 첫 실행에서 CRITICAL 발생
- **When**: `python3 tools/post-impl-verify.py --spec-dir extracted/ --html output/a_main/index.html --css output/a_main/common.css --profile basic --converge --max-iter 2`
- **Then**: 수렴 루프가 최대 2회 재dispatch 후 exit 0 달성 (또는 max-iter 도달 시 exit 1 로 사용자 개입)
- **Test**: exit code 기록, iteration 수 로그 확인

### AC-008 `[automatable]` — DOM 구조 해시 일치

- **Given**: 구현된 HTML + spec 의 frame_nodes 계층
- **When**: `python3 tools/structural-diff.py --html output/a_main/index.html --spec-dir extracted/ --dump-hash`
- **Then**: DOM 구조 해시가 spec 의 frame 계층 해시와 일치 (wrapper 임의 삭제 없음)
- **Test**: exit 0

### AC-009 `[manual]` — 실행 로그 기록

- **Given**: 모든 파이프라인 단계 완료
- **When**: REQ 폴더 확인
- **Then**: `tasks/01/running.log` 에 pre-setup + gemini-dev dispatch + 수렴 루프 반복 이력이 기록됨
- **Test**: `wc -l running.log > 50` 및 iteration count 기록 확인

### AC-010 `[manual]` — 드릴 런 이슈 리포트

- **Given**: 파이프라인 1회 완주
- **When**: PM 이 실행 중 발견한 파이프라인 이슈(버그/UX/DX 이슈) 정리
- **Then**: `tasks/01/drill-report.md` 에 이슈 목록 + 개선 후보 정리 (PLN-012 소재)
- **Test**: `drill-report.md` 존재 + 최소 1건 이상 항목

## §3.2 Intent Trace

| AC ID | 의도 근거 |
|---|---|
| AC-001~003 | PLN-011 §4 인수 기준 초안 PAC-1/2/3 — 환경·spec·manifest 생성 |
| AC-004 | PAC-4 — text byte-exact 구현 |
| AC-005 | PAC-5 — figma-validate 충실도 |
| AC-006 | PAC-6 — validate-semantic 컨벤션 |
| AC-007 | PAC-7 — 수렴 루프 (REQ-041) |
| AC-008 | PAC-8 — structural-diff (REQ-036) |
| AC-009~010 | PAC-9/10 — 드릴 런 기록 가치 |

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-1 | MUST | AC-001 | FULL |
| PAC-2 | MUST | AC-002 | FULL |
| PAC-3 | MUST | AC-003 | FULL |
| PAC-4 | MUST | AC-004 | FULL |
| PAC-5 | MUST | AC-005 | FULL |
| PAC-6 | MUST | AC-006 | FULL |
| PAC-7 | MUST | AC-007 | FULL |
| PAC-8 | MUST | AC-008 | FULL |
| PAC-9 | SHOULD | AC-009 | FULL |
| PAC-10 | SHOULD | AC-010 | FULL |

모든 MUST PAC 커버됨. SPEC_ONLY AC 없음.

## §3.5 제약사항

- FIGMA_TOKEN 환경변수 필수 (위링 개인 토큰, `~/.figma_token` 또는 env)
- Figma MCP / raw Figma API 직접 해석 금지 — spec.md 경유만 (CLAUDE.md `PLN-004 워크플로우`)
- AI 합성 이미지 삽입 금지 — `asset_manifest.json` 등록 원본만 (`asset_manifest_consistency` CRITICAL)
- DOM 계층 wrapper 임의 삭제 금지 (CLAUDE.md `구조 불변 원칙`)
- text byte-exact 보존 (NBSP, ` `, `\xa0`, 연속 공백, `\n` 모두 원본 그대로)
- basic 프로파일 규칙 적용 (reset.css 별도 파일, PC rem / 모바일 px, 768px 이하 반응형)
- max_cli_retries=2 (config.json 기본값)
- 파이프라인 도구 코드 수정 금지 — 드릴 런 목적이므로 발견 버그는 `drill-report.md` 에 기록만

## §4 Assigned Agent

- **Primary**: `gemini-dev` (퍼블리싱 규정)
- **PM 직접 실행 단계** (dispatch 전/후):
  - Pre: `init-project.py`, `figma-extract.py --tree`, `figma-section-spec.py` (각 섹션 반복)
  - Post: `figma-validate.py`, `validate-semantic.py`, `post-impl-verify.py --converge`, `structural-diff.py`
- **gemini-dev 담당 단계**: HTML/CSS 작성 (spec.md 기반) + 수렴 루프 재dispatch 시 위반 수정

### 외주 브리프 규칙

- 템플릿: `/mnt/d/dev-base/rules/templates/publishing/impl-request.md` (rules_version: 2)
- 브리프 `## 코딩 규칙` 섹션에 `rule_ids: [all]` 명시 필수
- `## 구조 불변 원칙` 섹션 자동 주입 (REQ-042 PM 훅)

## §5 선행 작업 (blockedBy) / 후행 작업 (blocks)

- blockedBy: 없음
- blocks: 없음 (단일 태스크)

## §6 Quality Gates

| Gate | 도구 | 기준 |
|---|---|---|
| G1 — Figma 충실도 | `figma-validate.py` | CRITICAL 0건, 9 카테고리 PASS |
| G2 — 코드 컨벤션 | `validate-semantic.py --profile basic` | CRITICAL 0건 |
| G3 — DOM 구조 | `structural-diff.py --dump-hash` | spec frame 계층과 해시 일치 |
| G4 — 수렴 | `post-impl-verify.py --converge --max-iter 2` | exit 0 |

전체 AND 통과 조건. 하나라도 실패 시 수렴 루프 재dispatch.

## Test Scenarios (Pre-Impl)

| AC ID | 실행 명령 / 확인 방법 |
|---|---|
| AC-001 | `ls -la "D:/위링/2026-04-21 디에스솔루션/"` + `.claude/settings.local.json`, `.gran-maestro/config.json`, `CLAUDE.md` 존재 확인 |
| AC-002 | `ls extracted/*_spec.md extracted/*_spec.json \| wc -l` — 쌍 개수 동일 + `python3 -c "import json; d=json.load(open('extracted/{section}_spec.json')); assert '\xa0' in json.dumps(d) or len(d.get('text_nodes',[]))>0"` |
| AC-003 | `python3 -c "import json; d=json.load(open('extracted/asset_manifest.json')); print(len(d.get('assets',{}) or d.get('assets',[])))"` > 0 |
| AC-004 | `python3 D:/dev-base/tools/figma-validate.py --spec-dir extracted/ --html output/a_main/index.html --css output/a_main/common.css` → exit 0 |
| AC-005 | (AC-004 와 동일 명령) + stdout 에 "ALL PASS" 또는 CRITICAL 0건 로그 |
| AC-006 | `python3 D:/dev-base/tools/validate-semantic.py --html output/a_main/index.html --css output/a_main/common.css --profile basic` → exit 0 |
| AC-007 | `python3 D:/dev-base/tools/post-impl-verify.py --spec-dir extracted/ --html output/a_main/index.html --css output/a_main/common.css --profile basic --converge --max-iter 2` → exit 0, iteration 수 로그 확인 |
| AC-008 | `python3 D:/dev-base/tools/structural-diff.py --html output/a_main/index.html --spec-dir extracted/ --dump-hash` → exit 0 |
| AC-009 | `wc -l D:/dev-base/.gran-maestro/requests/REQ-043/tasks/01/running.log` > 50 |
| AC-010 | `ls D:/dev-base/.gran-maestro/requests/REQ-043/tasks/01/drill-report.md` + `wc -l drill-report.md` > 10 |

## §12 Intent (JTBD)

- **When I**: 어제까지 완성한 Figma 파이프라인을 실전 Figma 소스로 1회 검증하고 싶을 때
- **I want to**: 디에스솔루션 MAIN 페이지 전체에 파이프라인을 end-to-end 돌리고
- **So I can**: 수렴 루프·구조 불변 원칙·4종 게이트가 실전에서 기대대로 작동하는지 확인하고, 발견된 갭을 후속 PLN 소재로 만들 수 있다

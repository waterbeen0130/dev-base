# REQ-046 Task 01 — 디에스솔루션 MAIN HTML/CSS 구현 + 4종 게이트 (드릴 재시도)

- 소속 REQ: REQ-046 (PLN-012 Phase C)
- 생성일: 2026-04-21
- Assigned Agent: `[config: codex-dev] → gemini-dev` (퍼블리싱)

## §0 Context Manifest

- `/mnt/d/위링/2026-04-21 디에스솔루션/extracted/*_spec.md` — 6개 섹션 spec (header_b / MV / sec_1 / sec_2 / sec_5 / footer_bk)
- `/mnt/d/위링/2026-04-21 디에스솔루션/extracted/{section}/vectors/*.svg` — 다운로드된 SVG
- `/mnt/d/위링/2026-04-21 디에스솔루션/extracted/{section}/images/*.png` — 다운로드된 PNG
- `/mnt/d/위링/2026-04-21 디에스솔루션/extracted/{section}_asset_manifest.json` — local_path 포함
- `/mnt/d/dev-base/templates/index.html`, `/mnt/d/dev-base/templates/css/reset.css` — 골격
- `/mnt/d/dev-base/CLAUDE.md` — 퍼블리싱 규칙

## §1 요약

REQ-043 드릴 런에서 실패했던 "gemini HTML/CSS 작성 + 4종 게이트 통과" 를 REQ-044 의 `--download-assets` 로 재생성된 spec (실제 SVG/PNG 포함) 를 가지고 재시도한다. 출력은 `/mnt/d/위링/2026-04-21 디에스솔루션/output/a_main/` (index.html + common.css + reset.css + img/).

## §2 범위

**포함**
- 6개 섹션 (header_b / MV / sec_1 / sec_2 / sec_5 / footer_bk) HTML/CSS 구현
- `output/a_main/index.html` + `common.css` + `reset.css` 생성
- 이미지 src: `asset_manifest.json` 의 `local_path` 기반 `./img/*.svg` / `./img/*.png`
- asset 파일들을 `extracted/{section}/{vectors|images}/` → `output/a_main/img/` 로 복사
- 4종 게이트 전부 통과

**제외**
- 모바일 반응형 세부 조정
- JS 애니메이션
- 서브페이지

## §3 수락 조건

### AC-001 `[automatable]` `[tdd-required]` — HTML/CSS 생성

- **Given**: 6개 섹션 spec + asset 파일들
- **When**: gemini HTML/CSS 작성 완료
- **Then**: `output/a_main/{index.html,common.css,reset.css}` 존재, `output/a_main/img/` 에 SVG/PNG 복사됨, 각 섹션이 HTML 에 반영
- **Test**: `ls output/a_main/ | grep -E 'index.html|common.css|reset.css'` + `ls output/a_main/img/*`

### AC-002 `[automatable]` `[tdd-required]` — figma-validate 통과

- **Given**: 생성된 HTML/CSS
- **When**: `python3 /mnt/d/dev-base/tools/figma-validate.py --spec-dir extracted/ --html output/a_main/index.html --css output/a_main/common.css`
- **Then**: exit 0, CRITICAL 0건
- **Test**: 위 명령 exit code 확인

### AC-003 `[automatable]` `[tdd-required]` — validate-semantic 통과

- **Given**: 생성된 HTML/CSS
- **When**: `python3 /mnt/d/dev-base/tools/validate-semantic.py --html output/a_main/index.html --css output/a_main/common.css --profile basic`
- **Then**: exit 0, CRITICAL 0건
- **Test**: 위 명령 exit code 확인

### AC-004 `[automatable]` — post-impl-verify --converge 통과

- **Given**: 4종 게이트 수렴 루프
- **When**: `python3 /mnt/d/dev-base/tools/post-impl-verify.py --spec-dir extracted/ --html output/a_main/index.html --css output/a_main/common.css --profile basic --converge --max-iter 2`
- **Then**: exit 0 달성 (필요 시 재dispatch 후 통과)
- **Test**: 위 명령 exit code 확인

### AC-005 `[manual]` — 드릴 리포트 v2

- **Given**: 파이프라인 1회 완주
- **When**: PM 이 재시도 결과 정리
- **Then**: `tasks/01/drill-report-v2.md` 작성 (REQ-043 대비 개선 항목 + 새로 발견된 갭)

## Test Scenarios (Pre-Impl)

| AC ID | 실행 명령 |
|---|---|
| AC-001 | `ls /mnt/d/위링/2026-04-21\ 디에스솔루션/output/a_main/ \| grep -c index.html` → 1 |
| AC-002 | 위 figma-validate 명령 exit 0 |
| AC-003 | 위 validate-semantic 명령 exit 0 |
| AC-004 | 위 post-impl-verify 명령 exit 0 |
| AC-005 | `ls /mnt/d/dev-base/.gran-maestro/requests/REQ-046/tasks/01/drill-report-v2.md` + 최소 10줄 |

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-8 | SHOULD | AC-001/002/003/004 | FULL |
| PAC-9 | SHOULD | AC-005 (리포트 대체) | PARTIAL |

## §4 Assigned Agent

- **Primary**: `gemini-dev` (퍼블리싱)

## §5 선행/후행

- blockedBy: 없음 (REQ-044 완료됨)
- blocks: 없음

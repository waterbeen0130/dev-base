# AGI-004 핸드오프 — Figma→퍼블리싱 검증체계/룰 보강

> 작성: 2026-06-16 / 브랜치: `agi-004-verification-hardening` (origin push 완료)
> 내일 이어서 작업할 때 이 문서부터 읽으면 된다.

## 1. 한 줄 요약
"코드 추출 결과물의 규칙 위반을 검증이 못 잡고, '검증 끝내고 줘'가 안 지켜진" 문제를 → 검증 엔진 수리 + 규칙/검증도구 보강 + 검증 실행 강제 게이트 + AI-agnostic 단일 지시서로 해결. **objective 13/13 완료, A/B 룰 커버리지 갭 100% 해소, 테스트 147 passed/0 failed.**

## 2. 브랜치 / 커밋 (전부 origin push 완료)
- 브랜치: `agi-004-verification-hardening`
- `4ef93c0` 엔진 수리 + 규칙 3종 + 검증 실행 게이트 + 단일소스 통합
- `9af640a` 산출물경계 + 부분색상 + 커버리지리포트 + 노이즈 재점검
- `62379c7` follow-up 규칙 2종 (no_guess_prefix, no_korean_css_comment)
- `3f8b3f1` 런타임 계측 2종 (workflow_order, extraction-provenance)
- PR 미생성: https://github.com/waterbeen0130/dev-base/pull/new/agi-004-verification-hardening

## 3. 무엇이 바뀌었나 (파일 맵)

### 신규 검증 도구 (tools/)
| 파일 | 역할 | 실행 |
|------|------|------|
| `verify-evidence-gate.py` | 검증 실행 증거(파일 sha 일치 + passed) 없으면 완료 차단 | `--html --css --report` |
| `check-deprecated-tools.py` | 폐기 도구 부활/호출 + `--converge` 검출 | `--root .` |
| `check-output-boundary.py` | raw `extracted/`·노드명 덤프 HTML이 최종물로 오인되는 것 차단 | `--deliverable .` |
| `check-mixed-styles.py` | spec `has_mixed_styles` 구간색 누락(단일색 출력) 검출 | `--spec --html --css` |
| `rule-coverage-report.py` | 룰 커버리지 갭 측정 리포트(현 A/B 12/12=100%) | `--root . [--json]` |
| `check-workflow-order.py` | 워크플로우 원장 기반 2패스 순서 강제(values는 structure 이후) | `--ledger ...` |
| `check-extraction-provenance.py` | 추출 단계 provider(omx/codex/claude/gemini) 검증 | `--ledger ...` |
| `pm-verify.py` (수정) | `--emit-report PATH` 옵션 추가 → 검증 증거 JSON 출력 | 기존 + `--emit-report` |

### 신규/변경 규칙 (rules/rules.yaml, 현 86개)
- `no_figma_nodeid_class` (error) — main_f0 등 노드명 직역 차단
- `common_area_child_scope` (warning) — .logo{} 단독선언 검출
- `global_class_standalone` (warning) — body .header{} 부모오염 검출
- `no_guess_prefix` (warning) — site_/g_/common_ 추측 prefix
- `no_korean_css_comment` (warning) — CSS 주석 한글 금지
- 엔진 수리: 미등록 카테고리(css.image/css.format/spec.schema) 수정 + `EXPECTED_RULE_COUNT` 동기화(86) + `rules/models.py`

### 단일 지시서 (AI-agnostic)
- `rules/INSTRUCTIONS.md` (신규) — 스크린샷-우선 2패스 워크플로우 + 공통원칙 + 네이밍 + 워크플로우 원장 포맷. **손으로 유지하는 단 하나의 지시서.**
- `CLAUDE.md`(468→68줄 shim), `AGENTS.md`(규칙중복 제거), `GEMINI.md`(신규) — 모두 INSTRUCTIONS.md 가리키는 thin shim.
- 규칙 본문 단일소스 = `rules/rules.yaml` → 자동생성 `rules/common.md`(`python3 tools/build-rules.py`).

### 테스트 (tests/unit/)
test_no_figma_nodeid_class, test_common_area_scoping, test_verify_evidence_gate, test_deprecated_tools, test_output_boundary, test_mixed_styles, test_rule_coverage_report, test_noise_reclassification, test_no_guess_prefix, test_korean_css_comment, test_workflow_order, test_extraction_provenance + 수정(test_pydantic_rules_load, test_req024_rules_slimming).

## 4. 규칙 변경 시 반드시 동기화 (CRITICAL gotcha)
`rules/rules.yaml` 에 규칙 추가/변경 시 — 하나라도 어긋나면 `load_rules()` 전면 실패:
1. `category` 값이 rules.yaml `categories:` 목록에 존재해야 함
2. `rules/models.py:EXPECTED_RULE_COUNT` 를 실제 규칙 수와 일치시킴
3. `python3 tools/build-rules.py` 로 common.md + validation_schema.json 재생성
4. `python3 -m pytest tests/` 그린 확인

## 5. 내일 이어서 할 후보 (우선순위순)
1. **PR 생성 + 리뷰/머지** (위 링크). main 머지 전 `pytest tests/` 재확인.
2. **신규 체커를 accept 게이트에 실제 연결**: 현재 `verify-evidence-gate`/`check-workflow-order`/`check-extraction-provenance`/`check-output-boundary`/`check-deprecated-tools` 는 도구로 존재하나 `mst:accept` PreToolUse hook(`pm-verify-accept-gate.sh`)에는 미연결. 이걸 묶으면 "완료 차단"이 자동화됨. (지금은 수동 실행)
3. **`rules/claude.md`(init-project 템플릿) 정리**: 다른 프로젝트 배포용 템플릿이라 이번 범위 제외함. INSTRUCTIONS.md 패턴(thin shim)으로 맞추면 일관성↑. (pre-existing 미커밋 변경이 있으니 주의)
4. **워크플로우 원장 자동 기록**: 추출 파이프라인이 `.gran-maestro/workflow-ledger.json` 에 실제로 step을 append하도록 연결(현재 포맷만 정의됨).
5. 실제 추출 1건으로 end-to-end 검증(스크린샷-우선 2패스 → pm-verify --emit-report → 게이트들).

## 6. 커밋 안 한 것 (오늘 작업 아님 — 의도적 제외)
다음은 세션 시작 전부터 있던/다른 작업 산출물이라 이 브랜치에 넣지 않음:
- `.claude/hooks/*` (mst-stop-hook 등), `.gran-maestro/*/counter.json` (런타임)
- `rules/claude.md`, `tools/figma-section-spec.py` (pre-existing 미커밋)
- `tools/accept-preflight-verify.py` (pre-existing 미커밋, accept 게이트 일부)
- 다른 에이전트/세션 산출물: `AGI-002/003`, `DBG-002`, `IDN-003`, `PLN-014~016`, `REQ-047~049`, `dssolution_*.png`, `rules/gnuboard.md`, `tmp/`
→ 필요하면 별도로 정리/커밋할 것.

## 7. 재개 명령
- objective 상태 확인: `python3 {plugin}/scripts/mst.py agile status AGI-004 --json`
- 커버리지 현황: `python3 tools/rule-coverage-report.py --root .`
- 전체 테스트: `python3 -m pytest tests/ -q`

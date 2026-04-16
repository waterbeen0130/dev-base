# DSC-002 Round 0 종합

## 참여자 입장 요약
| 역할 (provider) | 핵심 입장 |
|---|---|
| architect (codex) | 검증기에 6개 신규 규칙 + figma-section-spec.py `main()` payload 생성 직후 전처리 삽입 + post-impl-verify rule_id 파싱 기반 MINOR 재분류. **우선순위 1. validate-semantic 2. figma-section-spec 3. post-impl-verify**. lineHeight 정돈 알고리즘: `step=0.05, 허용오차 0.03`. iteration cap hard 2회. |
| frontend-rules (gemini) | 에이전트 실패 3대 원인: Figma 충실도 편향/타입 혼동/scope 밖 규칙 망각. 브리프 상단에 "원본 충실도 < 컨벤션" 강제 명문화 + 3중 앵커(spec.md 메타·brief 헤더·HTML 첫 줄 주석)로 프로젝트 타입 전달. |
| risk (claude) | 3-Layer 주입 전략(short brief ≤800토큰 + external rules ref + runtime check). 검증기 false-positive ≤2%, impl-request 본문 ≤1500토큰, lineHeight 정돈 거리 ≤0.05일 때만 자동 변환. `design_intent_override` 화이트리스트. patch-only 재dispatch 권장(구현 가능성은 별도 검증 필요). |
| critic (claude) | architect(codex) 출력을 "미제출"로 오판(실제는 완성). 유효 지적: gemini 증거 라인 인용 0, 0.1 반올림이 risk 케이스 미대응, `.project-type` SoT가 HTML 주석보다 견고, 재dispatch patch-only 구현 가능성 미검증, 충돌5 strict profile이 "완벽 준수" 목표와 모순. |

## 수렴 포인트 (자동 합의)
1. **세 레이어 병행 + 우선순위 확정**: ①`validate-semantic.py` 검사 확장 → ②`figma-section-spec.py` 전처리 → ③`post-impl-verify.py` 재분류. 이유: 검증기가 기준선을 잡아야 전처리/재dispatch가 의미를 가진다 (codex + risk 일치).
2. **lineHeight 정돈 임계치 = 0.05 (step) + 0.03 (tolerance)**: codex 알고리즘과 risk 정량 가드레일이 일치. gemini의 0.1 단위는 케이스1(1.818)·케이스2(vertical centering)·케이스3(다국어 segment)에서 false-positive 위험이 크다 → 거부.
3. **정돈 비율 후보 목록**: `{1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0}` (risk) — 기본 step 0.05로 커버되지 않는 정돈 값(1.667, 1.45) 보존.
4. **프로젝트 타입 SoT**: `.project-type` 단일 파일 (프로젝트 루트). 모든 도구(figma-section-spec, validate-semantic, post-impl-verify, impl-request 생성기)가 이 파일을 읽는다. HTML 주석/spec 헤더/brief 헤더는 보조 앵커로 동기화.
5. **brief 계층화**: L1 인라인 short brief ≤800 토큰 (금지 패턴 5개 + Figma→CSS 변환표 6행 + 검증 명령어 1줄 + "원본 충실도 < 컨벤션" 명문화), L2 외부 규칙 파일 경로만(`D:/dev-base/rules/common.md` 등), L3 runtime validation.
6. **재dispatch 정책**: CRITICAL/MAJOR + retryable MINOR = 자동 재dispatch 1회. advisory MINOR = PM 리포트만. iteration cap hard 2회(초기+재 1). **단 patch-only 구현 가능성은 별도 REQ로 분리 검증**(현 시점 가능성 미검증 → 1차는 전체 재생성 + 위반 라인 첨부 방식).
7. **retryable MINOR = `no_hex8_literal`, `line_height_tidy_ratio`, `empty_media_block`, `landing_unit_mixed_scale`** (codex). advisory MINOR = `box_sizing_redundant` 등 컨벤션 위반(기능 영향 0).
8. **figma-section-spec 삽입점**: `main()`의 payload 생성 직후 `preprocess_payload(payload)` (codex). spec.json에 `original_value`/`normalized_value`/`normalization_reason` 3필드 병기(risk) → 검증기는 둘 중 하나만 PASS여도 OK.
9. **`design_intent_override` 거버넌스**: 에이전트 자동 채움 금지. PM이 spec.json 수정 시에만 기입 + override 사유 필수. 과사용 방지 메트릭: 세션당 override ≤3건 초과 시 경고.
10. **box-sizing 처리 책임**: reset.css 전역 `*{box-sizing:border-box}`로 1회 해결 + validator MINOR `box_sizing_redundant` 체크로 재발 방지.

## 미해결/유보 (Round 1 불필요, 후속 REQ에서 처리)
- **patch-only 재dispatch 구현 가능성**: Gemini/Codex CLI partial-edit 지원 여부 실측 필요. 1차 구현은 전체 재생성 유지.
- **검증기 false-positive 측정 방법론**: risk가 수치 한계선만 제시. 측정 스크립트(과거 REQ들에 runner를 돌려 집계)는 별도 REQ.
- **기존 2개 결과물(에이스디펜스/목포플레이파크) 재작업**: 사용자 선택에 따라 파이프라인 완성 후 진행. 현 plan 범위 외(이미 Step 2에서 "파이프라인 근본 개선" 선택됨).

## 공통 미해결 → 추가 합의 (critic이 지적한 공백 보강)
- **hex8 → rgba 자동 변환 코드 위치**: ①`figma-section-spec.py` 전처리에서 spec.json 기록 시 `rgba(r,g,b,a.aaa)`로 정규화, ②`validate-semantic.py`에서 HTML/CSS 상의 hex8 리터럴을 `no_hex8_literal` MAJOR로 검출. **2중 방어**.
- **빈 미디어쿼리 검출**: `validate-semantic.py` custom 체크 `empty_media_block` — `@media` 블록 body가 공백/주석만일 때 MAJOR. `@media print` 예외. 정규식이 아닌 AST parse(기존 `_extract_media_blocks` 활용, codex 제안).
- **단위체계 혼재 (`html{font-size:clamp(14px,1.2vw,16px)}` 등)**: `landing_unit_mixed_scale` 규칙 (profile=landing)에서 `html/body font-size`에 `clamp|vw|rem|calc` 금지. profile=basic에서는 허용.
- **critic 오판 정정**: architect(codex) 응답은 제대로 제출됨 확인. Round 1 재dispatch 불필요.

## 수렴 판정: CONVERGED (Round 0 종결)
- 10개 합의 포인트 중 불일치 0건, 보강 완료.
- 유보 3건은 본 plan 범위 외 후속 REQ로 분리.
- Step 5(consensus.md) 작성으로 이동.

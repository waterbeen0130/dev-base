# PLN-007 — Figma→퍼블리싱 파이프라인 규칙 완벽 준수 체계 구축

## 개요
Figma→HTML/CSS 자동 퍼블리싱 파이프라인이 `rules/common.md`, `basic.md`, `landing.md`를 100% 준수하도록 검증기·전처리기·브리프·프로젝트 타입 SoT를 3-Layer로 강화한다. 증거는 두 프로젝트(에이스디펜스/목포플레이파크)의 실측 위반 6종이다. 상세 합의는 `.gran-maestro/discussion/DSC-002/consensus.md` 참조.

## Intent (JTBD)
- **When I**: Figma 시안을 basic/landing 퍼블리싱 프로젝트로 자동 추출할 때
- **I want to**: 결과물이 프로젝트 CSS 규칙(common/basic/landing)을 수작업 없이 완벽 준수하도록 만들고 싶다
- **So I can**: 에이전트 결과물을 즉시 납품 가능하게 하고 PM의 수동 교정 루프를 제거할 수 있다

## 제약사항
- **Out-of-scope**: 기존 2개 결과물(에이스디펜스/목포플레이파크) 재작업은 파이프라인 완성 후 별도 plan으로 진행
- **기술**: Python 3, 기존 `tools/*.py` 구조 유지, Gemini/Codex CLI dispatch 패턴 유지
- **비즈니스**: 브리프 토큰 ≤ 8000, 인라인 규칙 ≤ 800, 본문 ≤ 1500

## 우선순위 (MoSCoW)
- **Must**: validate-semantic 6개 신규 규칙, figma-section-spec `preprocess_payload`, post-impl-verify exit code 재정의, `.project-type` SoT, impl-request.md L1 brief 재작성
- **Should**: init-project.py `.project-type` 자동 생성, MINOR retryable/advisory 분리, `design_intent_override` 거버넌스
- **Could**: false-positive 측정 runner, 기존 REQ 전수 스캔 리포트
- **Won't (this time)**: patch-only 재dispatch 구현, 기존 2개 결과물 재작업

## 의존성
- 선행 필요: 없음
- 연관: PLN-004(Figma 워크플로우), PLN-005(REQ-012~015 검증 후처리 계보)

## 분리 실행 (REQ 분리)

| REQ 후보 | 책임 | 레이어 | 블로커 |
|---|---|---|---|
| REQ-A | `validate-semantic.py` 신규 6규칙 (hex8/line-height 정돈/font-family 중복/빈 미디어쿼리/box-sizing 중복/landing 단위 혼재) | Layer A | — |
| REQ-B | `figma-section-spec.py` `preprocess_payload` + lineHeight 정돈·hex8 변환·hints 주입 | Layer B | REQ-A |
| REQ-C | `post-impl-verify.py` exit code 재정의 + MINOR retryable/advisory 분리 + 재dispatch 트리거 | Layer C | REQ-A, REQ-B |
| REQ-D | `rules/templates/publishing/impl-request.md` L1 short brief 재작성 (≤800토큰, Figma→CSS 변환표 6행, CRITICAL 선언) | 브리프 | REQ-B |
| REQ-E | `tools/init-project.py` `.project-type` 자동 생성 + backfill 스크립트 | SoT | — (병렬 가능) |

## 인수 기준 초안

이 plan의 구현이 완료됐다는 것은:
- [MUST] [TIER-A] `validate-semantic.py`가 `no_hex8_literal`, `line_height_tidy_ratio`, `font_family_redundant`, `empty_media_block`, `box_sizing_redundant`, `landing_unit_mixed_scale` 6개 규칙을 검출하고, `--profile landing|basic` flag에 따라 분기 동작한다
- [MUST] [TIER-A] `figma-section-spec.py`가 `main()` payload 생성 직후 `preprocess_payload(payload)`를 호출하고, spec.json 각 text 노드에 `lineHeightRatio`(정돈) + `lineHeightRatioRaw`(원본)가 병기된다 (정돈 알고리즘: step 0.05, tolerance 0.03, 후보 목록 `{1.0,1.1,1.2,1.25,1.3,1.4,1.45,1.5,1.6,1.667,1.75,1.8,2.0}`)
- [MUST] [TIER-A] spec.json `fills[].color`의 8자리 hex가 `rgba(r,g,b,a.aaa)` + `original_value` + `normalization_reason` 3필드로 정규화된다
- [MUST] [TIER-A] `post-impl-verify.py` exit code가 재정의되어 retryable-MINOR(`no_hex8_literal`/`line_height_tidy_ratio`/`empty_media_block`/`landing_unit_mixed_scale`) 발견 시 exit 1 + 자동 재dispatch 1회, advisory-MINOR만 있으면 exit 2를 반환한다
- [MUST] [TIER-B] 프로젝트 루트 `.project-type` 파일이 `basic` 또는 `landing` 값을 담고, 모든 도구가 이 파일을 읽어 profile 자동 결정(flag 미지정 시)한다
- [MUST] [TIER-B] `rules/templates/publishing/impl-request.md`에 L1 short brief(≤ 800 토큰)가 금지 패턴 5개 + Figma→CSS 변환표 6행 + 검증 명령어 1줄 + "원본 픽셀 충실도보다 CSS 컨벤션 준수가 최우선" 선언을 포함한다
- [MUST] [TIER-A] `tools/init-project.py --type {basic|landing}` 실행 시 `.project-type` 파일이 자동 생성된다
- [SHOULD] [TIER-B] `design_intent_override` 세션당 3건 초과 시 post-impl-verify가 경고를 출력한다
- [SHOULD] [TIER-A] 두 기존 결과물(에이스디펜스/목포플레이파크)에 새 파이프라인을 dry-run으로 돌렸을 때 목포 hex8 1건·비정돈 line-height 4건·빈 미디어쿼리 3건·font-family 중복 ≥10건이 모두 MAJOR로 검출된다 (회귀 테스트)
- [SHOULD] [IMPACT] [TIER-A] 기존 `figma-section-spec.py` 호출 경로(PLN-005 REQ-012~015 산출물)가 여전히 정상 동작하고 spec.md 표 형식 호환성이 유지된다
- [SHOULD] [IMPACT] [TIER-B] 기존 `post-impl-verify.py` exit code 0/1/2 사용처(CLAUDE.md §PM 검증 후처리)가 재정의 후에도 동일한 PM 액션 의미를 유지한다

## 범위 예산 (Appetite)
- 5개 REQ × 평균 1~2 task = 총 8~12 task
- 단일 배포(REQ-A)만으로도 기존 결과물 위반 즉시 식별 가능

## 제외 범위 (No-go Scope)
- patch-only 재dispatch 구현 (CLI partial-edit 지원 실측이 선행)
- 기존 2개 결과물 재작업
- validator false-positive 측정 runner (후속 plan)

## 리스크 레지스터
| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| 정돈 비율 반올림이 디자이너 의도 훼손 | 중 | 상 | step 0.05 + tolerance 0.03 + `design_intent_override` 화이트리스트, spec.json에 `original/normalized/reason` 3필드 병기 |
| 검증기 false-positive로 재dispatch 루프 마비 | 중 | 상 | ERROR FP ≤ 2% 가드, MINOR-only 재시도 0회, iteration cap hard 2회 |
| 브리프 비대화로 규칙 섹션이 컨텍스트 끝에 밀려 무시됨 | 하 | 중 | L1 inline ≤ 800 토큰 강제, L2는 경로 참조만, 금지 패턴 상단 CRITICAL 배치 |
| `post-impl-verify` exit code 변경이 기존 CLAUDE.md PM 액션 의미와 충돌 | 중 | 중 | PAC-11로 커버, 재정의 문서를 CLAUDE.md §PM 검증 후처리에 동시 업데이트 |
| `figma-section-spec.py` 변경이 PLN-005 산출물 regression | 하 | 상 | PAC-10 회귀 테스트 + `extracted/*` 샘플에 `preprocess_payload` dry-run |
| `.project-type` 파일 누락/오타로 profile 오판정 | 하 | 중 | 값 검증(`basic|landing`만 허용), 미존재 시 명시적 에러 + impl-request.md 생성 중단 |

## 테스트 전략
- 적용(커버리지 미설정): 단위 테스트 불필요. 실 파이프라인 dry-run 회귀 테스트를 PAC-9/10/11에 귀속.

## Loop 종료 조건
- 기본값: AC 통과 + max_iterations.

## 연관 컨텍스트

> 상세 내용은 아래 파일을 직접 참조하세요. 내용을 이 파일에 복사하지 않습니다.

| 유형 | ID | 파일 경로 |
|------|----|-----------|
| 논의 합의문 | DSC-002 | `.gran-maestro/discussion/DSC-002/consensus.md` |
| 증거 결과물 A | — | `/mnt/d/위링/2026-04-15 에이스디펜스/html/css/common.css` |
| 증거 결과물 B | — | `/mnt/d/위링/2026-04-15 목포플레이파크/html/css/common.css` |

## Confidence Score Matrix

| 축 | 점수 |
|----|------|
| Clarity | 0.85 |
| Feasibility | 0.80 |
| Decoupling | 0.75 |
| Completeness | 0.85 |

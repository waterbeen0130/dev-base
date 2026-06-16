# Objective — Figma→퍼블리싱 검증체계/룰 보강 (재발방지)

## 진행 상태 요약

- 상태: active (objective-version 1)
- 핵심 문제: "규칙을 철저히 지켜 추출하라 + 검증까지 끝내고 달라"고 지시했으나, 결과물은 Figma 노드명 직역(`main_f0`~`main_f175` 등 294개 클래스) + `<img>` 313개 래퍼 누락 등 규칙 위반 투성이였고, 현재 검증 툴은 ① 실태의 1순위 위반(Figma 노드명 클래스화)을 잡는 규칙이 아예 없고 ② 검증이 "실제로 실행됐는지"를 강제하지 못해 검증 없는 raw 결과물이 그대로 전달됨.
- 이번 프로젝트 범위: **검증체계 + 룰 보강(재발방지)에만 집중**. 특정 제천 결과물 재작업/참조는 범위에서 완전 제외(다른 에이전트 작업 중).

## JTBD 레이어

- **When I (상황)**: Figma 디자인을 OMX 등으로 코드 추출시키고 "규칙 준수 + 검증 완료"를 지시했을 때,
- **I want to (하고 싶은 것)**: 추출 완료 후 결과물이 dev-base 규칙(CLAUDE.md/rules) 전체에 대해 자동으로 철저히 검증되고, 핵심 위반(특히 Figma 노드명 직역)은 반드시 차단되며, 검증이 실제로 실행·통과됐다는 증거 없이는 완료/전달되지 못하게 하고 싶다.
- **So I can (얻는 가치)**: 검증 없는 raw 직역 결과물이 "검증 끝났다"는 보고와 함께 전달되는 일이 재발하지 않고, 결과물 품질을 기계적으로 신뢰할 수 있다.
- **성공 지표**:
  - 현재 미인코딩 규칙 21개 중 기계 검증 가능(A/B급) 항목의 검증 커버리지가 측정 가능하게 증가.
  - Figma 노드명 직역·공통영역 스코핑 위반 등 핵심 CRITICAL 유형이 회귀 픽스처에서 100% 검출.
  - 모든 신규/보강 규칙이 클린 픽스처에서 false positive 0건.
  - 검증 미실행 상태에서는 완료/전달 게이트가 차단됨(증거 기반).
- **완료 정의**: 아래 프로젝트 DoD 전 항목이 done.

## 프로젝트 완료 기준 (DoD)

- [ ] **DOD-001**: Figma 노드명 직역 클래스 차단
  - Direction: 검출률을 높인다
  - Measure: 노드명 패턴 클래스(`main_f0`, `main_v53`, `header_b`, `sec_1`, `_v2` 등)를 포함한 HTML/CSS
  - Object: validate-semantic / pm-verify
  - Context: 코드 추출 결과 검증 시
  - Target: 해당 패턴이 CRITICAL 위반으로 보고되어 차단된다 (현재는 미검출)
<!-- dod:DOD-001 status:done priority:must domain:rule-encoding-gaps -->

- [ ] **DOD-002**: 공통영역 스코핑 / 전역 클래스 선언 규칙 검출
  - Direction: 검출 범위를 넓힌다
  - Measure: 공통영역 자식 단독선언(`.logo{}`, `.gnb{}`)과 전역 클래스에 부모 붙이기(`body .header{}`, `html .cont{}`)
  - Object: validate-semantic
  - Context: HTML/CSS 검증 시
  - Target: 두 위반 유형 모두 검출되어 보고된다
<!-- dod:DOD-002 status:done priority:must domain:rule-encoding-gaps -->

- [ ] **DOD-003**: 텍스트 부분 색상(character_segments) 누락 검출
  - Direction: 검출한다
  - Measure: spec.json `has_mixed_styles:true`인데 HTML이 단일 스타일로 출력한 경우
  - Object: figma-validate / pm-verify
  - Context: spec↔HTML 대조 검증 시
  - Target: character_segments 무시가 위반으로 보고된다
<!-- dod:DOD-003 status:done priority:should domain:rule-encoding-gaps -->

- [ ] **DOD-004**: 폐기 도구/자동 생성·수리 스크립트 사용 검출
  - Direction: 검출한다
  - Measure: `generate.py`/`json-to-html.py`/`repair-from-violations.py`/`--converge` 등 폐기·금지 도구 참조/호출
  - Object: 검증 게이트(grep 기반)
  - Context: 산출물/작업 트리 검증 시
  - Target: 금지 도구 사용이 위반으로 보고된다
<!-- dod:DOD-004 status:done priority:should domain:rule-encoding-gaps -->

- [ ] **DOD-005**: 룰 커버리지 갭 측정 및 축소
  - Direction: 줄인다
  - Measure: CLAUDE.md/rules에 명시됐으나 어떤 검증 도구에도 인코딩 안 된 규칙 수(현 21개)
  - Object: rules.yaml / validate-semantic 커버리지
  - Context: 규칙↔검증 매핑 리포트 기준
  - Target: A/B급(기계 검증 가능) 미인코딩 항목이 문서화된 갭 목록 대비 측정 가능하게 감소하고, 미인코딩 잔여 항목과 사유가 리포트로 남는다
<!-- dod:DOD-005 status:done priority:must domain:rule-encoding-gaps -->

- [ ] **DOD-006**: 검증 실행 증거 기반 완료 게이트
  - Direction: 강제한다
  - Measure: pm-verify가 실제 실행되어 통과(exit 0 + 리포트)했다는 증거
  - Object: 완료/전달(accept 또는 완료 보고) 게이트
  - Context: 코드 추출 완료 후
  - Target: 증거가 없으면 완료/전달이 기계적으로 차단된다
<!-- dod:DOD-006 status:done priority:must domain:verification-execution-gate -->

- [ ] **DOD-007**: 검증 우회/자가보고 탐지
  - Direction: 탐지·차단한다
  - Measure: 검증을 건너뛰거나 실행 흔적 없이 "통과" 자가보고만 한 경우
  - Object: 완료 게이트
  - Context: 완료 보고 시점
  - Target: 실제 실행 흔적 부재가 탐지되어 차단된다
<!-- dod:DOD-007 status:done priority:should domain:verification-execution-gate -->

- [ ] **DOD-008**: 신뢰/노이즈 분류 재점검
  - Direction: 재분류한다
  - Measure: 현재 노이즈로 억제 중인 카테고리(layoutSizing/opacity/reset_duplicate/inner_wrapper_limit 등)
  - Object: pm-verify의 TRUSTED/NOISY 분류
  - Context: 검증 리포트 생성 시
  - Target: 각 항목이 "실제 위반을 가리는지" 판정·문서화되고, 잘못 억제된 항목은 신뢰 카테고리로 복귀한다
<!-- dod:DOD-008 status:done priority:should domain:trust-noise-reclassification -->

- [ ] **DOD-009**: 스크린샷-우선 2패스 변환 워크플로우 채택
  - Direction: 전환한다
  - Measure: 변환 워크플로우가 (Pass1) PNG만 보고 시맨틱 구조 구현 → (Pass2) spec.json 값 정밀 보정 순서로 정의되고, spec 노드 트리를 구조 입력으로 쓰지 않음
  - Object: 변환 워크플로우 문서(rules/INSTRUCTIONS.md) + 추출 진입점
  - Context: Figma→코드 변환 시
  - Target: 워크플로우가 2패스로 재작성되고, 이 방식으로 만든 샘플 산출물에서 Figma 노드명 직역·비시맨틱 구조 등 핵심 CRITICAL 유형이 미발생한다
<!-- dod:DOD-009 status:done priority:should domain:conversion-step-hardening -->

- [ ] **DOD-012**: 룰/워크플로우 단일 소스 통합 (AI-agnostic)
  - Direction: 통합한다
  - Measure: 모든 HTML/CSS 룰 + 변환 워크플로우 본문이 단일 파일(`rules/INSTRUCTIONS.md`)에만 존재하고, AI별 파일(CLAUDE.md/AGENTS.md/GEMINI.md)에는 룰 본문 중복이 없음
  - Object: 지시문서 구조
  - Context: PM(Claude/Codex/Gemini 무관)이 룰을 참조할 때
  - Target: 룰 본문 중복 0건, 각 AI 파일은 단일 소스를 가리키는 thin shim으로 축소된다
<!-- dod:DOD-012 status:done priority:must domain:ai-agnostic-instructions -->

- [ ] **DOD-013**: AI 무관 진입점 정비 (Gemini 포함)
  - Direction: 정비한다
  - Measure: Claude/Codex(OMX)/Gemini 3개 PM 진입점이 모두 동일 단일 소스(`rules/INSTRUCTIONS.md`)를 읽도록 구성되고, `GEMINI.md`가 신규 생성됨
  - Object: AI 진입점(CLAUDE.md/AGENTS.md/GEMINI.md)
  - Context: 어느 AI가 PM이 되든
  - Target: 3개 진입점 모두 단일 소스를 참조하고, 기존 common.md 등으로의 깨진 참조 경로가 없다
<!-- dod:DOD-013 status:done priority:should domain:ai-agnostic-instructions -->

- [ ] **DOD-010**: 회귀 테스트 픽스처 체계
  - Direction: 보장한다
  - Measure: 각 신규/보강 규칙에 대한 위반 픽스처 + 클린 픽스처 쌍
  - Object: 검증 회귀 테스트
  - Context: 검증 툴 변경 시
  - Target: 위반 픽스처는 잡고 클린 픽스처는 통과(false positive 0)함을 반복 실행으로 확인할 수 있다
<!-- dod:DOD-010 status:done priority:must domain:regression-fixtures -->

- [ ] **DOD-011**: 산출물 경계 인식
  - Direction: 규정·인식한다
  - Measure: 최종 산출물 경로 규정 + raw 추출 잔재(예: extracted/) 식별
  - Object: 검증 게이트
  - Context: 검증 대상 선정 시
  - Target: raw 추출 잔재가 최종 산출물로 오인·검증·전달되지 않도록 검증이 산출물 경계를 인식한다
<!-- dod:DOD-011 status:done priority:should domain:verification-execution-gate -->

## 설계 결정 (Architecture Decisions)

- **AD-001 (rule-encoding-gaps)**: Figma 노드명 클래스 탐지 규칙(`no_figma_nodeid_class`)을 신설한다. 페이지 prefix(`main_`, `greeting_` 등 사용자 지정)와 형태가 유사하므로, 노드명 패턴은 보수적으로 정의(`*_f{N}`, `*_v{N}`, `*_t{N}` 연속 인덱스, `header_b`/`footer_bk`/`sec_{N}`/`_v{N}` 등 디자이너 식별자)하고 픽스처로 경계를 검증한다. 상세 → `details/rule-encoding-gaps.md`.
- **AD-002 (verification-execution-gate)**: 완료/전달 차단은 "검증이 실제 실행되어 통과했다는 증거(exit 0 + 리포트 산출물)"를 기준으로 한다. 자가보고가 아닌 실행 흔적을 신뢰 소스로 삼는다. 상세 → `details/verification-execution-gate.md`.
- **AD-003 (trust-noise-reclassification)**: 노이즈 억제는 false positive 감소가 목적이지 위반 은폐가 아니다. 각 억제 항목을 "정당한 억제 / 잘못된 억제"로 판정하고 후자만 복귀시킨다. 상세 → `details/trust-noise-reclassification.md`.
- **AD-004 (regression-fixtures)**: 모든 규칙 변경은 위반/클린 픽스처 쌍 + 회귀 실행을 동반한다. 픽스처는 제천 결과물을 참조하지 않고 새로 작성한다. 상세 → `details/regression-fixtures.md`.
- **AD-005 (conversion-step-hardening)**: 검증은 사후 게이트이고, 추출 단계 개선은 사전 예방이다. 둘을 병행한다. 상세 → `details/conversion-step-hardening.md`.
- **AD-007 (conversion-step-hardening)**: 변환은 **스크린샷-우선 2패스**로 한다. 구조/시맨틱의 권위 출처는 시각(PNG)이고, 정확한 값(text/hex/font/px)의 권위 출처는 spec.json이다. spec 노드 트리를 구조 생성 입력으로 쓰면 노드명 직역(transliteration)이 발생하므로, spec은 Pass2의 "값 오라클"로만 사용한다. 상세 → `details/conversion-step-hardening.md`.
- **AD-008 (ai-agnostic-instructions)**: PM은 Claude/Codex/Gemini 중 무엇이든 될 수 있으므로 룰/워크플로우를 AI별로 복제하지 않는다. 단일 소스 `rules/INSTRUCTIONS.md`(기존 common.md 흡수)에 본문을 두고, 각 AI 파일은 "단일 소스 필독 + 해당 AI 고유 실행법"만 담는 thin shim으로 둔다. 상세 → `details/ai-agnostic-instructions.md`.

## 제약사항 (Out-of-scope / 기술 / 비즈니스)

- **Out-of-scope**: 특정 제천한방힐링아카데미 결과물의 재작업/수정/참조(다른 에이전트 담당). LLM 시각 비교(Playwright PNG 대조)의 완전 자동화. 의도 기반 규칙(거짓보고 금지, 요청외 개선 금지 등) C급 항목의 완전 자동화.
- **기술 제약**: 기존 `pm-verify.py` / `validate-semantic.py` / `accept-preflight-verify.py` / `pm-verify-accept-gate.sh` 인터페이스를 하위 호환 보존. 규칙은 `rules/rules.yaml` + `rules/validation_schema.json` 단일 소스를 기준으로 추가. 폐기 자동 생성/수리 스크립트(generate.py, json-to-html.py, repair-from-violations.py, `--converge` 등) 부활 금지.
- **비즈니스/스타일 제약**: 응답 한국어, 코드 주석 영어. false positive 최소화 설계 철학(신뢰/노이즈 분리) 유지.

## 우선순위 (MoSCoW)

- **Must**: DOD-001(노드명 직역 차단), DOD-002(스코핑/전역 클래스), DOD-005(커버리지 갭 축소), DOD-006(검증 실행 게이트), DOD-010(회귀 픽스처), DOD-012(룰/워크플로우 단일 소스 통합).
- **Should**: DOD-003(character_segments), DOD-004(폐기 도구), DOD-007(우회 탐지), DOD-008(신뢰/노이즈 재점검), DOD-009(스크린샷-우선 2패스 워크플로우), DOD-011(산출물 경계), DOD-013(AI 무관 진입점 정비).
- **Could**: (없음)
- **Won't (this time)**: 제천 결과물 재작업, 시각 비교 자동화, 의도 기반 규칙 완전 자동화.

## 프로젝트 NFR

- **성능**: 검증 1회 실행 시간이 규칙 추가 후에도 단일 페이지 기준 수 초 내로 유지(기존 대비 과도한 저하 금지).
- **호환성**: 기존 검증 CLI 인자/출력 포맷 하위 호환. accept-gate가 의존하는 `[CRITICAL]` 출력 규약 보존.
- **오류 처리**: 신규 규칙은 클린 픽스처 통과(false positive 0) 전에는 CRITICAL 게이트로 승격하지 않는다(경고 단계 우선). 검증 대상 파일 부재 시 SKIP(graceful) 동작 유지.
- **보안**: 해당 없음(로컬 정적 검증 도구).

## 리스크 레지스터

- **R1 (가능성 中 / 영향 高)**: 신규 규칙 false positive로 정상 코드 차단 → 완화: 클린 픽스처 회귀 테스트 필수, 신규 규칙 단계적 승격(MAJOR→CRITICAL).
- **R2 (가능성 高 / 영향 中)**: Figma 노드명 패턴이 사용자 지정 페이지 prefix와 충돌(오탐) → 완화: 노드명 패턴 보수적 정의 + 경계 픽스처(`main_intro` 통과 / `main_f12` 차단)로 검증.
- **R3 (가능성 中 / 영향 高)**: 검증 실행 강제 게이트가 워크플로우 외부(폴더 직접 전달) 경로를 못 막음 → 완화: 게이트 적용 지점·범위를 명시하고, 우회 가능 경로를 리스크로 문서화.
- **R4 (가능성 中 / 영향 中)**: rules.yaml ↔ validate-semantic 핸들러 동기화 누락 → 완화: 단일 소스 우선 + 픽스처가 양쪽을 동시 검증.

## 참조 레퍼런스

- `rules/rules.yaml`, `rules/validation_schema.json` — 현 규칙 인코딩 단일 소스(74/95 규칙 인코딩됨).
- `CLAUDE.md`, `rules/common.md`, `rules/landing.md`, `rules/basic.md` — 규칙 원문.
- `tools/pm-verify.py`, `tools/validate-semantic.py`, `tools/accept-preflight-verify.py`, `tools/figma-section-spec.py`, `.claude/hooks/pm-verify-accept-gate.sh` — 검증 체인 구현.
- 조사 산출물(Sprint 0 컨텍스트): 검증 툴 검사 항목표 / 결과물 위반 감사 / 규칙↔검증 커버리지 매핑(95개 규칙, 78% 인코딩, 21개 갭) — `details/` 각 도메인 문서에 핵심 반영됨.

## 변경 이력

- v1 (2026-06-15): 초기 objective 생성. JTBD + 11개 DoD + 5개 도메인(rule-encoding-gaps / verification-execution-gate / trust-noise-reclassification / conversion-step-hardening / regression-fixtures). 스냅샷: `history/v1.md`.
- v2 (2026-06-15): 사용자 스티어링 반영(Level C). ① DOD-009를 "스크린샷-우선 2패스 변환 워크플로우 채택"으로 재정의(could→should). ② 신규 도메인 `ai-agnostic-instructions` + DOD-012(룰/워크플로우 단일 소스 `rules/INSTRUCTIONS.md` 통합, must)·DOD-013(Claude/Codex/Gemini 진입점 정비, GEMINI.md 신규). ③ AD-007(스크린샷-우선 2패스)·AD-008(AI-agnostic 단일소스) 추가. DoD 11→13개, 도메인 5→6개.

## 상세 문서 (Details)

- [rule-encoding-gaps](details/rule-encoding-gaps.md) — 미인코딩 규칙 21개와 신규/보강 규칙(특히 Figma 노드명 직역 차단) 명세.
- [verification-execution-gate](details/verification-execution-gate.md) — 검증 실행 증거 기반 완료/전달 게이트 + 산출물 경계 인식.
- [trust-noise-reclassification](details/trust-noise-reclassification.md) — 신뢰/노이즈 억제 카테고리 재분류 정책.
- [conversion-step-hardening](details/conversion-step-hardening.md) — 스크린샷-우선 2패스 변환 워크플로우(구조=시각, 값=spec).
- [ai-agnostic-instructions](details/ai-agnostic-instructions.md) — 룰/워크플로우 단일 소스(rules/INSTRUCTIONS.md) 통합 + AI 진입점 thin shim.
- [regression-fixtures](details/regression-fixtures.md) — 위반/클린 픽스처 회귀 테스트 체계.

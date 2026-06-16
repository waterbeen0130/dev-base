<!-- source-mapping: original=AGI-004/objective-qa-session sections=[조사:figma-section-spec, CLAUDE.md Step4 OMX, 사용자 스티어링:스크린샷-우선 2패스] -->
# conversion-step-hardening (스크린샷-우선 2패스 변환 워크플로우)

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-009

## 개요

기존 워크플로우(Step 4)는 OMX에게 **spec.json(Figma 노드 트리)을 1차 입력**으로 주어 코드를 추출시켰다. 그 결과 에이전트가 Figma 문서 구조를 그대로 베끼는 **구조 직역(transliteration)**이 발생했다 — `main_f0`~`main_f175` 294개 노드명 클래스, img 래퍼 없음, ul/li 없음. 근본 원인은 **Figma 노드 트리는 시맨틱 HTML 구조가 아니라 디자이너의 레이어 정리 산물**인데, 그것을 구조 생성 입력으로 줬기 때문이다.

해결: **스크린샷-우선 2패스**. 구조/시맨틱은 시각(PNG)에서, 정확한 값은 spec.json에서 — 각 출처를 권위 있는 것에만 쓴다.

## 설계 결정

### AD-007: 스크린샷-우선 2패스 (구조=시각, 값=spec)
- **결정**: 변환을 2패스로 분리한다. Pass1은 PNG만 보고 시맨틱 구조를 구현하고, Pass2는 spec.json으로 값만 정밀 보정한다. spec 노드 트리는 구조 생성 입력으로 쓰지 않는다.
- **근거**:
  - 시맨틱 구조(nav/ul/section/heading)는 **역할(role) 판단**이며, 이는 시각적 인지에서 자연 발생한다. 노드 트리엔 역할 정보가 없다.
  - 스크린샷에는 노드명이 없으므로 `main_f0`를 붙일 수가 없다(직역 원천 차단).
  - 정확한 값(text byte-exact·hex·font-weight·px)은 픽셀에서 신뢰성 있게 복원 불가 → spec.json이 권위.
  - 최종 합격 기준이 시각 일치(Playwright PNG ↔ Figma PNG)이므로, 시각을 처음부터 직접 최적화하는 것이 정확도에 유리.
- **대안 검토**: (a) 기존 spec-우선 + 룰 강제 — 룰을 적어도 노드 트리 구조 관성이 이김(실증됨). (b) 스크린샷-우선 2패스 — 채택.
- **영향 범위**: rules/INSTRUCTIONS.md 워크플로우 섹션, 추출 진입점 지시, pm-verify(Pass2 값 검증과 정렬).

## 상세 명세

### 변환 워크플로우 (재작성 대상)

| 단계 | 입력 | 출력 | 핵심 제약 |
|------|------|------|----------|
| **0. 추출** | Figma file/node | spec.json + figma-png + asset_manifest | `figma-section-spec.py --download-assets` (이미지 1:1). spec은 이후 "값 오라클"로만 |
| **1. 구조 (Pass1)** | **PNG만** | 시맨틱 HTML + 골격 CSS | spec 노드 트리 미열람. 역할 기반 마크업(header/nav/ul/li/section/heading), 클래스명은 INSTRUCTIONS.md 네이밍 규칙(공통영역 prefix 없음/페이지 prefix/부모 스코핑). 모든 img는 .img_area |
| **2. 값 보정 (Pass2)** | spec.json | 값이 정밀해진 HTML/CSS | text byte-exact(NBSP/\n/공백), hex, font 5필드, px, letter-spacing em, character_segments 분리. **구조는 변경 금지** |
| **3. 검증** | pm-verify | 통과/위반 + 실행 증거 | DOD-006 실행 증거 게이트. CRITICAL 0건이어야 완료 |
| **4. 시각 비교** | Playwright 1920 렌더 | PNG ↔ Figma PNG | 자연어 피드백 → Pass1/2 복귀 |

### 관찰 가능 판정 (DOD-009 Target)
- 워크플로우 문서가 위 2패스 순서로 재작성됨(grep 가능).
- 이 방식으로 만든 샘플 산출물에서 핵심 CRITICAL 유형(노드명 클래스, img 래퍼 누락, ul/li 누락) 미발생.

### 범위 경계 / 주의
- 텍스트·값을 **스크린샷에서 추측 금지** — 반드시 Pass2에서 spec byte-exact로 덮어쓰기(OCR 오류·NBSP 손실 방지).
- 스크린샷은 1개 해상도 → 반응형은 별도 처리.
- Pass2를 건너뛰면 값 어긋남 → pm-verify 게이트로 강제.
- 폐기 자동 생성 스크립트(generate.py 등) 부활 금지 — 추출은 AI 에이전트(OMX/Gemini/Claude) 경로로만.

## Q&A 보강 사항

- 사용자 제안: "스크린샷을 먼저 보고 그대로 구현 → Figma 값 정밀 비교 → 시맨틱 마크업 수정"이 정확도가 더 높다. → AD-007로 채택.
- 정확도 우위의 이유(합의): 구조와 값의 권위 출처가 다르며, 노드-트리-우선은 구조 직역을 유발하기 때문.
- 이 워크플로우는 특정 AI에 종속되지 않게 rules/INSTRUCTIONS.md에 기술한다([[ai-agnostic-instructions]] 연계).

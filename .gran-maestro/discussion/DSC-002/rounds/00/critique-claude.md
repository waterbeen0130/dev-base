# Critic 분석 — DSC-002 Round 0

## Architect(codex)
**치명적 결함: 의견 미제출**. 파일 655줄 전체가 도구 호출 trace + sed/rg 출력 raw dump이며, 4개 질문에 대한 **결론·제안·코드 스니펫이 0건**이다. 마지막 줄까지 컨텍스트 로딩만 반복하다 중단 — Codex가 reasoning effort high에서 탐색만 하고 답안을 쓰지 않은 전형적 실패 케이스.

- 체크포인트 1(증거 기반): trace 도중 `validate-semantic.py`를 실제 두 프로젝트에 돌려 "MINOR clamp_threshold 1건만 검출, 16개 custom 체크 skip"이라는 **유일하게 가치 있는 데이터**를 산출했지만, 이 사실에서 어떤 규칙을 추가할지 결론을 내지 않음.
- 누락: regex/AST/심각도/false-positive 억제 전략, lineHeight 반올림 알고리즘, post-impl-verify 재분류, 우선순위 — 전부 미응답.
- **반론 불가** — 의견이 없으므로 비판할 내용도 없음. **재dispatch 권고**.

## Frontend(gemini)
1500자 정도의 응답이 8번 줄에서 한 번 깨져 ("ADSC-002...") 출력 손상이 있다. 그래도 핵심 4개는 답함.

- **장점**: "원본 충실도 < 컨벤션" 우선순위 명문화, O/X 패턴, 3중 앵커(spec/brief/HTML 주석)는 실용적.
- **체크포인트 1**: **증거 라인 번호 0건**. 두 프로젝트 css/html을 직접 인용하지 않고 일반론에 머묾. shared-context의 위반 6종을 그대로 paraphrase.
- **체크포인트 3 미해결**: "line-height 1.1~1.8 허용, 0.1 단위 반올림"이라는 **단순 규칙은 risk가 지적한 케이스1(1.818 의도) / 케이스2(vertical centering) / 케이스3(다국어 segment)을 전부 catch하지 못함**. 0.1 단위는 너무 거칠다 (risk는 0.05).
- **누락**: 검증기/전처리기 책임 경계 미언급(역할상 frontend라 그렇다 치더라도), 재dispatch 정책 무응답, 토큰 비용 고려 없음.
- 제안한 "HTML 첫 줄 주석 `<!-- [Project Type: landing] -->`"은 risk의 `.project-type` 단일 파일 SoT보다 약함 — HTML이 여러 페이지면 동기화 실패 위험.

## Risk(claude)
가장 구조화된 응답. 4개 트레이드오프 정량 한계선, 엣지 케이스 3종, 3-Layer 주입, 5종 충돌 시나리오 모두 커버.

- **체크포인트 1**: 케이스1·2에서 목포플레이파크 line 28/42를 정확 인용 — **유일하게 증거 기반**.
- **약점 A**: 한계선 수치(false-positive ≤2%, 토큰 ≤1500 등)가 **경험적 근거 없이 제시**됨. 측정 방법론 누락.
- **약점 B**: `design_intent_override` 화이트리스트는 **누가 채우는가?** PM이 매번 수동 마킹하면 워크플로우 부담; 에이전트가 채우면 우회 도구로 악용. 거버넌스 미정의.
- **약점 C**: "patch-only 재dispatch"는 이상적이지만 Gemini CLI가 partial-edit 모드를 지원하는지 검증 안 됨 — 현재 dispatch 패턴은 전체 파일 재생성. **구현 가능성 미확인**.
- **약점 D**: Layer3 self-check `grep -E '#[0-9a-f]{8}'`는 6자리 hex(`#ffffff`)도 매치하므로 false-positive. 정규식 결함.
- **약점 E**: 충돌5의 `--profile strict` 분리는 신규 REQ만 적용 → "완벽 준수" 목표(공유 컨텍스트 §주제)와 충돌. 기존 프로젝트는 영원히 풀리지 않음.

## 종합 발산점
1. **Codex 부재 → architect 영역(검증기 구현 디테일/우선순위) 공백**. Round 1 이전에 재dispatch 또는 PM 직접 보강 필수.
2. **lineHeight 반올림 임계치 충돌**: gemini 0.1 vs risk 0.05 — risk 근거가 더 강함(케이스2 픽셀 분석).
3. **프로젝트 타입 SoT**: gemini 3중 앵커 vs risk 단일 `.project-type` 파일 — **risk 우세**(동기화 실패 위험 회피).
4. **재dispatch 정책**: risk만 답변(MINOR 0회, 1회 한정). 정량 근거는 약하나 유일한 답.
5. **공통 미해결**: 두 응답 모두 (a) hex8 → rgba 자동 변환 코드 위치, (b) 빈 미디어쿼리 검출 정규식, (c) box-sizing 반복 제거 책임 레이어, (d) 단위체계 혼재(`clamp(14px,1.2vw,16px)`)의 처리 주체를 명시하지 않음.
6. **공통 누락**: 두 응답 모두 figma-section-spec.py의 구체적 diff 위치(`normalize_text_node` 함수 등)를 짚지 못함. Round 1에서 architect 재dispatch 필수.

**Round 1 의제 후보**: (1) Codex 재dispatch + 구체 diff 요구, (2) lineHeight 임계치 0.05 vs 0.1 결착, (3) `design_intent_override` 거버넌스 정의, (4) patch-only 재dispatch 구현 가능성 검증.

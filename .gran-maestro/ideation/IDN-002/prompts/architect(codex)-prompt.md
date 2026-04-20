[MST skill=ideation step=2/4 return_to=null]

# Architect 관점 의견 요청 — IDN-002

## 공유 컨텍스트 (필수 Read)
아래 파일을 먼저 Read 하세요:
- /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/context.md
- /mnt/d/dev-base/CLAUDE.md
- /mnt/d/dev-base/rules/common.md (처음 200줄)
- /mnt/d/dev-base/tools/figma-section-spec.py (전체 구조 파악 목적, 필요 시 grep으로 주요 함수만)
- /mnt/d/dev-base/tools/post-impl-verify.py

## 당신의 역할
파이프라인 **전체 아키텍처** 관점. 데이터 흐름, 단계 분리, 책임 경계, 재현성(determinism), 확장성, 테스트 가능성 관점에서 분석.

## 질문 (각 항목에 구체적 근거/파일 라인 인용)
1. 현재 파이프라인(figma-extract → section-spec → 외주 AI → figma-validate + validate-semantic → post-impl-verify → repair-from-violations)의 **구조적 결함 Top 5**는 무엇인가? 각 결함이 fidelity를 해치는 메커니즘 서술.
2. "Figma와 완전 동일한 추출물"을 보장하려면 파이프라인 어느 단계에 무엇이 추가되어야 하는가? (예: IR(intermediate representation) 도입, 이미지/벡터 asset 파이프라인, 렌더 diff 루프 등)
3. 현재 tools/ 내 스크립트들의 **책임 중복/경계 모호성**을 구체적으로 지적하고 재편 제안.
4. `.gran-maestro/` 산출물과 `extracted/`, `rules/`의 관계에서 **단일 진실 공급원(SSOT)** 위반 지점이 있는가?

## 출력 요구사항
- 파일로 저장: /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-architect(codex).md
- 2000자 이내, 한국어, 불릿 위주, 각 주장에 파일경로:라인 또는 구체 근거 첨부
- 마지막에 "## Top 3 우선순위 개선 액션" 3줄 정리
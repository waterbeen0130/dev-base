# Architect(validator/tooling) 관점 의견 요청 — DSC-002 Round 0

## 공유 컨텍스트
/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/rounds/00/shared-context.md 파일을 Read하세요.

## 추가 참조 파일 (반드시 Read)
- /mnt/d/dev-base/tools/validate-semantic.py — 현재 규칙 검증기
- /mnt/d/dev-base/tools/figma-section-spec.py — Figma 정규화 스펙 생성기
- /mnt/d/dev-base/tools/post-impl-verify.py — 후처리 검증/분류
- /mnt/d/dev-base/tools/figma-validate.py — Figma 충실도 검증
- /mnt/d/dev-base/rules/common.md — 공통 CSS/HTML 규칙
- /mnt/d/dev-base/rules/basic.md
- /mnt/d/dev-base/rules/landing.md
- /mnt/d/위링/2026-04-15 에이스디펜스/html/css/common.css 와 page/index.html
- /mnt/d/위링/2026-04-15 목포플레이파크/html/css/common.css 와 page/index.html

## 당신의 역할
validator/tooling architect 관점에서 분석합니다. 실제 스크립트 코드와 위반 결과물을 모두 읽고 구체적 구현 제안을 내십시오.

## 질문
1. `validate-semantic.py`에 어떤 검사 규칙을 추가해야 공유 컨텍스트에 나열된 6가지 위반을 모두 catch하는가? 각 규칙에 대해: 이름, 구현 방법(정규식/AST/단순 치환), 심각도(CRITICAL/MAJOR/MINOR), false-positive 억제 전략.
2. `figma-section-spec.py`의 어느 지점에 전처리 단계를 넣으면 lineHeightPx→정돈 비율, hex8→rgba, box-sizing 중복 제거 힌트가 spec.json에 자동 반영되는가? 정돈 비율 알고리즘 구체안 (반올림 단위, 허용 임계치).
3. `post-impl-verify.py`의 분류를 어떻게 재정의해야 MINOR 위반도 적절히 재dispatch 되는가? 재시도 루프 비용과 품질의 균형을 맞추는 구체적 기준(exit code / iteration cap)은?
4. 세 스크립트 변경의 의존성/구현 우선순위는? 한 가지만 먼저 배포한다면 어느 것이 가장 효과가 큰가?

## 출력 요구사항
- /mnt/d/dev-base/.gran-maestro/discussion/DSC-002/rounds/00/architect(codex).md 에 저장
- 2000자 이내
- 구체적 코드 스니펫 또는 diff-level 변경 제안 포함
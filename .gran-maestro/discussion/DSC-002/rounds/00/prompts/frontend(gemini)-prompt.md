# Frontend-rules 관점 의견 요청 — DSC-002 Round 0

## 공유 컨텍스트
/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/rounds/00/shared-context.md 파일을 Read하세요.

## 추가 참조 파일 (반드시 Read)
- /mnt/d/dev-base/rules/common.md
- /mnt/d/dev-base/rules/basic.md
- /mnt/d/dev-base/rules/landing.md
- /mnt/d/dev-base/rules/gemini.md
- /mnt/d/dev-base/rules/templates/publishing/impl-request.md (존재 시)
- /mnt/d/위링/2026-04-15 에이스디펜스/html/css/common.css
- /mnt/d/위링/2026-04-15 목포플레이파크/html/css/common.css

## 당신의 역할
CSS 규칙 전문가 겸 외주 브리프 설계자 관점. 실제 위반 결과물이 나온 이유를 에이전트 행동 관점에서 진단하고, 브리프를 어떻게 재작성하면 다시는 같은 위반이 나지 않을지 구체 제안하십시오.

## 질문
1. 두 결과물의 6가지 위반이 발생한 에이전트 측 인지 실패 원인은 무엇인가? (규칙 인식 실패 / Figma 충실도 우선 / 단위체계 혼동 등 각각 어떤 위반에 해당하는지 매핑)
2. `rules/templates/publishing/impl-request.md`를 어떻게 재작성해야 브리프 비대화 없이 위반을 원천 차단할 수 있는가? 구체적 섹션 구조, 금지 패턴 인라인 예시 개수, Figma 속성→CSS 변환표 포함 여부와 형식.
3. Figma 원본 충실도와 규칙 준수가 충돌할 때 우선순위 규칙을 어떻게 브리프에 명시해야 에이전트가 망설임 없이 결정하는가? (예: "lineHeightPx 52/fontSize 40=1.3은 1.3으로 기입, 47/fontSize 40=1.175는 가장 가까운 정돈 비율인 1.2로 반올림")
4. landing/basic 프로젝트 타입 자동 판정 힌트를 어디에 심어야 에이전트가 올바른 단위체계를 선택하는가? (파일명? HTML 첫 줄 주석? spec.md 헤더?)

## 출력 요구사항
- /mnt/d/dev-base/.gran-maestro/discussion/DSC-002/rounds/00/frontend(gemini).md 에 저장
- 2000자 이내
- 브리프 재작성안은 실제 마크다운 샘플 포함
# Risk 관점 의견 요청 — DSC-002 Round 0

## 공유 컨텍스트
/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/rounds/00/shared-context.md 파일을 Read하세요.

## 추가 참조 파일 (반드시 Read)
- /mnt/d/dev-base/rules/common.md
- /mnt/d/dev-base/tools/validate-semantic.py
- /mnt/d/dev-base/tools/figma-section-spec.py
- /mnt/d/dev-base/tools/post-impl-verify.py
- /mnt/d/위링/2026-04-15 목포플레이파크/html/css/common.css
- /mnt/d/위링/2026-04-15 에이스디펜스/html/css/common.css

## 당신의 역할
리스크/트레이드오프 분석가 관점. 세 레이어 병행 강화안이 만들 수 있는 부작용과 숨은 비용을 냉정하게 평가하고, 엣지 케이스에서 파이프라인이 무너질 지점을 찾으십시오.

## 질문
1. 다음 4개 트레이드오프 각각에서 **수용 가능한 한계선**을 제안하십시오. 한계를 넘으면 어떤 증상이 나타나는가? (a) 검증기 강화→false-positive, (b) 규칙 주입 강화→브리프 비대화, (c) 전처리기 강화→Figma 원본 충실도 훼손, (d) 재dispatch 강화→비용.
2. "lineHeightPx→정돈 비율 자동 반올림"이 잘못 작동할 수 있는 실제 엣지 케이스 3개를 들고, 각각에 대한 가드레일 제안.
3. 브리프 비대화 리스크를 회피하면서 규칙을 완벽히 전달하는 **계층화된 주입 전략**(short brief + external rules reference + runtime check 세 단계) 설계안.
4. 세 레이어 병행 추진 시 발생할 **상호 충돌**(예: 전처리기가 정돈한 값을 검증기가 여전히 거부) 시나리오와 방지책.

## 출력 요구사항
- /mnt/d/dev-base/.gran-maestro/discussion/DSC-002/rounds/00/risk(claude).md 에 저장
- 2000자 이내
- 각 리스크에 대해 증상/징후/가드레일 3줄 세트 권장
[MST skill=ideation step=2/4 return_to=null]

# Risk Analyst 관점 의견 요청 — IDN-002

## 공유 컨텍스트 (필수 Read)
/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/context.md 파일을 반드시 Read 한 뒤 답하세요.
추가로 필요하면:
- /mnt/d/dev-base/CLAUDE.md 의 "PLN-004 Figma 워크플로우", "PM 자동 검증 후처리" 섹션
- /mnt/d/dev-base/tools/figma-section-spec.py (필드 추출 범위 파악)
- /mnt/d/dev-base/rules/rules.yaml

## 당신의 역할
제안될 개선안의 **실패 모드, 엣지 케이스, 유지보수 리스크**를 비판적으로 식별. 공식화 자체가 가진 잠재적 부작용도 다뤄라.

## 질문
1. 현재 spec 기반 구현에서 실제로 **어떤 Figma 요소가 생성물에 누락되거나 왜곡**될 가능성이 가장 큰가? Top 10 실패 시나리오를 "Figma 입력 → 현재 파이프라인 출력 → 실제 기대" 형태로 구체화.
2. spec을 엄격 공식화(JSON Schema 강제)할 경우 발생 가능한 **역효과**:
   - (a) Figma 가 스키마 외 필드를 새로 추가했을 때의 실패
   - (b) 기존 섹션과의 하위 호환 깨짐
   - (c) validator가 지나치게 엄격해져 false-positive 폭증
   - (d) 외주 에이전트가 스키마에 과최적화되어 의도된 디자인 해석(예: 시각적 동일성 확보를 위한 창의적 치환)을 못 하는 경우
3. 이미지/벡터/폰트 자원 파이프라인 추가 시의 리스크(저작권, 외부 CDN, 폰트 라이선스, 이미지 해상도 결정론).
4. CLAUDE.md가 강제하는 "PM은 직접 코드 수정 금지" 원칙과 "개선을 즉시 적용해야 하는 긴급 상황" 사이의 충돌 지점.
5. 현재 검증 2단(figma-validate + semantic)의 통과가 **시각적 동일성을 의미하지 않는** 구체적 예시.

## 출력 요구사항
- 파일로 저장: /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-risk(claude).md
- 2000자 이내, 한국어
- 각 리스크에 "심각도(High/Med/Low) × 발생가능성(High/Med/Low)" 라벨
- 마지막에 "## 개선 추진 시 사전 차단해야 할 리스크 Top 5"
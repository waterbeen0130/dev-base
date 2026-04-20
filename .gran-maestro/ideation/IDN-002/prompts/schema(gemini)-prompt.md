[MST skill=ideation step=2/4 return_to=null]

# Schema Designer 관점 의견 요청 — IDN-002

## 공유 컨텍스트 (필수 Read)
- /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/context.md
- /mnt/d/dev-base/extracted/section_03_spec.json
- /mnt/d/dev-base/extracted/section_04_spec.json
- /mnt/d/dev-base/tools/figma-section-spec.py (현재 스키마 생성 로직)
- /mnt/d/dev-base/rules/validation_schema.json (기존 스키마 파일 — 용도 확인)

## 당신의 역할
"Figma와 완전 동일한 추출물"을 보장하는 **결정적(deterministic) JSON 스키마 설계**. 스키마 공식화 가능성을 실제 설계안으로 답하라.

## 질문
1. **공식화 가능성 판단**: 현재 spec.json을 JSON Schema(Draft 2020-12) 또는 Pydantic 모델로 엄격 공식화하는 것이 실용적으로 가능한가? 가능하다면 단계별 로드맵, 불가능하다면 이유.
2. **제안 스키마 초안**: Figma fidelity 갭(effects, gradients, strokes, cornerRadius, layoutSizing, constraints, vector paths, componentId 등)을 포함한 **v2 스키마 구조**를 JSON Schema 초안 스타일로 작성. 필수/선택, enum, nullable을 명시.
3. **스키마 버저닝 전략**: schema_version 숫자 1개 → major.minor 전환, 하위 호환 정책, validator의 version 분기 처리 방안.
4. **단일 진실 공급원**: 동일 스키마를 (a) Python 생성기, (b) Python validator, (c) 외주 에이전트 브리프, (d) 규칙 문서 네 곳에서 일관되게 쓰려면 어떤 구조가 좋은가? (예: pydantic → JSON Schema 자동 생성 → markdown 테이블 자동 생성)
5. **결정성 보장**: 동일 Figma 노드가 실행마다 동일 spec.json을 낳도록 보장하는 정렬·정규화 규칙(키 순서, 실수 반올림, 옵션 필드 생략 vs null) 제안.

## 출력 요구사항
- 파일로 저장: /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-schema(gemini).md
- 2000자 이내, 한국어, JSON Schema 초안 코드블록 포함 필수
- 마지막에 "## 공식화 가능성: 가능/부분가능/불가능" 한 줄 결론 + 근거 2줄
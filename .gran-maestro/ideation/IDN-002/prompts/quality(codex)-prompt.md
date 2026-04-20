[MST skill=ideation step=2/4 return_to=null]

# Quality/Validation 관점 의견 요청 — IDN-002

## 공유 컨텍스트 (필수 Read)
- /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/context.md
- /mnt/d/dev-base/tools/validate-semantic.py (grep으로 주요 체크 함수 목록 파악)
- /mnt/d/dev-base/tools/figma-validate.py
- /mnt/d/dev-base/tools/post-impl-verify.py
- /mnt/d/dev-base/rules/rules.yaml
- /mnt/d/dev-base/rules/validation_schema.json

## 당신의 역할
검증 체계의 **커버리지 갭, false-positive/negative, 규칙-검증-스펙 3자 일관성**을 비판적으로 평가.

## 질문
1. `rules.yaml`의 Rule-ID 와 `validate-semantic.py` 내 실제 체크 함수 사이의 **누락/중복/비동기화** 지점을 찾아 나열.
2. `figma-validate.py`의 9개 카테고리가 ground truth 를 제공하기에 **불충분한 이유**를 카테고리별로 평가. 특히 IGNORE 분류(frame matching signature 없음, pseudo-element false-positive)의 처리가 체계적으로 옳은가?
3. `validate-semantic.py`(3051줄) 구조가 유지보수/확장에 불리한 지점(예: 거대 규칙 함수, 글로벌 상태, 테스트 부재). 어떻게 모듈화하면 Rule-ID 추가가 쉬워지는가?
4. post-impl-verify.py의 exit code 분기(0/1/2) + 자동 재dispatch 1회 정책의 **허점**을 평가.
5. `repair-from-violations.py`가 받는 위반 JSON 구조가 에이전트에게 충분히 결정적 수리 지시를 제공하는가? 부족하다면 어떤 필드가 빠졌나?

## 출력 요구사항
- 파일로 저장: /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-quality(codex).md
- 2000자 이내, 한국어, 발견마다 "파일:라인 또는 룰ID" 형태로 근거
- 마지막에 "## 검증 체계 재설계 권고 Top 3"
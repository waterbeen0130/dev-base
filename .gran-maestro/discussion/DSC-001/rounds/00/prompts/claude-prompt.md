# 규칙 체계 일관성 분석 (전체 구조 관점)

당신은 규칙 체계의 전체적인 일관성과 유지보수성을 평가하는 전문 분석가입니다.
아래 퍼블리싱 규칙 파일 체계(CLAUDE.md, codex.md, common.md, landing.md, rule_engine.json, validation_schema.json)를 분석하여 **구조적 문제점과 개선 방향**을 제시하세요.

---

## 규칙 파일 체계 구조

```
rules/
├── CLAUDE.md      - Claude 전용 규칙 (common.md 참조)
├── codex.md       - Codex/GitHub Copilot 전용 규칙 (common.md 참조)
├── common.md      - 모든 AI 공통 규칙 (Base)
├── landing.md     - 랜딩페이지 전용 규칙 (common.md 참조)
├── rule_engine.json       - 기계 판독용 규칙 엔진
└── validation_schema.json - 코드 검증 스키마
```

---

## 주요 파일별 현황

### CLAUDE.md 특이사항
- common.md 참조하지만 Figma 텍스트 추출 규칙 일부만 간략히 포함
- "텍스트 추출 품질" 섹션이 common.md/codex.md의 상세 버전과 불일치 가능성
- CLAUDE.md에는 "레이아웃 추출 보정 규칙"이 없음 (common.md에 있음)
- CLAUDE.md에는 "텍스트 태그 자동 판정 규칙"이 없음 (common.md에 있음)

### codex.md 특이사항
- "자동 검증 필수" 섹션: `node tools/validate.js` 명령 포함 (다른 파일에 없음)
- JS 들여쓰기 4 spaces (common.md도 4 spaces, 동일)
- common.md와 거의 동일하지만 약간의 차이 있음

### common.md vs landing.md 관계
- landing.md가 common.md의 일부를 override하지만 명확한 우선순위 표시 없음
- "Basic과 다른 점" 섹션으로 구분하지만, font-size override가 핵심 충돌 지점

### rule_engine.json 구조 분석
- mode: "strict_transform" — 엄격한 변환 모드
- landing/basic 프로젝트 타입 구분 없음
- "output_policy.replicate_existing_style_profile: true" — 기존 스타일 복제 정책

### validation_schema.json 구조 분석
- 프로젝트 타입별 conditional check 없음
- 47개 체크 중 no_duplicate_selector가 2번 등록 (버그)
- font_size_pc_rem check → landing 프로젝트에서 false positive 가능

---

## 분석 요청

1. **규칙 계층 구조 문제**: CLAUDE.md, codex.md, landing.md가 common.md를 참조하는데, 참조가 명시적이지 않아 AI가 어떤 규칙을 따라야 할지 혼란스러울 수 있는 지점
2. **override 메커니즘 부재**: landing.md가 common.md의 font-size를 override하지만, AI가 이를 인식하는 방법이 없음 → 해결 방안
3. **codex.md 자동 검증 명령의 위치 적절성**: codex.md에만 있는 validate.js 실행 명령이 common.md나 별도 파일로 이동해야 하는지
4. **rule_engine.json 확장 방향**: 현재 단일 JSON으로 Basic+Landing 모두 커버하려는 한계점 → 프로젝트 타입별 분리 또는 overlay 패턴 제안
5. **유지보수성 관점**: 지금과 같이 같은 규칙이 여러 파일에 중복될 때, 하나를 업데이트하면 다른 파일들이 뒤처지는 드리프트 문제 → 단일 소스 원칙(Single Source of Truth) 적용 방법

응답 형식:
- 구조적 문제점 5가지 (우선순위 순)
- 각 문제에 대한 구체적 해결 방안
- 규칙 체계 개선을 위한 전체 아키텍처 제안 (간략히)
- 2000자 이내

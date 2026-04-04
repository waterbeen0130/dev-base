# PLN-002: figma-extract.py 정규화 엔진 재설계 + 변환 규칙 문서화

## 요약
기존 figma-extract.py(916행)를 전면 재작성하여, Figma MCP JSON을 정규화된 중간 JSON으로 변환하는 엔진을 구축한다. 모든 변환 규칙을 문서화하고, basic/landing 프로젝트 타입 프로필을 분리한다.

## Intent (JTBD)
- When I: Figma MCP JSON을 정규화 엔진에 입력할 때
- I want to: 모든 시각적 속성을 규칙 기반으로 정규화된 JSON 중간 포맷으로 변환하고 싶다
- So I can: 어떤 AI 모델이 읽어도 동일한 해석이 가능하여 일관된 코드 추출 품질을 확보할 수 있다

## Objective 컨텍스트
- objective.md: /mnt/d/dev-base/.gran-maestro/agile/AGI-001/objective/objective.md
- JTBD 요약: Figma JSON 정규화 → 시멘틱 HTML/CSS 생성 → 일관된 품질 + 수작업 절감
- 프로젝트 DoD:
  - DOD-001: 정규화된 JSON 변환 (must) — 이번 Sprint 대상
  - DOD-002: 변환 규칙 문서화 (must) — 이번 Sprint 대상
  - DOD-003: 프로필 분리 (must) — 이번 Sprint 대상
  - DOD-004: 시멘틱 변환 파이프라인 (must) — 다음 Sprint
  - DOD-005: 디자인 동일 품질 (must) — 이후
- 성공 지표: 서로 다른 피그마 디자인 3개 이상에서 디자인과 거의 동일한 결과

## 인수 기준 초안

이 plan의 구현이 완료됐다는 것은:
- [MUST] [TIER-A] Figma MCP JSON을 stdin으로 입력하면 정규화된 중간 JSON이 출력된다 (트리 구조 보존, 모든 시각적 속성 포함)
- [MUST] [TIER-A] 레이아웃 속성(layoutMode, itemSpacing, padding, alignment, sizing)이 CSS 값으로 정확히 변환된다
- [MUST] [TIER-A] 시각 속성(fills→background, strokes→border, cornerRadius→border-radius)이 정확히 변환된다
- [MUST] [TIER-A] 타이포그래피 속성(fontSize, fontWeight, lineHeight→ratio, letterSpacing→em, color)이 정확히 변환된다
- [MUST] [TIER-A] characterStyleOverrides 누적 병합이 정확하게 세그먼트로 분할된다
- [MUST] [TIER-A] --profile basic 시 font-size가 rem으로, --profile landing 시 px로 변환된다
- [MUST] [TIER-B] 프로필 설정이 JSON 파일로 분리되어 코드 내 하드코딩된 분기가 없다
- [MUST] [TIER-B] 모든 변환 규칙이 문서(docs/conversion-rules.md)에 매핑표로 정리되어 있다
- [SHOULD] [TIER-B] 기존 --tree 모드가 호환 유지된다
- [SHOULD] [IMPACT] 기존 smoke test(tests/test_smoke.py)가 여전히 통과한다
- [MUST] [TIER-A] 신규 테스트가 각 변환 카테고리(레이아웃/시각/타이포/오버라이드/프로필)를 검증한다

## 범위 예산 (Appetite)
- figma-extract.py 전면 재작성 (1파일)
- 프로필 JSON 2개 (basic.json, landing.json) in tools/profiles/
- 변환 규칙 문서 1개 (docs/conversion-rules.md)
- 테스트 파일 확장 (tests/test_normalization.py)

## 제외 범위 (No-go Scope)
- 2차 AI 시멘틱 변환 (DOD-004 — 다음 Sprint)
- validate.js 연동 (DOD-006)
- 마크다운 테이블 출력 (기존 포맷은 제거)
- Figma API 직접 호출 기능 (--node-id 모드 제거 또는 최소 유지)

## 제약사항
- Python 3.x, 외부 라이브러리 최소화 (stdlib만 권장)
- stdin 파이프 방식 유지
- 기존 --tree 모드 호환
- 단일 파일 유지 (figma-extract.py)

## 우선순위 (MoSCoW)
- Must: 정규화 JSON 출력, 전체 속성 변환, 프로필 분리, 변환 규칙 문서화, 테스트
- Should: --tree 모드 호환, 기존 smoke test 호환
- Won't: 마크다운 테이블 출력, validate.js 매핑 출력, --node-id API 호출

## 의존성
- 선행: PLN-001/REQ-001 (pytest 환경) — 완료됨

## 테스트 전략
- 적용 (커버리지 미설정)
- 기존 smoke test 호환 + 신규 normalization test 추가

## Loop 종료 조건
- 기존 검증 통과(기본값)

## 리스크 레지스터
| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| characterStyleOverrides 재작성 시 edge case | 중 | 중 | 다양한 오버라이드 조합 테스트 케이스 |
| 프로필 분리 시 누락 규칙 | 중 | 낮 | rule_engine.json 기준으로 체크리스트 작성 |
| 트리 구조 JSON이 대용량 피그마에서 과도하게 큼 | 낮 | 낮 | depth 제한 옵션 유지 |

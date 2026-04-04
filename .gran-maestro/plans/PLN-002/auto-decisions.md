# 자율 결정 로그 — PLN-002

> 자율 모드(-a)로 실행됨. 아래 항목들이 PM에 의해 자율 결정되었습니다.

| 항목 | 결정값 | Confidence | 판단 방식 | 강제 여부 |
|------|--------|-----------|-----------|-----------|
| Cynefin 분류 | Complicated | 0.90 | PM 자율 판단 — 916행 전면 재작성, 20+ 속성 변환 규칙, 프로필 분리 포함 | 자율 |
| WHO | 피그마 기반 퍼블리싱 작업자 + AI 에이전트 | 0.95 | PM 자율 판단 — objective JTBD에서 확인 | 자율 |
| WHAT | figma-extract.py 전면 재작성 + 변환 규칙 문서화 + 프로필 분리 | 0.95 | PM 자율 판단 — DOD-001/002/003 매핑 | 자율 |
| WHY | AI 해석 편차 제거, 일관된 추출 품질 확보 | 0.95 | PM 자율 판단 — objective JTBD | 자율 |
| WHEN | 마감 없음, 품질 만족 시 완료 | 0.95 | PM 자율 판단 — agile-plan에서 확인 | 자율 |
| WHERE | tools/figma-extract.py + tools/profiles/ (신규) + docs/conversion-rules.md (신규) | 0.90 | PM 자율 판단 | 자율 |
| HOW MUCH | 모든 시각적 속성 100% 매핑, 프로필 2종(basic/landing) 완전 분리 | 0.90 | PM 자율 판단 — DOD 타겟 | 자율 |
| HOW | 트리 구조 보존 JSON 출력 + 프로필 기반 CSS 값 확정 | 0.85 | PM 자율 판단 — details 스키마 참조 | 자율 |
| 제약 Out-of-scope | 2차 시멘틱 변환(DOD-004), validate.js 연동(DOD-006), 로그 추적(DOD-007) | 0.95 | PM 자율 판단 — 이번 Sprint 범위 | 자율 |
| 제약 기술 | Python 단일 파일, 외부 라이브러리 최소화, stdin 파이프 유지 | 0.90 | PM 자율 판단 — objective 설계 결정 | 자율 |
| MoSCoW Must | 정규화 엔진 핵심 변환 + JSON 출력 + 프로필 분리 + 규칙 문서화 | 0.90 | PM 자율 판단 | 자율 |
| MoSCoW Should | --tree 모드 호환 유지, 기존 CLI 인터페이스 유사 구조 | 0.80 | PM 자율 판단 | 자율 |
| MoSCoW Won't | validate.js 매핑 출력, 마크다운 테이블 출력 | 0.85 | PM 자율 판단 | 자율 |
| 테스트 전략 | 적용 (커버리지 미설정) — 기존 smoke test 확장 | 0.85 | PM 자율 판단 | 자율 |
| Loop 종료 조건 | 기존 검증 통과(기본값) | 0.95 | PM 자율 판단 | 자율 |
| 의존성 | PLN-001/REQ-001 완료 (Sprint 0 테스트 환경) — 충족됨 | 0.95 | PM 자율 판단 | 자율 |
| INVEST-I | 충족 — DOD-001/002/003 독립 완결 가능 | 0.90 | PM 자율 판단 | 자율 |
| INVEST-N | 충족 — 내부 구조는 유연 (전면 재작성 허용) | 0.95 | PM 자율 판단 | 자율 |
| INVEST-V | 충족 — 프로젝트 핵심 목표 (AI 해석 편차 제거) | 0.95 | PM 자율 판단 | 자율 |
| INVEST-E | 충족 — 기존 코드 분석 완료, 변환 규칙 매핑표 정의됨 | 0.85 | PM 자율 판단 | 자율 |
| INVEST-S | 충족 — 단일 REQ로 완결 가능 (파일 1개 재작성 + 프로필 + 문서) | 0.80 | PM 자율 판단 | 자율 |
| INVEST-T | 충족 — pytest로 각 변환 함수 검증 + 샘플 JSON 입출력 비교 | 0.90 | PM 자율 판단 | 자율 |
| REQ 분리 | 분리 불필요 — 단일 도메인(정규화 엔진), 레이어 혼재 없음 | 0.85 | PM 자율 판단 | 자율 |

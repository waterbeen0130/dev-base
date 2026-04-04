# PLN-001: pytest smoke test 환경 구축

## 요약
figma-extract.py의 핵심 함수를 검증하는 pytest smoke test 1개를 포함한 최소 테스트 환경을 구축한다.

## Intent (JTBD)
- When I: AGI-001 스프린트 루프를 시작하려 할 때
- I want to: 프로젝트에 최소한의 테스트 환경을 갖추고 싶다
- So I can: 정규화 엔진 재설계 과정에서 변경 사항을 자동 검증할 수 있다

## Objective 컨텍스트
- objective.md: /mnt/d/dev-base/.gran-maestro/agile/AGI-001/objective/objective.md
- JTBD 요약: Figma JSON 정규화 엔진 + 시멘틱 변환 파이프라인 구축
- 프로젝트 DoD:
  - DOD-001: 정규화된 JSON 중간 포맷 변환
  - DOD-002: 변환 규칙 문서화
  - DOD-003: 프로젝트 타입 프로필 분리
  - DOD-004: 시멘틱 변환 파이프라인
  - DOD-005: 디자인 동일 품질 달성
  - DOD-006: validate.js 연동
  - DOD-007: 로그 추적
- 성공 지표: 서로 다른 피그마 디자인 3개 이상에서 디자인과 시각적으로 거의 동일한 결과

## 인수 기준 초안

이 plan의 구현이 완료됐다는 것은:
- [MUST] [TIER-B] pyproject.toml에 pytest 설정이 존재하고 `pip install pytest`로 테스트 실행 가능하다
- [MUST] [TIER-B] tests/ 디렉토리에 smoke test 파일이 존재한다
- [MUST] [TIER-A] smoke test가 figma-extract.py의 rgba_to_hex, extract_fill_color 함수를 import하여 기본 동작을 검증한다
- [MUST] [TIER-B] `pytest` 명령으로 모든 테스트가 통과한다

## 범위 예산 (Appetite)
- 파일 3개 이내 생성/수정 (pyproject.toml, tests/__init__.py, tests/test_smoke.py)

## 제외 범위 (No-go Scope)
- 커버리지 설정
- CI/CD 연동
- 복잡한 fixture나 mock
- 기존 figma-extract.py 코드 수정

## 제약사항
- Out-of-scope: 기존 코드 변경 최소화
- 기술 제약: Python 3.x, pytest만 사용
- 비즈니스 제약: 없음

## 우선순위 (MoSCoW)
- Must: pyproject.toml pytest 설정, tests/ smoke test
- Won't: coverage 설정, CI 연동

## 의존성
- 없음

## 테스트 전략
- 적용 (커버리지 미설정)

## Loop 종료 조건
- 기존 검증 통과(기본값)

## 리스크 레지스터
| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| 식별된 리스크 없음 | - | - | - |

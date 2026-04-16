# REQ-024 / Task 01 구현 지시

PLN-008 / DBG-001 기반. 상세 사양은 `spec.md` 참조.

## 실행 원칙
1. **TDD 우선**: AC-001/002/004/006은 테스트 먼저 작성하고 통과시킨 뒤 구현.
2. **롤백 용이성**: 규칙 삭제/수정은 git 단위 커밋으로 분리 (각 AC별 또는 각 규칙 쌍별).
3. **회귀 방지**: 규칙 1개 수정마다 최소 1개 회귀 샘플에 `post-impl-verify.py` 재실행.

## 핵심 시작점
- `rules/rules.yaml` 현재 규칙 수 파악부터 시작
- `tools/validate-semantic.py`의 `column flex gap 금지` 함수(`:2626-2648`)와 룰 디스패치 테이블 구조 파악

## 주의 사항
- `manual_review`/`documentation` 타입 규칙은 판단 기준을 명확히 하고 이동 이력을 `rules/deprecated.md`에 기록
- 충돌 해소 시 한 방향으로 통일하되 결정 근거를 커밋 메시지에 남김
- rules/templates/publishing/impl-request.md의 인라인 규칙 섹션은 REQ-027에서 다룸 (이번 범위 아님)

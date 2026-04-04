# REQ-002 T02: 통합 테스트 + 회귀 테스트

## §1 요약
T01(정규화 엔진 재작성) 완료 후, 각 변환 카테고리를 종합 검증하고 기존 smoke test 회귀를 확인하는 테스트 태스크.

## §2 테스트 범위
- 통합 검증: T01의 AC-001~AC-009 전체 통과 확인
- 증분 테스트: tests/test_normalization.py의 레이아웃/시각/타이포/오버라이드/프로필 테스트
- 회귀 테스트: tests/test_smoke.py 기존 7개 테스트 통과

## §3 통합 AC

### AC-T01 [automatable] 전체 pytest 통과
- **Given**: T01 구현이 완료된 상태
- **When**: `pytest tests/ -v` 실행 시
- **Then**: 모든 테스트 PASSED (smoke + normalization)
- **Test**: `pytest tests/ -v --tb=short`

### AC-T02 [automatable] [regression-test] smoke test 회귀
- **Given**: 재작성된 figma-extract.py
- **When**: `pytest tests/test_smoke.py -v` 실행 시
- **Then**: 기존 7개 테스트 모두 PASSED
- **Test**: `pytest tests/test_smoke.py -v`

### AC-T03 [automatable] 샘플 MCP JSON 파이프라인 검증
- **Given**: 실제 Figma MCP 응답 형태의 샘플 JSON
- **When**: stdin으로 입력하여 정규화 실행 시
- **Then**: 유효한 정규화 JSON이 출력되고, meta.total_nodes > 0
- **Test**: `echo '<sample>' | python3 tools/figma-extract.py --stdin --profile basic | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['meta']['total_nodes']>0"`

## §4 회귀 테스트 항목
- rgba_to_hex 함수 시그니처 호환
- extract_fill_color 함수 시그니처 호환
- line_height_to_ratio 함수 시그니처 호환
- figma_align_to_css 함수 시그니처 호환

## §5 선행 작업 (blockedBy)
- T01

## §5 후행 작업 (blocks)
- 없음

## §7 Assigned Agent
[config: codex-dev] → codex-dev

## §8 실행 지시
1. `pytest tests/ -v --tb=short` 실행
2. 실패 테스트가 있으면 원인 분석 후 수정
3. 전체 PASSED 확인

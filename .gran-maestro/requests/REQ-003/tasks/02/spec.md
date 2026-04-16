# REQ-003 T02: 통합 검증 + 회귀 테스트

## §0 Context Manifest

- `tools/json-to-html.py` — T01에서 수정된 변환기
- `tools/validate-semantic.py` — 검증 도구
- `tools/figma-extract.py` — 정규화 엔진 (참조용)
- `output/youngwol/` — 영월 프로젝트 output
- `output/a_main/` — 제천 프로젝트 output
- `tests/test_smoke.py` — 기존 smoke 테스트

## §1 요약

T01 수정 완료 후 영월/제천 output을 재생성하여 통합 검증 + 회귀 테스트를 수행한다.

## §2 테스트 범위

통합 검증 + 증분 테스트 + 회귀 테스트

## §3 통합 AC

### AC-INT-001 [automatable] — 영월 output 재생성 검증
- **Given**: T01 수정이 완료된 json-to-html.py로 영월 정규화 JSON을 변환한 후
- **When**: validate-semantic.py로 검증하면
- **Then**: CRITICAL 0건, MAJOR 0건

### AC-INT-002 [automatable] — 영월 텍스트 무손실 검증
- **Given**: 재생성된 영월 index.html에서
- **When**: 기존 output 대비 텍스트 노드를 비교하면
- **Then**: 기존에 존재하던 텍스트가 누락되지 않고, 추가 텍스트(depth flatten으로 숨겨졌던 것)가 복원됨

### AC-INT-003 [automatable] — flex 비율 검증
- **Given**: 재생성된 영월 common.css에서
- **When**: width 고정px 사용을 grep하면
- **Then**: 이미지/아이콘/divider 제외 고정 width px가 0건

### AC-INT-004 [automatable] — 범용 클래스명 감소 검증
- **Given**: 재생성된 영월 common.css에서
- **When**: main_el_*, main_txt_* 패턴을 카운트하면
- **Then**: 기존 대비 50% 이상 감소

### AC-INT-005 [impact-check] — 제천 회귀 검증
- **Given**: T01 수정이 완료된 json-to-html.py로 제천 정규화 JSON을 변환한 후
- **When**: validate-semantic.py로 검증하면
- **Then**: 기존 대비 CRITICAL/MAJOR 증가 없음

### AC-INT-006 [automatable] — smoke test PASS
- **Given**: T01 수정 완료 후
- **When**: `pytest tests/test_smoke.py`를 실행하면
- **Then**: 모든 테스트 PASS

## §4 회귀 테스트 항목

- json-to-html.py의 기존 기능: 컴포넌트 템플릿 적용(header/footer/quick), 벡터 그룹 skip, 불필요 래퍼 제거, reset.css 생성
- figma-extract.py의 정규화 JSON이 변경되지 않았으므로 입력은 동일

## §5 선행 작업 (blockedBy)

- T01

## §6 후행 작업 (blocks)

없음

## §7 에이전트 배정

[config: codex-dev] → codex-dev

## §8 실행 지시

```
1. 영월 output 재생성:
   FIGMA_TOKEN 없이 기존 정규화 JSON 파일이 있으면 그것을 사용.
   없으면 T01의 변경사항만으로 검증 (json-to-html.py의 단위 테스트).

2. validate-semantic.py 실행 (영월 + 제천)

3. pytest tests/test_smoke.py 실행

4. 결과 비교 리포트 생성 (before/after)
```

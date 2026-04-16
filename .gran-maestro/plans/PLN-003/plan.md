# PLN-003: json-to-html.py 핵심 품질 문제 4건 해결

## 요약
json-to-html.py의 출력 품질을 DOD-005(시각적 동일성) 실질 달성 수준으로 끌어올리기 위해 핵심 품질 문제 4건을 해결한다.

## 배경
2026-04-04 작업에서 figma-extract.py(정규화 엔진)과 json-to-html.py(HTML/CSS 변환기)를 구축하고 반값여행_제천/영월 2개 프로젝트로 테스트했다. DOD-001~007이 완료 표기되었으나, json-to-html.py의 구조적 한계로 출력물 품질이 디자인 원본과 차이가 있어 수작업이 필요한 상태다.

## 결정사항
1. **depth limiter + 텍스트 누락** (연관 문제): depth 5 제한 시 카드/리스트 내부가 flatten되어 텍스트가 사라지는 문제 해결. 스타일 있는 노드뿐 아니라 텍스트 포함 노드도 depth limiter에서 보존해야 한다.
2. **flex 비율 변환**: Figma의 고정 width px 값을 flex 비율(%, flex:1 등)으로 자동 변환. 규칙상 width 고정px 금지.
3. **클래스명 개선**: main_el_1~46, main_txt_1~40 같은 의미 없는 클래스명을 피그마 노드 구조/역할에서 유추하여 개선.
4. **이미지 이름 중복**: 같은 이름 노드의 _1, _2 suffix를 부모 컨텍스트 기반 의미 있는 이름으로 개선.

## 범위 예산 (Appetite)
json-to-html.py 단일 파일 (665행) 내 수정. 영월(youngwol) output으로 검증.

## 제외 범위 (No-go Scope)
- 반응형 CSS 미디어쿼리 자동 생성
- 시각적 검증 도구 (Playwright 스크린샷 비교)
- MV(메인비주얼) 슬라이드/페이지네이션 등 인터랙티브 요소
- 새 피그마 프로젝트 추가 테스트
- figma-extract.py 수정

## 제약사항
- Python 3.10+ 표준 라이브러리만 사용 (외부 패키지 추가 불가)
- CSS 값은 100% 정규화 JSON에서 추출 (AI 추측 금지)
- 기존 validate-semantic.py 34개 규칙 통과 유지

## 우선순위 (MoSCoW)
- **Must**: depth limiter + 텍스트 무손실, flex 비율 변환
- **Should**: 클래스명 개선 (범용 이름 제거)
- **Could**: 이미지 이름 중복 개선
- **Won't (this time)**: 반응형 CSS, 시각적 검증, MV 인터랙티브

## 테스트 전략
- 적용 (커버리지 미설정)
- 검증 도구: validate-semantic.py (34개 규칙) + tests/test_smoke.py
- 영월(youngwol) output으로 E2E 확인

## Loop 종료 조건
- 기존 검증 통과(기본값) — AC 충족 + validate-semantic.py PASS

## 의존성
- 선행 완료: PLN-002/REQ-002 (figma-extract.py 정규화 엔진 재설계)
- 연관: AGI-001 (프로젝트 전체 Objective)

## 인수 기준 초안

이 plan의 구현이 완료됐다는 것은:
- [MUST] [TIER-A] depth 5 제한을 유지하면서 텍스트 노드가 하나도 누락되지 않는다. 영월 output에서 공지사항 등 리스트 내부 텍스트가 모두 보존된다.
- [MUST] [TIER-A] Figma 고정 width px 값이 flex 비율(%, flex:1, flex:0 0 N%)로 자동 변환된다. common.css에 width 고정px(이미지/아이콘 제외)가 0건이다.
- [SHOULD] [TIER-B] main_el_N, main_txt_N 같은 범용 클래스명이 부모 컨텍스트/역할 기반 의미 있는 이름으로 대체된다. validate-semantic.py의 범용클래스명 경고가 50% 이상 감소한다.
- [SHOULD] [TIER-B] 같은 이름 노드의 이미지 파일명이 부모 컨텍스트를 반영한 의미 있는 이름을 갖는다.
- [MUST] [TIER-A] 기존 validate-semantic.py 34개 규칙이 모두 PASS 유지된다.
- [SHOULD] [IMPACT] 기존 반값여행_제천(a_main) output이 이번 변경으로 기능 퇴행하지 않는다.

## 리스크 레지스터
| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| depth limiter 완화로 DOM 깊이 5 초과 발생 | 중 | 상 | 텍스트 노드만 보존하는 선택적 완화, 빈 래퍼는 여전히 flatten |
| flex 비율 변환이 특정 레이아웃에서 깨짐 | 중 | 중 | 형제 노드 width 합산 기반 비율 계산, 단독 노드는 100% |
| 클래스명 추론이 잘못된 의미 부여 | 하 | 하 | 추론 실패 시 기존 이름 유지 (worst case: 현재와 동일) |

## Intent (JTBD)
- When I: json-to-html.py로 피그마 정규화 JSON을 HTML/CSS로 변환할 때
- I want to: depth 제한으로 인한 텍스트 누락, 고정px width, 의미 없는 클래스명 문제가 자동으로 해결되길 원한다
- So I can: 변환 결과물이 디자인 원본과 거의 동일하여 수작업 보정이 불필요한 수준이 된다

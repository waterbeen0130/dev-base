# PLN-006 — figma-section-spec.py 근본 수정 + 두 퍼블리싱 프로젝트 재추출

> Cynefin: **Complicated** — 원인 후보 다수(Figma API instance 해석, character_segments 병합, 섹션 분할 전략) 이나 분석 가능. ideation/discussion 생략, 단일 탐사 후 수정.

## 배경 (진단)

"Figma MCP → 코드 추출" 결과물이 두 프로젝트(`D:\위링\2026-04-15 목포플레이파크`, `D:\위링\2026-04-15 에이스디펜스`)에서 Figma 원본과 크게 다르며, 에이전트는 "완료"라고 보고한다. 직접 확인 결과:

- **목포플레이파크 `extracted/A_Main_spec.md`** 에 instance 중복 행이 존재하고 `characters` 필드와 `character_segments[].text` 가 **서로 다른 텍스트**를 가리킴.
  - 예) node `134:6899` — `characters`="남녀노소…" / segments text="스릴만점! 모험의 정점을 찍는 어드벤처 코스"
  - 예) node `134:6901` — `characters`="Easy" / segments text="Adventure"
  - 예) node `134:6916` — `characters`="Easy" / segments text="Extreme"
  - 이 상태에서 `figma-validate.py` 의 "텍스트 위변조" 검증은 spec.json 의 `characters` 기준으로 HTML 을 검사하므로, spec 자체가 오염되어 있으면 검증은 통과하지만 실제 Figma 와 어긋난다.
- **에이스디펜스** 는 `extracted/` 폴더 없이 빈 템플릿(`page/index.html` 50줄) 만 존재. Figma 파이프라인이 사실상 진입조차 안 함.
- 두 프로젝트 모두 `.gran-maestro/` 미설치 → `post-impl-verify.py` 자동 재dispatch 루프 없이 에이전트 자가 보고만 신뢰.
- 목포는 `A_Main` 섹션 하나로 `text_nodes(57)` 을 통째로 뽑음 → 섹션 단위 분할이 없어 구조/순서 오류 확률 상승.

## 문제

1. `tools/figma-section-spec.py` 가 Figma component instance 의 텍스트 해석을 잘못 수행한다 → spec.json 의 `characters` 와 `character_segments` 가 불일치하고, 검증을 통과해도 결과물이 Figma 와 다르다.
2. 섹션 분할 전략이 없어 대형 프레임을 통짜로 spec 화한다.
3. 두 퍼블리싱 프로젝트는 `.gran-maestro/` 게이트가 없어 "완료" 자가 보고를 막을 장치가 없다.

## 인수 기준 초안

이 plan 의 구현이 완료됐다는 것은:

- [MUST] [TIER-A] `tools/figma-section-spec.py` 수정 후 목포플레이파크 `134:6708` 노드를 재추출했을 때, 결과 spec.json 의 모든 text_node 에서 `characters` 와 `character_segments` 의 연결된 text 가 완전히 일치한다 (불일치 0건).
- [MUST] [TIER-A] 수정 후 재추출한 spec 에서 Figma instance override 된 텍스트(예: `Easy` → `Adventure`, `Extreme`)가 spec.json 에 실제 override 값으로 기록된다.
- [MUST] [TIER-A] `tools/figma-section-spec.py` 에 instance 해석 로직에 대한 최소 단위 테스트 또는 fixture 기반 검증 스크립트가 추가되고, 재실행 시 PASS 한다.
- [MUST] [TIER-B] 목포플레이파크 프로젝트에 `.gran-maestro/` 가 `init-project.py --publishing` 으로 설치되고, `config.json`/`agents.json` 이 퍼블리싱 템플릿으로 구성된다.
- [MUST] [TIER-B] 에이스디펜스 프로젝트에 `.gran-maestro/` 가 동일하게 설치된다.
- [MUST] [TIER-A] 목포플레이파크 메인 페이지를 섹션 단위로 재추출 후 `figma-validate.py` + `validate-semantic.py` + `post-impl-verify.py` 가 모두 exit 0.
- [SHOULD] [TIER-B] 에이스디펜스 메인 페이지에 대해서도 동일한 5단계 플로우(spec → 구현 → validate → semantic → post-impl) 가 1회 성공한다.
- [SHOULD] [IMPACT] [TIER-B] 기존 PLN-003~005 에서 생성된 dev-base 내 extracted/ 산출물이 새 스펙 포맷으로도 그대로 검증을 통과한다 (하위 호환).

## 제약사항

- **하지 않을 것**: figma-validate.py / validate-semantic.py / post-impl-verify.py 의 검증 로직 자체는 건드리지 않음. 입력 데이터(spec.json) 의 정확성만 개선한다.
- **기술 제약**: Figma REST API `/v1/files/:key/nodes` 응답을 1차 소스로 사용 (MCP 응답 구조와 다를 수 있음을 감안). Python 표준 라이브러리만 사용.
- **비즈니스 제약**: 두 프로젝트의 기존 `html/` 산출물은 재작업 전 백업만 하고 폐기한다 (기존 코드 유지 불필요 — 어차피 잘못된 결과물).

## 우선순위 (MoSCoW)

- **Must**: 툴 버그 수정, 두 프로젝트 `.gran-maestro` 설치, 목포 재추출 성공
- **Should**: 에이스디펜스 재추출 성공, 기존 PLN-003~005 산출물 회귀 검증
- **Could**: 섹션 자동 분할 heuristic (최상위 자식 기준) 추가
- **Won't**: figma-validate.py / semantic validator 확장, MCP 호출 경로 자동화

## 의존성

- 선행 필요: 없음 (dev-base 내 tool 수정이 전제, 외부 blocker 없음)
- 연관: PLN-005 (post-impl-verify.py 기본 후처리) — 이 plan 이 올바른 spec 을 만들어야 post-impl-verify 가 의미를 가짐

## 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|---|---|---|---|
| Figma API instance 텍스트 해석 스펙이 문서화되지 않아 수정이 여러 케이스를 놓칠 수 있음 | 중 | 상 | 수정 전 raw API 응답을 `D:/dev-base/extracted/fixture_mokpo_a_main.json` 으로 스냅샷 저장, 단위 테스트 fixture 로 활용 |
| 기존 PLN-003~005 산출물의 spec 포맷이 달라 회귀 실패 | 중 | 중 | 수정은 확장만, 필드 제거 금지. 새 필드는 optional 로 추가 |
| 두 프로젝트의 Figma file-key/node-id 미기록 → 재추출 불가 | 중 | 상 | REQ 진입 시 사용자에게 두 프로젝트의 Figma URL 을 1회 확인 |
| 섹션 분할 heuristic 도입 시 기존 단일 섹션 동작 깨짐 | 하 | 중 | Could 범위로 한정, 기본 동작은 그대로 유지 |

## 분리 실행

이 plan 은 성격이 다른 3개 REQ 로 분리한다.

1. **REQ-A: 툴 근본 수정** (dev-base 단독) — `figma-section-spec.py` 의 instance / character_segments 병합 로직 수정 + fixture 기반 회귀 검증 추가. 결과물은 `tools/` 변경과 `tests/` 또는 `extracted/fixtures/` 신설.
2. **REQ-B: 목포플레이파크 재구축** — `.gran-maestro` 설치 → 섹션별 spec 재추출 → 섹션별 HTML/CSS 작성 → 5단계 검증 루프로 완결.
3. **REQ-C: 에이스디펜스 재구축** — B 와 동일 플로우. B 의 학습을 반영해 순차 실행.

REQ-A 완료가 REQ-B/C 의 선행 조건. B → C 는 순차 (동일 패턴 반복).

## 테스트 전략

- 적용 (커버리지 미설정) — `figma-section-spec.py` 수정에 대해 Figma API 응답 fixture(JSON) 기반 회귀 테스트를 추가한다. 재추출 결과 spec.json 을 golden file 과 비교.
- 프로젝트 재구축(REQ-B/C) 은 `post-impl-verify.py` 의 exit code 기반 자동 검증으로 대체.

## Loop 종료 조건

기본값 — AC 통과 + config 의 `max_iterations` 준수. 추가 조건 없음.

## 브라우저 테스트

- enabled: false (툴/파이프라인 수정이 주이며, 결과 HTML 은 `post-impl-verify.py` + 스크린샷 비교로 이미 검증됨)

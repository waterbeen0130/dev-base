# PLN-005 — 모제림 랜딩 레거시 섹션 재검증 + PLN-004 도구·워크플로우 보강

- 생성일: 2026-04-13
- Cynefin: Complicated
- 상태: active

## 1. 요청 (Refined)

모제림 비절개 랜딩 프로젝트의 **레거시 4 섹션(Hero, Section_02, Section_03 일부 잔여, Section_04)** 이 PLN-004 도구가 만들어지기 전에 작성되어 한 번도 figma-validate.py 검증을 거치지 않은 상태다. Section_03을 직접 검증해본 결과 텍스트 환각·한국어 조사 오류·정렬·폰트 누락·color override 미반영 등 사용자가 직접 지적한 문제가 모두 spec과의 차이로 잡혔다.

또한 Section_05 신규 작업 중 PLN-004 도구의 한계(characterStyleOverrides 미추출, cornerRadius 미추출, pseudo-element ::before false-positive, 외주 에이전트가 spec 파일을 못 읽음, 사용자 반복 피드백인 "section 좌우 padding 금지"가 brief에 자동 주입되지 않음)가 동시에 노출되었다.

본 plan은 **두 갈래 작업을 단일 plan에 묶어** PLN-004 워크플로우를 실전에서 자기완결적으로 만든다:

A. 레거시 3 섹션 재검증·정정 (Hero/Section_02/Section_04)
B. PLN-004 도구·워크플로우 4종 보강

## 2. 범위 (Scope)

**포함**:
- (Part A) 모제림 프로젝트 Hero/Section_02/Section_04를 figma-section-spec.py로 추출 → figma-validate.py로 검증 → 잡힌 위반 정정 → validate-semantic.py 통과
- (Part B-1) `tools/figma-section-spec.py` 보강:
  - characterStyleOverrides 추출 (TEXT 노드 캐릭터 단위 오버라이드 — 색상/굵기/크기 분할)
  - cornerRadius 추출 (FRAME 노드)
  - bbox / parent_id 추출 (HANDOVER §6-A 항목)
- (Part B-2) `tools/figma-validate.py` 보강:
  - CSS pseudo-element (`::before`, `::after`) 분리 처리 — li 색상 같은 false-positive 제거
  - frame 매칭 휴리스틱 개선 (signature 미매칭 false-positive 감소)
- (Part B-3) 외주 brief 표준 강화:
  - `templates/impl-request.md` 또는 `rules/templates/publishing/impl-request.md`에 "section 좌우 padding 금지 + max-width 패턴 강제" 인라인 주입
  - 외주 에이전트의 sandbox 우회 패턴: PM이 spec.md/json을 프로젝트 내부(`extracted/{name}_spec.{md,json}`)로 복사 후 brief에 절대경로 명시
  - 9개 검증 카테고리 + characterStyleOverrides 체크리스트를 brief에 인라인
- (Part B-4) PM 자동 검증 후처리 훅:
  - 외주 완료 직후 자동으로 figma-validate.py + validate-semantic.py 실행
  - 위반 발견 시 PM이 자동 정정 dispatch (현재는 수동 검증 → 수동 정정)

**제외**:
- 모제림 Section_06/08/10 신규 진행 (별도 작업)
- Section_07/09/FAQ (사용자 별도 지시 보류)
- figma-section-spec.py 전면 재작성 (필드 추가만)
- 새 validation 카테고리 신설

**시작점 힌트**:
- `tools/figma-section-spec.py` (필드 추가 대상)
- `tools/figma-validate.py` (pseudo-element 처리 + 매칭 휴리스틱)
- `templates/impl-request.md` 또는 publishing 템플릿
- `/home/waterbeen/.claude/projects/-mnt-d-dev-base/memory/feedback_no_section_padding.md` (이번 세션에 저장한 강한 피드백)
- `/mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/index.html` + `css/common.css` (Part A 대상)

## 3. 결정 사항

### 분리 전략: 5개 REQ 순차 실행 (사용자 확정)

| REQ | 주제 | 의존성 | 에이전트 |
|---|---|---|---|
| ① | Hero/Section_02/Section_04 일괄 재검증·정정 (Part A) | 독립 | gemini-dev (퍼블리싱) + PM 직접 검증 |
| ② | tools/figma-section-spec.py 보강 (B-1) | 독립 | codex-dev |
| ③ | tools/figma-validate.py 보강 (B-2) | 독립 | codex-dev |
| ④ | 외주 brief 표준 강화 (B-3) | 독립 | claude-dev |
| ⑤ | PM 자동 검증 후처리 훅 (B-4) | blockedBy ③ (validator 안정화 후) | claude-dev |

### Part A 실행 방식
- 각 섹션마다: figma-section-spec.py 실행 → spec.md/json 생성 → figma-validate.py 즉시 실행 → 위반 목록 생성 → PM이 위반 1:1 매핑한 정정 brief를 gemini-dev에 외주 → 재검증 → 통과 시 다음 섹션
- 환각/오타/색상은 spec.json 기준이 absolute (사용자 합의)
- false-positive(::before pseudo, frame 휴리스틱)는 정정 대상에서 제외 (③ 보강 후 자동 해소)

### Part B-1 (figma-section-spec.py)
- characterStyleOverrides:
  - `TEXT.characters` + `TEXT.characterStyleOverrides[]` + `TEXT.styleOverrideTable{}` 함께 추출
  - text_node에 `character_segments[]` 필드 추가: `[{start, end, text, fontFamily, fontWeight, color, ...}]` 형식
  - 오버라이드 없는 노드는 빈 배열로 기록 (하위 호환)
- cornerRadius:
  - FRAME 노드 추출 시 `cornerRadius` (단일) 또는 `rectangleCornerRadii` (4모서리 배열) 모두 캡처
  - 50% 클램프 판정: cornerRadius >= min(width, height)/2 이면 `border_radius_hint: "50%"` 부가
- bbox / parent_id:
  - 모든 TEXT/FRAME 노드에 `bbox: {x,y,w,h}` (이미 frame엔 있음, text에 추가)
  - 모든 노드에 `parent_id` (walk 시 부모 추적)

### Part B-2 (figma-validate.py)
- pseudo-element 분리:
  - CSS 파서가 `selector::before`/`::after`를 별도 가상 요소로 인식
  - 색상 검증 시 본 요소의 `color` 값에서 pseudo의 영향을 분리 (현재는 둘 다 li 본체로 합산되어 false-positive)
  - REQ-008/02 회귀 fixture에 pseudo-element 케이스 추가
- frame 매칭 휴리스틱 개선:
  - 현재 signature가 `padding+gap+layoutMode` 조합 → 매칭 후보 너무 좁음
  - `bbox` 좌표 + `parent_id` 정보가 있으면 그것을 우선 (Part B-1 의존)
  - 매칭 실패 시 "미매칭 (signature 없음)" 대신 노드 경로 힌트 출력으로 변경
  - 부모 frame이 매칭되면 자식 frame은 자동 매칭 후보에서 제외 (중복 false-positive 제거)

### Part B-3 (외주 brief 표준)
- 템플릿 위치 결정:
  - 퍼블리싱: `D:\dev-base\rules\templates\publishing\impl-request.md` (이미 존재)에 인라인 주입
  - 일반: `templates/impl-request.md`도 동일 패턴
- 인라인 주입 항목:
  - "section 좌우 padding 절대 금지, inner max-width + margin:auto 패턴 강제" (강조 표시)
  - "spec.md / spec.json은 반드시 프로젝트 내부 경로로 전달, sandbox 밖 경로 금지"
  - "9개 figma-validate 카테고리 표 + spec 필드 매핑" (CLAUDE.md §PLN-004와 동일)
  - "characterStyleOverrides 처리: 오버라이드 있는 글자만 별도 `<em>`으로 분리"
  - "cornerRadius 처리: 50% 클램프 시 `border-radius:50%`"

### Part B-4 (PM 자동 검증 후처리)
- 트리거: 외주 dispatch 완료 직후 (Bash background → completion notification)
- 자동 실행:
  ```
  python3 tools/figma-validate.py --spec ... --html ... --css ...
  python3 tools/validate-semantic.py --html ... --css ... --profile {detected}
  ```
- 위반 분류:
  - CRITICAL (텍스트 위변조, 폰트 5필드, color hex 정확 일치): 자동 재dispatch에 위반 목록 첨부
  - MAJOR (clamp, lineHeight): 자동 재dispatch
  - false-positive 의심 (frame signature, pseudo-element): 1차 무시, PM에 보고만
- 재dispatch 횟수 최대 2회 (`max_cli_retries` 준용), 초과 시 PM 직접 개입 escalation
- 구현 위치: 새 스크립트 `tools/post-impl-verify.py` 또는 PM 워크플로우 가이드 (Part 4는 코드보다 워크플로우 문서로 시작 → PM이 매번 따르는 패턴화)

## 4. 인수 기준 초안

이 plan의 구현이 완료됐다는 것은:

- [MUST] [TIER-A] (Part A) 모제림 프로젝트의 Hero / Section_02 / Section_04에 대해 figma-validate.py + validate-semantic.py(--profile landing) 모두 핵심 위반 0건 (텍스트 위변조 0, 폰트 5필드 0, lineHeight 0, fills color hex 0, column flex gap 0)
- [MUST] [TIER-A] (Part A) 사용자가 브라우저로 시각 확인했을 때 Section_03/05와 동등한 품질 (Figma 디자인과 일치)
- [MUST] [TIER-A] (B-1) `figma-section-spec.py`가 spec.json에 `character_segments[]` 필드를 모든 TEXT 노드에 출력하고, 오버라이드 있는 노드의 분할 결과가 정확
- [MUST] [TIER-A] (B-1) 모든 FRAME 노드에 `cornerRadius` (또는 `rectangleCornerRadii`) 출력, 50% 클램프 시 `border_radius_hint: "50%"` 추가
- [SHOULD] [TIER-B] (B-1) 모든 노드(TEXT/FRAME)에 `bbox` + `parent_id` 출력
- [MUST] [TIER-A] (B-2) `figma-validate.py`가 `::before`/`::after` 색상을 본 요소 색상과 분리 처리하여 li 같은 케이스에서 false-positive 0건
- [MUST] [TIER-A] [IMPACT] (B-2) REQ-008/02 회귀 12개 fixture가 여전히 모두 정확히 탐지 (무회귀)
- [SHOULD] [TIER-B] (B-2) frame 매칭 false-positive 50% 이상 감소 (현재 Section_05 19건 → 10건 이하 목표)
- [MUST] [TIER-A] (B-3) `rules/templates/publishing/impl-request.md`에 section padding 금지 + spec 파일 경로 + 9개 카테고리 + characterStyleOverrides + cornerRadius 처리 5개 항목 모두 인라인 주입
- [MUST] [TIER-A] [IMPACT] (B-3) 기존 brief 사용 사례(REQ-008/009/010)에서 동일 brief가 적용 가능 (구조 호환)
- [SHOULD] [TIER-B] (B-4) PM 워크플로우 가이드 문서 또는 `tools/post-impl-verify.py` 신설로 외주 완료 직후 자동 검증 수행. 위반 시 자동 재dispatch 1회 최소
- [SHOULD] [TIER-B] (B-4) 자동 재dispatch 완료 후에도 위반이 남으면 PM에 명확한 escalation 메시지

## 5. 제약사항

- 보안: Figma 토큰은 환경변수만 (코드/로그 평문 금지)
- 성능: 도구 보강 후에도 단일 섹션 검증 < 5초
- 호환성: Python 3.10+, 외부 의존성 추가 금지 (stdlib만)
- 운영: 기존 REQ-007/008/009/010 산출물과 호환 — 회귀 fixture 12개 무회귀 필수

## 6. 우선순위 (MoSCoW)

- **Must have**: Part A 3 섹션 정정 완료, B-1 character_segments + cornerRadius, B-2 pseudo-element 분리, B-3 brief 표준 5종 인라인 주입
- **Should have**: B-1 bbox/parent_id, B-2 frame 매칭 휴리스틱 개선, B-4 자동 후처리 훅
- **Could have**: B-4 자동 재dispatch 루프 (현 단계는 가이드만)
- **Won't have**: figma-section-spec.py 전면 재작성, 새 validation 카테고리

## 7. 의존성

- 선행: 없음 (PLN-004 산출물 모두 사용 가능)
- 연관: PLN-004 (figma-section-spec.py + figma-validate.py + workflow), REQ-010 (CSS 상속 fix), REQ-009 (rules/문서 기반)
- 후속: 모제림 Section_06 이후 신규 진행 (별도 plan)

## 8. 분리 실행

이 plan은 **5개 REQ로 분리 실행**:

| 단계 | REQ 주제 | 의존성 | 에이전트 |
|---|---|---|---|
| ① | 모제림 Hero/Section_02/Section_04 일괄 재검증·정정 (Part A) | 독립 | gemini-dev + PM 검증 |
| ② | tools/figma-section-spec.py 보강 — characterStyleOverrides + cornerRadius + bbox/parent_id | 독립 | codex-dev |
| ③ | tools/figma-validate.py 보강 — pseudo-element 분리 + frame 매칭 휴리스틱 | 독립 | codex-dev |
| ④ | 외주 brief 표준 강화 — publishing 템플릿 5종 인라인 주입 | 독립 | claude-dev |
| ⑤ | PM 자동 검증 후처리 — post-impl validate hook (가이드 + 선택 스크립트) | blockedBy ③ | claude-dev |

## 9. 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|---|---|---|---|
| Part A에서 figma-validate.py가 추가 false-positive를 낼 수 있음 (B-2 보강 전이라) | 중 | 중 | PM이 false-positive 패턴(::before, frame 미매칭)을 인지하고 정정 대상에서 제외. ③ 완료 후 Part A 재검증 옵션 (Could) |
| character_segments 추출이 styleOverrideTable 누적 병합 케이스에서 잘못 처리 | 중 | 상 | CLAUDE.md §"텍스트 추출 품질"에 명시된 누적 병합 알고리즘 정확 구현 + Section_05의 "남성" 사례를 회귀 fixture로 추가 |
| frame 매칭 휴리스틱 개선이 기존 12개 회귀 fixture 무회귀를 깨뜨림 | 중 | 상 | ③ 완료 후 반드시 REQ-008/02 회귀 스크립트 실행, base/scenarios 모두 기존 동일 결과 유지 |
| brief 표준 강화 후에도 외주 에이전트가 인라인 규칙을 무시 | 중 | 중 | brief 상단에 "이 규칙을 무시하면 PM이 자동 재dispatch함" 명시 + ⑤ PM 자동 후처리로 보완 |
| sandbox 우회 패턴(spec 프로젝트 복사)이 매번 PM 수동 작업 | 하 | 중 | ④ brief 표준에 PM 책임 명시. 추후 자동화 대상 |

## 10. 테스트 전략

- **적용** (목표 커버리지 미설정 — 회귀 fixture 기반)
- 회귀: REQ-008/02 fixture 12개 + 신규 ::before pseudo-element fixture (B-2 추가)
- 시각 검수: Part A 3 섹션 모두 1920px 브라우저에서 사용자 검수
- 도구 자체: figma-section-spec.py에 단위 fixture 1개 추가 ("남성" 오버라이드 케이스)

## 11. Loop 종료 조건

기존 검증 통과(기본값) — figma-validate + validate-semantic 모두 PASS

## 12. AC ↔ TIER 매핑

| PAC ID | Grade | Tier | 검증 핵심 |
|---|---|---|---|
| PAC-1 | MUST | TIER-A | Part A 위반 0건 |
| PAC-2 | MUST | TIER-A | Part A 시각 검수 |
| PAC-3 | MUST | TIER-A | character_segments 출력 |
| PAC-4 | MUST | TIER-A | cornerRadius 출력 |
| PAC-5 | SHOULD | TIER-B | bbox/parent_id |
| PAC-6 | MUST | TIER-A | pseudo-element 분리 |
| PAC-7 | MUST | TIER-A [IMPACT] | 회귀 12개 무회귀 |
| PAC-8 | SHOULD | TIER-B | frame 매칭 50% 감소 |
| PAC-9 | MUST | TIER-A | brief 5종 인라인 |
| PAC-10 | MUST | TIER-A [IMPACT] | brief 호환 |
| PAC-11 | SHOULD | TIER-B | post-impl-verify 가이드/스크립트 |
| PAC-12 | SHOULD | TIER-B | 자동 재dispatch 1회 |

## 13. Confidence Score Matrix

| 축 | 점수 | 근거 |
|---|---|---|
| Clarity | 0.9 | 사용자가 직접 문제를 지적하고 검증 도구가 모두 catch함 |
| Feasibility | 0.85 | 도구 보강은 명확한 필드 추가, 외부 의존성 없음 |
| Decoupling | 0.9 | 5 REQ 분리 명확 (Part A 독립, B-1/B-2/B-3 독립, B-4만 ③ 의존) |
| Completeness | 0.85 | 회귀 fixture 누가 + sandbox 우회 패턴 명시 |

전체 평균 0.875 — 0.5 미만 항목 없음. 진행 가능.

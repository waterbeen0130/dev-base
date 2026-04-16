# REQ-009-02 — PLN-004 워크플로우 드라이런 리포트

생성일: 2026-04-13
검증 대상: REQ-009-01이 문서화한 5단계 워크플로우 (CLAUDE.md `## PLN-004 Figma 워크플로우`)
입력: `extracted/section_03_spec.json` (main worktree 산출물, text_nodes=12 / frame_nodes=33 / interactions=0 / images=0)

## 드라이런 결과

| 단계 | 명령/작업 | exit | 결과 요약 |
|---|---|---|---|
| 1 | spec sheet 확보 | - | `dryrun/section_spec.json` 복사 완료 (814 lines, schema_version=1) |
| 2 | HTML/CSS 작성 (spec.json만 보고) | - | `dryrun/index.html` + `dryrun/style.css` 작성. 12개 text_node 전수 반영, 프레임 래퍼는 최소화 |
| 3 | figma-validate.py | **1** | 35건 위반 — 텍스트 12/12 PASS, frame padding/gap 30건, clamp 4건, fills 1건 |
| 4 | validate-semantic.py | **2** | 11건 위반 — CRITICAL 1 (generic_class_name `section_\d+`), MAJOR 10 (page prefix, max-width 패턴, root vars 등 basic 프로파일 규칙) |
| 5 | commit 가능 여부 | **NO** | 3번/4번 모두 non-zero → 5단계 커밋 게이트 정상 동작 확인 |

전체 파이프라인이 5단계를 처음부터 끝까지 실행 가능했고, 각 단계가 예상대로 분리된 산출물을 생성했다. CLAUDE.md 문서만 보고 따라 할 수 있는 수준이다.

## 발견된 갭

### 갭 #1 — `validate-semantic.py --profile` 기본값이 `all`이라 basic 전용 규칙이 모든 HTML에 적용됨 (절차 불명확)

- 재현: `python3 tools/validate-semantic.py --html dryrun/index.html --css dryrun/style.css` → `reset_css_separate`, `font_size_pc_rem`, `root_vars_required`, `word_break_korean`, `gsap_animation_css_present` 등 basic.md 전용 규칙이 섹션 단위 dry-run HTML에도 발사됨.
- 추정 원인: 기본 프로파일이 `all`이라 landing/basic 프로젝트 전용 체크가 전부 켜진 상태. PLN-004 5단계에서는 `--profile`을 명시하라는 지시가 없음.
- 영향: "섹션 HTML만 먼저 검증" 같은 단일-섹션 워크플로우에서 관련 없는 규칙이 터져 CRITICAL을 유발 → commit 게이트가 불필요하게 막힐 수 있음.
- 후속 REQ 후보: CLAUDE.md §PLN-004 5단계에 `--profile {basic|landing|section}` 선택 기준과 예시 커맨드를 추가. 또는 섹션 단위 검증용 `section` 프로파일 신설.

### 갭 #2 — figma-validate.py가 CSS 상속을 계산하지 않음 (도구 버그 후보)

- 재현: 초기 HTML에서 li 내부를 `<li><span>...</span></li>` 로 감싸고 font-* 규칙을 `.section_03_list li` 에 두면, 자식 `span`이 매칭된 경우 "폰트 5필드 완결성 missing: font-family, font-size, font-weight, line-height, color" 18건 위반 발생 (6 nodes × 3 categories). span을 제거해 li 자체에 텍스트를 넣으면 모두 해결.
- 추정 원인: `compute_element_properties()` 는 해당 element에 직접 매칭되는 규칙만 수집하고 ancestor로부터의 CSS inheritance(font-family/size/weight/line-height/color는 상속 속성)를 고려하지 않음.
- 영향: AI가 규칙상 허용된 `li span` 구조를 쓰면 무조건 위반으로 잡혀, 실제 브라우저 렌더링과 괴리가 생김. 드라이런은 HTML을 우회 수정해서 통과시켰지만, 본 프로젝트에서는 피그마 노드 구조에 맞춰 span이 필요한 경우가 많음.
- 후속 REQ 후보: `compute_element_properties`에 상속 속성 ancestor walk 추가. 최소 `font-family / font-size / font-weight / line-height / color / letter-spacing` 6종은 부모로부터 상속.

### 갭 #3 — `tools/figma-validate.py --help` 출력에 spec 스키마 / 위반 카테고리 설명이 없음 (문서 부재)

- 재현: `python3 tools/figma-validate.py --help` → 단순 usage 3줄만 출력. CLAUDE.md §PLN-004 3번에도 9개 카테고리가 구체적으로 뭔지 명시돼 있지 않음. 실제 카테고리는 `폰트 5필드 완결성 / lineHeight 비율 일치 / fills color hex 일치 / frame padding/gap 반영 / clamp 적용 / column flex gap 금지 / 줄바꿈 보존 / 텍스트 위변조 / interaction URL 일치` 9종이다.
- 추정 원인: 문서는 "9개 카테고리 자동 검증"이라고만 적혀있어 외주 에이전트가 어떤 위반이 나올 수 있는지 사전에 알 수 없음.
- 후속 REQ 후보: CLAUDE.md §PLN-004 3단계에 카테고리 9종을 표로 나열 + 각 카테고리가 어떤 spec 필드를 보는지 한 줄 설명. 또는 `figma-validate.py --list-categories` 옵션 신설.

### 갭 #4 — CLAUDE.md §PLN-004에 "spec.md만 보고 구현" 이라 돼 있으나 `figma-section-spec.py` 가 생성하는 실제 산출물은 `.json` + `.md` 두 종류, 검증은 `.json` 기준 (절차 불명확)

- 재현: 드라이런 중 "spec.md에 명시된 layout/gap/padding/fills/typography 값만으로 HTML/CSS 작성" 이라는 지시와 "figma-validate.py --spec extracted/{section}_spec.json" 이 모순 없이 보이지만, 실제 AI가 읽는 소스는 `.md`인데 검증 기준은 `.json`이다. `.md`가 `.json`의 모든 필드를 빠짐없이 직렬화하지 않으면 "md대로 작성했는데 json 기준 위반" 이 나올 수 있음. 본 드라이런은 시간 절약을 위해 `.json`을 직접 읽었으므로 이 리스크를 실증하지 못함.
- 후속 REQ 후보: CLAUDE.md §PLN-004 1단계에 "AI 구현자는 `.md`와 `.json` 모두 접근 허용. `.json`은 검증 레퍼런스, `.md`는 읽기 편의" 라고 명시 + `.md` 스키마 완결성 테스트 추가.

## 결론

- [ ] (a) 누락 0건 — 워크플로우 자기완결적, REQ-009 종료 가능
- [x] (b) 갭 4개 발견 — 후속 REQ로 이관 권장

근거:
1. 5단계 파이프라인은 끝까지 실행 가능했고 각 도구는 정상 동작했음 → 프레임웍 자체는 기능함.
2. 그러나 #1(`--profile` 지침 부재)과 #3(카테고리 9종 미문서화)은 외주 에이전트가 CLAUDE.md만 읽고 작업할 때 즉시 막히는 지점이라 문서 보강이 필수.
3. #2(CSS 상속 미반영)는 실제 피그마 추출 작업에서 구조적 false-positive를 유발하는 도구 버그 성격이라 코드 수정이 필요.
4. #4(`.md` vs `.json` 비대칭)는 당장 블로커는 아니지만 잠재 모순이라 문서 명시 권장.
5. 따라서 REQ-009는 문서화 REQ-009-01 + 드라이런 REQ-009-02 완료 선언 가능하되, 위 4건을 후속 REQ(REQ-010 후보)로 이관해야 워크플로우가 실전에서 "자기완결적"이라 할 수 있음.

# Implementation Spec

- Request ID: REQ-011
- Task ID: 01
- Created: 2026-04-13
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: external project text fix] → 최종: claude-dev
- Worktree: N/A (외부 프로젝트 — `/mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/`)
- Complexity: Standard (3 섹션 × validate→fix 사이클)

## §0 Context Manifest

- /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/index.html
- /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/css/common.css
- /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/HANDOVER.md
- tools/figma-section-spec.py
- tools/figma-validate.py
- tools/validate-semantic.py

## 1. 요약 (Summary)

모제림 비절개 랜딩 프로젝트의 **3 섹션 (Hero, Section_02 ba_section, Section_04 plan)** 을 PLN-004 도구로 일괄 재검증한다. Section_03/05에서 입증된 동일 패턴으로 figma-validate.py + validate-semantic.py(--profile landing) 두 도구를 돌리고, 잡힌 위반 중 실제 문제(false-positive 제외)를 정정한다.

## 2. 범위 (Scope)

- **포함**:
  - Hero (Figma node `842:36`, class `.hero`)
  - Section_02 (Figma node `842:37`, class `.ba_section` — Before/After 슬라이더)
  - Section_04 (Figma node `842:196`, class `.plan`)
  - 각 섹션마다 spec.md/json 추출 → figma-validate → validate-semantic → 위반 분류 → 정정 → 재검증
  - 정정 적용 파일: `index.html`, `css/common.css`
  - Section_05에서 검증한 "section 좌우 padding 금지" 패턴을 위반하는 기존 코드 발견 시 동시 정정
  - "남성"같은 character override가 있는지 figma 원본에서 확인 (Pretendard 문자색 분리 케이스 발견 시 적용)
- **제외**:
  - Section_03 추가 정정 (이미 이번 세션에서 처리됨)
  - Section_05 (이미 정정 완료)
  - Section_06/08/10 신규 진행
  - Section_07/09/FAQ (사용자 별도 지시 보류)
  - 기존 ba_slider.js 인터랙션 변경 (Section_02 슬라이더는 문제 없음)
- **시작점 힌트**: HANDOVER.md §2 진행 표 (Hero/Section_02/Section_04 클래스 매핑), 기존 common.css 패턴

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable]
Given: Hero (842:36), Section_02 (842:37), Section_04 (842:196) spec.json이 추출됨
When: 각 섹션에 대해 `python3 tools/figma-validate.py --spec ... --html ... --css ...` 실행
Then: 각 섹션의 핵심 카테고리(텍스트 위변조, 폰트 5필드 완결성, lineHeight 비율 일치, fills color hex 일치, column flex gap 금지, 누락된 spec 행) **위반 0건**. frame padding/gap matching false-positive는 보고만 하고 정정 대상에서 제외.
Test:
```bash
for SEC in 842:36 842:37 842:196; do
  NAME=$(echo $SEC | tr ':' '_')
  FIGMA_TOKEN=... python3 tools/figma-section-spec.py --file-key T8xEPS7sR5MZCUQ9JVa4hH --node-id $SEC --output /tmp/mojelim_extracted --name section_${NAME}
  python3 tools/figma-validate.py --spec /tmp/mojelim_extracted/section_${NAME}_spec.json --html "$HTML" --css "$CSS"
done
```

#### AC-002 [MUST] [automatable] [impact-check]
Given: 3 섹션 정정 완료
When: `python3 tools/validate-semantic.py --html "$HTML" --css "$CSS" --profile landing` 실행
Then: Section_05에서 이미 통과한 baseline 대비 신규 CRITICAL 0건. MAJOR 신규 0건 (page_prefix_required 등 pre-existing 제외).
Test: 위 명령 + 출력 grep `^\[CRITICAL\]|^\[MAJOR\].*\.(hero|ba_|plan)`

#### AC-003 [MUST] [manual]
Given: 정정 완료 후 사용자가 1920px 브라우저로 visual 검수
Then: Hero/Section_02/Section_04가 Figma 디자인과 시각적으로 일치 (Section_03/05와 동등한 품질)
Test: 사용자 시각 검수 후 OK 응답

#### AC-004 [MUST] [automatable]
Given: 모든 정정이 완료된 상태
When: Section_03/Section_05의 figma-validate 결과 (이전 세션 정정 결과)와 동일 명령 재실행
Then: 두 섹션 모두 무회귀 (이번 작업이 다른 섹션을 깨뜨리지 않음)
Test: section_03 + section_05 spec으로 figma-validate 재실행

## 3.5 Constraints

- 외부 프로젝트 (git repo 아님) → git worktree/commit 없음. 변경은 직접 적용.
- 정정 결과 리포트는 `.gran-maestro/requests/REQ-011/tasks/01/report.md` 에 기록 (dev-base 내부)
- "section 좌우 padding 금지" 메모리 규칙 반드시 적용 (max-width + margin:auto 패턴 강제)

## 4. 구현 컨텍스트

- **따라야 할 패턴**: 이번 세션에서 Section_03/05에 적용한 정정 패턴
  1. spec.json characters와 HTML 텍스트 1:1 일치 확인
  2. 모든 텍스트 노드의 font-family/size/weight/line-height/color CSS 명시
  3. lineHeightRatio 무단위 비율
  4. characterStyleOverrides 있으면 `<em>` 분리
  5. cornerRadius 50% 클램프 시 border-radius:50%
  6. column flex (VERTICAL frame) → margin, gap 금지
  7. 100px 이상 padding/gap → clamp() (단, 좌우는 inner max-width로)
- **알아야 할 제약**:
  - figma-validate.py에 ::before/::after pseudo-element 처리 한계 있음 (REQ-013에서 보강 예정) → list 색상 6건 같은 false-positive는 무시
  - figma-validate.py frame matching 휴리스틱 false-positive 다수 → frame padding/gap 매칭 보고는 무시
- **접근법 방향**: 3 섹션 spec을 모두 추출 → 일괄 검증 → false-positive 분류 → 실제 위반만 Python 스크립트로 batch 정정 (Section_03 fix_fue.py 패턴) → 재검증

## 5. 의존성

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): [REQ-012]

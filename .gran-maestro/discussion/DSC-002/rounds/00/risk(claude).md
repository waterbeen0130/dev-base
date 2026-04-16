# Risk 관점 의견 — DSC-002 Round 0

## 1. 4개 트레이드오프 한계선

### (a) 검증기 강화 → false-positive
- **한계선**: ERROR 카테고리 false-positive 율 ≤ 2%, WARNING ≤ 8%. 같은 spec.json 기준 동일 위반이 3회 이상 PM에 의해 "디자인 의도"로 override 되면 즉시 severity 강등.
- **초과 시 증상**: 에이전트가 자동 재dispatch 루프를 빠져나오지 못해 max_cli_retries 소진 → PM 직접 개입 빈도 급증, 워크플로우 마비. 디자이너 의도 line-height(1.193 같은 비정돈 비율)까지 반올림 강요로 시각 차이 발생.
- **가드레일**: spec.json에 `design_intent_override` 화이트리스트 필드 추가 → 해당 노드는 검사 skip. severity는 ERROR/WARNING/INFO 3단으로 고정하고 ERROR는 텍스트 위변조/CSS Grid/inline style 같은 "절대 금지"로만 한정.

### (b) 규칙 주입 강화 → 브리프 비대화
- **한계선**: impl-request.md 본문 ≤ 1500 토큰 (≈6KB). 브리프 전체 ≤ 8000 토큰. 규칙 인라인 텍스트는 ≤ 800 토큰.
- **초과 시 증상**: Gemini 컨텍스트 경합으로 규칙 섹션 자체를 무시하고 Figma raw value만 직역. 브리프 후반부의 spec.md 참조 경로/검증 명령어가 prompt 끝에 묻혀 실행되지 않음. 토큰 비용 1.5~2배 증가.
- **가드레일**: 계층 3에 따른 외부 참조(아래 Q3 참조). 규칙은 "금지 패턴 5개 + 변환표 1개"만 인라인, 나머지는 파일 경로.

### (c) 전처리기 강화 → Figma 충실도 훼손
- **한계선**: 자동 변환은 "의미 보존 변환"만 허용. lineHeightPx → ratio 반올림은 ratio 차이 ≤ 3% (=픽셀 차이 ≤ 0.5px @16px font)일 때만. 정돈 비율 후보(1.0/1.1/1.2/1.25/1.3/1.4/1.45/1.5/1.6/1.667/1.75/1.8/2.0)와의 거리 > 0.05이면 원본 보존.
- **초과 시 증상**: 헤딩의 의도된 1.05 line-height가 1.0으로 반올림되어 텍스트 베이스라인 깨짐. 서브픽셀 정렬 의도 padding(예: 17px)이 20px로 강제되어 그리드 어긋남.
- **가드레일**: spec.json에 `original_value` + `normalized_value` + `normalization_reason` 3필드를 함께 기록. 검증기는 둘 중 하나만 만족해도 PASS.

### (d) 재dispatch 강화 → 비용
- **한계선**: 자동 재dispatch는 CRITICAL/MAJOR 한정 1회. MINOR는 0회 (PM 보고만). 동일 REQ 누적 토큰 ≤ 초기 dispatch의 2.5배.
- **초과 시 증상**: MINOR(예: snake_case 1건) 위반 1개로 전체 섹션 재생성 → 토큰 비용이 한 섹션당 50K → 200K로 폭증. 재생성 결과가 다른 곳에서 새 위반 발생하는 회귀 루프.
- **가드레일**: post-impl-verify.py에 `--max-retry-cost {tokens}` 가드. 재dispatch 브리프는 "위반 라인만 patch" 모드로 한정 (전체 재생성 금지).

## 2. lineHeightPx → 정돈 비율 자동 반올림 엣지 케이스 3개

### 케이스 1: 의도된 비정돈 비율 (디자이너 명시)
- **시나리오**: 헤로 타이틀 fontSize 50, lineHeightPx 65 → ratio 1.3 (정상). 그러나 fontSize 22, lineHeightPx 40 → ratio 1.818 (목포플레이파크 line 42 실제 사례). 디자이너가 줄간격을 의도적으로 넓힌 것.
- **증상**: 1.818 → 1.8로 강제 반올림 시 0.4px 줄어들어 모바일에서 줄간격 좁아짐, 한국어 줄바꿈 조판 깨짐.
- **가드레일**: 후보 정돈 비율과의 거리 ≤ 0.05일 때만 자동 적용. 0.05~0.1은 spec.md에 "검토 필요" 마킹만, 변환은 안 함. > 0.1은 원본 그대로.

### 케이스 2: 작은 폰트 + 작은 lineHeight (UI 라벨)
- **시나리오**: fontSize 14, lineHeightPx 16.7 → ratio 1.193 (목포플레이파크 line 28 실제). 정돈 후보 1.2와 거리 0.007.
- **증상**: 1.2로 반올림 시 픽셀 차이 0.1px이지만, 해당 요소가 부모 높이 50px 안에 정확히 align되도록 디자인됐다면 vertical centering 깨짐.
- **가드레일**: bbox.h가 부모 frame 높이의 정수배에 가까운 노드는 변환 보류. 또는 픽셀 차이 ≤ 0.5px만 변환.

### 케이스 3: 다국어/혼합 폰트 (한글 + 영문)
- **시나리오**: 한 노드 안에 한글 700 + 영문 400 mixed (characterStyleOverrides). 폰트별 cap-height가 다르므로 디자이너가 영문 ratio만 1.46로 미세 조정.
- **증상**: 자동 반올림이 두 segment 모두 1.5로 통일 → 영문 베이스라인이 한글보다 위로 떠서 시각적 misalignment.
- **가드레일**: character_segments가 2개 이상이고 segment별 lineHeight가 다르면 변환 skip. text_node 단위 ratio만 변환하고 segment-level은 원본 보존.

## 3. 계층화된 주입 전략 (3단계)

### Layer 1 — Short Brief (인라인, 항상 포함, ≤ 800 토큰)
- 절대 금지 5개: hex8 색상, CSS Grid, inline style, line-height px, 999px radius
- Figma → CSS 변환표 6행: `lineHeightPx→ratio`, `letterSpacing→em`, `fills.color.a<1→rgba`, `cornerRadius>=min/2→50%`, `width 픽셀→flex 비율`, `paddingLR≥100→max-width`
- 검증 명령어 1줄: `python3 tools/post-impl-verify.py --spec ... --html ... --css ... --profile {basic|landing}`
- "exit 0이 아니면 commit 금지" 1줄

### Layer 2 — External Rules Reference (경로만)
- `D:/dev-base/rules/common.md` (전체 규칙)
- `D:/dev-base/rules/{basic|landing}.md` (프로젝트 타입별)
- spec sheet 경로: `extracted/{section}_spec.md` + `_spec.json`
- "위 5개 금지 항목 외 추가 케이스는 common.md 참조"

### Layer 3 — Runtime Check (에이전트 자가 검증, optional)
- 브리프 끝에: "코드 생성 후 self-check 명령을 직접 실행하고 출력을 첨부할 것"
- `grep -E '#[0-9a-f]{8}|line-height:\s*[0-9]+px|999px' output.css || echo OK`
- self-check 실패 시 에이전트가 commit 전 자체 수정 → PM 재dispatch 절약

**효과**: Layer1(~800tok) + Layer3(~200tok) = 1000 토큰 인라인. Layer2는 경로만. Gemini 컨텍스트 압박 최소화하면서 핵심 규칙 100% 전달.

## 4. 세 레이어 상호 충돌 시나리오와 방지책

### 충돌 1: 전처리기 정돈 ↔ 검증기 거부
- **시나리오**: 전처리기가 lineHeight 1.818 → 1.8 정돈, 그러나 spec.json의 `lineHeightRatio` 필드는 원본 1.818 유지. figma-validate.py의 "lineHeight 비율 일치" 검사가 CSS 1.8 vs spec 1.818 → 차이 0.018 (허용 ±0.05) → PASS. 그런데 validate-semantic.py가 "정돈 비율 외 사용 금지" 신규 규칙으로 1.818 자체를 거부 → CSS는 1.8인데 spec.md가 여전히 1.818 표시 → 에이전트가 다시 1.818로 되돌리는 핑퐁.
- **방지책**: 전처리기는 spec.json/spec.md 양쪽에 `normalized_lineHeightRatio` 필드를 동시 기록. validate-semantic은 normalized 값만 검사. figma-validate는 둘 중 하나 일치하면 PASS.

### 충돌 2: 브리프 인라인 규칙 ↔ 외부 rules 파일 불일치
- **시나리오**: rules/common.md는 업데이트됐는데 impl-request.md 인라인 규칙은 옛 버전. 에이전트가 어느 쪽을 따를지 결정 못 해 임의 선택.
- **방지책**: build-rules.py가 rules.yaml에서 impl-request.md의 인라인 섹션도 함께 자동 생성. 인라인 섹션 상단에 `<!-- AUTO-GENERATED FROM rules.yaml -->` 명시. CI에서 인라인/외부 sha256 일치 검사.

### 충돌 3: post-impl-verify 자동 재dispatch ↔ 전처리기 변환
- **시나리오**: 1차 dispatch 후 검증 실패로 재dispatch. 재dispatch 시점에 PM이 spec.json을 재추출하면 새 정규화 값이 들어와 에이전트가 다시 처음부터 작업 → 토큰 2배.
- **방지책**: 재dispatch는 동일 spec.json 해시 고정. spec 재추출은 PM이 명시적으로 트리거할 때만. 재dispatch 브리프에 "spec_hash: {sha}" 명시.

### 충돌 4: profile=basic ↔ profile=landing 자동 판정 오류
- **시나리오**: 전처리기가 단위 힌트를 `landing`(고정 px)로 주입했는데 validate-semantic은 `basic` profile로 실행되어 rem 사용 강요 → 무한 핑퐁.
- **방지책**: 프로젝트 루트에 `.project-type` 파일(basic/landing) 1줄. 모든 도구가 이 파일을 단일 소스로 참조. spec.json 헤더에도 `project_type` 필드 복사.

### 충돌 5: 검증기 강화 ↔ 기존 통과 코드 회귀
- **시나리오**: validate-semantic에 신규 규칙 추가 → 기존 PASS 프로젝트들이 일제히 FAIL → 대량 재작업.
- **방지책**: 신규 규칙은 `--profile strict`에만 추가. 기존 프로젝트는 default profile 유지. 신규 REQ부터 strict 적용.

---

**핵심 권장**: 세 레이어 동시 강화 시 가장 큰 위험은 "전처리기 변환값 ↔ 검증기 기대값 ↔ 브리프 규칙"의 3자 sha 불일치다. 모든 변환/검사/주입은 단일 spec.json을 source of truth로 하고, 변환된 값은 항상 `original_*` + `normalized_*` 두 필드로 병기해야 어느 도구가 봐도 모순이 없다. 재dispatch 강화는 **patch-only 모드**가 필수 — 전체 재생성 허용 시 비용 폭증과 회귀 루프를 동시에 부른다.

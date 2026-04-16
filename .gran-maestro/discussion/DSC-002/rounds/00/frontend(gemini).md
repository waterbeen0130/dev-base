# Frontend-rules 관점 의견 — DSC-002 Round 0

## 1. 에이전트 인지 실패 원인 진단
위반 사항들은 크게 3가지 에이전트 인지 한계에서 기인합니다.

- **Figma 충실도 최우선 편향 (Over-reliance on Raw Data)**: `1.193` 같은 비정돈 line-height, hex8 (`#ffffff26`) 직접 사용 등. 에이전트는 명시적인 '가공/반올림' 지시가 없으면 제공된 raw JSON 값을 원본 그대로 주입하는 것이 가장 충실한 결과라고 판단합니다.
- **프로젝트 타입(단위체계) 혼동**: landing(px전용)과 basic(rem/px 혼용) 규칙이 섞이는 현상. 현재 작업 스코프가 어떤 타입인지 명시적인 힌트가 부족하여, 에이전트가 일반적인 패턴이나 최근 기억에 의존해 폴백(fallback)을 선택한 결과입니다.
- **Scope 밖 규칙 망각 (Context Window/ADSC-002 Round 0 논의에 대한 Frontend-rules 관점의 의견 작성을 완료했습니다. 

`/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/rounds/00/frontend(gemini).md` 파일에 요청하신 4가지 질문(인지 실패 원인, 브리프 재작성안 및 샘플, 우선순위 명시 방법, 프로젝트 타입 판정 힌트 위치)에 대한 답변을 2000자 이내로 정리하여 저장했습니다.
� 합니다.

**구조 제안**:
1. **메타 정보**: 프로젝트 타입 명시
2. **Figma → CSS 강제 변환 표**: 에이전트의 '직역'을 막는 안전장치
3. **CRITICAL 금지 패턴**: 자주 위반하는 3~4개 항목만 O/X 코드 예시로 제공

**브리프 적용 샘플 (Markdown)**:
```markdown
## [CRITICAL] 원본 충실도보다 CSS 컨벤션(정규화) 준수가 무조건 우선합니다.

### 1. Figma 속성 강제 변환 (직역 금지)
- **Line-height**: `lineHeightPx / fontSize` 계산 후 **가장 가까운 0.1 단위 정돈 비율로 반올림** 적용. (예: 47/40=1.175 → 1.2로 기입. 허용값: 1.1~1.8)
- **Colors**: hex8(`#ffffff26`) 형태는 절대 사용 금지. 투명도는 반드시 `rgba(255, 255, 255, 0.15)`로 변환.

### 2. 금지 패턴 O/X
- [X] `font-family`, `box-sizing` 개별 요소 반복 지정 / [O] `*` 또는 `body`에 1회만 지정
- [X] 미디어쿼리 내부 들여쓰기 / [O] 들여쓰기 없이 컬럼 0부터 작성
- [X] `<section>`에 좌우 padding 직접 부여 / [O] 내부 wrapper에 `max-width` 및 `margin: 0 auto` 적용
```

## 3. 원본 충실도 vs 규칙 준수 최우선순위 선언
에이전트가 망설이지 않도록 위 샘플처럼 브리프 최상단에 강제 우선순위를 명문화해야 합니다.
`"원본 픽셀 충실도보다 CSS 컨벤션(정규화, 반올림) 준수가 최우선입니다."`

## 4. 프로젝트 타입 자동 판정 힌트 심기
에이전트가 맥락을 잃지 않도록 교차 검증 가능한 위치에 힌트를 배치해야 합니다.
1. **`spec.md` 및 `spec.json` 최상단 메타데이터**: 파싱 데이터 자체에 포함
2. **`impl-request.md` 헤더**: `- Project Type: {{PROJECT_TYPE}}` 변수 주입
3. **HTML 파일 첫 줄 주석**: `<!-- [Project Type: landing] Use PX only -->` (HTML 컨텍스트 내 지속적인 앵커 역할)EXIT_CODE:0

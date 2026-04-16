# DSC-002 Round 0 — 공유 컨텍스트

## 주제
Figma→퍼블리싱 파이프라인이 `D:/dev-base/rules/common.md`, `basic.md`, `landing.md`를 **완벽하게** 준수하도록 만드는 최상의 방법에 합의한다.

## 발단: 두 프로젝트 결과물에서 발견된 실제 위반 (증거)

### 프로젝트 A — 에이스디펜스 (`/mnt/d/위링/2026-04-15 에이스디펜스/html`)
파일: `css/common.css` (243 lines), `page/index.html` (238 lines)

**위반 목록 (실측)**:
1. **단위 체계 혼재**: 전체가 `rem` 기반이나 `html{font-size:clamp(14px,1.2vw,16px)}` (line 19) — `clamp+vw 단독` + `calc/vw 단독 사용` 규칙 위반 가능성.
2. `font-family:'Pretendard',sans-serif` — `body` + `*` 중복 선언 (line 20–21).
3. `<i class="mv_cover">` 같이 장식용 `<i>` 태그를 `::before` 대신 사용 — semantic 논쟁 여지.
4. 반응형은 1200/1024/768 3단계 구현되어 있으나 px 값만 기술.

### 프로젝트 B — 목포플레이파크 (`/mnt/d/위링/2026-04-15 목포플레이파크/html`)
파일: `css/common.css` (79 lines), `page/index.html` (82 lines)

**위반 목록 (실측)**:
1. **hex8 색상 직접 사용**: `#ffffff26` (line 28) — 규칙 "hex 전용, 투명도 필요 시만 rgba()".
2. **line-height 비정돈 비율**: `1.193` (line 28), `1.667` (line 28/67/68), `1.818` (line 42), `1.471` (에이스와 공통 line 107) — Figma `lineHeightPx/fontSize`를 직역한 값. 규칙 "무단위 정돈 비율(예 1.3, 1.45)".
3. **font-family 규칙별 중복 선언**: 거의 모든 rule에 `font-family:'Pretendard',sans-serif` 또는 `'NanumSquare Neo',sans-serif` 반복 (약 20회). `*{}` 공통 처리 미적용.
4. **빈 미디어쿼리 블록** (line 72–79): 1200/1024/768 전부 `{}` 비어있음 — 반응형 **완전 미구현**.
5. **`box-sizing:border-box` 반복**: 거의 모든 주요 블록에 개별 선언 — reset 전역 처리 안 됨.
6. **landing 단위체계 불일치**: landing 규칙은 "PC/모바일 고정 px" 또는 "basic PC rem/모바일 px". 현재는 고정 px 위주인데 `html,body{font-size:clamp(14px,1.2vw,16px)}` (line 10) 혼재.
7. **CSS 변수 없이 반복 색상**: `#212121`, `#424242` 등 중복 — common.md의 CSS 변수 패턴 미적용.

## 근본 원인 가설 (discussion에서 검증할 대상)

- **H1**: 규칙이 impl-request.md에 인라인 주입되어도 외주 에이전트(Gemini)가 "Figma 원본 충실도"를 규칙보다 우선시한다.
- **H2**: `tools/validate-semantic.py`의 검사 커버리지가 부족하여 hex8 / 비정돈 line-height / 중복 font-family / 빈 미디어쿼리 / 단위체계 불일치를 catch 하지 못한다.
- **H3**: `tools/post-impl-verify.py`의 분류가 CRITICAL/MAJOR 중심이라 MINOR 컨벤션 위반은 자동 재dispatch되지 않는다.
- **H4**: `tools/figma-section-spec.py`가 Figma raw value를 그대로 spec.json에 넣어 에이전트가 직역하게 만든다. 전처리(반올림/정돈/변환)가 없다.
- **H5**: landing/basic 프로젝트 타입에 따른 단위 규칙 분기가 에이전트 판단에 맡겨져 있다.

## 이번 논의의 목표 (합의 대상 결정사항)

### 세 레이어 병행 강화 (사용자 이미 승인)
- **레이어 A — 검증기 강화**: `validate-semantic.py`에 추가할 검사 규칙 목록과 각 규칙의 심각도(CRITICAL/MAJOR/MINOR). false-positive 위험 높은 규칙 식별.
- **레이어 B — 규칙 주입 강화**: `rules/templates/publishing/impl-request.md` / `impl-request.md` 개선 방법. 금지 패턴 인라인 예시, Figma 속성→CSS 변환표 포함 여부.
- **레이어 C — 전처리기 강화**: `tools/figma-section-spec.py`에 추가할 정규화 로직. lineHeightPx→정돈 비율 반올림 알고리즘, hex8→rgba 변환, 프로젝트 타입에 따른 단위 힌트 주입.

### 구체 합의 항목
1. 각 레이어에 포함시킬 **구체적 검사/주입/변환 항목 최종 리스트**.
2. 세 레이어의 **실행 순서 및 의존성** (어느 것부터 구현하면 나머지 부담이 줄어드나?).
3. **재dispatch 정책 재정의**: MINOR까지 자동 재dispatch할지, 재시도 횟수, escalation 기준.
4. **post-impl-verify 카테고리 재분류**: 발견된 6가지 위반을 어디에 매핑할지.
5. **landing/basic 자동 판정 로직**: 프로젝트 구조로 판단할지, 초기화 시 태그를 박아둘지.
6. **전처리기가 너무 적극적으로 Figma 값을 변형할 때 "원본 충실도 훼손" 리스크를 어떻게 제어할지**.

## 핵심 트레이드오프 (반드시 논의할 것)

- **검증기 강화 ↔ false-positive 증가** — 정돈되지 않은 비율(line-height 1.23 등)은 디자인 의도일 수 있음.
- **규칙 주입 강화 ↔ 브리프 비대화** — impl-request.md가 너무 길면 에이전트 컨텍스트 압박.
- **전처리기 강화 ↔ Figma 원본 충실도 훼손** — 자동 반올림이 의도한 간격을 바꿀 수 있음.
- **재dispatch 강화 ↔ 토큰/시간 비용** — MINOR까지 재시도하면 비용 폭증.

## 이번 라운드 질문 (역할별 프롬프트에서 구체화)
- 각 발견 위반을 어느 레이어에서 어떻게 처리해야 하는가?
- 세 레이어 중 구현 우선순위는?
- 놓친 근본 원인 또는 더 나은 구조적 대안이 있는가?

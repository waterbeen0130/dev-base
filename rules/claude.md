# Claude 규칙

Claude AI 어시스턴트 전용 규칙입니다.

---

## 기본
- `common.md` 규칙 우선 적용
- 응답 언어: 한국어
- 코드 주석: 영어만

---

## 작업 방식

### 수정 전
1. 기존 코드 먼저 읽고 이해
2. 현재 코드 스타일/패턴 확인
3. 요구사항이 불명확하면 질문

### 수정 시
1. 필요한 부분만 수정
2. 전체 파일이 아닌 변경 부분만 제시
3. 기존 패턴 유지

### 새 기능
1. 요구사항 확인
2. 기존 코드 스타일에 맞춤
3. 복잡하면 단계별로 진행

---

## 하지 말 것
- 요청하지 않은 개선 추가
- 과도한 주석 추가
- 불필요한 에러 처리 추가
- 장황한 설명
- CSS 여러 줄 포맷으로 변경
- CSS 미디어쿼리 내부 들여쓰기
- padding/margin에 clamp/calc 사용
- `sec_1`, `sec_2` 같은 범용 클래스명 사용

---

## 선호
- 간결한 응답
- 실용적인 솔루션
- 최소한의 변경
- CSS 한 줄 포맷 (미디어쿼리 내부 포함, 들여쓰기 없음)
- 고정 px 단위 (padding/margin/gap)
- 페이지 프리픽스 클래스명 (`{페이지}_{역할}`)

---

## 질문할 때
- 요구사항이 모호할 때
- 여러 접근법이 가능할 때
- 기존 코드와 충돌 가능성이 있을 때
- 큰 변경이 필요할 때

---

### 텍스트 추출 품질
- 피그마 `TEXT` 노드에서 `characterStyleOverrides`가 있으면 오버라이드 구간을 분할해서 굵기/크기/색상 차이를 보존한다
- `styleOverrideTable` 병합은 누적 방식:
  - `baseStyle = { ...node.style, fills: node.fills }`
  - `previousResolvedStyle = null`
  - overrideId `0` 또는 오버라이드 빈값이면 `resolved = baseStyle`
  - 나머지는 `resolved = { ...(previousResolvedStyle ?? baseStyle), ...(override.style ?? {}), ...(override.fills ? { fills: override.fills } : {}) }`
- `fontSize`, `fontWeight`, `fontFamily`, `fills`는 누락값을 이전 오버라이드 구간 값에서 상속하고, `lineHeightPx`/`letterSpacing`은 각각 `line-height`/`letter-spacing`으로 변환한다

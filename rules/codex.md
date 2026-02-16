# Codex 규칙

GitHub Copilot, Cursor 등 Codex 기반 AI 전용 규칙입니다.

---

## 기본
- `common.md` 규칙 우선 적용
- 코드 주석: 영어만

---

## 코드 스타일

### HTML
- 시맨틱 태그 사용
- 들여쓰기: 4 spaces
- BEM 또는 프로젝트 네이밍 컨벤션 따름

### CSS
- **한 줄 포맷**으로 작성 (미디어쿼리 내부 포함)
- **미디어쿼리 내부 들여쓰기 없음**
- 들여쓰기 없음 (미디어쿼리 블록 내부)
- 클래스명: **페이지 프리픽스 형식** (`{페이지}_{역할}`)
- `sec_1`, `sec_2` 같은 범용 이름 금지
- ul/ol/li/p 같이 구조 태그에 의존한 스타일은 최소화하고, 필요 시 `section_ul`, `section_li`, `section_p` 형태의 명시적 클래스 스타일로 대체한다.
- padding/margin/gap: 고정 `px` (clamp, calc, vw 금지)
- 단축 속성 사용

```css
/* correct */
@media screen and (max-width: 768px) {
.main_about { padding: 60px 0; }
.main_about .tit h2 { font-size: 28px; }
}

/* wrong */
@media screen and (max-width: 768px) {
    .sec_1 { padding: clamp(60px, calc(120 / 1920 * 100vw), 120px) 0; }
}
```

### JavaScript
- ES6+ 문법
- 들여쓰기: 4 spaces
- 세미콜론 사용
- const/let 사용 (var 금지)

---

## 자동완성 힌트

### 주석으로 의도 전달
```javascript
// remove duplicates from array
const unique = [...new Set(arr)];

// format date as YYYY-MM-DD
const formatDate = (date) => { ... }
```

### 함수명 예시
- `getUserById` - ID로 사용자 조회
- `validateEmail` - 이메일 유효성 검사
- `formatPrice` - 가격 포맷 (콤마 추가)

---

## 선호 패턴

### 조건문
```javascript
// ternary for simple cases
const status = isActive ? 'active' : 'inactive';

// early return for complex cases
if (!user) return null;
```

### 반복문
```javascript
// prefer map, filter, reduce
const names = users.map(user => user.name);
const adults = users.filter(user => user.age >= 18);
```

### 비동기
```javascript
// prefer async/await
const data = await fetchData();
```

---

## 피할 것
- 깊은 중첩
- 매직 넘버/문자열
- 과도한 추상화
- 불필요한 의존성
- CSS 여러 줄 포맷
- CSS 미디어쿼리 내부 들여쓰기
- padding/margin에 clamp/calc 사용
- `sec_1`, `sec_2` 같은 범용 클래스명

### 텍스트 추출 품질
- 피그마 `TEXT` 노드는 `characterStyleOverrides`와 `styleOverrideTable`를 함께 해석해서 오버라이드 단위로 분리 출력
- 스타일이 달라지는 구간만 `span`으로 분리해 기본 클래스와 함께 적용하고, 색/두께/크기 변화를 보존
- `styleOverrideTable` 항목이 `fontSize`, `fontWeight`, `fontFamily` 등을 누락한 경우(예: `lineHeight`만 있는 오버라이드)는 이전 오버라이드 구간의 실제 적용 스타일을 기준으로 누락값을 상속해 병합한다
- 오버라이드가 존재하는 텍스트는 `characterStyleOverrides` 전체 일치만으로 “정상 추출 완료” 판정하지 않고, 수동으로 굵기/크기/색상 구간을 1차 점검한다
- 오버라이드가 적용되는 구간은 가능하면 인라인 `style` 대신 class 분리 출력한다.
- 동일 스타일은 `t1`, `t2` 처럼 짧은 공통 텍스트 클래스(`figma-inline-style-map`)로 병합한다.
- 강제 병합 규칙:
  - `baseStyle = { ...node.style, fills: node.fills }`
  - `previousResolvedStyle = null`
  - 오버라이드 id가 0 또는 누락 → `resolved = baseStyle`
  - 오버라이드 id가 존재 → `resolved = { ...(previousResolvedStyle ?? baseStyle), ...(override.style ?? {}), ...(override.fills ? { fills: override.fills } : {}) }`
  - 출력 시 `resolved`를 기준으로 계산하고 `previousResolvedStyle = resolved`로 갱신
  - `fontSize`, `fontWeight`, `fontFamily`, `fills`의 누락값은 `previousResolvedStyle` 유지

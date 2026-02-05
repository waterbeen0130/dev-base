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

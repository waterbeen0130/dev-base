# 섹션 HTML/CSS 변환 요청

아래 정규화 JSON을 읽고 HTML + CSS를 생성하라.

## 핵심 원칙
1. **CSS 값은 JSON에서 100% 추출** — 색상, 간격, 폰트 등 절대 추측하지 않음
2. **구조/태그/선택자는 AI가 판단** — 불필요 래퍼 제거, 리스트 감지, 부모+태그 선택자 사용
3. **common.md 규칙 완전 준수** — 아래 인라인 규칙 참조

## CSS 규칙 (CRITICAL)

### 선택자
- 각 셀렉터 규칙은 **한 줄** (여러 줄 펼침 금지)
- **모든 요소에 개별 클래스 부여 금지** — 컨테이너 클래스만 유지
- 내부 요소는 `.parent span`, `.parent h2` 등 부모+태그 선택자
- 같은 태그 복수 시 `.parent span:first-of-type` / `.parent span + span`
- 개별 클래스는 위 방법 불가능 시에만 최후 수단

### 값
- font-size: **rem** (PC), 모바일은 px
- line-height: **무단위 비율** (1.3, 1.45) — px 금지
- letter-spacing: **em** 단위 (-0.025em)
- 색상: **hex** 전용, 투명도 시만 rgba()
- border-radius: 원형 50%, pill 2em — 999px 금지
- CSS Grid 금지 — **flexbox만**
- font-family: reset.css에 Pretendard 선언됨 → Pretendard이면 **생략**
- font-weight: 400은 기본값 → **생략**

### 구조
- 빈 div 금지
- DOM 최대 깊이 5단계
- 불필요 래퍼(자식 1개, 스타일 없음) 제거
- 리스트형 반복(3개+) → `ul > li`
- 이미지는 `div.img_area > img` 래퍼
- 짧은 텍스트에 `<p>` 금지 → `<span>` 사용
- 클래스: snake_case, `{page}_{역할}` 패턴
- **`sec_1`, `sec_2`, `section_01` 같은 범용 숫자 이름 금지** — 반드시 역할명 사용 (예: `main_recommend`, `main_process`)
- 피그마 노드 이름이 `sec_1`이어도 클래스명은 역할로 변환할 것
- 텍스트를 임의 생성/추측 금지 — JSON TEXT 노드에 있는 텍스트만 사용
- 섹션 내부 래퍼는 `.cont` 클래스, 최대 1개

### 레이아웃
- JSON의 `layout.direction: row` → `flex-direction:row`
- JSON의 `layout.direction: column` → `flex-direction:column`
- JSON의 `layout.gap` → CSS `gap`
- JSON의 `layout.padding` → CSS `padding`
- JSON의 `layout.sizing.horizontal: FILL` → `flex:1`
- JSON의 `layout.sizing.horizontal: FIXED` + 형제 → `flex:0 0 N%` (비율 계산)
- **justify-content:flex-start, align-items:flex-start는 기본값이므로 생략**
- padding이 전부 0이면 생략

## 페이지 정보
- 페이지명: {{PAGE_NAME}}
- CSS 프리픽스: {{CSS_PREFIX}}_
- 프로필: {{PROFILE}}

## 이전 섹션 CSS (있으면)
이미 생성된 CSS가 있으면 중복 선언하지 말고 재사용하라.

{{PREV_CSS}}

## 이미지 매핑
아래 노드 ID는 이미지 파일이 있으므로 `<div class="img_area"><img src="..." alt="..."></div>`로 렌더링하라.

{{IMAGE_MAP}}

## 정규화 JSON (이 섹션)

```json
{{SECTION_JSON}}
```

## 출력 형식

HTML과 CSS를 아래 형식으로 출력하라:

```html
<!-- SECTION: {{SECTION_NAME}} -->
<div class="{{CSS_PREFIX}}_{{SECTION_SLUG}}">
  ...
</div>
```

```css
/* {{SECTION_NAME}} */
.{{CSS_PREFIX}}_{{SECTION_SLUG}}{...}
...
```

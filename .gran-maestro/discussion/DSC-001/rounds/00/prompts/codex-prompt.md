# 퍼블리싱 규칙 충돌 분석 (HTML/CSS 규칙 전문가 관점)

당신은 HTML/CSS 규칙 충돌을 탐지하는 전문 분석가입니다.
아래 퍼블리싱 규칙 파일들(CLAUDE.md, codex.md, common.md, landing.md)과 JSON 변환 파일들(rule_engine.json, validation_schema.json)을 비교 분석하세요.

## 분석 목적
각 MD 규칙 파일을 코드 추출에 사용할 때 **서로 충돌하거나 무시될 수 있는 규칙**을 찾아내세요.

---

## 규칙 파일 원문

### 1. CLAUDE.md (Claude 전용 규칙)
```
# Claude 규칙
Claude AI 어시스턴트 전용 규칙입니다.

## 기본
- `common.md` 규칙 우선 적용
- 응답 언어: 한국어
- 코드 주석: 영어만

## 작업 방식
### 수정 전: 기존 코드 먼저 읽고 이해, 현재 코드 스타일/패턴 확인
### 수정 시: 필요한 부분만 수정, 전체 파일이 아닌 변경 부분만 제시

## 하지 말 것
- CSS 셀렉터를 여러 줄로 펼치기 (각 규칙은 한 줄로)
- CSS 미디어쿼리 내부 들여쓰기
- 미디어쿼리 안 모든 규칙을 한 줄에 이어붙이기
- padding/margin에 100px 미만 clamp 사용
- calc/vw 단독 사용
- `sec_1`, `sec_2` 같은 범용 클래스명 사용

## 선호
- CSS 각 셀렉터 규칙은 한 줄 포맷
- 미디어쿼리 블록 안에서 각 규칙은 줄바꿈 분리 (들여쓰기 없음)
- 고정 px 단위 (padding/margin/gap)
- 페이지 프리픽스 클래스명 (`{페이지}_{역할}`)

## 텍스트 추출 품질 (요약)
- characterStyleOverrides 있으면 구간 분할
- styleOverrideTable 누적 병합: baseStyle = { ...node.style, fills: node.fills }
- fontSize, fontWeight, fontFamily, fills 누락 시 이전 값 상속
- lineHeightPx → CSS line-height 비율 변환, letterSpacing → em 단위 변환
```

### 2. codex.md (Codex 전용 규칙)
```
## CSS 핵심
- 각 셀렉터 규칙은 한 줄로 작성
- 같은 셀렉터를 여러 번 선언하지 않음
- 미디어쿼리 블록 안에서 각 규칙은 줄바꿈으로 분리
- 미디어쿼리 내부 들여쓰기 없음
- font-size: PC는 rem, 모바일(768px 이하)은 고정 px
- line-height: 무단위 비율만 (1.3, 1.45, 1.6) — computed px 금지
- letter-spacing: em 단위만 (-0.025em) — px 금지
- border-radius: 원형은 50%, pill 형태는 2em — 999px 금지
- 클래스명: 페이지 프리픽스 형식, snake_case 전용
- 유틸리티 클래스 금지
- :root 변수 네이밍: --point-color-1, --font-color-1, --width, --padding 패턴
- padding/margin/gap: 고정 px
- 100px 이상 값에 한해 clamp() 허용
- 100px 미만 값은 반드시 고정 px
- calc() 단독 사용 금지, vw 단독 사용 금지
- 색상: hex 전용
- CSS Grid 금지 — flexbox만
- !important 금지
```

### 3. common.md (공통 규칙)
```
## CSS 핵심 (codex.md와 동일한 내용)
- font-size: PC는 rem, 모바일(768px 이하)은 고정 px
- 768px 이하: padding/margin은 PC 값의 절반
- 유틸리티 클래스 금지
- CSS Grid 사용 금지
- !important 사용 금지

## 레이아웃 보정 규칙 (추가)
- block 요소에 불필요한 width: 100% 금지
- Figma 고정 폭 큰 컨테이너는 max-width + margin: 0 auto
- line-height는 font-size 대비 비율로 기록
- 배경색/보더 명시되지 않은 레이어는 배경 속성 생략

## 텍스트 태그 자동 판정 규칙
- 기본 태그는 span/헤딩 계열 기준
- p 태그는 \n 포함/길이 95자 초과/문장형 마침표 반복 중 하나 충족 시만
```

### 4. landing.md (랜딩페이지 전용)
```
## Basic과 다른 점 (중요!)
- font-size: PC/모바일 모두 고정 px (rem 사용 안 함)  ← common.md와 충돌!
- padding/margin: PC/모바일 모두 고정 px
- CDN 방식 JS 사용 (로컬 파일 아님)

## 브레인바디 특화 규칙
- 같은 y를 가지는 블록이 2개라면 inline-flex 행 정렬 우선
- BrainBody, MRI 등 라벨성 키워드는 절대 p 태그로 바꾸지 않음
- Barlow Semi Condensed → "Barlow Semi Condensed", "Pretendard", sans-serif

## GSAP 애니메이션 CSS 필수 포함
[data-delay] { position: relative; transition: all 1s ease; opacity: 0; }
[data-direction="left"] { left: -40px; }
...
```

### 5. rule_engine.json (핵심 부분)
```json
{
  "css": {
    "font_size": { "pc": "rem", "mobile": "px" },
    "border_radius": { "circle": "50%", "pill": "2em or 50%" }
  }
}
```

### 6. validation_schema.json (핵심 부분)
```json
{ "checks": [
  { "type": "font_size_pc_rem", "note": "PC uses rem for font-size" },
  { "type": "no_duplicate_selector" },
  ...
  { "type": "no_duplicate_selector" }  ← 중복 등록됨!
]}
```

---

## 분석 요청

다음 관점에서 **충돌 및 무시될 수 있는 규칙**을 분석하세요:

1. **프로젝트 타입별 충돌**: Basic vs Landing 프로젝트에서 font-size 규칙(rem vs px) 충돌이 코드 추출 시 어떤 문제를 일으키는가?
2. **CLAUDE.md vs codex.md 충돌**: 두 파일에서 서로 다르거나 누락된 규칙은?
3. **common.md 기준 충돌**: landing.md가 common.md를 override하는 규칙이 명확히 표시되지 않을 때 어떤 충돌이 발생하는가?
4. **rule_engine.json의 충돌**: `border_radius.pill: "2em or 50%"`는 실제 규칙("2em만")과 어떤 충돌을 일으키는가?
5. **validation_schema.json 이슈**: `no_duplicate_selector`가 2번 등록된 문제와 랜딩 페이지 font-size 검증 부재 문제

응답 형식:
- 각 충돌 항목을 번호로 나열
- 충돌 규칙 A vs 규칙 B 형식으로 명확히 대비
- 코드 추출 시 실제 영향 설명
- 2000자 이내

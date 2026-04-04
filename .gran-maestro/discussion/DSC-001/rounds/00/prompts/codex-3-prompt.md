# 누락된 퍼블리싱 규칙 발굴 (규칙 완성도 전문가 관점)

당신은 퍼블리싱 규칙 체계의 완성도를 평가하는 전문 분석가입니다.
아래 규칙 파일들을 검토하고, rule_engine.json과 validation_schema.json에 **반드시 추가해야 할 누락 규칙**을 찾아내세요.

## 현재 MD 파일에 있지만 JSON에 없는 규칙들

### 1. 텍스트 태그 자동 판정 규칙 (common.md에만 있음)
```
- 기본 태그는 p가 아니라 span/헤딩 계열
- p 태그 사용 조건: \n 포함, 95자 초과, 문장형 마침표 반복 중 하나
```
→ rule_engine.json에 없음, validation_schema.json에 없음

### 2. Landing vs Basic 프로젝트 구분 (landing.md)
```
- font-size: PC/모바일 모두 고정 px (rem 사용 안 함)
- JS: CDN 방식
- reset.css: 별도 파일 없이 CSS 최상단에 포함
```
→ rule_engine.json의 font_size.pc는 "rem"만 명시 (landing 예외 없음)

### 3. 좌표 기반 레이아웃 추출 보정 (landing.md, common.md)
```
- 같은 부모 내 두 개 이상의 박스가 같은 y에 있고 유사한 높이 → inline-flex 행 정렬 우선
```
→ rule_engine.json에 없음

### 4. GSAP 애니메이션 CSS 패턴 (landing.md)
```
- [data-delay] 기본 opacity:0, position:relative, transition:all 1s ease
- [data-direction="left"] { left: -40px }
- .section_on [data-delay] { opacity:1 }
- GSAP 미탑재 환경 fallback 예외처리 필요
```
→ rule_engine.json structure.animation_attrs에 ["data-delay", "data-direction"]만 있고 CSS 패턴 없음

### 5. fontFamily 매핑 규칙 (landing.md 브레인바디 특화)
```
- Barlow Semi Condensed → "Barlow Semi Condensed", "Pretendard", sans-serif
```
→ rule_engine.json에 fontFamily 매핑 테이블 없음

### 6. 클래스 최소화 규칙 (landing.md, common.md)
```
- t1, g137 같은 연속 클래스 번호 기반 생성 방식 지양
- 동일 구조 블록에 클래스가 과도하면 자식 선택자 우선
- nth-child보다 의미 클래스 우선
```
→ rule_engine.json naming에 forbidden 배열만 있고, 클래스 최소화 정책 없음

### 7. 이미지 섹션 규칙 (landing.md 주의사항)
```
- 이미지 기반 섹션: 원본 이미지 픽셀 높이에 맞춰 height 지정 + object-fit: cover
- 섹션 내부 img: width: 100% % 기반 + aspect-ratio로 비율 유지
- 모바일 전용 이미지 반드시 사용
```
→ rule_engine.json에 이미지 처리 규칙 없음

### 8. 속성 순서 검증 (common.md/codex.md)
```
CSS 속성 순서: position → margin → padding → width/height → display → alignment → background → font-size → font-weight → color → 기타
```
→ rule_engine.json에 property_order 있음, 하지만 validation_schema.json에 속성 순서 검증 없음

### 9. CSS 변수 필수 패턴 (landing.md)
```
:root { --padding, --header_h, --width, --point-color-1 }
```
→ rule_engine.json에 root_var_format/naming만 있고 필수 변수 목록 없음

### 10. 모바일 padding 절반 규칙 (common.md)
```
768px 이하: padding/margin은 PC 값의 절반
```
→ rule_engine.json에 없음, validation_schema.json에 없음

---

## 분석 요청

1. **우선순위 높은 누락 규칙 TOP 5**: 코드 추출 품질에 가장 큰 영향을 미치는 누락 규칙
2. **rule_engine.json 추가 항목**: 각 누락 규칙에 대한 JSON 형식 초안 제시
3. **validation_schema.json 추가 체크**: 검증이 필요한 새 check 항목
4. **landing vs basic 분리 방안**: rule_engine.json에 프로젝트 타입별 설정을 어떻게 추가할지

응답 형식:
- 누락 규칙 TOP 5 (우선순위 순)
- 각 항목별 JSON 추가 초안
- 2000자 이내

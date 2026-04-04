# Figma→코드 변환 완성도를 위한 추가 규칙 제안

당신은 Figma 디자인을 HTML/CSS로 변환하는 자동화 품질을 전문으로 합니다.

## 현재 변환 규칙 요약

- TEXT 노드 1:1 HTML 매핑, 인접 노드 합치기 금지
- `\n` → `<br>`, `\n\n` → 블록 분리
- characterStyleOverrides → `<span>` 분리 (fontSize/fontWeight/fontFamily/fills/letterSpacing 차이 시)
- styleOverrideTable 누적 병합 (baseStyle + previousResolvedStyle)
- layoutMode VERTICAL/HORIZONTAL → flex-direction
- itemSpacing → gap, padding → CSS padding
- 구분선(divider) DOM 보존, border는 strokes.visible===true 시만
- 좌표 기반: 같은 y값 블록 2개 → inline-flex 우선

## 제안 요청 영역 (Figma→코드 변환)

아래 항목들에 대해 **현재 없지만 Figma 변환 정확도를 높일 규칙**을 제안하세요:

1. **Auto Layout 제약 처리**: `constraints` (FILL, FIXED, SCALE) → CSS 변환 규칙
2. **SVG/벡터 노드 처리**: 벡터 노드(VECTOR, ELLIPSE, POLYGON)를 img/svg 중 어떤 것으로 추출할지
3. **컴포넌트/인스턴스 처리**: Figma 컴포넌트 인스턴스가 여러 개 있을 때 반복 구조 추출 방법
4. **이펙트 스타일 매핑**: drop-shadow, inner shadow, blur effect → CSS 변환 규칙
5. **색상 스타일 변수화**: Figma 색상 스타일 → CSS 변수로 자동 매핑 규칙
6. **그라디언트 처리**: Linear/Radial gradient → CSS gradient 변환
7. **stroke 두께 및 위치**: stroke-align(center/inside/outside) → CSS border 처리

각 항목에 대해:
- 제안 규칙 내용
- 구체적 변환 예시 (Figma 노드 → HTML/CSS)
- rule_engine.json 추가 시 JSON 형식 초안

응답 형식: 번호 목록, 각 항목 3-5줄, 총 2000자 이내

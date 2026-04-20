[MST skill=ideation step=2/4 return_to=null]

# Figma Fidelity 관점 의견 요청 — IDN-002

## 공유 컨텍스트 (필수 Read)
- /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/context.md
- /mnt/d/dev-base/tools/figma-section-spec.py (추출 필드 파악)
- /mnt/d/dev-base/tools/figma-validate.py (검증 카테고리 파악)
- /mnt/d/dev-base/extracted/section_03_spec.json (현재 스키마 실제 샘플)
- /mnt/d/dev-base/extracted/section_04_spec.json

## 당신의 역할
Figma 원본 ↔ 생성 HTML/CSS 간의 **시각적·구조적 fidelity 갭**을 식별. 현재 spec이 추출하지 않기 때문에 반드시 누락되는 Figma 속성을 모두 나열.

## 질문
1. 현재 `section_spec.json`에서 **누락되어 생성물이 Figma와 달라질 수밖에 없는 필드**를 카테고리별로 열거하라:
   - (a) 시각 효과: effects(shadow/blur), opacity, blendMode
   - (b) 채우기: linear/radial gradient, image fill(imageRef, scaleMode, crop)
   - (c) 테두리/모서리: strokes, strokeWeight, strokeAlign, cornerRadius(개별 corner 포함)
   - (d) 텍스트: characterStyleOverrides, textCase, textDecoration, paragraphSpacing
   - (e) 자동 레이아웃 디테일: layoutSizingHorizontal/Vertical, layoutAlign, layoutGrow
   - (f) 제약/반응형: constraints, layoutMode가 null인 absolute 배치
   - (g) 아이콘/벡터: SVG export path vs raster
   - (h) 컴포넌트 인식: componentId, 반복 인스턴스
   각 항목에 대해 "Figma는 X를 가지고 있는데 spec에 없으면 생성물은 Y로 깨진다"는 형태의 구체적 실패 사례 서술.
2. 9개 카테고리로 검증하는 figma-validate.py가 **놓치는 fidelity 축** 나열 (위 1번과 대응).
3. 이 갭을 메우기 위해 figma-section-spec.py에 우선 추가해야 할 **Top 5 필드** + 각각을 CSS로 매핑하는 규칙 제안.
4. 실제 section_03/section_04 spec에서 **이미 시각 효과·그라디언트·이미지가 누락된 증거**가 보이면 id 번호와 함께 지적.

## 출력 요구사항
- 파일로 저장: /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-figma-fidelity(codex).md
- 2000자 이내, 한국어, 표와 불릿 적극 활용
- 마지막에 "## 필드 추가 우선순위 Top 5" 목록
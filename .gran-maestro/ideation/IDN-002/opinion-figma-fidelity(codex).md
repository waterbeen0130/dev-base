# IDN-002 Figma Fidelity 의견 (Codex)

## 1) section_spec 누락 필드와 깨짐
|축|누락 필드|깨짐 예시|
|---|---|---|
|a 효과|`effects`,`blendMode`,`opacity`|shadow/blur/합성 소실으로 평면화|
|b 채우기|gradient(`type/stops/handles`), image(`imageRef/scaleMode/crop`)|그라디언트 각도·스톱, 이미지 크롭·포커스 오차|
|c 테두리|`strokes`,`strokeWeight`,`strokeAlign`, 개별 corner|보더 두께/정렬, pill radius 불일치|
|d 텍스트|`characterStyleOverrides`,`textCase`,`textDecoration`,`paragraphSpacing`|부분 스타일, 대소문자, 밑줄, 문단 간격 손실|
|e 오토레이아웃|`layoutSizingH/V`,`layoutAlign`,`layoutGrow`|HUG/FILL/FIXED 및 자식 확장 오차|
|f 반응형|`constraints`, `layoutMode:null` absolute 규칙|해상도 변경 시 위치 드리프트|
|g 아이콘|SVG path/export 메타|벡터를 래스터/빈 img 처리로 선명도 저하|
|h 컴포넌트|`componentId`,`componentSetId`, instance 정보|반복 요소 재사용 실패, 클래스 난립|

## 2) figma-validate(9개) 미검증 축
- 현재 9개: 텍스트 무결성, 폰트5, lineHeight, color, padding/gap, clamp, column-gap 금지, interaction URL.
- 미검증: a~h 전체(효과/gradient-image/stroke/텍스트 고급속성/auto-layout sizing/constraints/SVG/컴포넌트).

## 3) extractor 우선 추가 필드 + CSS 매핑
|필드|매핑|
|---|---|
|`fills[]`(gradient+image)|`background`(linear/radial-gradient), `background-image/size/position`|
|`effects[]`|`box-shadow`, `filter:blur()`, `backdrop-filter`|
|`strokes*`|`border/outline` + 필요 시 pseudo-element|
|`layoutSizing* + layoutGrow + layoutAlign`|`fit-content`, `flex:1`, `align-self`|
|`constraints`|`position:absolute` + `inset/transform` anchor|

## 4) section_03/04 누락 증거(id)
- `842:196`(Section_04): `fills`가 해시(`7257...`)인데 `images`가 `{}` -> image URL/scale/crop 없음.
- `842:84`,`842:87`,`842:197` 등: `fills`가 `null`/단일값만 존재, `effects/gradient/blendMode` 키 없음.
- `842:133`(div.cmp-icon:margin) 존재 대비 `vector_nodes` 없음 -> 아이콘 fidelity 검증 불가.

## 필드 추가 우선순위 Top 5
1. `fills[]`(gradient/image 상세)
2. `effects[]`
3. `strokes`/`strokeWeight`/`strokeAlign`
4. `layoutSizingHorizontal/Vertical` + `layoutGrow` + `layoutAlign`
5. `constraints` (absolute 배치 포함)
EXIT_CODE:0

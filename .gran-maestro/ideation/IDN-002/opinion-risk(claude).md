# Risk Analyst 의견 — IDN-002

## 1. Figma 요소 누락/왜곡 Top 10 실패 시나리오

| # | Figma 입력 | 현재 파이프라인 출력 | 실제 기대 | 심각도×가능성 |
|---|-----------|---------------------|----------|------------|
| 1 | fills.type=IMAGE (배경 이미지) | hex 필드만 추출, imageRef 무시 | background-image: url(...) | High×High |
| 2 | characterStyleOverrides (인라인 굵기/색) | characters 전체를 단일 스타일로 처리 | `<strong>` 또는 별도 span | High×High |
| 3 | linearGradient fill | 단색 hex 또는 null 추출 | linear-gradient(deg, ...) | High×Med |
| 4 | drop-shadow effect | effects 필드 미추출 | box-shadow/filter: drop-shadow | Med×High |
| 5 | cornerRadius 개별 값 (top-left만 8px) | 단일 border-radius로 처리 | border-radius: 8px 0 0 0 | Med×Med |
| 6 | layoutSizingHorizontal=FILL (부모 채움) | 고정 bbox.w 사용 → flex:1 미적용 | flex:1 또는 width:100% | High×High |
| 7 | strokes (선 테두리) | 완전 누락 | border: Npx solid #hex | Med×High |
| 8 | textCase=UPPER | characters 원문 소문자 추출 | CSS text-transform:uppercase | Med×Med |
| 9 | opacity < 1 (레이어 투명도) | 불투명 hex로 변환 | rgba() 또는 opacity 속성 | Med×Med |
| 10 | VERTICAL frame + itemSpacing (패딩 아님) | gap으로 주입 → column flex gap 금지 규칙 위반 | margin-bottom 또는 gap 없음 | Med×High |

---

## 2. JSON Schema 공식화의 역효과

### (a) Figma 스키마 외 신규 필드 추가 시 [High×Med]
- strict additionalProperties:false 선언 시 신규 Figma 노드 타입(예: SECTION, STICKY) 진입 시 figma-section-spec.py 전체 파싱 실패
- 완화책: additionalProperties:true + unknown 필드는 `_extra` 키에 보존

### (b) 기존 섹션과의 하위호환 깨짐 [High×Med]
- schema_version 1 spec.json에 required 필드 추가 시 기존 extracted/ 산출물이 validator에서 즉시 실패
- PLN-008 이전 커밋의 spec.json이 모두 재생성 강제 → 대규모 재작업 유발

### (c) Validator false-positive 폭증 [Med×High]
- 현재 figma-validate.py 9개 카테고리 중 "signature 없음" IGNORE 처리가 있음
- 스키마 required 강화 시 padding=0인 frame도 "gap 미반영"으로 오판 가능
- VERTICAL frame + itemSpacing=0 케이스는 gap:0 CSS가 없으면 false-positive 발생

### (d) 에이전트의 창의적 해석 차단 [Med×Med]
- spec.json이 구체화될수록 "값 없으면 구현 금지" 규칙이 묵시적으로 강화됨
- 예: Figma에서 hover 효과가 interactions에 없으나 UI 관행상 필요한 경우 스키마 과최적화 에이전트는 구현 생략

---

## 3. 이미지/벡터/폰트 자원 파이프라인 리스크

| 리스크 | 심각도×가능성 | 설명 |
|-------|------------|------|
| imageRef 해상도 결정 불확실 | High×High | Figma export scale 미지정 시 1x/2x 중 무작위 선택 → Retina 대응 실패 |
| 아이콘 SVG export 저작권 | Med×Med | Figma 내 구매 플러그인/유료 아이콘셋의 SVG 경로는 라이선스 위반 가능 |
| 웹폰트 CDN 의존 | Med×High | Google Fonts URL을 spec에 하드코딩 시 CDN 장애=전체 폰트 실패 |
| 폰트 라이선스 | High×Low | Figma에서 사용한 상업 폰트를 웹 embed 시 별도 라이선스 필요 (OFL 비해당 폰트) |
| crop transform 미지원 | Med×Med | Figma image fill의 scaleMode=CROP은 CSS object-position 매핑 필요하나 현재 파이프라인 미구현 |

---

## 4. "PM 코드 수정 금지" vs "긴급 수정 상황" 충돌

**충돌 시나리오** [Med×High]:
- 외주 에이전트 max_cli_retries 소진 후에도 CRITICAL 위반 1건 잔여
- 사용자가 즉시 배포 요구
- CLAUDE.md는 "외주 에이전트 소진 후에만 PM 직접 개입 예외" 허용

**숨겨진 리스크**:
- "예외 조건"이 모호 → PM이 편의상 직접 수정 관행화 위험
- PM이 직접 CSS 수정 시 rules.yaml 규칙을 읽지 않고 진행할 가능성
- 긴급 수정 내역이 외주 브리프에 반영되지 않아 다음 재dispatch 시 덮어쓰기 발생

**필요한 보호 장치**: 긴급 개입 시 `[PM-DIRECT-FIX]` 커밋 태그 + 외주 브리프에 변경 사항 역기록 의무화

---

## 5. 검증 2단 통과 ≠ 시각적 동일성

| 예시 | 통과 이유 | 실제 차이 |
|-----|---------|---------|
| 배경 이미지 누락 | hex fill이 없으면 fills 검증 PASS | Figma에선 photo, HTML은 단색 배경 |
| lineHeightRatio ±0.05 허용 | 수치 범위 내 통과 | 멀티라인 텍스트 1줄 높이 차이 누적 |
| clamp 적용 ≥100px | 수치 통과 | clamp 범위 min/max가 디자인 의도와 다름 |
| VERTICAL frame gap 금지 규칙 | gap:0 또는 gap 없음 통과 | margin-bottom 미적용 → 요소 간격 0 |
| SVG 아이콘 → PNG 대체 | validator는 img src만 확인 | 벡터 품질 손실, 다크모드 미대응 |

---

## 개선 추진 시 사전 차단해야 할 리스크 Top 5

1. **[High×High] imageRef/linearGradient 완전 누락** — fills.type=IMAGE, gradientStops가 spec에서 hex 치환되어 배경 이미지/그라디언트가 코드에서 사라짐. spec.json fills 스키마를 type 분기 구조로 교체 필수.

2. **[High×High] layoutSizingHorizontal=FILL 미반영** — bbox.w 고정값이 flex:1 대신 고정 px로 생성되어 반응형 레이아웃 전체 붕괴. spec에 `sizingHorizontal`/`sizingVertical` 필드 추가 필수.

3. **[High×Med] schema_version 강화 시 기존 spec.json 전량 무효화** — required 필드 추가 전에 마이그레이션 스크립트와 버전 분기 처리 없이 배포 시 이전 extracted/ 산출물이 figma-validate.py에서 전량 실패.

4. **[High×Med] characterStyleOverrides 미처리로 인라인 텍스트 스타일 손실** — 특히 한 문장 내 굵기/색상 혼용 디자인에서 spec.json이 단일 스타일로 압축되어 검증도 통과하지만 시각적으로 완전히 다름.

5. **[Med×High] VERTICAL frame itemSpacing이 gap 금지 규칙과 충돌** — spec.json에 gap 값이 있으나 rules.yaml이 column flex gap 금지이므로 외주 에이전트가 어느 쪽을 따를지 명확하지 않음. spec vs rules 우선순위를 명문화하지 않으면 재dispatch 반복 루프 발생.

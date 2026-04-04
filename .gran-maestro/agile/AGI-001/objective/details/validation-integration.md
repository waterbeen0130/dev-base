# 검증 연동

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-006, DOD-007

## 개요

정규화 엔진의 출력과 기존 validate.js(67개 검증 규칙) 체계를 연동하여 자동 품질 검증을 수행하고, 정규화 과정의 규칙 적용 로그를 추적 가능하게 한다.

## 설계 결정

### AD-005: 기존 검증 체계 확장 (신규 도구 X)
- **결정**: validate.js + figma-checks.js 기존 구조를 확장하여 정규화 엔진 출력 검증을 추가
- **근거**: 이미 67개 검증 규칙이 체계적으로 구성되어 있음. 새 검증 도구를 만들기보다 기존 체계에 정규화 관련 검증을 추가하는 것이 효율적
- **대안 검토**: Python 기반 별도 검증기 — 기각: 이중 관리 부담
- **영향 범위**: validate.js, validation_schema.json, figma-checks.js

## 상세 명세

### 1. 현재 검증 체계 구조

```
validate.js (5.4KB)
├── validation_schema.json (67개 체크 정의)
├── checks/
│   ├── html-checks.js (7개 HTML 검증)
│   ├── css-checks.js (25+ CSS 검증)
│   └── figma-checks.js (20+ Figma 매핑 검증)
```

실행 방식:
```bash
node validate.js --html output.html --css output.css --type basic|landing
node validate.js --html output.html --css output.css --mapping mapping.json --type basic
```

### 2. 정규화 엔진과의 연동 지점

#### 2.1 정규화 중간 JSON → mapping.json 호환

현재 `to_json_mapping()` 출력과 정규화 중간 JSON의 관계:
- 기존 mapping.json: 노드별 `{ figma: {...}, css: {...} }` flat 구조
- 정규화 중간 JSON: 트리 구조 + CSS 값 포함

연동 방안: 정규화 엔진이 validate.js 호환 mapping.json도 함께 출력하는 옵션 추가
```bash
python3 figma-extract.py --stdin --profile basic --output ./ --emit-mapping
```

#### 2.2 값 비교 검증 (figma-checks.js)

기존 6개 값 비교 체크:
- `figma_value_gap_match`: itemSpacing ↔ CSS gap
- `figma_value_padding_match`: padding ↔ CSS padding
- `figma_value_color_match`: fills ↔ CSS color/background
- `figma_value_font_match`: fontSize/fontWeight ↔ CSS font
- `figma_value_border_match`: strokes ↔ CSS border
- `figma_value_radius_match`: cornerRadius ↔ CSS border-radius

정규화 엔진 도입 후: 중간 JSON에 CSS 값이 확정되어 있으므로, 최종 HTML/CSS가 중간 JSON의 값을 정확히 반영했는지 검증 가능.

#### 2.3 구조 검증 (추가 가능)

정규화 중간 JSON의 트리 ↔ 최종 HTML DOM 구조 비교:
- 노드 수 일치 확인
- 부모-자식 관계 일치 확인
- 텍스트 오버라이드 세그먼트 수 일치 확인

### 3. 로그 추적 (DOD-007)

정규화 엔진 실행 시 각 노드별로 적용된 규칙을 로그로 출력:

```
[NORM] node "hero_title" (TEXT)
  [RULE] fontSize: 32px → 2rem (profile:basic, base:16px)
  [RULE] lineHeightPx: 44.8 → line-height: 1.4 (ratio conversion)
  [RULE] letterSpacing: -0.5 → letter-spacing: -0.016em (em conversion)
  [RULE] fills → color: #090944 (hex conversion)
  [RULE] characterStyleOverrides: 2 segments detected
    [SEG-0] "Brand " base style (fontWeight:700)
    [SEG-1] "Name" override (fontWeight:400, color:#ff0000)

[NORM] node "hero_wrap" (FRAME)
  [RULE] layoutMode: VERTICAL → flex-direction: column
  [RULE] itemSpacing: 24 → gap: 24px
  [RULE] padding: [60,40,60,40] → padding: 60px 40px
  [RULE] primaryAxisAlignItems: CENTER → justify-content: center
  [RULE] counterAxisAlignItems: CENTER → align-items: center
```

로그 레벨:
- `--verbose`: 모든 노드의 모든 규칙 출력
- 기본: 변환이 적용된 노드만 출력
- `--quiet`: 경고/에러만 출력

### 4. 검증 결과 리포트

validate.js의 기존 출력 형식 (PASS/FAIL/WARN/SKIP)에 정규화 관련 항목 추가:

```
=== Validation Report ===
[PASS] no_inline_style
[PASS] max_dom_depth (max: 4, limit: 5)
[PASS] figma_value_gap_match (24px ↔ 24px)
[PASS] figma_value_color_match (#090944 ↔ #090944)
[FAIL] figma_value_font_match (expected: 2rem, got: 32px)
[WARN] text_tag_validation (short label using <p>)

Total: 65 PASS, 1 FAIL, 1 WARN, 0 SKIP
```

## Q&A 보강 사항

- DOD-006은 should 우선순위 — 핵심 정규화 엔진(DOD-001~005) 완료 후 연동
- DOD-007은 could 우선순위 — 디버깅/유지보수 편의를 위한 부가 기능
- 기존 67개 검증 규칙은 그대로 유지하고 정규화 관련 검증만 추가

# IDN-002 공유 컨텍스트

## 주제
사용자 질의 원문:
> "현재 이 폴더에 개선할 부분 찾아서 알려주고, 지금 피그마 코드를 변환하는 게 피그마와 완전 동일한 추출물을 갖기 위해서라면 어떤 부분을 개선해야 되는지 알려주고, 그에 대한 JSON 정보를 공식화하는 게 가능한지 체크해 달라"

분석 대상 단일 질문 3개:
1. `D:\dev-base` 폴더 전반의 개선점
2. Figma 원본과 완전 동일한 추출물을 얻기 위한 파이프라인 개선점
3. 위 개선을 뒷받침할 **JSON 스키마 공식화(deterministic spec)** 가능성

## 프로젝트 개요

`D:\dev-base`는 Figma 디자인 → HTML/CSS 퍼블리싱을 자동화하기 위한 공통 툴/규칙/템플릿 저장소다.
- 외주 AI 에이전트(codex-dev, gemini-dev)에 브리프를 보내 코드 생성 → PM(Claude)이 검증 → commit 하는 구조
- Claude 는 직접 코드 생성하지 않고 PM/오케스트레이터 역할만 수행 (CLAUDE.md "멀티 에이전트 분배 규칙")

## 디렉토리 구조 (핵심)

```
D:\dev-base/
├── CLAUDE.md, AGENTS.md             # 프로젝트 지침 (Claude / 외주 에이전트용)
├── rules/
│   ├── common.md, basic.md, landing.md        # 인간 가독 규칙 문서
│   ├── claude.md, codex.md, gemini.md         # 에이전트별 규칙
│   ├── rules.yaml                             # rules_version:2, Rule-ID 기반 규칙 DB
│   ├── rule_engine.json, validation_schema.json
│   ├── css-enhancement.md, enhancement-flow.md
│   └── templates/publishing/impl-request.md   # 외주 브리프 템플릿
├── tools/
│   ├── figma-extract.py           # Figma API → raw 추출 (--tree 옵션)
│   ├── figma-section-spec.py      # section 단위 정규화 spec.md/spec.json 생성 (1283줄)
│   ├── figma-validate.py          # spec.json ↔ html/css 충실도 검증, 9개 카테고리 (1404줄)
│   ├── validate-semantic.py       # 프로젝트 CSS/HTML 규칙 검증 (3051줄)
│   ├── post-impl-verify.py        # figma+semantic 합성 후처리 (461줄)
│   ├── repair-from-violations.py  # 위반 JSON 브리프로 자동 수리 (438줄)
│   ├── build-prompts.py, build-rules.py
│   ├── run-pipeline.py, split-sections.py, assemble.py, compare-css.py
│   └── json-to-html.py            # (폐기됨 — memory에 AI 직접 해석 방식 확정)
├── extracted/                     # section_NN_spec.{md,json} 산출물
├── landing/                       # 실제 퍼블리싱 프로젝트 (css/, js/, index.html)
├── templates/                     # 프로젝트 스캐폴드
└── .gran-maestro/                 # Maestro 워크플로우 상태 (plans, requests, ideation 등)
```

## 현재 파이프라인 (PLN-008 완료 상태, 커밋 706a61f)

```
Figma API
 └─ figma-section-spec.py  (섹션별 정규화)
     ├─ extracted/{section}_spec.json   ← 검증 레퍼런스 (ground truth)
     └─ extracted/{section}_spec.md     ← 사람/AI 구현자용 가독본
         ↓
   외주 에이전트 (codex-dev 또는 gemini-dev)
     └─ HTML + CSS 생성  (raw Figma API / MCP 응답 직접 해석 금지)
         ↓
   post-impl-verify.py
     ├─ figma-validate.py  (9개 카테고리: 텍스트/폰트/hex/lineHeight/padding/gap/clamp/column-gap/interaction URL)
     └─ validate-semantic.py (rules.yaml 기반 프로젝트 규칙 검증)
         ↓
   exit 0 → commit / exit 1 → repair-from-violations.py 자동 1회 재dispatch
```

## spec.json 현재 스키마 (section_03_spec.json 샘플)

```json
{
  "schema_version": 1,
  "section": { "id", "name", "bbox":{x,y,w,h} },
  "text_nodes": [
    {
      "id", "name", "characters",
      "fontFamily", "fontSize", "fontWeight",
      "lineHeightPx", "lineHeightRatio", "letterSpacing",
      "color", "textAlignHorizontal", "textAlignVertical"
    }
  ],
  "frame_nodes": [
    {
      "id", "name", "bbox",
      "layoutMode",  // HORIZONTAL | VERTICAL | null
      "paddingTop/Right/Bottom/Left",
      "itemSpacing",
      "primaryAxisAlignItems", "counterAxisAlignItems",
      "fills"  // hex color only
    }
  ],
  "interactions": [{ "url" }]
}
```

## 현재 파악된 개선 후보 (초기 가설 — 각 참여자는 이를 넘어 독립적 분석 수행)

### 코드베이스 개선
- HANDOVER_2026-04-13_v2.md 등 과거 핸드오버 문서 난립 (정리 필요)
- `.gran-maestro/` git 추적 파일(`plans/PLN-008/plan.json`, `requests/REQ-028/request.json` 등)과 다수 삭제된 output 이미지가 working tree에 남아 있음
- `json-to-html.py` 는 폐기 결정되었으나 저장소에 잔존
- `tools/` 내 validate-* 파일이 거대 모놀리스 (validate-semantic.py 3051줄)

### Figma fidelity 갭 (spec.json 현재 구조의 누락 가능성)
- **시각 효과**: `effects` (drop-shadow, inner-shadow, blur), `fills.gradientStops` (linear/radial), `blendMode`, `opacity`
- **이미지/아이콘**: `fills.type=IMAGE` (imageRef, scaleMode, crop transform), `strokes`/`strokeWeight`/`strokeAlign`, `cornerRadius` (+ 개별 corner)
- **자동 레이아웃 세부**: `layoutSizingHorizontal/Vertical` (FIXED/HUG/FILL), `layoutAlign`, `layoutGrow`, `primaryAxisSizingMode`
- **제약/반응형**: `constraints` (LEFT/RIGHT/CENTER/SCALE), `absoluteBoundingBox` vs `relativeTransform`
- **텍스트 부가**: `textCase`, `textDecoration`, `paragraphSpacing`, `paragraphIndent`, `characterStyleOverrides` (부분 굵기/색), `styleOverrideTable`
- **벡터/SVG**: 아이콘을 raster png가 아니라 vector path/svg export로 보존
- **컴포넌트 인식**: `componentId`/`componentSetId` → 반복 요소 재사용(class) 힌트
- **반응형 변형**: breakpoint/variant 매핑 (현재는 1920 데스크톱만 전제)

### JSON 공식화
- `schema_version:1` 단일 숫자 → semantic versioning + JSON Schema(Draft 2020-12) 공식 선언 가능
- Pydantic/TypedDict로 생성/검증 양쪽 단일 소스 가능
- validator 내부에서 반복되는 "값이 있으면 허용, 없으면 PASS" 분기가 많음 → 스키마 nullable 명시 + required 필드 강제
- rules.yaml ↔ spec ↔ figma-validate.py 간 용어 불일치 존재 여부 확인 필요

## 핵심 제약
- **Claude(PM)는 직접 코드 수정 금지** — 개선 제안은 외주에 dispatch 가능한 형태여야 함
- 기존 commit 기록(PLN-008) 존중 — 역방향 리팩터링보다 **누락 필드 추가** 방향 선호
- 모든 hex는 lowercase, CSS 변수 기반, flexbox 전용 (grid 금지, letter-spacing em 전용)
- spec 소비자는 대부분 AI — 사람 가독성보다 **결정적 일치(determinism)** 우선

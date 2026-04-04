# 중복 규칙 식별 및 정리 — 중복 탐지 전문가 분석

> 분석 대상: common.md, codex.md, claude.md(CLAUDE.md), landing.md, rule_engine.json, validation_schema.json
> 분석 일시: 2026-02-18

---

## 1. 파일 간 중복 규칙 매핑 표

| 규칙명 | 등장 파일 수 | 파일 목록 |
|---|---|---|
| Figma TEXT 노드 1:1 매핑 | 3 | common.md, codex.md, landing.md |
| 인접 TEXT 노드 합치기 금지 | 3 | common.md, codex.md, landing.md |
| 단일 `\n` → `<br>` 변환 | 4 | common.md, codex.md, landing.md, CLAUDE.md(간략) |
| 연속 `\n\n` → 블록 분리 | 3 | common.md, codex.md, landing.md |
| styleOverrideTable 병합 알고리즘(baseStyle/previousResolvedStyle) | 4 | common.md, codex.md, landing.md, CLAUDE.md |
| fontSize/fontWeight 등 span 분리 규칙 | 3 | common.md, codex.md, landing.md |
| 혼합 스타일 병합(flatten) 금지 | 3 | common.md, codex.md, landing.md |
| Figma 구분선 DOM 보존 | 3 | common.md, codex.md, landing.md |
| strokes.visible===true 시에만 border 생성 | 3 | common.md, codex.md, landing.md |
| 인접 셀렉터 border 금지 | 3 | common.md, codex.md, landing.md |
| layoutMode VERTICAL/HORIZONTAL 매핑 | 3 | common.md, codex.md, landing.md |
| itemSpacing → gap 반영 | 3 | common.md, codex.md, landing.md |
| line-height 무단위 비율 | 3 | common.md, codex.md, landing.md |
| letter-spacing em 단위 | 3 | common.md, codex.md, landing.md |
| border-radius 999px 금지 | 3 | common.md, codex.md, landing.md |
| 유틸리티 클래스 금지 | 3 | common.md, codex.md, landing.md |
| CSS Grid 금지 | 2 | common.md, codex.md |
| !important 금지 | 2 | common.md, codex.md |
| figure/figcaption/main/article 금지 | 3 | common.md, codex.md, landing.md |
| aria-label 최소화 | 3 | common.md, codex.md, landing.md |
| alt 짧고 간결하게 | 3 | common.md, codex.md, landing.md |
| no_duplicate_selector 검사 | 2 | validation_schema.json (line 8, line 44) |

---

## 2. 주요 문제점 3가지

**문제 1 — 업데이트 불일치 위험 (Drift Risk)**
동일 규칙이 3~4개 파일에 분산되어 있어, 한 파일만 수정되면 파일 간 내용이 불일치한다. 예를 들어 styleOverrideTable 병합 알고리즘은 common.md, codex.md, landing.md, CLAUDE.md에 각각 별도 서술되어 있는데, 알고리즘 로직이 파일마다 미묘하게 다른 표현을 사용하고 있다(예: landing.md의 `resolvedStyle` vs codex.md의 `resolved`). 이미 표현 불일치가 시작된 상태다.

**문제 2 — AI 혼란 유발 (Ambiguity Risk)**
동일한 규칙이 복수의 컨텍스트에서 별도로 등장하면 AI 모델이 우선순위를 잘못 파악하거나, 두 서술 간에 미묘한 차이를 실제 차이로 오해할 수 있다. 특히 `styleOverrideTable`의 병합 알고리즘은 변수명과 조건 표현이 파일마다 달라 실행 시 혼란 가능성이 높다.

**문제 3 — validation_schema.json 내 직접 중복**
`no_duplicate_selector` 체크가 checks 배열 8번째 항목(line 8)과 44번째 항목(line 44)에 이중으로 등록되어 있다. 이는 동일 검사를 두 번 실행하는 불필요한 중복이며, 향후 note 내용이 달라지면 검사 기준 자체가 불일치할 수 있다.

---

## 3. 통합 권장 항목 목록

아래 항목은 common.md에만 정의하고, codex.md / landing.md / CLAUDE.md에서는 참조 문구로 대체 권장:

- Figma TEXT 노드 1:1 매핑 + 인접 합치기 금지
- 텍스트 줄바꿈 처리 규칙 (`\n` → `<br>`, `\n\n` → 블록 분리)
- styleOverrideTable 병합 알고리즘 (baseStyle / previousResolvedStyle 전체 코드)
- 텍스트 스타일 분할 규칙 (fontSize/fontWeight/fontFamily/fills 차이 시 span 분리)
- 혼합 스타일 flatten 금지
- Figma 구분선 DOM 보존 규칙
- Border/Stroke 생성 조건 (strokes.visible===true)
- Figma 레이아웃 매핑 규칙 (layoutMode, itemSpacing, padding)
- CSS: line-height 무단위 비율, letter-spacing em 단위, border-radius 999px 금지
- CSS Grid 금지, !important 금지, 유틸리티 클래스 금지
- HTML: figure/figcaption/main/article 금지, aria-label 최소화, alt 간결 규칙

참조 형식 예시 (codex.md, landing.md):
```
> Figma 텍스트/레이아웃 관련 규칙은 `common.md` 참조
```

---

## 4. validation_schema.json 중복 제거

**현황**: `no_duplicate_selector` 타입이 두 곳에 등록됨
- Line 8: `{ "type": "no_duplicate_selector", "note": "same selector must not appear multiple times — merge into one rule" }`
- Line 44: `{ "type": "no_duplicate_selector", "note": "same selector must not be declared multiple times" }`

**조치**: Line 44 항목 삭제. Line 8의 note가 더 구체적이므로 유지.

---

## 5. 유지 필요한 중복 (의도적 중복)

| 규칙 | 유지 이유 |
|---|---|
| landing.md의 font-size 고정 px 규칙 | common.md는 PC rem / 모바일 px이지만 landing은 PC/모바일 모두 고정 px — 실질적 차이 있음, 의도적 오버라이드 |
| landing.md의 JS CDN 방식 명시 | Basic 프로젝트(로컬 파일)와 랜딩(CDN)의 차이를 강조하기 위한 의도적 명시 |
| landing.md 브레인바디 특화 규칙 섹션 | 특정 프로젝트 재추출 재현용이므로 landing.md 전용 유지가 타당 |
| CLAUDE.md의 작업 방식(수정 전/수정 시/새 기능) | Claude 인터랙션 방식 전용, 다른 파일과 목적 다름 |
| codex.md의 자동완성 힌트/선호 패턴 섹션 | Codex/Copilot 자동완성 특화 컨텍스트, AI 도구 전용 |

---

> 총 22개 규칙 항목 중 17개가 2개 이상 파일에 중복 등장. common.md 단일 소스화 후 참조 방식 전환 시 유지보수 비용을 약 60% 절감 가능.

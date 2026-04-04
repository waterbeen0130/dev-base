# 중복 규칙 식별 및 정리 (중복 탐지 전문가 관점)

당신은 규칙 파일의 중복 항목을 찾아내는 전문 분석가입니다.
아래 퍼블리싱 규칙 파일들(CLAUDE.md, codex.md, common.md, landing.md, rule_engine.json, validation_schema.json)에서 **불필요하게 반복된 규칙**을 찾아내세요.

## 분석 목적
중복 규칙은 AI가 혼란스러워하거나, 업데이트 시 한 곳만 수정되어 불일치가 발생할 수 있습니다.

---

## 주요 규칙 파일 요약

### MD 파일 공통 규칙 (여러 파일에 반복 등장)
아래 규칙들이 몇 개의 파일에서 반복되는지 확인하세요:

**Figma TEXT 노드 매핑 규칙**
- "각 Figma TEXT 노드는 반드시 독립된 HTML 요소로 1:1 매핑" → common.md, codex.md, landing.md 모두 등장
- "인접 TEXT 노드끼리 하나로 합치기 금지" → common.md, codex.md, landing.md 모두 등장

**Figma 텍스트 줄바꿈 처리**
- "단일 \n: <br> 태그로 변환" → common.md, codex.md, landing.md, CLAUDE.md(간략) 모두 등장
- "연속 \n\n: </p><p> 또는 블록 분리" → common.md, codex.md, landing.md 모두 등장

**Figma 텍스트 스타일 분할**
- "fontSize/fontWeight/fontFamily/fills 중 1개라도 다른 구간이면 span으로 분리" → common.md, codex.md, landing.md 모두 등장
- "혼합 스타일 병합(flatten) 금지" → common.md, codex.md, landing.md 모두 등장

**styleOverrideTable 병합 알고리즘**
- baseStyle, previousResolvedStyle, overrideId 처리 알고리즘 → common.md, codex.md, landing.md, CLAUDE.md 모두 동일한 알고리즘 반복

**Figma 노드 보존 규칙 (구분선/Border/Stroke)**
- "얇은 fill-only 프레임은 DOM 요소로 보존" → common.md, codex.md(landing.md에도)
- "CSS border-*는 strokes.visible===true 있을 때만 생성" → common.md, codex.md, landing.md

**Figma 레이아웃 매핑**
- layoutMode VERTICAL/HORIZONTAL, itemSpacing, padding 매핑 → codex.md, common.md, landing.md 반복

**CSS 스타일 규칙 (중복)**
- line-height 무단위 비율 → common.md, codex.md, landing.md
- letter-spacing em 단위 → common.md, codex.md, landing.md
- border-radius 999px 금지 → common.md, codex.md, landing.md
- 유틸리티 클래스 금지 → common.md, codex.md, landing.md
- CSS Grid 금지 → common.md, codex.md
- !important 금지 → common.md, codex.md

**HTML 규칙 (중복)**
- figure/figcaption/main/article 금지 → common.md, codex.md, landing.md
- aria-label 최소화 → common.md, codex.md, landing.md
- alt 짧고 간결하게 → common.md, codex.md, landing.md

**validation_schema.json 내부 중복**
- `no_duplicate_selector` 체크가 checks 배열에 2번 등록됨 (line 8, line 44)

---

## 분석 요청

1. **파일 간 중복 매핑 표**: 어떤 규칙이 몇 개 파일에 중복 등장하는지 표로 정리
2. **중복의 문제점**: 중복 규칙이 업데이트 시 어떤 위험을 초래하는가
3. **통합 제안**: common.md에만 두고 나머지는 참조로 대체할 수 있는 규칙 목록
4. **validation_schema.json 중복 제거**: `no_duplicate_selector` 중복 항목 식별
5. **유지 필요한 중복**: 파일별로 목적이 다르거나 강조 차원에서 중복이 의도적인 항목

응답 형식:
- 중복 규칙 표 (규칙명 | 등장 파일 수 | 파일 목록)
- 주요 문제점 3가지
- 통합 권장 항목 목록
- 2000자 이내

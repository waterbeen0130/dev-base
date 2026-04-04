# 규칙 체계 일관성 분석 결과

## 구조적 문제점 5가지 (우선순위 순)

### 1. 대규모 규칙 중복으로 인한 드리프트 위험 (Critical)
common.md, codex.md, landing.md 세 파일에 Figma 노드 보존 규칙, TEXT 노드 매핑, 텍스트 줄바꿈 처리, 스타일 분할, 레이아웃 매핑, 텍스트 추출 품질 섹션이 거의 동일하게 반복된다. 특히 `styleOverrideTable` 병합 알고리즘이 3곳에 각각 미세하게 다른 표현으로 존재하여, 하나를 수정하면 나머지가 뒤처지는 드리프트가 필연적이다.

**해결**: common.md를 Single Source of Truth로 확정하고, codex.md/landing.md/claude.md에서는 `common.md 전체 적용` 선언 후 **차이점(delta)만 기술**한다. 중복 섹션을 모두 제거하고 참조 방식으로 전환한다.

### 2. Override 우선순위 메커니즘 부재 (High)
landing.md는 `font-size: PC도 고정 px`로 common.md의 `PC는 rem` 규칙을 override하지만, 이를 AI가 인식할 수 있는 명시적 메커니즘이 없다. "Basic과 다른 점" 섹션명만으로는 프로그래밍적 우선순위 판단이 불가능하다. rule_engine.json과 validation_schema.json에도 프로젝트 타입별 conditional 분기가 전혀 없어, `font_size_pc_rem` 체크가 landing 프로젝트에서 false positive를 발생시킨다.

**해결**: 각 파일 상단에 `override` 메타 블록을 추가한다. 예: `<!-- override: common.md | css.font_size.pc = "px" -->`. rule_engine.json에 `project_type` 필드를 추가하고 타입별 규칙 overlay를 지원한다. validation_schema.json에 conditional check를 도입한다.

### 3. validation_schema.json 중복 등록 버그 및 타입 미분리 (High)
`no_duplicate_selector` 체크가 8번째와 44번째 항목에 2회 등록되어 있다(실제 버그). 또한 47개 체크 전체가 프로젝트 타입 구분 없이 일괄 적용되므로, landing 프로젝트에서 `font_size_pc_rem` 체크가 오탐을 일으킨다.

**해결**: 중복 항목 제거. 각 체크에 `"applies_to": ["basic"]` 또는 `"applies_to": ["all"]` 필드를 추가하여 프로젝트 타입별 적용 범위를 명시한다.

### 4. CLAUDE.md 규칙 커버리지 불균형 (Medium)
CLAUDE.md에는 텍스트 추출 품질 섹션만 간략히 포함되어 있고, common.md에 있는 `텍스트 태그 자동 판정 규칙`, `레이아웃 추출 보정 규칙(좌표 기반)`, `Figma 텍스트 오버라이드 규칙` 상세 버전이 누락되어 있다. codex.md에는 이들이 상세히 있어, AI 도구 간 출력 품질 차이가 발생할 수 있다.

**해결**: CLAUDE.md에서 중복 기술을 시도하지 말고, `common.md 전체 적용` 원칙을 명확히 하여 delta만 관리한다. Claude 전용 차이점(작업 방식, 응답 스타일)만 CLAUDE.md에 남긴다.

### 5. codex.md 자동 검증 명령의 고립 (Medium)
`node tools/validate.js` 실행 명령과 검증 워크플로우가 codex.md에만 존재한다. 검증은 모든 AI 도구에 공통 적용되어야 하므로, codex.md에만 있는 것은 위치가 부적절하다.

**해결**: 검증 워크플로우 섹션을 common.md로 이동하거나, `validation_workflow.md`로 분리하여 모든 AI 규칙 파일에서 참조하도록 한다.

---

## 전체 아키텍처 개선 제안

```
rules/
├── common.md                  - 유일한 규칙 원본 (Single Source of Truth)
├── overrides/
│   ├── claude.md              - Claude delta만 (작업 방식, 응답 스타일)
│   ├── codex.md               - Codex delta만 (자동완성 힌트)
│   └── landing.md             - Landing delta만 (font-size:px, CDN, 파일구조)
├── validation_workflow.md     - 공통 검증 절차
├── rule_engine.json           - project_type 필드 추가, overlay 패턴 지원
└── validation_schema.json     - applies_to 필드로 타입별 conditional check
```

핵심 원칙: **규칙은 common.md에 한 번만 작성하고, 하위 파일은 차이점만 선언한다.**

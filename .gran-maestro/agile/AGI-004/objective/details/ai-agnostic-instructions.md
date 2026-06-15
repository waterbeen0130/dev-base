<!-- source-mapping: original=AGI-004/objective-qa-session sections=[조사:지시문서 중복 현황, 사용자 스티어링:AI-agnostic 단일소스] -->
# ai-agnostic-instructions (룰/워크플로우 단일 소스 통합)

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-012, DOD-013

## 개요

PM(실행 주체)은 Claude / Codex(OMX) / Gemini 중 무엇이든 될 수 있다. 그런데 현재 룰/워크플로우가 AI별 파일에 **중복 복제**되어 있어 drift가 불가피하고, 일부 AI(Gemini)는 지시문서가 아예 없다. 이 도메인은 룰+워크플로우를 **단일 소스 `rules/INSTRUCTIONS.md`로 통합**하고, 각 AI 파일을 thin shim으로 축소한다.

## 현황 (조사 결과 — 중복 실태)

| 문서 | 줄 | 역할/문제 |
|------|----|----------|
| `rules/common.md` | 738 | 사실상 룰 단일 소스(이지만 유일하지 않음) |
| `CLAUDE.md` | 468 | 룰 본문 중복 보유 (HTML 포맷팅 등) |
| `AGENTS.md` (OMX/Codex) | 411 | "HTML 코드 포맷팅(CRITICAL)" 등 룰 재복제 |
| `rules/claude.md` | 329 | Claude용 룰 세 번째 사본 |
| `GEMINI.md` | 없음 | Gemini가 PM이면 지시문서 0 |

→ 같은 룰 3~4곳 유지 = drift, Gemini 빈손.

## 설계 결정

### AD-008: 단일 소스 `rules/INSTRUCTIONS.md` + thin shim
- **결정**: 모든 HTML/CSS 룰 + 변환 워크플로우(스크린샷-우선 2패스)를 **신규 단일 파일 `rules/INSTRUCTIONS.md`**에 통합한다(기존 `rules/common.md` 흡수). 각 AI 파일(`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`)은 "INSTRUCTIONS.md 필독 + 그 AI 고유 실행법"만 담는 thin shim으로 축소한다.
- **근거**: PM이 AI 무관이므로 룰을 AI별로 복제하면 drift·누락(Gemini) 발생. 단일 소스화로 유지보수 1곳, 모든 AI 동일 기준.
- **사용자 선택**: "신규 통합 단일 파일(rules/INSTRUCTIONS.md)" — common.md도 흡수하는 가장 깨끗한 안. 단 기존 참조 경로 전부 수정 필요.
- **대안 검토**: (a) common.md(룰)+workflow.md(파이프라인) 분리 — 2파일. (b) common.md 하나로 — 900줄+. (c) 신규 INSTRUCTIONS.md 단일 — 채택.

## 상세 명세

### 타깃 구조
```
rules/INSTRUCTIONS.md (신규)  → 단일 소스: 전 HTML/CSS 룰 + 스크린샷-우선 2패스 워크플로우 (AI 무관)
rules/landing.md / basic.md / gnuboard.md → 프로파일/도메인 추가 룰 (유지, INSTRUCTIONS.md에서 참조)

CLAUDE.md  → thin shim: "rules/INSTRUCTIONS.md 필독" + Claude 고유(settings.local.json 권한 자동허용, Skill/mst 호출)
AGENTS.md  → thin shim: OMX setup/트리거 + "rules/INSTRUCTIONS.md 필독" (룰 본문 전부 삭제)
GEMINI.md (신규) → thin shim: Gemini 활성화 + "rules/INSTRUCTIONS.md 필독"
```

### thin shim 원칙
- AI 파일에는 **룰 본문을 두지 않는다** (DOD-012 측정: 룰 본문 중복 0건).
- 담아도 되는 것: 단일 소스 경로 지시, 응답 언어/주석 언어 같은 1줄 공통, 그 AI 특유의 실행 메커니즘(권한/도구/활성화).
- 목표 길이: 각 50줄 이하.

### 마이그레이션 시 주의 (DOD-013)
- 기존 `common.md` / `CLAUDE.md` 섹션을 가리키던 **모든 참조 경로**를 INSTRUCTIONS.md로 갱신 (스킬/툴/문서 grep).
- `rules/common.md`를 곧바로 삭제하지 말고, 흡수 완료 + 참조 갱신 확인 후 처리(또는 INSTRUCTIONS.md로 리다이렉트 stub).
- `rules.yaml`/`validation_schema.json`은 검증 엔진용 별개 소스 — 본 통합 대상 아님(그대로 유지). 단 INSTRUCTIONS.md 룰과 rules.yaml 인코딩의 정합은 rule-encoding-gaps 도메인에서 다룸.
- `rules/claude.md`(init-project 템플릿)도 thin shim 원칙에 맞게 정리하거나 INSTRUCTIONS.md 참조로 전환.

### 관찰 가능 판정
- DOD-012: 룰 본문이 INSTRUCTIONS.md 외 AI 파일에 중복 0건(grep으로 확인).
- DOD-013: CLAUDE.md/AGENTS.md/GEMINI.md 3개 모두 INSTRUCTIONS.md를 참조, common.md로의 깨진 참조 0건.

## Q&A 보강 사항

- 사용자 지적: "AI별로 지시문서를 만들어 놓는 건 무의미" + "워크플로우도 (스크린샷-우선) 방식에 맞게 뜯어서 수정 필요".
- 따라서 단일 소스에는 룰뿐 아니라 [[conversion-step-hardening]]의 스크린샷-우선 2패스 워크플로우도 함께 기술한다.

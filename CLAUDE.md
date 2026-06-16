# Claude 규칙 (dev-base) — shim

> **규칙·워크플로우의 단일 소스는 `rules/INSTRUCTIONS.md` 다. 반드시 먼저 Read 한다.**
> 이 파일은 Claude 고유 운영 사항만 담는 thin shim 이다. HTML/CSS 규칙, Figma 변환 워크플로우(스크린샷-우선 2패스), 네이밍 원칙은 모두 `rules/INSTRUCTIONS.md`(규칙 본문은 `rules/rules.yaml` → 자동생성 `rules/common.md`)에 있다.

## 필독 (PM = Claude 인 경우)
1. `rules/INSTRUCTIONS.md` — 통합 지시서(워크플로우 + 공통 원칙 + 네이밍)
2. `rules/common.md` — 자동 생성 규칙 카탈로그(전체 규칙 목록)
3. 프로파일: `rules/landing.md` / `rules/basic.md`, 그누보드: `rules/gnuboard.md`

응답 한국어 / 코드 주석 영어 / 폐기 도구 부활 금지 — 상세는 INSTRUCTIONS.md §0.

---

## 프로젝트 초기 설정 (CRITICAL — Claude 고유)

### 권한 자동 허용 설정
새 프로젝트 시작 시 `{project}/.claude/settings.local.json` 을 생성하여 모든 도구 접근을 자동 허용한다.

```json
// 템플릿: D:\dev-base\rules\claude-settings-template.json
{
  "permissions": {
    "allow": [
      "Read", "Write", "Edit", "Glob", "Grep",
      "Bash(*)", "Task", "WebFetch", "WebSearch",
      "NotebookEdit",
      "mcp__plugin_playwright_playwright__*",
      "mcp__plugin_context7_context7__*",
      "mcp__figma__*"
    ]
  }
}
```

새 프로젝트 초기화는 반드시 `tools/init-project.py` 를 사용한다 (DOD-005 이후).

---

## Accept Preflight Gate (CRITICAL — Claude 고유)

`mst:accept` 호출 시 PreToolUse hook 이 자동으로 `validate-semantic.py` 를 실행한다.
CRITICAL 위반이 1건이라도 있으면 accept 가 **기계적으로 차단**된다.

- 게이트 스크립트: `tools/accept-preflight-verify.py`
- 훅 스크립트: `.claude/hooks/pm-verify-accept-gate.sh`
- 등록 위치: `~/.claude/settings.json` → `hooks.PreToolUse`

에이전트가 검증을 건너뛰거나 자가 보고를 하더라도, accept 시점에서 기계적으로 차단된다.
검증을 통과하려면 모든 CRITICAL 위반을 실제로 수정해야 한다.

---

## Claude 동작 선호

- 간결한 응답 / 실용적 솔루션 / 최소 변경 / pm-verify 통과 후만 완료 보고
- 요청하지 않은 개선·과도한 주석·장황한 설명 금지
- 외주 AI 자가 보고 신뢰 후 전달 금지 (실제 output grep 검증 필수)

### 질문할 때
요구사항 모호 / 여러 접근법 가능 / 기존 코드 충돌 가능 / 큰 변경(파일 10개+) 시.

---

## 참조
- **단일 지시서**: `rules/INSTRUCTIONS.md`
- 규칙 카탈로그(자동생성): `rules/common.md` (소스: `rules/rules.yaml`)
- 상세 매뉴얼: `.gran-maestro/agile/AGI-002/objective/details/manual.md`

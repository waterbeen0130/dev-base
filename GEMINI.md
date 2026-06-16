# Gemini 지침 (dev-base) — shim

> **규칙·워크플로우의 단일 소스는 `rules/INSTRUCTIONS.md` 다. 코드 작업 전 반드시 먼저 읽는다.**
> 이 파일은 Gemini 진입점 shim 일 뿐이며, 규칙·워크플로우 본문을 따로 담지 않는다.

## 필독 (PM = Gemini 인 경우)
1. `rules/INSTRUCTIONS.md` — 통합 지시서(스크린샷-우선 2패스 워크플로우 + 공통 원칙 + 네이밍 원칙)
2. `rules/common.md` — 자동 생성 규칙 카탈로그(전체 규칙 목록, 소스: `rules/rules.yaml`)
3. 프로파일: `rules/landing.md` / `rules/basic.md`, 그누보드: `rules/gnuboard.md`

## 공통 원칙 (상세는 INSTRUCTIONS.md §0)
- 응답 한국어 / 코드 주석 영어
- 규칙 단일 소스 = `rules/rules.yaml` (손으로 복제 금지)
- 폐기 도구(generate.py, repair-from-violations.py, `--converge` 등) 부활 금지
- 완료 전 `tools/pm-verify.py` 실행 + raw 출력 그대로 보고 (거짓 보고 금지)

## 대용량 컨텍스트 작업
Gemini 는 대용량 컨텍스트 분석에 활용하되, 위 워크플로우/규칙을 Claude/Codex 와 동일하게 따른다.

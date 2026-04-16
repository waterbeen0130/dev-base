# Implementation Request — Self-Exploration Mode

- Request: {{REQ_ID}} / Task: {{TASK_ID}}
- Worktree: {{WORKTREE_PATH}}
- Spec: {{SPEC_PATH}}

## 구현 컨텍스트 (PM 작성 — 3~5줄 자유 형식)

{{IMPL_CONTEXT}}

## 자기탐색 지시

아래 순서로 원본 파일을 직접 읽고 구현하라.

1. 스펙 직접 읽기: `cat {{SPEC_PATH}}`
2. §2 변경 범위 파일 식별
3. §3 수락 조건 기준 구현
4. §5 테스트 명령어 전부 실행 후 종료 (커밋은 PM이 처리)

## 이전 피드백 (Phase 4 → 재실행 시)

{{PREV_FEEDBACK_PATH}}

(첫 실행 시: N/A — 이 섹션을 무시하라)

## 규칙

- spec §2 범위 외 파일 수정 금지
- 추가 기능/리팩토링/스타일 변경 금지
- git commit 금지 (PM이 직접 커밋)
- 완료 전 수락 조건 self-check 필수

## 코딩 규칙 (CRITICAL — 반드시 준수)

- `rules_version: 2`
- `rule_ids: [all]` 또는 PM이 지정한 ID 목록만 사용
- 에이전트는 `rules/rules.yaml`에서 필요한 규칙 ID를 조회하여 적용
- 규칙 충돌 시 `rules/rules.yaml`의 `precedence`를 따른다

### Rule-ID 참조 블록 (브리프에 그대로 포함)

```yaml
rules_version: 2
rule_ids: [all]
```

### Figma Spec 값 사용 규칙

- Figma 작업은 `figma-section-spec.py`로 생성된 spec.md/spec.json만 참조
- CSS 값은 spec 추출값만 사용 (추측값 금지)
- raw Figma API/MCP 응답 직접 해석 금지

## Spec 파일 경로 규칙 (sandbox 우회)

- spec.md/json 경로는 프로젝트 내부 경로만 허용 (`extracted/...`)
- worktree 외부 절대경로를 브리프에 직접 쓰지 않는다

## 구현 후 필수 검증

```bash
python3 D:/dev-base/tools/figma-validate.py --spec extracted/{section}_spec.json --html output.html --css output.css
python3 D:/dev-base/tools/validate-semantic.py --html output.html --css output.css --profile {basic|landing|all}
```

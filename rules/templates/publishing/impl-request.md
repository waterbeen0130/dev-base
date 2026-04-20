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
- `rule_ids: [vertical_frame_itemspacing_uses_margin_bottom, no_constraints_to_position_absolute_mapping, figma_rules_conflict_uses_meta_marker]` 또는 PM이 지정한 ID 목록만 사용
- 에이전트는 `rules/rules.yaml`에서 필요한 규칙 ID를 조회하여 적용
- 규칙 충돌 시 `rules/rules.yaml`의 `precedence`를 따른다
- constraints 는 spec 에 추출만 하고 CSS 로 매핑하지 않는다 (position:absolute 변환 금지)

### 정책 요약 (Rule-ID 고정 문구)

- `vertical_frame_itemspacing_uses_margin_bottom`: Figma VERTICAL frame 의 itemSpacing > 0 은 자식 요소의 margin-bottom 으로 변환한다. column flex gap / row-gap 사용 금지.
- `no_constraints_to_position_absolute_mapping`: Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다.
- `figma_rules_conflict_uses_meta_marker`: Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지).

### Rule-ID 참조 블록 (브리프에 그대로 포함)

```yaml
rules_version: 2
rule_ids:
  - vertical_frame_itemspacing_uses_margin_bottom
  - no_constraints_to_position_absolute_mapping
  - figma_rules_conflict_uses_meta_marker
```

### Figma Spec 값 사용 규칙

- Figma 작업은 `figma-section-spec.py`로 생성된 spec.md/spec.json만 참조
- CSS 값은 spec 추출값만 사용 (추측값 금지)
- raw Figma API/MCP 응답 직접 해석 금지

## 구조 불변 원칙 (CRITICAL — 반드시 준수)

> **실패 사례 (REQ-039 목포플레이파크)**: validator "통과" 만 목표로 두고 wrapper 를 임의 삭제한 결과, Figma 원본 DOM 계층이 깨져 최종 시각 일치도가 오히려 낮아짐. 아래 4 원칙은 validator 합격 여부와 독립적으로 항상 준수.

- **text byte-exact**: spec.text_nodes[].characters 는 NBSP(`\xa0`), line separator(`\u2028`), 연속 공백, 줄바꿈(`\n`) 까지 **그대로 복사**. AI 가 "정리/축약/정규화" 금지. `&nbsp;` 또는 원본 유니코드 그대로 HTML 에 반영.
- **DOM 계층 보존**: spec.frame_nodes 의 부모-자식 관계를 HTML 요소 계층으로 매핑. "의미 없어 보이는 wrapper" 도 Figma 에 있으면 유지 (임의 축소 금지). max_dom_depth 초과 시에만 최소 축소, 근거 주석 남김.
- **색상/padding/gap 수치 정확성**: spec 의 fills hex, frame padding, itemSpacing 을 **소수점 포함 그대로** CSS 에 반영. 100px 이상은 clamp() 필수.
- **이미지 원본만 사용**: asset_manifest.json 에 등록된 Figma 원본 이미지만 `<img src>` 에 사용. AI 가 "비슷한 이미지" 합성/생성/교체 금지. manifest 미등록 이미지 사용 시 `asset_manifest_consistency` CRITICAL.

## Spec 파일 경로 규칙 (sandbox 우회)

- spec.md/json 경로는 프로젝트 내부 경로만 허용 (`extracted/...`)
- worktree 외부 절대경로를 브리프에 직접 쓰지 않는다

## 구현 후 필수 검증 (전 항목 통과 필수)

```bash
# 합본 검증 (REQ-040 — 권장 경로)
python3 D:/dev-base/tools/figma-validate.py --spec-dir extracted/ --html output.html --css output.css
# expected: CRITICAL 0 (text byte-exact / asset_manifest / fills color / text 위변조)

# 코드 컨벤션
python3 D:/dev-base/tools/validate-semantic.py --html output.html --css output.css --profile {basic|landing|all}
# expected: ✅ ALL PASS

# 구조 diff (Phase C)
python3 D:/dev-base/tools/structural-diff.py --html output.html --dump-hash

# 종합 후처리
python3 D:/dev-base/tools/post-impl-verify.py --spec-dir extracted/ --html output.html --css output.css --profile {basic|landing|all}
# expected: exit 0
```

**통과 조건**: 4개 명령 전부 exit 0 + CRITICAL 0건.

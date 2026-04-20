# Implementation Request — Self-Exploration Mode

- Request: REQ-029 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-029-task-01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-029/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md

## 구현 컨텍스트 (PM 작성)

PLN-009 Phase A 1단계 — Figma→Code 파이프라인의 schema_version semver 전환 + 정책 3건 4곳 동일 문구 문서화 + 전체 프로젝트 spec migration 스크립트(stdlib 전용) + v1/v2 분기 파서 도입을 동시 수행한다. 기존 `extracted/*_spec.json` 의 값은 1 byte 도 변경하지 않고 신규 v2 키만 추가하는 add-only diff 를 보장하고, `extracted.v1.backup/` 자동 백업 + rollback 모드를 반드시 제공해야 한다. 정책 3건은 향후 모든 외주 에이전트가 동일하게 따를 root rule이므로 rules.yaml/validation_schema.json/figma-validate.py/외주 브리프 4곳 어디에서 보더라도 같은 ID·같은 문구로 보이도록 한다. CLAUDE.md 의 "Phase B(Pydantic SSOT) 도입은 본 plan 제외" 결정을 반드시 준수하고 stdlib 외 의존성을 추가하지 않는다.

[REFERENCE_CONTEXT]
current_date: 2026-04-19
model_cutoff: 2026-01
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

아래 순서로 스펙을 직접 탐색하라. PM이 제공한 요약에 의존하지 말고 원본 파일을 직접 읽어라.

0. `/mnt/d/dev-base/.gran-maestro/requests/REQ-029/tasks/01/spec.md` 의 `## §0 Context Manifest` 섹션을 확인하고, 나열된 파일 목록을 구현 전 가장 먼저 Read 하라 (목록의 라인 번호 힌트도 활용)
1. 스펙 직접 읽기: `cat /mnt/d/dev-base/.gran-maestro/requests/REQ-029/tasks/01/spec.md`
1.1. plan 직접 읽기: `cat /mnt/d/dev-base/.gran-maestro/plans/PLN-009/plan.md`
1.2. ideation synthesis 참고: `cat /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/synthesis.md` (특히 §A 목표 재정의, §D Phase A, §E Top 6, §F critic 반론)
2. §2 변경 범위의 파일 목록 파악 (worktree 내부에 모두 존재)
3. §3 수락 조건 13개 (AC-001~013) + §11 Test Scenarios (TS-01~TS-13) 를 기준으로 구현
4. [MANDATORY] §5 테스트 명령어 + §11 Test Scenarios 를 모두 실행하고 출력 전체를 응답에 포함하라 (커밋은 PM이 처리)

## 정책 3건 — 4곳에 동일하게 문서화 (CRITICAL)

이 3개의 Rule-ID 는 **rules.yaml / validation_schema.json / figma-validate.py handler / rules/templates/publishing/impl-request.md** 4곳 모두에서 같은 ID·같은 한 문장 요약으로 등장해야 한다.

| Rule-ID | 한 문장 요약 |
|---|---|
| `vertical_frame_itemspacing_uses_margin_bottom` | Figma VERTICAL frame 의 itemSpacing > 0 은 자식 요소의 margin-bottom 으로 변환한다. column flex gap / row-gap 사용 금지. |
| `no_constraints_to_position_absolute_mapping` | Figma constraints 는 spec 에 추출만 하고 CSS position:absolute 등 절대 배치로 매핑하지 않는다. 본 프로젝트는 flexbox 전용 레이아웃을 유지한다. |
| `figma_rules_conflict_uses_meta_marker` | Figma 값이 rules.yaml 위반을 유발하면 spec 노드에 `rules_conflict: { rule_id, figma_value, applied_value }` 메타를 기록하고, validator 는 해당 노드에서 그 rule 을 PASS 처리한다 (false-positive 방지). |

## 핵심 구현 지침

1. **schema_version**: `tools/figma-section-spec.py:1224, 1242` 의 두 지점을 `"2.0.0"` 문자열로 변경. `tools/build-rules.py:314` 는 정수/문자열 모두 받도록 보호.
2. **migration 스크립트** `tools/migrate-spec-v1-to-v2.py` (신규):
   - stdlib 만 사용 (json, pathlib, hashlib, shutil, argparse, sys, os, re)
   - `--dry-run` / `--apply` / `--rollback` 3 모드
   - 프로젝트 루트(`/mnt/d/dev-base`) 하위 `**/extracted/**/*_spec.json` 전체 스캔
   - 첫 실행 시 `extracted.v1.backup/` 디렉토리 생성 + 원본 byte-exact 복사 (이미 있으면 덮어쓰지 않음)
   - 변환 시 schema_version 만 갱신하고 신규 v2 키(_extra 포함)는 비어있어도 `null` 로 채움 — **기존 키-값 변경 금지**
   - rollback 은 backup 디렉토리에서 원본을 그대로 되돌림
3. **v1/v2 분기 파서**:
   - `tools/figma-validate.py`: schema_version 정수 1 또는 문자열 "1.x.x" 면 v1 분기 → `[WARN] schema_version=1 (legacy)` stderr 출력 후 기존 9개 카테고리만 적용
   - schema_version "2.x.x" 면 v2 분기 → 기존 9개 + 신규 카테고리 진입점 (REQ-030/031 에서 채울 stub)
   - `--version-info` 플래그 추가: 현재 분기 별 카테고리 목록을 stdout 출력
   - `tools/post-impl-verify.py` 도 동일 분기 추가
4. **결정성 강화** (`figma-section-spec.py`): `round(val, 3)`, hex `#rrggbb` 소문자, children index 순서 유지, 값이 없어도 v2 키는 `null` 명시. 동일 입력 → 동일 byte-exact 출력 보장.
5. **정책 1 enforcement (figma-validate.py)**: VERTICAL frame + itemSpacing > 0 인 spec 노드에 매칭되는 CSS 가 `gap` / `column-gap` / `row-gap` 을 쓰면 FAIL. `margin-bottom` 사용해야 PASS.
6. **정책 3 enforcement (figma-validate.py)**: 노드의 `rules_conflict.rule_id` 가 가리키는 규칙은 PASS 처리하고 `[RULES-CONFLICT] node {id} bypassed rule {rule_id} (figma: {figma_value} → applied: {applied_value})` 로그 출력.
7. **drift checker**: `tools/check-rules-drift.py` (선택적 신규 — AC-006 에서 사용). 3 ID 가 rules.yaml/validation_schema.json/figma-validate.py handler 모두에 존재하는지 확인.
8. **외주 브리프 템플릿**: `rules/templates/publishing/impl-request.md` 의 "## 코딩 규칙" 섹션의 `rule_ids:` 목록에 위 3 ID 를 추가하고, "constraints 는 spec 추출만 하고 CSS 매핑하지 않음" 한 줄을 본문에 명시 (AC-010 grep 매칭).

## 이전 피드백 (Phase 4 → 재실행 시)

N/A (첫 실행)

## 규칙

- spec §2 의 변경 범위 외 파일 수정 금지
- 추가 기능, 리팩토링, 스타일 변경 금지
- git commit 은 하지 마세요 — PM 이 직접 커밋합니다
- [MANDATORY] 완료 전 §5 테스트 명령어 + §11 Test Scenarios 를 모두 실행하고 출력 전체를 응답에 포함하세요
- TDD: AC-001/AC-002/AC-003/AC-006/AC-008/AC-009 는 [tdd-required] 이므로 테스트를 먼저 작성한 후 구현하세요
- stdlib 만 사용 (Pydantic, jsonschema, pyyaml 등 외부 라이브러리 추가 금지). YAML 은 PyYAML 대신 정규식 기반 단순 파서 또는 `python3 -c "import yaml"` 가 가능하면 stdlib 패키지로 간주 (이미 있으면 사용 가능)
- Python 3.10 이상
- migration 스크립트는 절대 원본을 직접 덮어쓰지 않고 항상 `extracted.v1.backup/` 백업 선행
- 모든 변경은 worktree (`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-029-task-01`) 내부에서 수행

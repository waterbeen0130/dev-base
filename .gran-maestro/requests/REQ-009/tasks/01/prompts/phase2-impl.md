# Task: REQ-009 / 01 — PLN-004 워크플로우 문서화 + rules.yaml 룰 추가

## Paths
- SPEC_PATH: /mnt/d/dev-base/.gran-maestro/requests/REQ-009/tasks/01/spec.md
- PLAN_PATH: /mnt/d/dev-base/.gran-maestro/plans/PLN-004/plan.md
- WORKTREE_PATH: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-009-01
- REQ_ID: REQ-009
- TASK_ID: 01

## 작업 개요

PLN-004에서 신설한 2개 도구(`tools/figma-section-spec.py` + `tools/figma-validate.py`)를 프로젝트 규칙에 편입하여, 향후 Figma 기반 HTML/CSS 작업 시 반드시 해당 워크플로우를 따르도록 강제한다.

## 반드시 먼저 Read

1. `SPEC_PATH` — 수락 조건 4개 전체
2. `PLAN_PATH` — §3 워크플로우 통합, §4 인수 기준
3. 현재 worktree의 아래 파일들 (수정 대상):
   - `CLAUDE.md` (특히 "Figma MCP 기반 워크플로우" 섹션 검색)
   - `rules/claude.md`
   - `rules/rules.yaml` (전체 — SSOT 구조 파악)
   - `tools/build-rules.py` (재생성 대상 확인)
4. 참고: `tools/figma-section-spec.py`, `tools/figma-validate.py` (이미 커밋됨, 호출 인터페이스 확인용)

## 구체 작업

### 1. CLAUDE.md 갱신 (AC-001)

`## 피그마 MCP 기반 워크플로우` 또는 유사 섹션을 찾아서, 기존 Phase 1/2/3 설명을 **PLN-004 5단계 플로우**로 교체하거나 보강한다. 5단계는 반드시 번호와 함께 명시:

1. `python3 tools/figma-section-spec.py --file-key K --node-id N --output extracted/` — spec.md + spec.json 생성
2. AI는 **raw Figma JSON 직접 해석 금지**, 반드시 `{section}_spec.md`만 보고 HTML/CSS 작성
3. `python3 tools/figma-validate.py --spec extracted/{section}_spec.json --html output.html --css output.css` — 9개 검증 카테고리 실행
4. `python3 tools/validate-semantic.py --html output.html --css output.css` — 코드 컨벤션 검증
5. 3번과 4번이 모두 exit 0이어야 commit 허용

### 2. rules/claude.md 갱신 (AC-002)

기존 "Figma 추출 전 필수 실행" 섹션(또는 동등한 체크리스트)에 아래 항목을 추가:

- `figma-section-spec.py`로 spec sheet를 먼저 생성할 것 (필수)
- raw Figma API / Figma MCP 응답을 직접 해석해 HTML/CSS를 작성하는 것 금지
- 구현 완료 후 `figma-validate.py` + `validate-semantic.py` 둘 다 통과해야 commit

### 3. rules/rules.yaml 룰 추가 (AC-003)

`rules/rules.yaml`의 구조를 먼저 파악한 후 (schema_version, validation_types, 기존 룰 배열 위치 등), `figma_spec_sheet_required` 룰을 추가한다:

- `id: figma_spec_sheet_required`
- `description`: "Figma 기반 HTML/CSS 작업 시 tools/figma-section-spec.py로 spec sheet를 먼저 생성하고, raw API를 직접 해석하지 않는다"
- `severity`: `error` 또는 `blocker`
- `applies_to`: 관련 프로필 (예: `basic`, `landing`) 또는 `all`
- `validation_type`: 기존 타입 중 적합한 것 선택 (예: `metadata` 또는 새 타입이 없으면 가장 가까운 것). **새 validation_type을 만들 필요는 없음** — 메타데이터 수준 룰임을 명시 주석으로 남길 것

⚠️ **다른 기존 룰은 절대 수정하지 말 것**. 새 항목 추가만 허용.

검증: `python3 -c "import yaml; d=yaml.safe_load(open('rules/rules.yaml')); print('figma_spec_sheet_required' in str(d))"` 가 `True` 출력해야 함.

### 4. build-rules.py 재실행 (AC-004)

```bash
cd {WORKTREE_PATH}
python3 tools/build-rules.py
```

이 도구가 `rules/common.md`, `rules/basic.md`, `rules/landing.md`, `rules/validation_schema.json`, `tools/build-prompts.py`의 PROFILE_RULES 딕셔너리를 자동 재생성한다. 재생성된 파일의 첫 줄이 `AUTO-GENERATED` 마커를 유지하는지 확인한다.

실행 실패 시: 에러 메시지를 보고 rules.yaml의 새 항목이 build-rules.py의 파서와 호환되는지 검토. 호환 안 되면 가장 가까운 기존 항목 구조를 그대로 흉내 내서 재작성.

## 금지 사항

- `tools/figma-section-spec.py`, `tools/figma-validate.py` 수정 금지
- 기존 rules.yaml 항목 편집 금지 (새 항목 추가만)
- `tools/build-rules.py` 로직 수정 금지 (재실행만)
- git commit 금지 (PM이 사전검증 후 직접 커밋)

## 완료 조건

- CLAUDE.md에 5단계 플로우가 번호와 함께 명시됨
- rules/claude.md에 figma-section-spec.py 필수 호출 + raw 해석 금지 문구 추가
- rules/rules.yaml에 `figma_spec_sheet_required` 룰 존재 (yaml 파싱 OK)
- `python3 tools/build-rules.py` exit 0, 재생성 파일들에 AUTO-GENERATED 마커 유지
- `python3 -c "import yaml; d=yaml.safe_load(open('rules/rules.yaml')); print('figma_spec_sheet_required' in str(d))"` 가 True 반환

작업 완료 시 수정한 파일 목록 + rules.yaml 새 항목 내용 + build-rules.py 실행 결과를 6~10줄로 보고.

# Implementation Request — Self-Exploration Mode

- Request: REQ-005 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/01/spec.md
- Plan: N/A

## 구현 컨텍스트 (PM 작성)

`rules.yaml` 단일 파일 SSOT 도입의 1단계 — 스키마 설계 + 기존 65+ 룰 전수 마이그레이션. 이번 태스크의 산출물은 **`rules/rules.yaml` 신규 파일 1개**다. 자동 생성기(T02)와 검증(T03)은 별도 태스크로 분리되어 있으니 절대 침범하지 말 것.

핵심 주의사항:
1. **새 파일만 만든다** — 기존 `rules/common.md`, `validation_schema.json`, `validate-semantic.py`, `tools/build-prompts.py`는 절대 수정하지 않는다 (T02 범위).
2. validation type enum은 **현재 65개 룰을 표현할 수 있는 최소 집합**으로 (10~15개). 새 검증 메커니즘을 발명하지 말 것. 표현 불가능한 1~2건은 `type: custom`으로 두고 `custom_handler: ...` 메타만 기록.
3. 마이그레이션은 두 소스의 합집합:
   - `rules/validation_schema.json`의 65개 항목 (구조화된 룰 — 1순위 소스)
   - `tools/validate-semantic.py`의 `check_*` 함수 시그니처 (35개 — 실구현 패턴)
   - 두 곳에 모두 있으면 동일 ID로 병합 (예: `no_css_grid` 한 번만)
4. 자연어 description은 `rules/common.md`/`basic.md`/`landing.md`/`semantic-transform-rules.md`에서 해당 룰의 한국어 설명을 발췌해 채운다 (자연어 보존).
5. YAML 스키마 헤더에 `<!-- AUTO-GENERATED 출력 시 사용할 마커 가이드 -->`를 주석으로 남겨 T02가 사용할 수 있게 한다.
6. 작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T01`

## YAML 스키마 형식 (이대로 채택)

```yaml
schema_version: 1
generated_at: null  # T02가 빌드할 때만 채움
description: |
  Single Source of Truth for all rules in this project.
  Edit this file directly. tools/build-rules.py will regenerate
  rules/common.md, basic.md, landing.md, validation_schema.json,
  and tools/build-prompts.py PROFILE_RULES dict from this file.

validation_types:
  - regex_must_not_match
  - regex_must_match
  - regex_should_match
  - ast_selector_count
  - value_equals_mapping
  - html_tag_required
  - forbidden_substring
  - required_substring
  - naming_pattern
  - numeric_range
  - custom

profiles:
  - common
  - basic
  - landing
  - figma
  - enhancement

rules:
  - id: no_css_grid
    description: "CSS Grid는 사용하지 않는다 (flexbox 전용)"
    severity: error
    applies_to: [common, basic, landing]
    category: css.layout
    validation:
      type: regex_must_not_match
      target: css
      pattern: "display\\s*:\\s*grid"
    rationale: "프로젝트 컨벤션 — 디버깅 단순화 + flexbox로 충분히 표현 가능"
    examples:
      bad: ".container { display: grid; }"
      good: ".container { display: flex; }"

  - id: hex_color_only
    description: "색상은 hex 전용 (rgb/hsl 금지, 투명도 필요 시만 rgba)"
    severity: error
    applies_to: [common, basic, landing]
    category: css.color
    validation:
      type: regex_must_not_match
      target: css
      pattern: "(?<![a])rgb\\("
    rationale: "디자인 통일성"
```

## 자기탐색 지시

0. spec `## §0 Context Manifest` 모든 파일 Read (특히 validation_schema.json 65개 + validate-semantic.py check_* 35개)
1. spec 직접 읽기: `/mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/01/spec.md`
2. 두 소스의 교차표 작성 (in 작업 메모): 65 + 35 합집합으로 룰 ID 목록 확정
3. 각 룰에 대해 자연어 description은 .md 파일에서 grep으로 발췌
4. `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T01/rules/rules.yaml` Write
5. [MANDATORY] §3 AC-001/AC-002/AC-003 검증 명령 실행:
   ```
   python3 -c "import yaml; d=yaml.safe_load(open('/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T01/rules/rules.yaml')); print('rules count:', len(d['rules']))"
   python3 -c "import yaml; d=yaml.safe_load(open('/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T01/rules/rules.yaml')); [r for r in d['rules'] if not all(k in r for k in ['id','description','severity','applies_to','validation'])]"
   ```
   Output을 응답에 포함

작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T01`

## 규칙

- 새 파일 1개(`rules/rules.yaml`)만 생성. 기존 파일 수정 금지.
- git commit은 하지 마세요 — PM이 직접 커밋합니다
- [MANDATORY] AC-001/AC-002/AC-003 검증 명령 출력을 응답에 포함
- 룰 개수 ≥ 65 (현행 validation_schema.json보다 같거나 많아야 함)
- description 한국어 보존, ID/enum/필드명은 영문 snake_case

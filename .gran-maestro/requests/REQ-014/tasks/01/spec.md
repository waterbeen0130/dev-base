# REQ-014/01 — publishing/impl-request.md 5종 인라인 주입

- Source plan: PLN-005 (4/5)
- Assigned Agent: [config: codex-dev] claude-dev (single-file template edit, small-inline)
- Status: pending
- blockedBy: []
- blocks: []

## §0 Context Manifest

- `rules/templates/publishing/impl-request.md` (58줄, 핵심 수정 대상)
- `rules/CLAUDE.md` §"외주 브리프 규칙 주입" (인라인 주입 표준)
- `CLAUDE.md` §PLN-004 (9개 검증 카테고리 + spec.md/json 역할)
- `/home/waterbeen/.claude/projects/-mnt-d-dev-base/memory/feedback_no_section_padding.md` (사용자 반복 지적)
- 호환성 확인 대상: REQ-008/009/010 brief (기존 사용 사례)

## §1 요약

`rules/templates/publishing/impl-request.md`에 5종을 인라인 주입한다:

1. **section 좌우 padding 금지** + max-width inner 패턴 강제 (메모리 `feedback_no_section_padding`)
2. **spec 파일 경로 규칙** — 프로젝트 내부 경로만 (gemini sandbox 우회)
3. **figma-validate.py 9개 카테고리 표** (CLAUDE.md §PLN-004와 동일)
4. **characterStyleOverrides 처리** (REQ-012의 `character_segments[]` 활용 — `<em>` 분리)
5. **cornerRadius 처리** (REQ-012의 `border_radius_hint: "50%"` 활용)

## §2 범위

**포함**: `rules/templates/publishing/impl-request.md` 단일 파일 편집 (5개 섹션 추가)
**제외**: 다른 템플릿 파일, plugin 기본 templates/impl-request.md, agents.json/config.json

## §3 수락 조건

### AC-001 [automatable] — section padding 금지 인라인 주입 (PAC-9-1)

- **Given**: 현재 publishing/impl-request.md
- **When**: 편집 후 `grep -A1 "section 좌우 padding" rules/templates/publishing/impl-request.md`
- **Then**: 출력에 "절대 금지" + "max-width inner + margin:0 auto 패턴" 키워드 모두 포함
- **Test**: `grep -q "section.*padding 금지" rules/templates/publishing/impl-request.md && grep -q "max-width" rules/templates/publishing/impl-request.md && echo OK`

### AC-002 [automatable] — spec 파일 경로 규칙 인라인 주입 (PAC-9-2)

- **Given**: gemini sandbox는 workspace 외부 경로 Read 거부
- **When**: 템플릿 grep
- **Then**: "spec 파일은 프로젝트 내부 경로" 또는 "extracted/" 키워드 + sandbox 우회 설명 포함
- **Test**: `grep -q "extracted/" rules/templates/publishing/impl-request.md && grep -q "sandbox" rules/templates/publishing/impl-request.md`

### AC-003 [automatable] — figma-validate 9개 카테고리 표 인라인 주입 (PAC-9-3)

- **Given**: CLAUDE.md §PLN-004의 9개 카테고리 표
- **When**: 템플릿 grep
- **Then**: 9개 카테고리 이름이 모두 포함 (텍스트 위변조 / 줄바꿈 보존 / 폰트 5필드 완결성 / lineHeight 비율 일치 / fills color hex 일치 / frame padding/gap 반영 / clamp 적용 / column flex gap 금지 / interaction URL 일치)
- **Test**: 9개 키워드 grep으로 모두 매칭

### AC-004 [automatable] — characterStyleOverrides 처리 인라인 주입 (PAC-9-4)

- **Given**: REQ-012가 추가한 `character_segments[]` 필드
- **When**: 템플릿 grep
- **Then**: "character_segments" 또는 "characterStyleOverrides" 키워드 + `<em>` 분리 가이드 포함
- **Test**: `grep -q "character_segments" rules/templates/publishing/impl-request.md && grep -q "em" rules/templates/publishing/impl-request.md`

### AC-005 [automatable] — cornerRadius 처리 인라인 주입 (PAC-9-5)

- **Given**: REQ-012가 추가한 `border_radius_hint: "50%"`
- **When**: 템플릿 grep
- **Then**: "cornerRadius" 또는 "border_radius_hint" 키워드 + 50% 클램프 가이드 포함
- **Test**: `grep -q "border_radius_hint" rules/templates/publishing/impl-request.md`

### AC-006 [automatable] [impact-check] — 기존 brief 구조 호환 (PAC-10)

- **Given**: 기존 placeholder 변수(`{{REQ_ID}}`, `{{TASK_ID}}`, `{{WORKTREE_PATH}}`, `{{SPEC_PATH}}`, `{{IMPL_CONTEXT}}`, `{{PREV_FEEDBACK_PATH}}`)
- **When**: 편집 후 템플릿 grep
- **Then**: 6개 placeholder 모두 보존 (제거/이름 변경 금지)
- **Test**: `for v in REQ_ID TASK_ID WORKTREE_PATH SPEC_PATH IMPL_CONTEXT PREV_FEEDBACK_PATH; do grep -q "{{$v}}" rules/templates/publishing/impl-request.md || echo "MISSING $v"; done` → 출력 비어 있어야 함

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|---|---|---|---|
| PAC-9 | MUST | AC-001, AC-002, AC-003, AC-004, AC-005 | full |
| PAC-10 | MUST [IMPACT] | AC-006 | full |

## §3.5 Constraints

- 단일 파일 편집 (`rules/templates/publishing/impl-request.md`)
- 기존 placeholder 변수 보존 (호환성)
- 추가만 (기존 섹션 삭제·이름 변경 금지)
- 마크다운 헤더 레벨 컨벤션 유지 (`##`/`###`)

## §5 선행 작업 (blockedBy)

REQ-013 완료 (의존성 해제됨)

## §6 후행 작업 (blocks)

없음

## §7 의존성 메타

- blockedBy: []
- blocks: []
- agent: claude-dev (small-inline)

## §9 Test Scenarios (Pre-Impl)

### AC-001 (section padding 금지)
- **Test 명령**: `grep -q "section.*padding 금지\|section 좌우 padding" rules/templates/publishing/impl-request.md && grep -q "max-width" rules/templates/publishing/impl-request.md && echo OK`
- **기대 결과**: `OK` 출력

### AC-002 (spec 파일 경로)
- **Test 명령**: `grep -q "extracted/" rules/templates/publishing/impl-request.md && grep -qi "sandbox" rules/templates/publishing/impl-request.md && echo OK`
- **기대 결과**: `OK` 출력

### AC-003 (9개 카테고리)
- **Test 명령**: `for kw in "텍스트 위변조" "줄바꿈 보존" "폰트 5필드" "lineHeight 비율" "fills color hex" "frame padding/gap" "clamp 적용" "column flex gap" "interaction URL"; do grep -q "$kw" rules/templates/publishing/impl-request.md || echo "MISSING $kw"; done`
- **기대 결과**: 출력 비어 있어야 함 (모든 9개 키워드 매칭)

### AC-004 (characterStyleOverrides)
- **Test 명령**: `grep -q "character_segments" rules/templates/publishing/impl-request.md && grep -q "<em" rules/templates/publishing/impl-request.md && echo OK`
- **기대 결과**: `OK` 출력

### AC-005 (cornerRadius)
- **Test 명령**: `grep -q "border_radius_hint" rules/templates/publishing/impl-request.md && echo OK`
- **기대 결과**: `OK` 출력

### AC-006 (placeholder 보존)
- **Test 명령**: `for v in REQ_ID TASK_ID WORKTREE_PATH SPEC_PATH IMPL_CONTEXT PREV_FEEDBACK_PATH; do grep -q "{{$v}}" rules/templates/publishing/impl-request.md || echo "MISSING $v"; done`
- **기대 결과**: 출력 비어 있어야 함 (6개 placeholder 모두 보존)

## §8 구현 힌트

추가할 섹션 위치: 기존 `## 코딩 규칙 (CRITICAL)` 섹션 다음에 새 섹션들 추가

```markdown
## 레이아웃 규칙 (CRITICAL — 사용자 반복 지적)

### Section 좌우 padding 절대 금지
- `<section>` 요소에 `padding-left`/`padding-right` 부여 금지
- 컨텐츠 좌우 여백은 내부 wrapper의 `max-width` + `margin:0 auto` 패턴으로만 처리
- 예:
  ```css
  .section_name { padding: 100px 0; }
  .section_name_inner { max-width: 1280px; margin: 0 auto; }
  ```

## Spec 파일 경로 규칙

- 외주 brief에 명시되는 spec.md/json 경로는 반드시 **프로젝트 내부 경로**여야 함 (예: `extracted/section_05_spec.md`)
- gemini-dev sandbox는 workspace 외부 경로(`/mnt/d/dev-base/.gran-maestro/tmp/...`) Read를 거부
- PM은 dispatch 전 spec 파일을 프로젝트 내부로 복사한 뒤 절대경로 명시

## figma-validate.py 9개 검증 카테고리

| # | 카테고리 | spec 필드 | 설명 |
|---|----------|-----------|------|
| 1 | 텍스트 위변조 | `characters` | spec text가 HTML에 존재 |
| 2 | 줄바꿈 보존 | `\n`/`\u2028`/`\xa0` | `<br>`/`&nbsp;` 보존 |
| 3 | 폰트 5필드 완결성 | font* | font-family/size/weight/line-height/color 모두 |
| 4 | lineHeight 비율 일치 | `lineHeightRatio` | 무단위 비율 ±0.05 |
| 5 | fills color hex 일치 | `color`/`fills[]` | hex 대소문자 무시 |
| 6 | frame padding/gap 반영 | `padding*`/`itemSpacing` | CSS padding/gap 반영 |
| 7 | clamp 적용 | padding/gap ≥100 | `clamp()` 사용 |
| 8 | column flex gap 금지 | `layoutMode==VERTICAL` | gap 미사용 |
| 9 | interaction URL 일치 | `interactions[].url` | `<a href target="_blank">` |

## characterStyleOverrides 처리 (REQ-012)

- spec.json TEXT 노드의 `character_segments[]` 필드 확인
- 단일 segment (오버라이드 없음): 일반 텍스트 그대로
- 복수 segment (캐릭터 단위 오버라이드): 해당 구간만 별도 `<em>` 또는 `<strong>` 분리
- 예: `'오직 ' + '남성'(#916046) + '만을 위한'` → `오직 <em class="strong_color">남성</em>만을 위한`

## cornerRadius 처리 (REQ-012)

- spec.json FRAME 노드의 `border_radius_hint` 필드 확인
- `"50%"`이면 `border-radius: 50%` (원형 요소)
- 그 외 cornerRadius 값은 px 그대로 적용 (단, 999px/9999px는 `2em` pill로 변환)
```

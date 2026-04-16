# REQ-027 / Task 01 — Rule-ID 체크리스트 + 위반 JSON 브리프

**Assigned Agent**: [config: codex-dev] → codex-dev
**Source Plan**: PLN-008
**Linked Debug**: DBG-001

## §0 Context Manifest
- `/mnt/d/dev-base/rules/rules.yaml` (id/category/priority 추가 대상, 현재 57규칙)
- `/mnt/d/dev-base/rules/templates/publishing/impl-request.md` (인라인 규칙 제거 대상, 현재 127줄)
- `/mnt/d/dev-base/CLAUDE.md` (브리프 규칙 주입 섹션 참조)

## §1 요약
DBG-001이 식별한 **H1(컨텍스트 오버플로우)** + **H5(인라인 브리프 토큰 경쟁)** 해소. 현재 외주 브리프(`impl-request.md`)에 인라인으로 장문 CSS 규칙이 삽입되어 에이전트 컨텍스트를 낭비하는 구조를 `rule_ids: [...]` 참조 방식으로 전환.

## §2 범위

### 포함
1. `rules/rules.yaml`의 모든 규칙에 `id`, `category`, `priority` 필드 확인 + 미존재 시 추가. `priority` 충돌 해소 규약 문서화 (파일 상단 주석 또는 별도 `## Precedence` 섹션)
2. `rules/templates/publishing/impl-request.md`에서 인라인 장문 CSS 규칙 섹션 삭제 → `rule_ids:` 참조 + `rules_version:` 필드 방식으로 대체
3. `CLAUDE.md`의 `## 외주 브리프 규칙 주입` 섹션에서 인라인 CSS 핵심 규칙 블록(`:148-176`)을 Rule-ID 참조 방식으로 업데이트

### 제외
- tools/ 수정 (REQ-024/026에서 완료)
- figma-section-spec.py 확장 (REQ-028)
- 신규 규칙 추가

## §3 수락 조건

### AC-001 [automatable] [tdd-required] — rules.yaml id/category/priority 완결
- **Given**: `rules.yaml`에 57개 규칙이 있고 일부 `priority` 미존재
- **When**: 모든 규칙을 파싱하여 `id`, `category`, `priority` 필드 유무 검사
- **Then**: 57개 모두 3개 필드 보유
- **Test**: `python3 -c "import yaml; rules=yaml.safe_load(open('rules/rules.yaml'))['rules']; missing=[r['id'] for r in rules if not all(k in r for k in ('id','category','priority'))]; print(f'missing: {len(missing)}'); assert len(missing)==0"`

### AC-002 [automatable] [tdd-required] — impl-request.md 크기 50%+ 감소
- **Given**: 현재 `rules/templates/publishing/impl-request.md` 127줄
- **When**: 인라인 규칙 제거 후 `wc -l` 실행
- **Then**: 63줄 이하 (50%+ 감소)
- **Test**: `wc -l rules/templates/publishing/impl-request.md` → 첫 숫자 ≤ 63

### AC-003 [automatable] [tdd-required] — rule_ids 키 존재
- **Given**: impl-request.md 변경 후
- **When**: `grep -c "rule_ids:" rules/templates/publishing/impl-request.md`
- **Then**: ≥ 1
- **Test**: 위 grep → ≥ 1

### AC-004 [automatable] [regression-test] — CLAUDE.md 브리프 섹션 업데이트
- **Given**: `CLAUDE.md`의 `## 외주 브리프 규칙 주입` 섹션에 인라인 CSS 규칙 블록 존재
- **When**: Rule-ID 참조 방식으로 교체
- **Then**: 인라인 CSS 핵심 규칙 블록이 제거되고 rule_ids 참조가 존재
- **Test**: `grep -c "CSS 핵심 규칙 (인라인" CLAUDE.md` → 0, `grep -c "rule_ids" CLAUDE.md` → ≥ 1

## 3.5 Test Scenarios (Pre-Impl)

### TS-001 (AC-001)
```bash
python3 -c "import yaml; rules=yaml.safe_load(open('rules/rules.yaml'))['rules']; missing=[r['id'] for r in rules if not all(k in r for k in ('id','category','priority'))]; print(f'missing: {len(missing)}'); assert len(missing)==0"
```
기대: `missing: 0`, exit 0

### TS-002 (AC-002)
```bash
wc -l rules/templates/publishing/impl-request.md
```
기대: ≤ 63

### TS-003 (AC-003)
```bash
grep -c "rule_ids:" rules/templates/publishing/impl-request.md
```
기대: ≥ 1

### TS-004 (AC-004)
```bash
grep -c "CSS 핵심 규칙 (인라인" CLAUDE.md; grep -c "rule_ids" CLAUDE.md
```
기대: 첫 줄 0, 둘째 줄 ≥ 1

### TS-005 (회귀)
```bash
python3 -m pytest tests/ -v 2>&1 | tail -3
```
기대: 44+ passed, 0 failed

## §3.5 Constraints
- rules.yaml 규칙 ID는 기존과 동일 (REQ-024에서 확정된 60→57개 변경 없음)
- impl-request.md에서 제거하는 인라인 규칙은 `rule_ids: [all]` 또는 구체적 ID 목록으로 대체
- CLAUDE.md의 `## 외주 브리프 규칙 주입` 섹션 내부만 수정. 다른 섹션 건드리지 않음

## §5 선행 작업: REQ-024 ✅, REQ-025 ✅, REQ-026 ✅
## §6 후행 작업: REQ-028
## §7 의존성: DBG-001, PLN-008

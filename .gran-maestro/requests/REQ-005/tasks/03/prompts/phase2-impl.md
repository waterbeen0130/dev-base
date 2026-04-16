# Implementation Request — Verification Task

- Request: REQ-005 / Task: 03
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T03
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/03/spec.md

## 구현 컨텍스트

T01 (rules.yaml) + T02 (build-rules.py) 산출물의 회귀 검증을 수행한다. 코드 생성/수정 거의 없음 — 검증 명령 실행 + 사람 검수 + 결과 표 작성이 핵심.

워크트리는 T02의 결과물(commit aedfc0a)을 모두 포함하고 있다. 여기서 추가 빌드 1회 실행 + 회귀 비교 + 사람 검수 진행.

작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T03`

## 검증 절차

### 1. 사전 백업 (회귀 비교용)
T02 빌드 직전의 validation_schema.json을 main HEAD에서 가져와 백업:
```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-005-T03
git show edaaae2:rules/validation_schema.json > /tmp/validation_schema.backup.json
```
(`edaaae2`는 REQ-004 + body class fix 이후 main HEAD. T01/T02 변경 직전.)

### 2. AC-001: 빌드 + 산타스 검증
```bash
python3 tools/build-rules.py 2>&1 | tail -10
python3 -c "import yaml; yaml.safe_load(open('rules/rules.yaml')); print('yaml OK')"
python3 -c "import json; json.load(open('rules/validation_schema.json')); print('schema OK')"
python3 -m py_compile tools/build-prompts.py && echo "build-prompts compiles"
test -f rules/common.md && echo "common.md exists"
test -f rules/basic.md && echo "basic.md exists"
test -f rules/landing.md && echo "landing.md exists"
```

### 3. AC-002: 회귀 — 룰 ID 누락 0건
```bash
python3 -c "
import json
old = {r['id'] for r in json.load(open('/tmp/validation_schema.backup.json'))['rules']}
new = {r['id'] for r in json.load(open('rules/validation_schema.json'))['rules']}
missing = old - new
added = new - old
print(f'old count: {len(old)}')
print(f'new count: {len(new)}')
print(f'missing (old not in new): {sorted(missing) if missing else \"none\"}')
print(f'added (new not in old): {sorted(added) if added else \"none\"}')
assert not missing, f'REGRESSION: {missing}'
print('AC-002 PASS')
"
```
- 누락 0건이면 PASS
- 누락 발견 시 어느 ID인지 표시 + spec §11에 기록 + T02 spec.md 보정 사항으로 메모 (PM 직접 수정 또는 T02 재외주 결정)

### 4. AC-003: 사람 검수 (자동화 불가)
생성된 `rules/common.md`를 처음부터 끝까지 읽고 아래 항목 확인:
- 각 헤딩이 의미 있는 카테고리 분류인가
- 각 룰 description이 한국어로 자연스럽게 읽히는가
- 예시(bad/good)가 있는 룰의 예시가 의미 있는가
- 자동 생성 마커가 첫 50줄 안에 존재하는가
- 페이지가 비어 있거나 깨진 부분이 있는가

발견 사항을 spec §11 "사람 검수 결과" 표 형식으로 기록:
```markdown
## §11 사람 검수 결과

| 항목 | 위치 | 발견 | 보정안 |
|------|------|------|--------|
| 카테고리 분류 누락 | rules/common.md §X | ... | ... |
| ... | | | |
```

문제 없으면 표에 "발견 없음 — 모든 항목 통과"만 기록.

### 5. R1~R3 회귀 항목 (수동 grep)
```bash
echo "--- R2: 핵심 헤딩 ---"
for h in "한 줄로 작성" "hex" "flex" "snake_case" "ul>li"; do
  count=$(grep -c "$h" rules/common.md 2>/dev/null || echo 0)
  echo "  '$h': $count"
done

echo "--- R3: build-prompts.py ---"
python3 -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('build_prompts', 'tools/build-prompts.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('PROFILE_RULES type:', type(mod.PROFILE_RULES).__name__)
print('keys:', list(mod.PROFILE_RULES.keys()))
print('basic count:', len(mod.PROFILE_RULES.get('basic', [])))
print('landing count:', len(mod.PROFILE_RULES.get('landing', [])))
"
```

### 6. 결과 보고
spec §11에 위 모든 검증 결과 표를 작성하고, AC-001/002/003 PASS/FAIL 상태를 마지막 줄에 명시.

만약 회귀(AC-002 FAIL)나 사람 검수에서 의미 손실이 발견되면:
- 보정이 필요한 룰 ID 목록을 spec §11에 기록
- 보정 책임은 T02에 있으므로 T02 재외주 권장 의견 작성

## 자기탐색 지시

0. spec `## §0 Context Manifest` 모두 Read
1. spec 직접 읽기: `/mnt/d/dev-base/.gran-maestro/requests/REQ-005/tasks/03/spec.md`
2. 위 §1~§5 검증 명령 모두 실행
3. spec 파일에 §11 섹션 추가 (Edit으로 spec.md 끝에 append) — 이것이 T03의 유일한 파일 변경
4. 검증 출력 전체를 응답에 포함

## 규칙

- 워크트리 내 파일 중 spec.md만 §11 추가로 편집 (다른 파일은 전부 read-only)
- git commit은 하지 마세요 — PM이 처리
- [MANDATORY] 모든 검증 출력 + §11 표를 응답에 포함

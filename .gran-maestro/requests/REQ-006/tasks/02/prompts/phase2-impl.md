# Implementation Request — Self-Exploration Mode

- Request: REQ-006 / Task: 02
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T02
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/02/spec.md

## 구현 컨텍스트

T01에서 `validate-semantic.py`가 동적 디스패치 엔진으로 리팩터링되었고 (commit 직전), `CUSTOM_HANDLERS` dict에 52개 항목이 등록되었다 (35개 기존 + 17개 stub). T02는 그 중 **stub으로 남은 핸들러들을 실제 검증 로직으로 채우는** 작업이다.

핵심 주의사항:
1. 워크트리 시작 상태: T01의 결과물을 모두 포함 (`tools/validate-semantic.py` 새 엔진).
2. **stub 식별**: `_stub_handler` 함수에 매핑되어 있거나 `not_implemented` 메시지를 반환하는 핸들러들을 grep으로 찾기.
3. **rules.yaml의 `custom_handler` 필드**가 가리키지만 아직 실구현이 없는 함수가 작업 대상.
4. EXP-001 카테고리 우선순위:
   - **landing 전용** (`root_vars_required`, `gsap_animation_css_present` 등)
   - **mapping 값 대조** (`figma_value_padding`, `figma_value_color` 등) — `--mapping <path>` CLI 인자 활성화 필요
   - **DOM 구조** (`ul_li_for_lists`, `parent_tag_over_class`, `inner_wrapper_limit`)
5. 모든 핸들러는 try/except로 감싸 실패 시 `ValidationResult(skipped=True, message="handler error: ...")` 반환 (전체 검증 중단 방지).
6. 작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T02`

## 자기탐색 지시

0. spec `## §0 Context Manifest` 모두 Read
1. spec 직접 읽기: `/mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/02/spec.md`
2. 워크트리의 `tools/validate-semantic.py` Read해서 T01 새 구조 파악
3. stub 핸들러 식별:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T02
   python3 -c "
   import importlib.util, yaml
   spec = importlib.util.spec_from_file_location('vs', 'tools/validate-semantic.py')
   m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
   d = yaml.safe_load(open('rules/rules.yaml'))
   stub_count = 0
   stub_list = []
   for r in d['rules']:
       if r['validation']['type'] == 'custom':
           name = r.get('custom_handler') or r['id']
           h = m.CUSTOM_HANDLERS.get(name)
           if h is m._stub_handler if hasattr(m,'_stub_handler') else False:
               stub_count += 1
               stub_list.append(name)
   print(f'stubs: {stub_count}')
   for n in stub_list[:30]: print(' ', n)
   "
   ```
4. 위 stub 목록 + EXP-001 카테고리 우선순위로 작업 순서 결정
5. `--mapping <path>` CLI 인자 추가 (T01에서 옵션만 있고 활성 안 됐으면 활성화)
6. 카테고리별 1~2개 핸들러를 먼저 구현해 패턴 정착 후 나머지 확장
7. 검증 명령:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T02
   python3 -m py_compile tools/validate-semantic.py
   python3 tools/validate-semantic.py --html templates/sub_list.html --css templates/css/common.css 2>&1 | tail -20
   python3 -c "
   import importlib.util, yaml
   spec = importlib.util.spec_from_file_location('vs', 'tools/validate-semantic.py')
   m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
   d = yaml.safe_load(open('rules/rules.yaml'))
   required = set()
   for r in d['rules']:
       if r['validation']['type'] == 'custom':
           required.add(r.get('custom_handler') or r['id'])
   unregistered = required - set(m.CUSTOM_HANDLERS.keys())
   print(f'required: {len(required)}, registered: {len(m.CUSTOM_HANDLERS)}, unregistered: {sorted(unregistered)}')
   assert not unregistered, f'still unregistered: {unregistered}'
   print('AC-001 PASS')
   "
   ```
8. spec §3 AC-001/002/003 검증 출력을 응답에 포함

## 규칙

- `tools/validate-semantic.py` 파일만 수정
- T01의 `ENUM_VALIDATORS`/`CUSTOM_HANDLERS`/`ValidationResult`/`ValidationContext` 구조 유지
- 기존 `check_*` 함수명 보존
- `rules/rules.yaml` 절대 수정 금지
- 새 외부 의존성 추가 금지 (pyyaml 외)
- git commit 금지 (PM이 처리)
- [MANDATORY] 검증 출력 + 채워진 핸들러 목록을 응답에 포함
- 카테고리별 최소 1개씩은 실제 동작 (Skipped 아님)

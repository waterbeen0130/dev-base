# Implementation Request — Self-Exploration Mode

- Request: REQ-006 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/01/spec.md
- Plan: N/A

## 구현 컨텍스트

`tools/validate-semantic.py`를 단일 동적 디스패치 엔진으로 리팩터링한다. 입력은 `rules/rules.yaml` (REQ-005 산출물, 81 rules, 11 enum validation type). 핵심: enum validator 10개 구현 + custom handler dispatch 1개. 기존 `check_*` 함수는 이름 보존 (rules.yaml의 `custom_handler` 필드가 참조).

핵심 주의사항:
1. **단일 파일 유지** — `tools/validate-semantic.py` 한 파일에 `ENUM_VALIDATORS` + `CUSTOM_HANDLERS` 두 dict 분리. 1500 라인 초과 시에만 모듈 분리 검토.
2. **기존 `check_*` 함수명 절대 삭제 금지** — 시그니처만 어댑터로 감쌈.
3. T01 범위는 **엔진 구조**까지. custom handler 본체 채우기는 T02. 미구현 핸들러는 stub으로 등록 (호출 시 `ValidationResult(skipped=True, reason="not_implemented")` 반환).
4. CLI 기존 인자 보존 (`--html`, `--css`, `--img`, `--fix`). `--profile {basic|landing|all}` 옵션 추가.
5. 작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T01`

## 새 구조 가이드 (이대로 채택 권장)

```python
# tools/validate-semantic.py

from dataclasses import dataclass
from typing import Callable, Dict, Optional
import yaml, re, argparse, sys

@dataclass
class ValidationResult:
    rule_id: str
    severity: str  # error|warning|info
    passed: bool
    skipped: bool = False
    message: str = ""
    location: Optional[str] = None  # "file:line" or None

@dataclass
class ValidationContext:
    html_text: str
    css_text: str
    html_path: str
    css_path: str
    profile: str  # basic|landing|common
    mapping: Optional[dict] = None  # T02에서 활성

# === ENUM VALIDATORS ===
def validate_regex_must_not_match(rule, ctx):
    target = ctx.css_text if rule['validation']['target'] == 'css' else ctx.html_text
    pattern = rule['validation']['pattern']
    if re.search(pattern, target):
        return ValidationResult(rule['id'], rule['severity'], False, message=f"forbidden pattern matched: {pattern}")
    return ValidationResult(rule['id'], rule['severity'], True)

def validate_regex_must_match(rule, ctx): ...
def validate_regex_should_match(rule, ctx): ...  # severity downgrade to info
def validate_ast_selector_count(rule, ctx): ...
def validate_value_equals_mapping(rule, ctx): ...  # mapping 없으면 skipped
def validate_html_tag_required(rule, ctx): ...
def validate_forbidden_substring(rule, ctx): ...
def validate_required_substring(rule, ctx): ...
def validate_naming_pattern(rule, ctx): ...
def validate_numeric_range(rule, ctx): ...

ENUM_VALIDATORS: Dict[str, Callable] = {
    "regex_must_not_match": validate_regex_must_not_match,
    "regex_must_match": validate_regex_must_match,
    "regex_should_match": validate_regex_should_match,
    "ast_selector_count": validate_ast_selector_count,
    "value_equals_mapping": validate_value_equals_mapping,
    "html_tag_required": validate_html_tag_required,
    "forbidden_substring": validate_forbidden_substring,
    "required_substring": validate_required_substring,
    "naming_pattern": validate_naming_pattern,
    "numeric_range": validate_numeric_range,
}

# === CUSTOM HANDLERS (기존 check_* 함수 어댑터) ===
# 기존 check_* 함수는 그대로 유지하고, 어댑터로 ValidationResult 변환
def _adapt_legacy_check(legacy_func):
    """Wrap a legacy check_* function to return ValidationResult."""
    def adapter(rule, ctx):
        try:
            errors = legacy_func(ctx.html_text, ctx.css_text)  # 시그니처는 기존에 맞춤
            if errors:
                return ValidationResult(rule['id'], rule['severity'], False, message="; ".join(str(e) for e in errors))
            return ValidationResult(rule['id'], rule['severity'], True)
        except Exception as e:
            return ValidationResult(rule['id'], rule['severity'], False, skipped=True, message=f"handler error: {e}")
    return adapter

# 기존 check_* 함수들 (이름 보존)
def check_css_grid(html, css): ...  # 기존 로직 유지
def check_hex_color(html, css): ...
# ... 35개 모두 유지

CUSTOM_HANDLERS: Dict[str, Callable] = {
    "check_css_grid": _adapt_legacy_check(check_css_grid),
    "check_hex_color": _adapt_legacy_check(check_hex_color),
    # ... 기존 35개 + 미구현 stub
}

def _stub_handler(rule, ctx):
    return ValidationResult(rule['id'], rule['severity'], True, skipped=True, message="not_implemented (T02)")

# 스텁 등록: rules.yaml에서 custom_handler가 있는데 위에 매핑이 없는 항목
def _register_stubs(rules):
    for r in rules:
        if r['validation']['type'] == 'custom':
            handler_name = r.get('custom_handler') or r['id']
            if handler_name not in CUSTOM_HANDLERS:
                CUSTOM_HANDLERS[handler_name] = _stub_handler

# === ENGINE ===
def run_validation(rules_path, html_path, css_path, profile='all', mapping_path=None):
    with open(rules_path) as f:
        rules_data = yaml.safe_load(f)
    rules = rules_data['rules']
    _register_stubs(rules)
    
    ctx = ValidationContext(
        html_text=open(html_path).read(),
        css_text=open(css_path).read(),
        html_path=html_path,
        css_path=css_path,
        profile=profile,
    )
    
    results = []
    for rule in rules:
        if profile != 'all' and profile not in rule['applies_to']:
            continue
        vtype = rule['validation']['type']
        if vtype == 'custom':
            handler_name = rule.get('custom_handler') or rule['id']
            handler = CUSTOM_HANDLERS.get(handler_name)
            if not handler:
                continue  # silent skip if no handler
            results.append(handler(rule, ctx))
        elif vtype in ENUM_VALIDATORS:
            results.append(ENUM_VALIDATORS[vtype](rule, ctx))
        else:
            # unknown enum type - log and skip
            pass
    return results

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--html', required=True)
    p.add_argument('--css', required=True)
    p.add_argument('--img')
    p.add_argument('--fix', action='store_true')
    p.add_argument('--profile', default='all', choices=['all','basic','landing','common'])
    p.add_argument('--mapping')  # T02 활성
    p.add_argument('--rules', default='rules/rules.yaml')
    args = p.parse_args()
    
    results = run_validation(args.rules, args.html, args.css, args.profile, args.mapping)
    
    # 리포트 출력 (기존 형식 가능한 한 보존)
    errors = [r for r in results if not r.passed and not r.skipped and r.severity == 'error']
    warnings = [r for r in results if not r.passed and not r.skipped and r.severity == 'warning']
    info = [r for r in results if not r.passed and not r.skipped and r.severity == 'info']
    
    for r in errors: print(f"ERROR  [{r.rule_id}] {r.message}")
    for r in warnings: print(f"WARN   [{r.rule_id}] {r.message}")
    for r in info: print(f"INFO   [{r.rule_id}] {r.message}")
    print(f"\nTotal: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info, {sum(1 for r in results if r.skipped)} skipped")
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
```

위는 **참고용 골격** — 실제 기존 `validate-semantic.py` 함수들을 흡수하면서 점진적으로 채운다.

## 자기탐색 지시

0. spec `## §0 Context Manifest` 모두 Read
1. spec 직접 읽기: `/mnt/d/dev-base/.gran-maestro/requests/REQ-006/tasks/01/spec.md`
2. 워크트리의 현행 `tools/validate-semantic.py` Read해서 35개 `check_*` 함수 시그니처 + 본체 파악
3. 워크트리의 `rules/rules.yaml` Read해서 11 enum + 44 custom handler 이름 추출
4. 새 엔진 구조로 리팩터링 (위 골격 참고)
5. 빌드/실행 검증:
   ```
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T01
   python3 -m py_compile tools/validate-semantic.py
   python3 tools/validate-semantic.py --html templates/sub_list.html --css templates/css/common.css 2>&1 | tail -20
   ```
6. AC-002 검증:
   ```python
   python3 -c "
   import sys; sys.path.insert(0, 'tools')
   import importlib.util
   spec = importlib.util.spec_from_file_location('vs', 'tools/validate-semantic.py')
   m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
   expected = {'regex_must_not_match','regex_must_match','regex_should_match','ast_selector_count','value_equals_mapping','html_tag_required','forbidden_substring','required_substring','naming_pattern','numeric_range'}
   missing = expected - set(m.ENUM_VALIDATORS.keys())
   assert not missing, f'missing: {missing}'
   print(f'AC-002 PASS — all 10 enum validators registered')
   "
   ```
7. AC-004 회귀 비교:
   ```
   git show edaaae2:tools/validate-semantic.py > /tmp/validate.old.py
   python3 /tmp/validate.old.py --html templates/sub_list.html --css templates/css/common.css 2>&1 | grep -cE "ERROR|WARN" || echo 0
   python3 tools/validate-semantic.py --html templates/sub_list.html --css templates/css/common.css 2>&1 | grep -cE "ERROR|WARN" || echo 0
   ```
   결과를 응답에 포함

작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T01`

## 규칙

- 단일 파일 `tools/validate-semantic.py` 리팩터링만. 새 모듈 분리 금지 (1500 라인 초과 시 예외).
- 기존 `check_*` 함수명 보존 (rules.yaml의 `custom_handler` 메타가 참조).
- `rules/rules.yaml`은 SoT — 절대 수정 금지.
- git commit은 하지 마세요 — PM이 직접 커밋합니다
- [MANDATORY] AC-001~004 모두 응답에 포함
- pyyaml 외 외부 의존성 추가 금지

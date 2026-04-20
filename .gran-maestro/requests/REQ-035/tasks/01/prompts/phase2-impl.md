# Implementation Request — REQ-035 / Task 01

**Request**: REQ-035 (Phase B — Pydantic SSOT 자동 파생)
**Task**: 01 — Pydantic v2 SSOT 모델 정의 + validation_schema 자동 생성
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T01`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-035/tasks/01/spec.md`
**Plan**: `/mnt/d/dev-base/.gran-maestro/plans/PLN-010/plan.md`

---

## 구현 컨텍스트

`rules/rules.yaml` (SSOT) 에 정의된 63개 규칙을 **Pydantic v2 모델 기반 내부 SSOT** 로 승격한다.
Pydantic 모델이 rules.yaml 을 로드하여 구조적으로 검증하고, `model_json_schema()` 로 `rules/validation_schema.json` 을 자동 생성한다.
수동 편집 경로를 제거하고, `<!-- AUTO-GENERATED FROM rules/models.py — DO NOT EDIT -->` 주석을 삽입한다.

핵심 원칙:
- **add-only**: `rules/rules.yaml` 자체의 구조/내용은 변경하지 않는다 (읽기 전용)
- **semantic equivalence**: 생성된 `validation_schema.json` 은 기존 파일 대비 rule ID 목록/type enum/severity enum 이 의미적으로 동등해야 한다
- **외부 의존성**: `pydantic>=2.6` 만 추가 (yaml 로더는 기존 `pyyaml` 재사용)

## 자기탐색 지시

0. `§0 Context Manifest` 목록 파일을 모두 Read:
   - `rules/rules.yaml` (전체)
   - `rules/validation_schema.json` (전체)
   - `tools/check-rules-drift.py` (구조 파악)
   - `tools/build-rules.py` (참고)
   - `pyproject.toml`
   - `tests/unit/` 디렉토리 샘플 테스트 2~3개 (스타일 파악)

1. `spec.md` 의 §3 AC 5개 숙지

2. **의존성 설치**:
   ```bash
   pip install --break-system-packages --user "pydantic>=2.6" pyyaml
   ```
   (시스템 정책상 `--break-system-packages --user` 필요. 이미 설치돼 있으면 skip)

3. **`rules/models.py` 신규 작성**:
   - Python 3.10+ 문법 (typing, dataclasses, enum)
   - Pydantic v2 API 사용 (`from pydantic import BaseModel, Field, field_validator` 등)
   - 핵심 모델:
     - `class ValidationType(str, Enum)`: `regex_must_not_match`, `regex_must_match`, `regex_should_match`, `ast_selector_count`, `value_equals_mapping`, `html_tag_required`, `forbidden_substring`, `required_substring`, `naming_pattern`, `numeric_range`, `custom` (rules.yaml `validation_types` 섹션 그대로)
     - `class Severity(str, Enum)`: `error`, `warning`, `info`, `deprecated`
     - `class Profile(str, Enum)`: `common`, `basic`, `landing`, `figma`, `enhancement`
     - `class Category(str, Enum)` 또는 `str`: rules.yaml `categories` 섹션을 동적 로드
     - `class RuleDefinition(BaseModel)`: `id: str`, `category: str`, `type: ValidationType`, `severity: Severity`, `pattern: Optional[str]`, `message: str`, `profiles: list[Profile]`, `priority: Optional[int]`, `custom_handler: Optional[str]`, 기타 rules.yaml 에서 실제로 사용되는 optional 필드 포함
     - `class CategoryDefinition(BaseModel)`: id / description 등
     - `class ValidationSchema(BaseModel)`: `schema_version: str`, `rules: list[RuleDefinition]`, `categories: list[CategoryDefinition]`
   - 함수:
     - `def load_rules() -> list[RuleDefinition]`: `rules/rules.yaml` Read + 파싱 + 각 rule 을 `RuleDefinition` 으로 변환 + 총 개수 검증 (= 63)
     - `def generate_schema() -> dict`: `ValidationSchema.model_json_schema()` 반환, 또는 rules 배열과 함께 dict 구조 구성
     - `def write_schema(output_path: str)`: 생성된 dict 를 JSON 으로 직렬화 + 최상위에 `"$comment": "AUTO-GENERATED FROM rules/models.py — DO NOT EDIT"` 필드 주입 (JSON comment 불가)
     - `if __name__ == "__main__":` 블록에서 `python -m rules.models` 실행 시 `rules/validation_schema.json` 덮어쓰기

4. **`rules/__init__.py`** 확인/작성: `rules` 가 Python package 로 동작하도록 `__init__.py` 존재 여부 확인, 없으면 빈 파일 생성

5. **`pyproject.toml` 업데이트**:
   - 기존 파일이 minimal (pytest 만) 상태라면 `[project]` 섹션 추가:
     ```toml
     [project]
     name = "dev-base"
     version = "0.1.0"
     requires-python = ">=3.10"
     dependencies = [
       "pydantic>=2.6",
       "pyyaml>=6.0",
     ]
     ```
   - `[tool.pytest.ini_options]` 섹션은 유지

6. **검증 테스트 파일 5개 신규 작성** (`tests/unit/` 아래):
   - `test_pydantic_rules_load.py`: `from rules.models import load_rules; assert len(load_rules()) == 63` + 각 rule 이 `RuleDefinition` 인스턴스인지 확인
   - `test_schema_autogen.py`: `python -m rules.models` 실행 후 `rules/validation_schema.json` 이 생성됐는지 확인 + 기존 파일과 rule ID 목록 비교
   - `test_schema_autogen_header.py`: `validation_schema.json` 최상위 `$comment` 또는 첫 줄에 "AUTO-GENERATED" 문자열 존재
   - `test_pyproject_deps.py`: `pyproject.toml` 에 `pydantic>=2.6` 문자열 존재
   - (이미 `tests/` 에 existing test가 있으므로 통합 호환 주의)

7. **validation_schema.json 재생성 검증**:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T01
   # 기존 파일 백업
   cp rules/validation_schema.json rules/validation_schema.json.before_req035

   # 자동 생성
   python3 -m rules.models

   # 비교 (rule ID 목록만 의미 비교)
   python3 -c "
   import json
   a = json.load(open('rules/validation_schema.json.before_req035'))
   b = json.load(open('rules/validation_schema.json'))
   ids_a = set(r['id'] for r in a.get('rules', []))
   ids_b = set(r['id'] for r in b.get('rules', []))
   missing = ids_a - ids_b
   added = ids_b - ids_a
   print(f'missing in new: {missing}')
   print(f'added in new: {added}')
   assert not missing, f'rule ID regression: {missing}'
   "

   # 백업 파일 삭제
   rm rules/validation_schema.json.before_req035
   ```

8. **전체 회귀 테스트**:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T01
   pytest tests/ -v 2>&1 | tail -40
   ```
   - 기존 113+ passed + 신규 5개 테스트 passed 모두 0 failed 확인

9. **git 커밋 금지** — PM 이 직접 커밋. 변경 사항만 남기고 커밋은 하지 마세요.

## 규칙

- Python 3.10+ 문법 허용
- Pydantic v2 전용 (v1 API — `BaseConfig`, `validator`, `parse_obj` 등 — 사용 금지; v2 는 `model_config`, `field_validator`, `model_validate`)
- `rules/rules.yaml` 파일은 읽기 전용 (수정 금지)
- `validation_schema.json` 은 완전히 재생성되지만 기존 rule ID 목록은 100% 보존 (추가 가능, 삭제 금지)
- 외부 의존성은 pydantic/pyyaml 만. 다른 추가 금지.
- 에러 메시지는 한국어 허용, 코드 주석은 영어만
- atomic write 권장 (tempfile + os.replace)

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T01`

## 완료 후 산출물

- `rules/models.py` (신규)
- `rules/__init__.py` (없으면 신규)
- `rules/validation_schema.json` (재생성됨)
- `pyproject.toml` (dependencies 확장)
- `tests/unit/test_pydantic_rules_load.py` (신규)
- `tests/unit/test_schema_autogen.py` (신규)
- `tests/unit/test_schema_autogen_header.py` (신규)
- `tests/unit/test_pyproject_deps.py` (신규)
- 위 8번 회귀 테스트 통과 (전체 pytest ≥ 118 passed / 0 failed)

## [MANDATORY] 응답에 반드시 포함할 것

1. `rules/models.py` 전체 내용 (코드 블록)
2. `rules/validation_schema.json` 재생성 검증 출력 (missing: set(), added: {...})
3. `pytest tests/ -v` 전체 출력의 마지막 40줄 (summary 포함: `=== N passed, M skipped, 0 failed ===`)

# Implementation Request — REQ-035 / Task 02

**Request**: REQ-035 (Phase B — Pydantic SSOT 자동 파생)
**Task**: 02 — check-rules-drift 승격 + figma-validate handler Pydantic 재정렬
**Worktree**: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T02`
**Spec**: `/mnt/d/dev-base/.gran-maestro/requests/REQ-035/tasks/02/spec.md`
**Plan**: `/mnt/d/dev-base/.gran-maestro/plans/PLN-010/plan.md`

**선행 작업 (이미 완료)**: Task 01 커밋 `5b6a966` — `rules/models.py` + `validation_schema.json` 자동 생성 + 신규 테스트 5종

---

## 구현 컨텍스트

Task 01 에서 도입된 `rules/models.py` (Pydantic v2 SSOT) 를 활용하여:

1. **`tools/check-rules-drift.py` 승격**: Pydantic `ValidationSchema` 를 정합 기준으로 삼아 `rules.yaml` ↔ `figma-validate.py` handler 3자 정합 감지로 재작성. 기존 63/63 in sync 결과 유지.
2. **`tools/figma-validate.py` handler 재정렬**: handler dispatch 시 Pydantic `RuleDefinition` 인스턴스를 인자로 수용하도록 시그니처/호출 경로 정비. 기존 `_stub_handler` MAJOR FAIL 정책은 유지 (구조 변경 없음, Pydantic 기반 dispatch 만 적용).

## 자기탐색 지시

0. `§0 Context Manifest` 전체 Read:
   - `rules/models.py` (Task 01 산출물 — 모델 정의)
   - `rules/rules.yaml`
   - `rules/validation_schema.json` (Task 01 자동 생성물)
   - `tools/check-rules-drift.py` (현재 드리프트 감지 — 리팩토링 대상)
   - `tools/figma-validate.py` (handler 정의 — 시그니처 재정렬 대상)
   - `tools/post-impl-verify.py` (drift cache 참고)
   - 기존 tests/ 에서 drift 관련 테스트 샘플 1~2개

1. `spec.md` 의 §3 AC 4개 숙지

2. **의존성 이미 설치됨** — Task 01 에서 pydantic/pyyaml 설치 완료. 추가 설치 불필요.

3. **`tools/check-rules-drift.py` 리팩토링**:
   - 기존 CLI 인터페이스 유지: `--all` 모드, exit code 0/1
   - 내부 로직:
     - `from rules.models import load_rules, generate_schema` import
     - Pydantic 기반 rule 목록을 **정답 세트** 로 사용
     - rules.yaml hash / validation_schema.json hash / figma-validate handler 레지스트리 비교
     - 모든 rule ID 가 3자에서 일치 → "63/63 rules in sync" 출력, exit 0
     - 불일치 rule 감지 → 어느 계층에서 누락됐는지 리포트 + exit 1

4. **`tools/figma-validate.py` handler 재정렬**:
   - 기존 `run_v2_categories()` / `validate_text_nodes()` / `validate_frame_nodes()` / `validate_interactions()` 함수 시그니처는 불변 유지
   - handler dispatch 경로 (예: rule 별 dispatch 가 있는 부분) 에서 `RuleDefinition` 인스턴스를 인자로 수용
   - 기존 `_stub_handler` 의 MAJOR FAIL 반환은 그대로 유지
   - 카테고리 개수 (v1 9 + v2 14 = 23) 불변

5. **검증 테스트 작성**:
   - `tests/unit/test_drift_detection_on_injection.py` (신규): Pydantic 모델에서 rule 1개를 fixture 기반으로 빼고 drift 감지가 exit 1 반환하는지 확인 + 테스트 후 rollback
   - `tests/unit/test_handler_pydantic_signature.py` (신규): figma-validate handler 가 `RuleDefinition` 인스턴스를 인자로 받아 동작하는지 확인
   - `tests/regression/test_drift_zero.py` (신규 또는 기존 확장): 실제 63 rules 정합 확인 (`python3 tools/check-rules-drift.py --all` → exit 0)
   - `tests/regression/test_figma_validate_categories.py` (신규 또는 기존 확장): `figma-validate.py --version-info` 출력이 v1=9 + v2=14 유지

6. **검증 명령**:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T02

   # drift 감지 실행
   python3 tools/check-rules-drift.py --all
   # expected: "63/63 rules in sync" + exit 0

   # figma-validate 카테고리 확인
   python3 tools/figma-validate.py --version-info
   # expected: v1=9, v2=14, total=23

   # 전체 회귀 테스트
   pytest tests/ -v 2>&1 | tail -40
   # expected: Task 01 기준 118+ passed, 신규 Task 02 테스트 추가분 포함, 0 failed
   ```

7. **git 커밋 금지** — PM 이 직접 커밋.

## 규칙

- Task 01 의 `rules/models.py` 를 수정하지 않는다 (읽기 전용)
- `rules/rules.yaml`, `rules/validation_schema.json` 내용은 변경하지 않는다 (Task 01 산출물 보존)
- `tools/figma-validate.py` 의 run_v2_categories / validate_text_nodes 등 핵심 함수의 **공개 시그니처** 는 변경 금지 (내부 dispatch 경로만 재정렬)
- 기존 테스트가 깨지면 안 됨 — 전체 pytest 0 failed 유지
- 코드 주석은 영어만

## 작업 디렉토리

`/mnt/d/dev-base/.gran-maestro/worktrees/REQ-035-T02`

## 완료 후 산출물

- `tools/check-rules-drift.py` (리팩토링)
- `tools/figma-validate.py` (handler dispatch 재정렬)
- `tests/unit/test_drift_detection_on_injection.py` (신규)
- `tests/unit/test_handler_pydantic_signature.py` (신규)
- `tests/regression/test_drift_zero.py` (신규 또는 확장)
- `tests/regression/test_figma_validate_categories.py` (신규 또는 확장)

## [MANDATORY] 응답에 반드시 포함할 것

1. `tools/check-rules-drift.py` 리팩토링된 전체 코드
2. `tools/figma-validate.py` 변경 diff 요약 (주요 함수 변경부)
3. 검증 명령 6번 출력 전체
4. `pytest tests/ -v` 마지막 40줄 (summary 포함)

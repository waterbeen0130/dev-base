# REQ-001 T01: pytest smoke test 환경 구축

## §0 Context Manifest

> 아래는 시작점 힌트입니다. 구현 중 자율적으로 추가 탐색하세요.

- `tools/figma-extract.py` — 테스트 대상 (핵심 함수: rgba_to_hex, extract_fill_color, line_height_to_ratio, figma_align_to_css)
- `package.json` — 기존 프로젝트 설정 참조
- `/mnt/d/dev-base/.gran-maestro/agile/AGI-001/objective/objective.md` — 프로젝트 목표

## §1 요약

figma-extract.py의 핵심 유틸리티 함수를 검증하는 pytest smoke test 환경을 구축한다. pyproject.toml에 pytest 설정을 추가하고, tests/ 디렉토리에 smoke test 1개를 작성한다.

## §2 범위

### 포함
- pyproject.toml 생성 (pytest 설정)
- tests/__init__.py 생성
- tests/test_smoke.py 생성 (figma-extract.py 핵심 함수 import + 기본 검증)

### 제외
- 커버리지 설정
- CI/CD 연동
- 기존 파일 수정
- 복잡한 fixture/mock

## §3 수락 조건

### AC-001 [automatable] pyproject.toml pytest 설정
- **Given**: 프로젝트 루트에 pyproject.toml이 없는 상태
- **When**: pyproject.toml을 생성하고 pytest 설정을 추가할 때
- **Then**: `[tool.pytest.ini_options]` 섹션이 존재하고 testpaths에 "tests"가 포함됨
- **Test**: `python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); assert 'tests' in str(d['tool']['pytest']['ini_options']['testpaths'])"`

### AC-002 [automatable] tests ���렉토리 및 smoke test 파일 존재
- **Given**: tests/ 디렉토리가 없는 상태
- **When**: tests/ 디렉토리와 smoke test 파일을 생성할 때
- **Then**: tests/__init__.py와 tests/test_smoke.py가 존재함
- **Test**: `test -f tests/__init__.py && test -f tests/test_smoke.py`

### AC-003 [automatable] smoke test가 핵심 함수를 import하여 검증
- **Given**: figma-extract.py에 rgba_to_hex, extract_fill_color 함수가 존재
- **When**: smoke test를 실행할 때
- **Then**: rgba_to_hex와 extract_fill_color를 import하여 기본 입출력을 검증하는 테스트가 통과함
- **Test**: `pytest tests/test_smoke.py -v`

### AC-004 [automatable] pytest 전체 실행 통과
- **Given**: pyproject.toml과 tests/test_smoke.py가 모두 준비된 상태
- **When**: `pytest` 명령을 실행할 때
- **Then**: 모든 테스트가 PASSED 상태로 완료됨
- **Test**: `pytest --tb=short`

## §3.3 PAC Mapping

| PAC ID | Grade | Mapped Spec AC IDs | Coverage |
|--------|-------|--------------------|----------|
| PAC-1 | MUST | AC-001 | Covered |
| PAC-2 | MUST | AC-002 | Covered |
| PAC-3 | MUST | AC-003 | Covered |
| PAC-4 | MUST | AC-004 | Covered |

## §3.4 Epic DoD Mapping

| DoD ID | DoD 설명 | Mapped Spec AC IDs | Coverage |
|--------|---------|-------------------|----------|
| DOD-001 | 정규화된 JSON 변환 | - | Sprint 0 (테스트 인프라) |
| DOD-002 | 변환 규칙 문서화 | - | Sprint 0 (테스트 인프라) |

> 이 REQ는 Sprint 0 테스트 환경 구축으로, 개별 DoD에 직접 매핑되지 않음. 이후 Sprint에서 DOD-001~007 구현 시 이 테스트 환경 활용.

## §3.5 Constraints
- Python 3.x 호환
- pytest만 사용 (추가 라이브러리 금지)
- 기존 파일 수정 금지

## §5 선행 작업 (blockedBy)
- 없음

## §5 후행 작업 (blocks)
- 없음

## §7 Assigned Agent
[config: codex-dev] → codex-dev (Python 테스트 환경 구축, 단일 태스크)

## §8 실행 지시

### 구현 순서
1. 프로젝트 루트에 `pyproject.toml` 생성
2. `tests/__init__.py` 빈 파일 생성
3. `tests/test_smoke.py` 작성:
   - `sys.path`에 `tools/` 추가하여 `figma-extract.py`에서 함수 import 가능하게 처리
   - `rgba_to_hex` 기본 테스트 (예: `rgba_to_hex(1, 0, 0) == '#f00'`)
   - `extract_fill_color` 기본 테스트 (SOLID fill dict 입력 → hex 출력)
4. `pytest` 실행하여 전체 통과 확인

### 주의사항
- `figma-extract.py`는 `tools/` 디렉토리에 위치. import 경로 설정 필요.
- 기존 `figma-extract.py` 코드는 절대 수정하지 않음.

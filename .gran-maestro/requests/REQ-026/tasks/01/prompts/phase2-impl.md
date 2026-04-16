# Implementation Request — REQ-026 / Task 01

- Request: REQ-026 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-026-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-026/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-008/plan.md

## 구현 컨텍스트 (PM 작성)

REQ-026은 PLN-008 5단계 개선의 **3단계(B)** — 결정론적 위반 자동 수정 시스템 구축. DBG-001이 식별한 **H3(Post-hoc 검증 + auto-fix 부재)** 구조적 해소가 목표입니다.

**핵심 작업 3가지**:
1. `tools/repair-from-violations.py` 신규 작성 (CLI + 8종 결정론적 치환)
2. `tools/post-impl-verify.py`에 auto-repair 1회 루프 통합 (`--no-repair` 플래그 추가)
3. `tools/validate-semantic.py --fix` 미구현 상태 해소 (REQ-024 이후에도 여전히 stub)

**치환 8종**: pill radius(999px→2em), rgba 불투명→hex, rgb→hex, 8자리hex(알파 FF)→6자리, 멀티라인 셀렉터 한 줄, 미디어쿼리 내부 들여쓰기 제거, letter-spacing px→em(font-size 컨텍스트 필요), 동일 셀렉터 중복 통합.

**기술 선택**:
- CSS 파싱: `tinycss2` 우선. 없으면 `pip install tinycss2` 후 사용. 정규식 fallback 허용.
- HTML: BeautifulSoup4 또는 정규식 (letter-spacing em 변환 시 font-size lookup에만 사용)
- 멱등성 필수

**주의**:
- REQ-024가 남긴 `rules/rules.yaml`의 TODO(REQ-026) 마커 3건(:173, :197, :208)을 이번 REQ에서 제거해야 합니다 (auto-fix 완성 후 해당 규칙이 자동 처리 가능해지므로).
- `rules/deprecated.md`에 auto-fix로 대체된 규칙 ID와 매핑 기록 추가.
- **회귀 샘플**은 `output/youngwol/` + `extracted/section_03_spec.json`, `section_04_spec.json` 사용. REQ-024 TS-005에서 이미 검증 경로 확인됨.
- git commit은 하지 마세요 — PM이 처리합니다. `git add`도 하지 말고 수정만 하세요.
- 완료 전 spec §3.5 Test Scenarios TS-001~008 **전부 실행**하고 출력 전체를 응답에 포함하세요.

[REFERENCE_CONTEXT]
current_date: 2026-04-16
model_cutoff: unknown
references: none
[/REFERENCE_CONTEXT]

## 자기탐색 지시

1. spec.md 전체 Read (/mnt/d/dev-base/.gran-maestro/requests/REQ-026/tasks/01/spec.md)
2. plan.md Read (/mnt/d/dev-base/.gran-maestro/plans/PLN-008/plan.md)
3. 기존 `tools/post-impl-verify.py` 전체 Read (REQ-024 파서 버그픽스 반영 상태)
4. 기존 `tools/validate-semantic.py`에서 `--fix` 플래그 처리 위치 파악 (grep `--fix`)
5. `rules/rules.yaml`에서 TODO(REQ-026) 마커 3건 위치 확인
6. `rules/deprecated.md` 현재 포맷 확인 후 같은 형식으로 이동 이력 추가
7. TDD: 테스트 먼저 작성 후 구현 (AC-001~006)
8. [MANDATORY] TS-001~008 전부 실행하고 출력 전체를 응답에 포함

## 규칙

- spec §2의 수정 범위(`tools/`, `tests/`, `rules/rules.yaml`, `rules/deprecated.md`) 외 파일 수정 금지
- git commit/add 금지 — PM이 처리
- 멱등성 필수 (같은 입력 2회 실행 시 변경 0건)
- `--dry-run` 시 파일 수정 금지, diff만 출력
- 기존 post-impl-verify exit 코드 체계 변경 금지
- [MANDATORY] TS-001~008 전부 실행 후 출력 포함

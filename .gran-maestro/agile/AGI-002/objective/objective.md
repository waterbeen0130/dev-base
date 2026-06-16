---
agi_id: AGI-002
status: active
version: 1
created_at: 2026-04-21
---

# Objective: dev-base Figma 파이프라인 — 새 워크플로우 전환

## 진행 상태 요약

- 현재 Sprint: 0 (테스트 환경 구축 예정)
- 완료 DoD: 0 / 7
- 활성 단계: agile-plan 완료 → 스프린트 루프 진입 예정

## JTBD 레이어

- **When (상황)**: 디에스솔루션 a_main 작업 중 기존 파이프라인이 false-positive 다발 + AI 우회(generate.py 자동 생성) + Figma 수치 부정확 + 룰 위반 다수 발생. 사용자가 매번 같은 종류의 지적을 반복해야 했음.
- **I want (목표)**: dev-base 의 Figma→퍼블리싱 파이프라인을 PNG 시각 분석 + spec.json 정밀 보정 기반 새 워크플로우로 완전 전환한다.
- **So I can (가치)**: 새 프로젝트마다 반복 지적 없이 룰 준수 + 피그마 수치 정확 결과물을 보장받는다.
- **성공 지표**:
  - 폐기 파일 0 참조 (grep dev-base 전체)
  - 신규 3 도구 (`figma-png-download.py`, `asset-copy.py`, `pm-verify.py`) 동작 + 사용 예시 검증
  - PNG 분석 → 외주 AI 자동 선정 + 사유 통지 동작
  - 새 `init-project.py` 가 CLAUDE.md 룰 강제 템플릿 배포
  - pm-verify false-negative 회귀 케이스 1건 이상 통과
- **완료 정의 (프로젝트 DoD)**: 아래 DoD 7건 모두 충족

## 프로젝트 완료 기준 (DoD)

### DOD-001 — 폐기 도구 완전 삭제
- **Direction**: 제거한다
- **Measure**: grep 매칭 0건
- **Object**: `tools/.deprecated/` 11개 도구 + 관련 wrapper 함수 + dev-base 내 모든 참조
- **Context**: dev-base 어떤 스킬/문서/CLAUDE.md/rules.yaml/templates 에서도 참조되지 않아야 함
- **Target**: 완전 삭제 (git rm) — 백업 불필요

<!-- dod:DOD-001 status:done priority:must -->

### DOD-002 — 신규 3 도구 동작 검증
- **Direction**: 검증한다
- **Measure**: 인자 검증 + 정상 출력 + error 시 PM 콜백 + 사용 예시 1건 PASS
- **Object**: `figma-png-download.py`, `asset-copy.py`, `pm-verify.py`
- **Context**: 새 워크플로우의 핵심 도구로 사용
- **Target**: 3 도구 모두 통과

<!-- dod:DOD-002 status:done priority:must -->

### DOD-003 — 기존 워크플로우 설명 제거
- **Direction**: 대체한다
- **Measure**: 기존 워크플로우 키워드(자동 재시도 루프, generate.py, POLICY-1 강제, json-to-html.py, repair-from-violations) 0건 매칭
- **Object**: `CLAUDE.md`, `rules/common.md`, `rules/CLAUDE.md`, `rules/landing.md`, `rules/basic.md`, `rules/ai-pipeline.md`, `rules/publishing-workflow-guide.md`
- **Context**: 새 워크플로우 (PNG → AI 선정 → spec.json 정밀 → pm-verify) 로 모두 대체
- **Target**: grep 0건

<!-- dod:DOD-003 status:done priority:must -->

### DOD-004 — PNG 분석 → 외주 AI 자동 선정
- **Direction**: 자동 선정한다
- **Measure**: 점수표 + LLM 판단 혼합으로 gemini/codex/claude 중 하나 선택 + 선정 사유 + 사용자 통지 출력
- **Object**: PNG 복잡도(자산 수, 섹션 수, 이미지 fill 유무, 레이어 겹침, 텍스트 비중)
- **Context**: 새 도구 또는 pm-verify 의 일부로 통합
- **Target**: 임의 PNG 1건 입력 시 결정 결과 + 사유 출력

<!-- dod:DOD-004 status:done priority:must -->

### DOD-005 — init-project.py 가 새 룰 강제
- **Direction**: 배포한다
- **Measure**: `init-project.py` 가 새 워크플로우 CLAUDE.md 템플릿을 프로젝트에 배포 + 키워드 검증 (페이지 prefix, 공통 영역 prefix 없음, 시멘틱 마크업, 들여쓰기, hex/em/px)
- **Object**: 새 프로젝트 초기화 시 자동 배포되는 CLAUDE.md / config 템플릿
- **Context**: dev-base/tools/init-project.py + 관련 templates
- **Target**: 새 프로젝트 1건 초기화 시 새 룰 모두 포함 확인

<!-- dod:DOD-005 status:done priority:must -->

### DOD-006 — pm-verify normalize 회귀 줄임
- **Direction**: 줄인다
- **Measure**: 기존 false-negative 패턴 (`\n`↔`<br>`, HTML escape `&amp;`, span color 상속) 회귀 케이스 1건 이상 PASS
- **Object**: pm-verify.py 의 텍스트 byte-exact, 폰트 5필드, 색상 normalize 로직
- **Context**: 디에스솔루션 검증에서 발견된 false-negative 23건 같은 패턴
- **Target**: 회귀 fixture 1건 + PASS

<!-- dod:DOD-006 status:done priority:should -->

### DOD-007 — 새 워크플로우 실행 매뉴얼
- **Direction**: 정리한다
- **Measure**: details/manual.md 가 다른 사람이 혼자 새 프로젝트 수행 가능한 수준 (단계별 명령어, 의사결정 분기, 체크리스트 포함)
- **Object**: agile 산출물 details/manual.md
- **Context**: AGI-002 의 산출물
- **Target**: 단계별 매뉴얼 작성 완료

<!-- dod:DOD-007 status:done priority:should -->

## 설계 결정 (Architecture Decisions)

### AD-001: 폐기 도구는 완전 삭제 (백업 X)
- **결정**: tools/.deprecated/ 11개 파일 git rm
- **근거**: 사용자 명시 — "백업도 필요없고 아예 삭제". 회수 필요 시 git history 로 복구 가능하므로 별도 백업 불필요.
- **대안 검토**: tools/.deprecated/ 보관 (회수 가능) — 거부됨 (혼란 유발)

### AD-002: PNG 분석 + LLM 판단 혼합 라우팅
- **결정**: 정량 지표(자산 수, 섹션 수, 이미지 fill 유무) + LLM 판단(복잡도, 디자인 의도) 혼합으로 gemini/codex/claude 선정
- **근거**: 정량 단독은 false-positive 위험, LLM 단독은 비결정적. 혼합으로 신뢰도 + 설명력 확보.
- **대안 검토**: 정량 only (단순하지만 정확도 부족) — 거부, LLM only (블랙박스) — 거부

### AD-003: 새 도구 실패 시 PM 콜백 (문서화 X)
- **결정**: 새 도구가 실패하면 stderr + non-zero exit + 호출 PM 에게 control return. 별도 로그 파일 X.
- **근거**: 사용자 명시 — "당연히 PM 한테 콜백, 문서로 따로 남길 필요 없어"

### AD-004: pm-verify normalize 강화 — figma-validate 후처리에 집중
- **결정**: pm-verify.py 가 figma-validate 결과를 후처리하여 false-negative 줄임. figma-validate 자체는 수정하지 않음.
- **근거**: figma-validate 변경은 영향 범위 큼. 후처리가 안전.

## 제약사항 (Out-of-scope / 기술 / 비즈니스)

- **Out-of-scope**: 디에스솔루션 a_main 재검증 (사용자 후속 요청 시에만 별도 진행)
- **기술**: 모든 프로젝트 호환성 강제 X (이번 작업은 새 워크플로우만 고려)
- **비즈니스**: 시간 목표 없음

## 우선순위 (MoSCoW)

- **Must**: DOD-001, DOD-002, DOD-003, DOD-004, DOD-005
- **Should**: DOD-006, DOD-007
- **Could**: 없음
- **Won't (this time)**: 디에스솔루션 a_main 재검증, 모든 프로젝트 호환

## 프로젝트 NFR

- **성능**: 시간 목표 없음
- **보안**: 내부 도구, 보안 요구 없음
- **호환성**: 새 워크플로우만 지원, 기존 프로젝트 호환 강제 X
- **오류 처리**: 새 도구 실패 시 PM 콜백 (별도 로그/문서화 X)

## 리스크 레지스터

| ID | 리스크 | 가능성 | 영향 | 완화 방안 |
|----|-------|-------|------|---------|
| R1 | AI 자동 선정 정확도 부족 (잘못된 AI 선택) | 중 | 높음 | 점수표 + LLM 판단 혼합, 선정 사유 항상 출력하여 수동 override 가능 |
| R2 | pm-verify normalize 가 새 false-positive 만듦 | 중 | 중 | 회귀 fixture 1건 이상 통과 강제 (DOD-006) |
| R3 | tools/.deprecated/ 완전 삭제 후 회수 불가 | 낮 | 중 | git history 로 복구 가능, 삭제 commit 메시지에 명시 |
| R4 | 기존 워크플로우 키워드를 모두 잡지 못해 일부 가이드에 잔존 | 중 | 높음 | grep 검증을 DOD-003 의 measure 로 강제 |

## 참조 레퍼런스

- 이전 메모리 (MEMORY.md):
  - `feedback_unit_pass_is_not_pipeline_pass.md`
  - `feedback_no_figma_node_name_in_classes.md`
  - `feedback_common_vs_page_class_prefix.md`
  - `feedback_pm_verify_before_deliver.md`
  - `feedback_figma_text_fidelity.md`
  - `feedback_no_section_padding.md`
- 디에스솔루션 작업에서 도출된 실패 패턴 (이번 세션 외부 컨텍스트, 디에스솔루션 자체는 out-of-scope)

## 변경 이력

- 2026-04-21: AGI-002 생성, JTBD 정의, DoD 7건 확정 (사용자 OK 저장)

## 상세 문서 (Details)

- [deprecation.md](details/deprecation.md) — 폐기 도구 완전 삭제 + 참조 grep 전수 (DOD-001)
- [new-tools.md](details/new-tools.md) — 신규 3 도구 인자/출력/error 사양 + 회귀 fixture (DOD-002, DOD-006)
- [rules-rewrite.md](details/rules-rewrite.md) — CLAUDE.md / rules/*.md 기존 워크플로우 제거 + 새 워크플로우 대체 (DOD-003)
- [ai-routing.md](details/ai-routing.md) — PNG 분석 → 외주 AI 자동 선정 알고리즘 (DOD-004)
- [init-template.md](details/init-template.md) — init-project.py 가 배포할 새 CLAUDE.md 템플릿 사양 (DOD-005)
- [manual.md](details/manual.md) — 새 워크플로우 실행 매뉴얼 (DOD-007)

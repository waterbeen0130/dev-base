<!-- source-mapping: original=AGI-004/objective-qa-session sections=[조사:검증 체인 분석, accept-preflight-verify, pm-verify-accept-gate.sh] -->
# verification-execution-gate (검증 실행 강제 게이트)

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-006, DOD-007, DOD-011

## 개요

현재 검증은 `mst:accept` 시점의 PreToolUse hook(`pm-verify-accept-gate.sh` → `accept-preflight-verify.py` → `validate-semantic.py`)에서만 강제된다. 즉 워크플로우를 거치지 않고 raw 추출 결과를 폴더에 두고 "검증 끝냈다"고 전달하면 **어떤 게이트도 작동하지 않는다**. 이 도메인은 "검증이 실제 실행되어 통과했다는 증거" 없이는 완료/전달이 차단되도록 게이트를 보강하고, raw 추출 잔재가 최종 산출물로 오인되지 않게 산출물 경계를 인식시킨다.

## 설계 결정

### AD-002: 검증 실행 증거 기반 완료 게이트
- **결정**: 완료/전달 판정의 신뢰 소스를 "에이전트 자가보고"가 아니라 "pm-verify 실제 실행 흔적(exit code 0 + 타임스탬프된 리포트 산출물 + 검증 대상 파일 해시 일치)"으로 한다.
- **근거**: "검증까지 끝내고 줘"가 지켜지지 않은 핵심 원인은 검증 실행 자체가 강제되지 않았기 때문. CLAUDE.md:59 "외주 AI 자가 보고 신뢰 후 전달 금지" + memory `feedback_pm_verify_before_deliver`와 정합.
- **대안 검토**: (a) accept hook만 강화 — 워크플로우 외부 경로를 못 막음. (b) 완료 보고 단계에 증거 체크 추가 — 채택. 검증 리포트 산출물(예: `pm-verify-report.json`)을 필수 아티팩트로 요구하고, 해당 리포트가 현재 산출물 해시와 일치하는지 확인.

### AD-006: 산출물 경계 인식
- **결정**: 검증 대상 = "최종 산출물"임을 명확히 하고, raw 추출 잔재(`extracted/`, `*_base.html` 등 추출 직후 미가공본)는 최종물과 구분한다.
- **근거**: 실제 케이스에서 `html/page/index.html`(가공물)과 `html/extracted/main_base.html`(729줄 raw)이 공존했고, raw 쪽이 위반 덩어리였다. 검증이 어느 쪽을 봐야 하는지 규정이 없었다.

## 상세 명세

### 1. 검증 실행 증거 정의 (DOD-006)
- 필수 아티팩트: 검증 리포트 파일(JSON) — `{verified_at, html_path, css_path, html_sha, css_sha, exit_code, critical_count, major_count, report_lines[]}`.
- 통과 조건: `exit_code == 0` AND `critical_count == 0` AND 리포트의 `html_sha`/`css_sha`가 현재 산출물과 일치.
- 게이트 동작: 위 증거가 없거나 해시 불일치(=검증 후 코드가 또 바뀜)면 완료/전달 차단.

### 2. 우회/자가보고 탐지 (DOD-007)
- 검증 리포트 부재 → "검증 미실행"으로 판정, 차단.
- 리포트는 있으나 산출물 해시 불일치 → "검증 후 변경됨, 재검증 필요"로 판정, 차단.
- 리포트 타임스탬프가 산출물 mtime보다 과거 → 차단.

### 3. 기존 체인과의 관계 (하위 호환)
```
[추출 완료]
   → pm-verify 실행 → pm-verify-report.json 산출 (신규: 증거 아티팩트)
   → [완료/전달 게이트] 증거 검사 (신규)
        ↓
[mst:accept] → pm-verify-accept-gate.sh → accept-preflight-verify.py
   → validate-semantic.py → [CRITICAL] count → block/allow (기존 유지)
```
- accept-gate가 의존하는 `[CRITICAL]` 출력 규약은 보존(NFR 호환성).
- 신규 게이트는 accept 이전(완료 보고 시점)에 1차 방어선을 추가하는 형태.

### 4. 산출물 경계 인식 (DOD-011)
- 최종 산출물 경로 규정: 프로젝트 표준(예: `html/` 직하 또는 명시 deliverable 경로). raw 추출물은 `extracted/`(또는 `.gran-maestro/`)에 격리.
- 검증 대상 자동 탐색 시 raw 추출 디렉토리는 기본 제외하고, 최종 산출물만 검증 대상으로 선정.
- raw 잔재가 최종 경로에 섞여 있으면 경고.

### 5. R3 리스크 (우회 경로)
- 게이트는 워크플로우/완료 보고 경로에 걸린다. 사용자가 완전히 수동으로 폴더만 복사하는 경로는 기술적으로 100% 막을 수 없다 → 이 한계를 리스크로 문서화하고, 최소한 dev-base 표준 완료 경로에서는 강제되도록 한다.

## Q&A 보강 사항

- 사용자 핵심 불만: "검증까지 끝내고 주라고 했는데" 안 됨 → 본 도메인이 그 직접 해결책(Must DOD-006).
- 자가보고 불신은 memory(feedback_pm_verify_before_deliver, feedback_unit_pass_is_not_pipeline_pass)와 일관 → 증거 기반 게이트로 구현.

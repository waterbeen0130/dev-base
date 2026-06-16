# PLN-013 — 파이프라인 검증 결함 수정 + gemini 규칙 준수 개선

- 생성일: 2026-04-21
- Cynefin: Complicated
- 상태: active
- 근거 리포트: `.gran-maestro/requests/REQ-046/tasks/01/drill-report-v2.md`

## 1. 요청 (Refined)

REQ-046 드릴 런 V2 에서 **파이프라인 검증 레이어가 거짓 PASS 를 반환하는 구조적 결함** 을 발견했다. `figma-validate.py` 와 `validate-semantic.py` 가 CRITICAL 위반이 있어도 `exit 0` 반환하므로, 수렴 루프 (`post-impl-verify --converge`) 가 무의미해지고 pipeline 전체가 거짓 PASS 상태로 진행된다. 이 plan 에서 (1) validator exit code 결함 수정, (2) `validate-semantic.py` 상대경로 버그 수정, (3) PM 자동 asset 복사 단계 추가, (4) gemini 브리프 재설계, (5) asset_manifest local_path 정규화 헬퍼, (6) gemini 모델 fallback 체인을 수행하여 파이프라인을 "거짓 PASS" 상태에서 "실질 검증 가능" 상태로 복구한다.

## 2. 범위

**포함**
- **CRITICAL 수정**:
  - `tools/figma-validate.py`: CRITICAL 건수 > 0 → `sys.exit(1)` 반환
  - `tools/validate-semantic.py`: CRITICAL 건수 > 0 → `sys.exit(1)` 반환
  - `tools/validate-semantic.py`: `rules/rules.yaml` 하드코딩 상대경로 → `Path(__file__).parent.parent / 'rules' / 'rules.yaml'` 로 변경
- **HIGH**:
  - `tools/post-impl-verify.py` 또는 신규 `tools/copy-assets.py`: `asset_manifest.local_path` → `output/a_main/img/` 자동 복사 스크립트 추가
  - `rules/templates/publishing/impl-request.md`: gemini 브리프 재설계 — 규칙 체크리스트를 짧고 강하게 (현재 장문 규칙이 gemini 에 의해 무시됨)
- **MEDIUM**:
  - asset_manifest local_path 정규화 헬퍼 — `extracted/{section}/vectors/*.svg` → `./img/{id_safe}.svg` 매핑
  - `mst.py resolve-model gemini`: fallback 체인 (`gemini-3.1-pro-preview → gemini-2.5 → gemini-default`)
- **통합 검증**: REQ-043/046 수정된 output 으로 4종 게이트 재실행, 이번엔 실제로 CRITICAL 0건 + exit 0 달성

**제외**
- 신규 validator 추가 (기존 수정만)
- gemini 모델 자체 개선 (프롬프트 설계만)
- 전체 파이프라인 리팩터링 (점진 개선만)
- REQ-043/046 디에스솔루션 output 자체 재시도 (별도 plan)

## 3. 결정 사항

### Validator exit code 기준
- **CRITICAL 건수 > 0 → `exit 1`** (수렴 루프 재dispatch 신호)
- **CRITICAL 0 + MAJOR 건수 > 0 → `exit 0` + stderr warning** (허용)
- **전체 0건 → `exit 0`**

### gemini 브리프 재설계 방향
현재 장문 규칙(150줄) 이 gemini 에 의해 무시됨. 대안:
- 짧은 체크리스트 (핵심 20줄)
- `rules_version: 2` + `rule_ids: [all]` 사용 (rules.yaml 참조)
- **완료 전 self-check 명령** 을 프롬프트에 포함 (agent 가 실제로 실행해야 함)

### asset 복사 정책
- spec 생성 시: `extracted/{section}/{vectors|images}/*.{svg|png}` 에 저장 (REQ-044 기존)
- HTML 구현 시: AI 가 `<img src="./img/xxx.svg">` 로 작성
- PM 자동 단계: `copy-assets.py --manifest extracted/*_asset_manifest.json --output output/a_main/img/` 로 일괄 복사 + local_path 재매핑

### REQ 분리 방침
- **REQ-A**: validator exit code 수정 (CRITICAL #7 + #8) — codex-dev 단일 REQ, 테스트 중심
- **REQ-B**: PM 자동 asset 복사 + local_path 정규화 (HIGH #9 + MEDIUM #10) — codex-dev
- **REQ-C**: gemini 브리프 재설계 (HIGH #11) — claude-dev (문서 수정)
- **REQ-D**: gemini 모델 fallback (MEDIUM #12) — codex-dev

4 REQ 체인. REQ-A/B/C/D 모두 독립, 병렬 실행 가능.

## 4. 인수 기준 초안

- [MUST] [TIER-A] `figma-validate.py` 가 CRITICAL 위반 존재 시 `exit 1` 반환
- [MUST] [TIER-A] `validate-semantic.py` 가 CRITICAL 위반 존재 시 `exit 1` 반환
- [MUST] [TIER-A] `validate-semantic.py` 를 dev-base 외 디렉토리에서 호출해도 `rules/rules.yaml` 정상 로드
- [MUST] [TIER-A] 단위 테스트: CRITICAL 있는 fixture 에서 두 validator 가 exit 1 반환, CRITICAL 없는 fixture 에서 exit 0 반환
- [MUST] [TIER-A] `copy-assets.py` (또는 post-impl-verify 확장) 가 asset_manifest 기반으로 `output/a_main/img/` 자동 복사
- [SHOULD] [TIER-B] 퍼블리싱 브리프 템플릿이 150줄 → 50줄 이내로 축소되고 핵심 규칙이 체크리스트 형식
- [SHOULD] [TIER-B] `mst.py resolve-model gemini` 가 429 오류 시 fallback 모델 반환
- [SHOULD] [TIER-B] REQ-046 의 디에스솔루션 output 재검증 시 figma-validate `exit 1` 정상 반환 (거짓 PASS 더이상 안 남)

## 5. 범위 예산 (Appetite)

- 총 예상 시간: 4시간 (REQ-A 1.5h + REQ-B 1h + REQ-C 0.5h + REQ-D 0.5h + 통합 검증 0.5h)
- 외주 호출 상한: codex max_retries=2, claude max_retries=2

## 6. 제외 범위 (No-go Scope)

- 신규 validator 추가
- validate-semantic 의 custom handler 재작성 (기존 유지)
- 전체 파이프라인 리팩터링
- CI/CD 통합

## 7. 제약사항

- Python 3 표준 + 기존 pytest
- 기존 fixture 회귀 금지 (CRITICAL 없는 기존 fixture 는 exit 0 유지)
- `rules/rules.yaml` 절대경로화는 breaking change 없이 (기존 dev-base cwd 에서 동작 유지)

## 8. 우선순위 (MoSCoW)

- **Must**: validator exit code 수정 + 상대경로 버그 수정 + 테스트
- **Should**: asset 자동 복사, 브리프 재설계, 모델 fallback
- **Could**: validator 출력 구조화 (JSON 모드), CI 연동
- **Won't**: 신규 validator, 전체 리팩터링

## 9. 의존성

- 선행 필요: 없음 (PLN-012 완료)
- 연관: PLN-011 (드릴 소재 제공), PLN-012 (REQ-044/045/046 기반)

## 10. 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| exit code 변경으로 기존 CI/사용자 스크립트 회귀 | 중 | 중 | CHANGELOG 에 명시, `--no-strict-exit` 옵션 제공 |
| 상대경로 수정이 기존 호출 시 경로 오해 | 낮 | 중 | 다중 cwd 테스트 |
| 브리프 축약이 규칙 누락 유발 | 중 | 상 | 핵심 규칙만 추리고 나머지는 `rules.yaml` 자동 참조 유도 |
| gemini fallback 이 다른 제한에 걸림 | 중 | 하 | 로깅 후 사용자 수동 개입 안내 |

## 11. Loop 종료 조건

- 기존 검증 통과 (AC + max_iterations=2)
- REQ-046 의 디에스솔루션 output 으로 재검증 시 validator exit 1 정상 반환 (실패가 실패로 감지됨)

## 12. 테스트 전략

- 적용 (80% 커버리지)
- 회귀: 기존 `tests/` 의 validator fixture 중 CRITICAL 없는 것 → exit 0 유지
- 신규: CRITICAL 있는 fixture 에서 exit 1 명시 테스트

## 13. 분리 실행

### ① REQ-A: validator exit code + 상대경로 버그 수정
- codex-dev — `tools/figma-validate.py`, `tools/validate-semantic.py`, `tests/`
- blockedBy: 없음

### ② REQ-B: copy-assets.py + local_path 정규화
- codex-dev — 신규 스크립트 + post-impl-verify 통합
- blockedBy: 없음 (REQ-A 와 병렬)

### ③ REQ-C: 퍼블리싱 브리프 재설계
- claude-dev — `rules/templates/publishing/impl-request.md` 축약, `brief-checksum.py` 조정
- blockedBy: 없음 (병렬)

### ④ REQ-D: gemini fallback 체인
- codex-dev — `scripts/mst.py resolve-model` 확장
- blockedBy: 없음 (병렬)

### ⑤ REQ-E: 통합 검증 (디에스솔루션 output 재검증)
- PM 직접 실행 — 위 REQ-A/B/C 완료 후 4종 게이트 재실행, CRITICAL 감지 확인
- blockedBy: [REQ-A, REQ-B, REQ-C]

## 14. Intent (JTBD)

- **When I**: REQ-046 드릴 V2 에서 validator 가 거짓 PASS 를 반환하는 것을 발견했을 때
- **I want to**: validator 들이 CRITICAL 위반 시 exit 1 을 정확히 반환하고, PM 이 asset 복사를 자동화하며, gemini 가 규칙을 실제로 준수하게 만들고 싶다
- **So I can**: 파이프라인의 "거짓 PASS" 결함을 제거해 실제 시각 완성도 향상 피드백 루프를 복구하고, 이후 모든 퍼블리싱 프로젝트에서 reliably 검증 가능한 end-to-end 파이프라인을 사용할 수 있다

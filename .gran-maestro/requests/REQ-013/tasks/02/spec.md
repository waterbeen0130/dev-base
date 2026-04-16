# REQ-013/02 — 통합 검증: 회귀 12 + 신규 fixture + Section_05 false-positive 측정

- Source plan: PLN-005 (3/5)
- Assigned Agent: [config: codex-dev] codex-dev
- Status: pending
- blockedBy: ["01"]
- blocks: []
- Type: test (templates/test-spec.md 기반)

## §1 요약

REQ-013/01 구현 완료 후, 변경된 `figma-validate.py`가 (a) REQ-008/02 회귀 fixture 13개 무회귀 (b) 신규 fixture 14/15 PASS (c) 모제림 Section_05 frame false-positive 50%+ 감소를 모두 만족하는지 통합 검증한다.

## §2 테스트 범위

- **통합 검증**: REQ-008/02 회귀 13개 + 신규 14/15 일괄 실행 (`run_regression.sh`)
- **증분 테스트**: 신규 fixture 14 (pseudo-element), 15 (frame bbox 매칭) 단독 결과 검증
- **회귀 테스트**: 기존 13개 fixture(base + scenarios 1~13)의 PASS/FAIL 카운트 변경 전 baseline 동일 보존
- **현장 검증**: 모제림 Section_05 spec.json + html/css에 대해 보강 전후 frame false-positive 카운트 비교

## §3 통합 AC

### AC-001 [automatable] [regression-test] — 회귀 13 + 신규 2 모두 PASS

- **Given**: REQ-013/01 구현 완료 상태
- **When**: `cd /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures && bash run_regression.sh`
- **Then**: 모든 시나리오(base + scenarios/01..15)의 실제 exit code = expected_exit_code, 총 PASS 카운트 ≥ 14
- **Test**: 위 명령 실행 후 stdout/regression-report.md에서 PASS 카운트 추출, 14 이상 확인

### AC-002 [automatable] — Section_05 false-positive 50%+ 감소

- **Given**: 모제림 Section_05 spec.json (REQ-012 산출, bbox/parent_id 포함) + Section_05 html/css
- **When**: `python3 tools/figma-validate.py --spec {section_05_spec.json} --html {index.html} --css {common.css}` 실행 (PLN-005 §3 기준 frame 매칭 19건 false-positive baseline)
- **Then**: frame 매칭 카테고리 위반이 10건 이하로 출력
- **Test**: stdout grep으로 "frame" 카테고리 위반 카운트 추출 + baseline 19와 비교한 감소율을 보고

### AC-003 [automatable] — pseudo-element li 케이스 0건

- **Given**: scenarios/14-pseudo-before-color-ok fixture
- **When**: 단독 실행
- **Then**: exit 0, `fills color hex 일치` 카테고리 위반 0건
- **Test**: scenarios/14 단독 명령 실행 후 위반 카운트 확인

## §4 회귀 테스트 항목

PM 변경 영향 분석:

1. `compute_direct_element_properties` / `compute_element_properties` — pseudo 분리 후 정상 요소 색상 계산 무회귀 (scenarios/01-color-mismatch, 02-color-ok, 13-inherited-font-ok)
2. `evaluate_frame_rule` / `best_frame_rule` — bbox 미존재 spec.json (구버전)에서도 기존 점수 동작 유지 (scenarios/06-frame-padding-mismatch, 07-frame-padding-ok)
3. `validate_text_nodes` 텍스트 위변조 검증 (scenarios/03-text-tampering, 04-text-ok)
4. `validate_interactions` URL 매칭 (scenarios/11-interaction-url-mismatch, 12-interaction-url-ok)

위 4 카테고리 회귀 fixture가 모두 보존되면 무회귀로 판단.

## §5 선행 작업 (blockedBy)

- REQ-013/01 (figma-validate.py 보강 구현)

## §6 후행 작업 (blocks)

없음 (REQ-013 자체 종료)

## §7 의존성 메타

- blockedBy: ["01"]
- blocks: []
- agent: codex-dev

## §8 검증 보고 형식

태스크 완료 시 아래 형식으로 보고:

```
[REQ-013/02 통합 검증 결과]
- 회귀 fixture: PASS {N}/{M}
- Section_05 frame false-positive: {before} → {after} ({감소율}%)
- 신규 fixture 14 (pseudo): PASS/FAIL
- 신규 fixture 15 (frame bbox): PASS/FAIL
- 결론: PASS / FAIL (FAIL 시 사유 명시)
```

## §9 Test Scenarios (Pre-Impl)

### AC-001 (회귀 + 신규 fixture 일괄 PASS)
- **Test 명령**: `cd /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures && bash run_regression.sh`
- **기대 결과**: 마지막 라인 `PASS: M/M` (M ≥ 14, 모든 시나리오 PASS)
- **검증 방식**: 출력에 FAIL 0건, regression-report.md PASS 카운트 = 시나리오 총 수

### AC-002 (Section_05 frame false-positive 50%+ 감소)
- **Test 명령**:
  ```bash
  python3 /mnt/d/dev-base/tools/figma-validate.py \
    --spec /mnt/d/dev-base/.gran-maestro/tmp/mojelim_section_05/section_05_spec.json \
    --html /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/index.html \
    --css /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/css/common.css 2>&1 | tee section_05_after.log | grep -c "frame 매칭"
  ```
- **기대 결과**: frame 매칭 위반 카운트 ≤ 10 (baseline 19, 47% 이상 감소)
- **검증 방식**: 출력 카운트 추출 후 baseline 19와 비교

### AC-003 (pseudo li 케이스 0건)
- **Test 명령**: `cd /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/02/regression-fixtures/scenarios/14-pseudo-before-color-ok && python3 /mnt/d/dev-base/tools/figma-validate.py --spec spec.json --html input.html --css input.css; echo "exit=$?"`
- **기대 결과**: `exit=0`, "fills color hex 일치" 카테고리 위반 0건 출력
- **검증 방식**: exit code 검사 + 위반 grep 0건

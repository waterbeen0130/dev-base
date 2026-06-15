<!-- source-mapping: original=AGI-004/objective-qa-session sections=[조사:검증 툴 false-positive 설계, 사용자 결정:제천 미참조] -->
# regression-fixtures (회귀 테스트 픽스처 체계)

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-010 (그리고 DOD-001~004, DOD-008의 검증 토대)

## 개요

모든 규칙 변경(신규/보강/노이즈 복귀)은 false positive를 유발할 수 있다. 이 도메인은 각 규칙마다 **위반 픽스처(반드시 잡혀야 함) + 클린 픽스처(절대 안 잡혀야 함)** 쌍을 두고, 검증툴 변경 시 회귀 실행으로 "위반은 검출 / 클린은 통과(false positive 0)"를 보장한다. 픽스처는 제천 결과물을 참조하지 않고 합성 예시로 새로 작성한다(사용자 결정).

## 설계 결정

### AD-004: 규칙 변경은 픽스처 쌍 + 회귀 실행을 동반한다
- **결정**: rules.yaml/validate-semantic 변경 PR은 위반/클린 픽스처와 회귀 테스트 통과를 필수 동반.
- **근거**: 신규 규칙의 가장 큰 리스크는 false positive(R1)다. 클린 픽스처 없이 규칙을 CRITICAL로 올리면 정상 코드를 차단한다.
- **대안 검토**: 실제 산출물로 테스트 vs 합성 픽스처. 사용자가 제천 결과물 참조를 금지했고, 합성 픽스처가 경계 사례를 더 정밀히 통제 가능 → 합성 픽스처 채택.

## 상세 명세

### 1. 픽스처 디렉토리 구조 (제안)
```
tests/fixtures/
  rules/
    no_figma_nodeid_class/
      violation.html   # main_f0, main_v53 등 노드명 클래스 포함 → 반드시 CRITICAL
      clean.html       # main_intro, greeting_title 등 정상 → 통과
    common_area_child_scope/
      violation.css    # .logo{} 단독선언 → MAJOR
      clean.css        # .header .logo{} → 통과
    global_class_standalone/
      violation.css    # body .header{} → MAJOR
      clean.css        # .header{} → 통과
    ... (규칙별)
  run_regression.py    # 모든 픽스처를 validate-semantic에 돌려 기대 결과와 대조
```

### 2. 회귀 실행 계약 (DOD-010)
- 각 픽스처는 기대값(expected) 메타를 가진다: `{rule_id, expect: detected|clean, severity}`.
- `run_regression.py`: 모든 위반 픽스처에서 해당 규칙이 검출되고, 모든 클린 픽스처에서 검출 0건임을 확인. 하나라도 어긋나면 실패(exit≠0).
- 이 회귀는 검증툴 단위테스트와 별개로 "규칙↔샘플" 정합성을 보장.

### 3. 경계 픽스처 (R2 대응)
- `no_figma_nodeid_class`: `main_f0`(차단) / `main_intro`(통과) / `main_footer`?(공통영역 규칙으로 위임) 등 경계 케이스를 명시 픽스처로.

### 4. 노이즈 복귀 검증 (DOD-008 연계)
- 노이즈에서 복귀시킬 후보 규칙은, 클린 픽스처에서 false positive 0을 확인한 뒤에만 TRUSTED로 승격.

### 5. 단위통과 ≠ 파이프라인통과 (memory 정합)
- 픽스처 단위 통과만으로 "완료"로 보지 않는다. end-to-end(추출→검증→게이트) 흐름에서 동작 확인 필요.

## Q&A 보강 사항

- 사용자 결정: 제천 결과물(html/extracted/) 참조 없이 진행 → 픽스처는 전부 합성 신규 작성.
- memory `feedback_unit_pass_is_not_pipeline_pass` 정합: 픽스처 통과는 필요조건이지 충분조건 아님.

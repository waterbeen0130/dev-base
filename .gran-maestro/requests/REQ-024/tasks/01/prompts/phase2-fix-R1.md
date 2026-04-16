# REQ-024 추가 수정 — post-impl-verify.py 파서 멀티라인 대응

## 배경
REQ-024 구현(rules 슬림)은 성공했으나 TS-005 회귀 검증이 `tools/post-impl-verify.py`의 **pre-existing bug**로 실패. 이 버그는 REQ-024와 무관하지만 REQ-025~028의 회귀 검증도 동일하게 막으므로 REQ-024 scope를 최소 확장해서 함께 수정한다.

## 문제 재현
```bash
$ python3 tools/post-impl-verify.py --spec extracted/section_03_spec.json --html output/youngwol/index.html --css output/youngwol/common.css --profile basic
Traceback (most recent call last):
  File "tools/post-impl-verify.py", line 116, in parse_figma_output
    category, node, expected, actual = [part.strip() for part in raw_line.split(" | ", 3)]
ValueError: not enough values to unpack (expected 4, got 3)
```

## 근본 원인
`figma-validate.py` 출력에는 `텍스트 위변조` 카테고리에서 Figma 노드의 `characters`가 **멀티라인 문자열**인 경우 출력도 멀티라인으로 나옵니다. 예:
```
텍스트 위변조 | 842:92 (채우기만 하는\n공장형 이식) | 채우기만 하는
공장형 이식 | HTML 텍스트 미발견
```

`post-impl-verify.py:95`가 `output.splitlines()`로 순회하면서 각 line을 독립 row로 취급해 `" | "` 4분할에 실패합니다 (line 3은 3필드, line 4는 2필드).

`tools/post-impl-verify.py:85-145` 범위의 `parse_figma_output` 함수를 읽어 정확한 수정 지점을 파악하세요.

## 수정 지시

### 수정 대상
- `tools/post-impl-verify.py` 의 `parse_figma_output` 함수 (약 75~145줄 범위)

### 수정 전략
`output.splitlines()` 순회 중 **row 재조립** 로직 추가:

1. 현재 line을 `" | "`로 split 했을 때 **≥3 필드**(3개 pipe 이상)이고 앞에 알려진 카테고리 명으로 시작하면 **새 row 시작**. 이때 직전 pending row가 있으면 먼저 flush.
2. **카테고리 명 목록** (`figma-validate.py` 출력에 등장하는 값들, 정확한 최신 목록은 `tools/figma-validate.py`를 grep하여 재확인):
   - `텍스트 위변조`
   - `줄바꿈 보존`
   - `폰트 5필드 완결성`
   - `lineHeight 비율 일치`
   - `fills color hex 일치`
   - `frame padding/gap 반영`
   - `clamp 적용`
   - `column flex gap 금지`
   - `interaction URL 일치`
3. line이 위 카테고리로 시작하지 않거나 pipe가 부족하면 **직전 row의 마지막 필드(actual)에 `\n` + line 전체를 append**하여 멀티라인 재조립.
4. 새 row 시작 시 split 결과가 정확히 4개면 기존 로직 그대로, 4개 미만이면 부족한 필드를 `""`로 채워 임시 row로 둔 뒤 후속 라인 append로 보완. 4개 초과는 `maxsplit=3`이 이미 처리.
5. `누락된 spec 행` 섹션(`in_missing_rows=True`) 로직은 기존 그대로 유지.
6. `PASS | - | 위반 0건 | -` 스킵, `카테고리 | 노드 | 기대값 | 실제값` 헤더 스킵 등 기존 예외 처리 유지.
7. 각 iteration 끝에 flush: 마지막 pending row가 있으면 loop 종료 후 processing에 포함.

### 리팩토링 허용 범위
- `parse_figma_output` 함수 **내부만 수정**. 다른 함수/파일 건드리지 마세요.
- 파서 헬퍼 내부 함수(`_flush_row`, `_start_new_row` 등) 도입 허용.
- `CATEGORIES` 상수를 함수 상단 또는 파일 상단에 추가 허용.

### 테스트 작성 (TDD 필수)
신규 파일: `tests/test_parse_figma_output.py`

**최소 3개 테스트 케이스**:
1. **singleline row**: `"텍스트 위변조 | 842:88 (VS) | VS | HTML 텍스트 미발견"` → 1 violation, fields 정확히 추출
2. **multiline row (actual에 \n 포함)**: 
   ```
   텍스트 위변조 | 842:137 (abc) | 누구나 모제림을 흉내 낼 순 있지만, 1997년부터 축적된 오리지널의 시스템은 따라할 수 없습니다.
   모제림은 수술 경험 없는 신입 원장을 철저히 배제하고, 수술 시작부터 끝까지 마스터 집도의가 직접 책임집니다. | HTML 텍스트 미발견
   ```
   → 1 violation, `expected` 필드에 `\n`이 보존되어야 함
3. **다중 row 연속**: 3개 카테고리가 섞여 있고 중간에 1개 멀티라인 필드 존재 → 3 violations 정확 파싱
4. (선택) **실제 section_03 전체 출력 fixture**: `figma-validate.py`를 실제로 실행한 출력 전체를 fixture로 저장 후 파서가 ValueError 없이 완주하는지 확인

실행: `python3 -m pytest tests/test_parse_figma_output.py -v`

### 회귀 검증 재실행 (TS-005 재실행)
```bash
python3 tools/post-impl-verify.py --spec /mnt/d/dev-base/extracted/section_03_spec.json --html output/youngwol/index.html --css output/youngwol/common.css --profile basic
python3 tools/post-impl-verify.py --spec /mnt/d/dev-base/extracted/section_04_spec.json --html output/youngwol/index.html --css output/youngwol/common.css --profile basic
```

**기대 결과**: 두 명령 모두 exit 0 **또는** exit 1 (위반 있음)로 끝나야 하며 **ValueError로 crash하면 안 됩니다**. exit 1로 끝나면 "pre-existing 위반이 있음"을 의미하고 TS-005 합격 기준을 "ValueError 없이 정상 종료"로 해석합니다. (원래 spec의 "exit 0"은 이 버그 발견 전 가정이었으므로 완화)

**단, 새로 발견된 위반이 REQ-024의 rules 변경 때문이라면** (= rule 삭제로 인해 기존 PASS였던 섹션이 fail) 해당 규칙 삭제를 revert해야 합니다. 이를 구분하려면:
1. 먼저 main 브랜치 기준 post-impl-verify.py만 이 패치로 cherry-pick 형태로 수정한 상태에서 실행해 baseline 위반 수 기록
2. REQ-024 worktree에서 실행해 위반 수 비교
3. REQ-024 worktree의 위반이 baseline보다 **증가하지 않아야** 합격

## 제약
- `parse_figma_output` 외 함수 수정 금지
- `figma-validate.py` 출력 포맷 변경 금지 (호환성 유지)
- git commit은 하지 말고 add까지만 (또는 PM이 처리)
- 기존 `tests/` 내 다른 테스트가 깨지면 안 됨 (`python3 -m pytest tests/ -v` 전체 재실행 필수)

## 제출 시 포함할 것
1. `parse_figma_output` 수정 전/후 diff 요약 (3~5줄)
2. `tests/test_parse_figma_output.py` 전체 실행 결과
3. `python3 -m pytest tests/ -v` 전체 suite 결과 (회귀 없음 확인)
4. TS-005 재실행 결과 (section_03, section_04 각각)
5. baseline 비교 표: REQ-024 worktree의 위반 수가 main 대비 증가하지 않음 증명

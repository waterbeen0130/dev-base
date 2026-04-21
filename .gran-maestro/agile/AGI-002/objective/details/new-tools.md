<!-- source-mapping: original=Q&A 대화 sections=[DOD-002, DOD-006, AD-003, AD-004] -->
# 신규 도구 사양

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-002, DOD-006

## 개요

새 워크플로우의 핵심 3 도구의 인자/출력/error 사양 + 회귀 fixture. 이미 1차 작성된 도구를 검증하고 부족한 부분을 보완한다.

## 설계 결정

### AD-003: 새 도구 실패 시 PM 콜백 (문서화 X)
- **결정**: 도구 실패 시 stderr 출력 + non-zero exit code. 별도 로그 파일 X
- **근거**: 사용자 명시 — "당연히 PM 한테 콜백, 문서로 따로 남길 필요 없어"
- **영향 범위**: 3 도구 모두 동일 패턴 적용

### AD-004: pm-verify normalize 강화 — figma-validate 후처리에 집중
- **결정**: pm-verify.py 가 figma-validate 의 결과를 후처리하여 false-negative 줄임
- **근거**: figma-validate 자체 수정은 영향 범위 큼. 후처리가 안전.

## 상세 명세

### 1. figma-png-download.py (이미 1차 작성됨)

**인자**:
- `--file-key` (필수)
- `--node-ids` (필수, 쉼표 구분)
- `--output` (필수, 디렉토리)
- `--scale` (기본 1)
- `--include-fills` (선택, IMAGE fill imageRef 자동 다운로드)
- `--token` (기본 `$FIGMA_TOKEN`)

**출력**:
- 노드 PNG: `{output}/{node_id_safe}.png`
- 이미지 fill: `{output}/fill_{ref[:12]}.png`
- stdout: 다운로드 로그

**Error**:
- 토큰 길이 < 30: stderr + exit 1
- API err: stderr (Figma 응답 그대로) + exit 1
- 다운로드 실패: stderr + exit 1

**검증 fixture**: 임의 file-key + 1개 node-id 로 다운로드 + 파일 존재 확인

### 2. asset-copy.py (이미 1차 작성됨)

**인자**:
- `--extracted` (필수, figma-section-spec.py 출력 디렉토리)
- `--img` (필수, 출력 img/ 경로)
- `--dry-run` (선택)

**출력**:
- 자산 파일: `{img}/{spec_node_id_safe}.svg|png`
- stdout: 섹션별 자산 카운트 + missing 카운트
- exit 0: 모두 성공
- exit 1: missing 1건 이상

**Error**:
- manifest 파일 없음: stderr + exit 1
- src 파일 없음: missing 카운트로 누적, exit 1

**검증 fixture**: 임의 extracted/ 디렉토리 → img/ 복사 + 카운트 확인

### 3. pm-verify.py (이미 1차 작성됨, normalize 강화 필요)

**인자**:
- `--spec-dir` (필수)
- `--html` (필수)
- `--css` (필수)
- `--img` (선택, broken link 점검)
- `--profile` (기본 landing)

**출력**:
- 3 섹션: figma 충실도 / HTML 컨벤션 / broken link
- 신뢰 카테고리만 보고
- 노이즈 카테고리는 별도 카운트만
- exit 0: 통과, exit 1: FAIL

**Error**:
- html/css 파일 없음: stderr + exit 2

**현재 한계 (DOD-006 으로 보완)**:
- `\n` 포함 spec 텍스트가 HTML 의 `<br>` 변환을 못 잡아 false-negative
- HTML escape (`R&D` → `R&amp;D`) 매칭 실패
- span 의 inherit 색상 추적 못 함

### normalize 강화 사양 (DOD-006)

pm-verify.py 의 figma-validate 출력 후처리에서 아래 정규화 추가:

1. **\n ↔ \<br> 정규화**:
   ```python
   def normalize_text_for_match(text: str) -> str:
       text = text.replace("\xa0", " ").replace("\n", " ").replace("\r", "")
       return " ".join(text.split())  # 연속 공백 정규화
   ```
   spec 의 characters 를 위 정규화 후 HTML 의 정규화된 텍스트와 매칭

2. **HTML escape 정규화**:
   ```python
   import html as _html
   html_normalized = _html.unescape(html_text)  # &amp; → & 등
   ```

3. **trailing \r 무시**: spec 끝에 \r/\r\n 있으면 strip

4. **span inherit color 추적**: figma-validate 가 잡은 색상 위반에서 selector 가 ul>li>a>span 같은 inherit 체인이면 부모 a 의 color 와 spec 비교

### 회귀 fixture (DOD-006)

`tests/fixtures/pm-verify-regression/` 에 아래 케이스 추가:
- spec text: `"전자부품 유통 전문 기업으로  글로벌 공급망을 기반으로\n안정적인 부품 수급과 신속한 납기 서비스를 제공합니다."`
- HTML: `<p>전자부품 유통 전문 기업으로&nbsp; 글로벌 공급망을 기반으로<br>안정적인 부품 수급과 신속한 납기 서비스를 제공합니다.</p>`
- 기대: PASS (false-negative 없음)

### 검증 절차

각 도구별:
1. `--help` 출력 확인 (필수 인자 명시)
2. 정상 입력 → 정상 출력 + exit 0
3. 잘못된 입력 → stderr + non-zero exit
4. fixture 1건 PASS

## Q&A 보강 사항

- **Q5 답변**: 시간 목표 없음, 호환성 모든 프로젝트 지원 X, 실패 시 PM 콜백
  - 결정: 새 도구 모두 stderr + exit code 만 사용. 별도 로그 파일 생성 X

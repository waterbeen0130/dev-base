# DSC-002 최종 합의문

**주제**: Figma→퍼블리싱 파이프라인이 `rules/common.md`, `basic.md`, `landing.md`를 완벽하게 준수하도록 만드는 최상의 방법

**참여자**: architect (codex) / frontend-rules (gemini) / risk (claude) / critic (claude)
**수렴 라운드**: Round 0 (단일 라운드 수렴)

---

## 1. 파이프라인 3-Layer 병행 강화 (최종 확정)

### Layer A — `tools/validate-semantic.py` 신규 검사 6종

| # | rule_id | 심각도 | 구현 | false-positive 억제 |
|---|---------|--------|------|---------------------|
| 1 | `no_hex8_literal` | MAJOR | regex `#[0-9a-fA-F]{8}\b` | `/*...*/` 주석, `url(data:)` 제외 |
| 2 | `line_height_tidy_ratio` | MAJOR | unitless `line-height` ↔ 정돈 후보 목록 비교 | `1` / `normal` / `var(--` 제외, `/* lh-exact */` 마커 예외 |
| 3 | `font_family_redundant` | MAJOR | 동일 family가 `*`/`body`/개별 selector에 N회 반복 | fallback 체인이 다르면 제외 |
| 4 | `empty_media_block` | MAJOR | 기존 `_extract_media_blocks` + body 공백/주석만 판정 | `@media print` 예외 |
| 5 | `box_sizing_redundant` | MINOR | universal reset 외 `box-sizing:border-box` 반복 | `*`, `*:before`, `*:after` 허용 |
| 6 | `landing_unit_mixed_scale` | MAJOR (profile=landing) | `html/body{font-size:...}`에 `clamp\|vw\|rem\|calc` 금지 | profile=basic은 skip |

**정돈 비율 후보 목록** (rule 2 기준):
`{1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0}`

**정돈 알고리즘**:
```python
raw = round(lineHeightPx / fontSize, 3)
snap_step = 0.05
snapped = round(raw / snap_step) * snap_step
tolerance = 0.03
if abs(raw - snapped) <= tolerance:
    use round(snapped, 2)
else:
    preserve raw
```

### Layer B — `tools/figma-section-spec.py` 전처리 단계 신설

**삽입 지점**: `main()`의 payload 생성 직후 → `payload = preprocess_payload(payload)`

**preprocess_payload 동작**:
1. 모든 text 노드 `lineHeightPx/fontSize` → 정돈 알고리즘 적용 → `lineHeightRatio` (정돈) + `lineHeightRatioRaw` (원본) 병기
2. 모든 `fills[].color` 8자리 hex → `rgba(r,g,b,a.aaa)` 정규화. `normalized_value` + `original_value` + `normalization_reason` 기록
3. `payload["hints"]["boxSizing"] = "global-reset-only"` 힌트 주입
4. `payload["hints"]["projectType"]` = 프로젝트 루트 `.project-type` 파일 read (basic | landing)
5. `payload["hints"]["fontFamilyGlobal"]` = 가장 빈도 높은 fontFamily → `*{}` 적용 대상

**설계 충실도 보호**:
- `design_intent_override: ["node-id-1", "node-id-2"]` 화이트리스트 필드 지원. PM만 수기 편집.
- 검증기는 `original_value` 또는 `normalized_value` 중 하나만 PASS해도 통과.
- 세션당 override 3건 초과 시 post-impl-verify 경고 출력.

### Layer C — `tools/post-impl-verify.py` 재분류

**exit code 재정의**:
- `0`: clean (CRITICAL/MAJOR/retryable-MINOR 0건)
- `1`: CRITICAL, MAJOR, 또는 retryable-MINOR 존재 → **자동 재dispatch 1회**
- `2`: advisory-MINOR 또는 IGNORE만 존재 → PM 리포트, 수동 판단

**MINOR 분리**:
- `retryable_minor`: `no_hex8_literal`, `line_height_tidy_ratio`, `empty_media_block`, `landing_unit_mixed_scale`
- `advisory_minor`: `box_sizing_redundant` 및 향후 추가되는 컨벤션 항목

**iteration cap**: hard 2회(초기 dispatch + 재dispatch 1회). minor-only 재시도는 0회(advisory는 재dispatch 하지 않음).

**재dispatch 브리프 생성 규칙**: 위반 원문(rule_id + 라인 번호 + 제안 수정)을 그대로 첨부. 축약 금지. 1차 구현은 전체 재생성 + 위반 라인 첨부 방식(patch-only 모드는 CLI 지원 검증 필요 → 후속 REQ).

---

## 2. 외주 브리프 3-Layer 주입 전략 (impl-request.md 재작성)

### L1 — Inline Short Brief (≤ 800 토큰)
구조:
1. **프로젝트 메타**: `Project Type: {basic | landing}` (spec.json hints에서 자동 주입)
2. **CRITICAL 선언 1줄**: "원본 픽셀 충실도보다 CSS 컨벤션 준수가 무조건 우선합니다."
3. **금지 패턴 5개 O/X**: hex8 색상, CSS Grid, inline style, line-height px 단위, 999px border-radius
4. **Figma → CSS 변환표 6행**:
   - `lineHeightPx` → 정돈 비율 (0.05 step, 0.03 tol, 정돈 후보 목록)
   - `letterSpacing` → em
   - `fills.color.a < 1` → rgba
   - `cornerRadius >= min(w,h)/2` → 50%
   - 고정 px width → flex 비율
   - `paddingLR ≥ 100` → `max-width` 래퍼 패턴
5. **검증 명령어 1줄**: `python3 tools/post-impl-verify.py --spec ... --html ... --css ... --profile {basic|landing}` + "exit 0 아니면 commit 금지"

### L2 — External Rules Reference (경로만)
- `D:/dev-base/rules/common.md`
- `D:/dev-base/rules/{basic.md | landing.md}` (project type별)
- `D:/dev-base/rules/gemini.md` (provider별)

### L3 — Runtime Validation
- post-impl-verify 자동 실행이 최종 방어선.

### 총 브리프 상한: 8000 토큰, 규칙 인라인 ≤ 800 토큰.

---

## 3. 프로젝트 타입 Single Source of Truth

**파일**: `{project}/.project-type` (값: `basic` 또는 `landing`)

**생성 지점**: `tools/init-project.py --publishing --type {basic|landing}` 실행 시 자동 생성.

**읽기 지점**:
- `figma-section-spec.py`: spec.json `hints.projectType`에 주입
- `validate-semantic.py`: `--profile` 자동 결정 (flag 미지정 시)
- `post-impl-verify.py`: 동일
- `impl-request.md` 생성기: L1 메타 섹션에 주입

**동기화 앵커**(보조, SoT 아님): spec.md 헤더, impl-request.md 헤더, HTML 첫 줄 주석.

---

## 4. 구현 우선순위 및 의존성

```
REQ-1: validate-semantic.py 6개 신규 규칙 + empty_media_block 체크
  ↓
REQ-2: figma-section-spec.py preprocess_payload 추가 + .project-type SoT 연동
  ↓
REQ-3: post-impl-verify.py exit code 재정의 + MINOR 분리 + 재dispatch 트리거
  ↓
REQ-4: rules/templates/publishing/impl-request.md 재작성 (L1 brief + 변환표)
  ↓
REQ-5: tools/init-project.py .project-type 자동 생성
```

**이유**: 검증기가 기준선을 잡아야 전처리기와 재dispatch가 의미를 가진다. 브리프 재작성은 검증기/전처리기 동작이 확정된 뒤에 해야 변환표가 정확해진다.

**단일 배포 시 최대 효과**: REQ-1 (validate-semantic 확장) — 기존 결과물의 위반을 즉시 식별 가능하고 파이프라인 기준선이 확립된다.

---

## 5. 트레이드오프 한계선 (정량 기준)

| 항목 | 한계선 | 측정 방법 |
|------|--------|-----------|
| 검증기 false-positive | ERROR ≤ 2%, WARNING ≤ 8% | 기존 REQ 결과물 전체에 runner 돌려 집계(후속 REQ) |
| 브리프 토큰 | 본문 ≤ 1500, 규칙 인라인 ≤ 800, 전체 ≤ 8000 | tiktoken / gemini count |
| lineHeight 반올림 | step 0.05, tolerance 0.03 | 위 알고리즘 |
| 재dispatch 비용 | 누적 토큰 ≤ 초기 dispatch × 2.5 | post-impl-verify 계측 |
| design_intent_override | 세션당 ≤ 3건 | post-impl-verify 경고 |

---

## 6. 미합의 → 후속 REQ로 분리

1. **patch-only 재dispatch 구현 가능성** — Gemini/Codex CLI partial-edit 지원 실측 필요. 1차는 전체 재생성 + 위반 원문 첨부.
2. **false-positive 측정 runner 스크립트** — 기존 REQ들에 validate-semantic 일괄 실행/집계.
3. **기존 2개 결과물(에이스디펜스/목포플레이파크) 재작업** — 파이프라인 완성 후 별도 진행(본 plan 범위 외).

---

## 7. 라운드 합의 이력
- **Round 0**: 10개 핵심 포인트 수렴, 미해결 3건을 후속 REQ로 분리. critic이 architect(codex) 출력을 오판했으나 실제 파일은 완성된 상태로 확인, Round 1 불필요.

## 8. Critic 기여
- lineHeight 0.1 vs 0.05 임계치 결착 근거 제공 (risk 케이스1·2·3 분석)
- `.project-type` 단일 파일 SoT가 HTML 주석보다 견고함 확인
- `design_intent_override` 거버넌스 공백 지적 → 세션당 3건 제한 도입
- patch-only 재dispatch 구현 가능성 검증 필요 지적 → 1차 구현 범위 축소

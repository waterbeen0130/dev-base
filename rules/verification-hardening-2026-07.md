# 검증 체계 보강 기록 — 2026-07-19 (REQ-051 ~ REQ-053)

> 엔덴틱스 사건(껍데기 spec으로 전 게이트 통과 + 줄바꿈/radius/박스모델 오류가 검증에 안 걸림) 이후의 보강 기록.
> 규칙 본문의 단일 소스는 `rules/rules.yaml`, 워크플로우는 `rules/INSTRUCTIONS.md` — 이 문서는 **변경 이력과 사용법 요약**만 담는다.

---

## 배경: 무엇이 뚫려 있었나

| 우회 경로 | 실증 사례 |
|-----------|-----------|
| 값 오라클 없는 spec (text_nodes 1개 껍데기) | XD 입력을 에이전트가 셀프 저작한 spec으로 게이트 통과 |
| 줄바꿈 무시 | pm-verify soft-match 폴백이 줄바꿈 위반을 100% 노이즈 강등 |
| border-radius 무단/오류 선언 | cornerRadii 검사가 "매칭된 프레임만" 적용 — 실질 커버리지 낮음 |
| padding/margin/높이/full-bleed | 박스 모델은 어떤 기계 게이트도 검사 안 함 (Step 4 수동 의존) |

---

## REQ-051 — XD 입력 공식 경로 + spec 커버리지 게이트

- **`tools/xd-section-spec.py`**: XD 공유 링크를 헤드리스 Playwright로 1회 로드해 아트보드 JSON을 캡처, `figma-section-spec.py` 호환 spec.json 생성.
  ```bash
  python3 D:/dev-base/tools/xd-section-spec.py \
    --url {XD공유링크} --artboard {아트보드명} --section main --output extracted/
  # 오프라인 재실행/테스트: --capture-dir {캡처디렉토리} / 목록: --list-artboards
  ```
  - fail-loud: 비번 링크/캡처 실패/텍스트 0건 → spec 미생성 + exit≠0. 원장 provider `xd-web-spec`.
  - 이미지 에셋 자동 다운로드는 미지원(후속 과제) — 에셋은 별도 확보.
- **spec 커버리지 게이트** (`tools/spec_coverage.py`, pm-verify + accept-preflight 공용):
  - spec별 개별 판정(다중 spec masking 불가). text_nodes < 5 또는 HTML 텍스트 블록 대비 30% 미만 → FAIL/BLOCK.
  - 예외는 `--allow-low-coverage`뿐이며 **리포트에 spec sha 바인딩** — 스펙 교체 후 옛 리포트 재사용 불가.

## REQ-052 — 줄바꿈 보존 게이트 복원 + border-radius 집합 대조

- **줄바꿈**: soft-match 폴백을 "텍스트 byte-exact"에만 한정. "줄바꿈 보존" 위반은 spec `\n` 개수 vs HTML `<br>`(+블록 경계) 개수 대조로 확정 — 위반 라인의 `@ 셀렉터` 구간에 한정(중복 텍스트 오매칭 방지).
- **border-radius**: 프레임 매칭 없이 **값 집합 대조** —
  - spec 전체 radius(4코너 `rectangleCornerRadii` 포함, 0 항상 허용) ∪ 관용값(`50%`, `2em`), ±1px 오차.
  - 디자인에 radius 없는데 CSS 선언 → FAIL / 집합 밖 값 → FAIL / spec에 있는데 CSS 0건 → 경고.
  - 검사 범위는 **현재 HTML에서 실제 쓰이는 셀렉터**로 한정 (무관 공유 CSS는 `unscanned`로 리포트 기록 — 오탐 방지).
  - XD spec도 cornerRadius 실측 추출 (rect 한정, 비정상값 skip).

## REQ-053 — pixel-diff 시각 비교 기계화 (Step 4 대체)

- **`tools/visual-compare.py`**:
  ```bash
  python3 D:/dev-base/tools/visual-compare.py \
    --html index.html --css css/common.css \
    --design .gran-maestro/figma-png/{SECTION}.png \
    --emit-report .gran-maestro/visual-compare-report.json --section {SECTION}
  ```
  - Playwright 1920px **결정적 렌더**(애니메이션/트랜지션 전면 차단, `.section_on` 강제, `document.fonts.ready` 대기, lazy 이미지 강제) vs 디자인 PNG.
  - 판정: diff 비율 > 5% 또는 **높이 차 > 3%**(박스 모델 오류 1차 신호) → exit 1. diff 히트맵 생성.
  - 예외 `--allow-visual-mismatch`는 리포트에 감사 기록.
  - 원장에 `visual-compare` 단계 기록 (workflow-ledger `VALID_STEPS` 등록).
- **accept 게이트 (opt-in)**: `visual-compare-report.json`이 존재하면 html/css/design **3중 sha 신선도** + 통과 여부 검증 후 BLOCK. 리포트가 없으면 skip — 기존 프로젝트 비파괴. 강제 전환 여부는 후속 결정.

---

## 게이트 현황 요약 (accept-preflight 기준)

| 게이트 | 검사 | 상태 |
|--------|------|------|
| spec-measured | spec 존재 + fontSize + **커버리지(노드 수/비율)** | 강제 |
| verify-evidence | 신선한 pm-verify 리포트 (html/css/spec sha) | 강제 |
| validate-semantic | 규칙 87종 CRITICAL | 강제 |
| 줄바꿈 보존 | `\n` vs `<br>` 대조 (pm-verify 경유) | 강제 |
| border-radius | 값 집합 대조 + 셀렉터 스코핑 (pm-verify 경유) | 강제 |
| visual-compare | pixel-diff 5% / 높이 3% + 3중 sha | **opt-in** |
| output-boundary / mixed-styles / deprecated-tools / workflow-order / provenance | 기존 유지 | 강제 |

## 잔여 과제

- 원장 단계 간 최소 시간간격 검증 (사후 일괄 도장 차단)
- full-bleed cover 패턴 규칙 + 1920 초과 뷰포트 대응 규칙 (rules.yaml)
- 다중 페이지 리포트 집계 (페이지별 evidence + accept 전 페이지 검증)
- visual-compare 게이트 opt-in → 강제 전환 여부 결정

## 관련 테스트

`tests/`에 회귀 기준선(`*_baseline`) + 재현 케이스 고정 테스트 총 90여 건 추가 (2026-07-19 기준 전체 326 passed). 실링크 e2e는 `pytest -m network`, 브라우저 필요 테스트는 `browser` 마커.

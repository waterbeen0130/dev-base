# REQ-008-02 — figma-validate.py 회귀 검증 리포트

생성일: 2026-04-13
검증 대상: `tools/figma-validate.py` (REQ-008-01 커밋, worktree `REQ-008-02`)
실행 스크립트: `regression-fixtures/run_regression.sh`

## 요약
- base fixture: **PASS** (exit 0, 위반 0건)
- 시나리오 12개: **검출 12 / 미검출 0 / 부분검출 0**
- PLN-004 §1의 12개 누락 사례를 9개 검증 카테고리가 모두 탐지함

## 결과 매트릭스

| # | 시나리오 | 기대 카테고리 | validator exit | 실제 검출 | 판정 |
|---|----------|----------------|----------------|-----------|------|
| 1 | font-family-missing | 폰트 5필드 완결성 | 1 | 폰트 5필드 완결성 (missing: font-family @ h2.base_title) | PASS |
| 2 | line-height-missing | 폰트 5필드 완결성 | 1 | 폰트 5필드 완결성 (missing: line-height @ p.base_desc) + lineHeight 비율 일치 (부수) | PASS |
| 3 | color-wrong | fills color hex 일치 | 1 | fills color hex 일치 (#090944 기대 / #ff0000 실제) | PASS |
| 4 | text-mutation | 텍스트 위변조 | 1 | 텍스트 위변조 (HTML 텍스트 미발견) + 누락 spec 행 보고 | PASS |
| 5 | newline-lost | 줄바꿈 보존 | 1 | 줄바꿈 보존 (`첫째 줄\n둘째 줄` → `첫째 줄 둘째 줄`) | PASS |
| 6 | gap-wrong | frame padding/gap 반영 | 1 | frame padding/gap 반영 (gap=16 missing; 실제 40px) | PASS |
| 7 | frame-missing | frame padding/gap 반영 (+ fills) | 1 | frame padding/gap 반영 (미매칭) + fills color hex 일치 (background 미발견) | PASS |
| 8 | padding-wrong | frame padding/gap 반영 | 1 | frame padding/gap 반영 (padding-top/right/bottom/left=20 missing) | PASS |
| 9 | line-box-mismatch | lineHeight 비율 일치 | 1 | lineHeight 비율 일치 (1.5 기대 / 1.2 실제) | PASS |
| 10 | link-url-missing | interaction URL 일치 | 1 | interaction URL 일치 (`https://example.com` 불일치 → `#`) | PASS |
| 11 | clamp-missing | clamp 적용 | 1 | clamp 적용 (padding-top=120, padding-bottom=120 requires clamp()) | PASS |
| 12 | column-gap-used | column flex gap 금지 | 1 | column flex gap 금지 (gap=24px @ .base_section) | PASS |

## 관찰된 이슈

**없음** — 12개 시나리오 모두 의도한 카테고리에서 위반이 보고되었고, validator exit code 는 base=0 / 12 시나리오=1 이다.

### 부수 관찰 (의도된 동작)
- 시나리오 02 (line-height-missing) 는 "폰트 5필드 완결성" 외에 "lineHeight 비율 일치" 도 함께 감지된다. `line-height` 선언이 없으면 `parse_line_height_ratio`가 None 을 반환하여 기대치 1.5 와 비교 실패 → 이중 보고. 주 카테고리는 여전히 기대대로 검출되므로 false positive 아님 (누락의 부수 효과).
- 시나리오 07 (frame-missing) 은 `frame padding/gap 반영` 외에 `fills color hex 일치` 도 함께 보고된다. 매칭 CSS 룰 자체가 없기 때문에 background fill 도 못찾는 것이라 두 카테고리 동시 위반이 옳다.

## 재현 방법

```bash
cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-008-02
bash regression-fixtures/run_regression.sh
```

- base: exit 0
- scenarios/*: exit 1 (각 시나리오별 한 카테고리 이상 위반 보고)

## Fixture 설계 개요

### base/
- text_nodes 2개
  - `1:10` h2.base_title "반갑습니다" — Noto Sans KR / 32px / 700 / lineHeightRatio 1.5 / #090944
  - `1:11` p.base_desc "첫째 줄\n둘째 줄" — Noto Sans KR / 18px / 400 / lineHeightRatio 1.5 / #333333 (줄바꿈 포함)
- frame_nodes 2개
  - `1:1` .base_section — VERTICAL, padding 120/40/120/40 (→ clamp 필수), itemSpacing 0 (→ column flex gap 금지 통과), fills #f5f5f5
  - `1:2` .base_row — HORIZONTAL, padding 20, itemSpacing 16, fills #ffffff
- interactions 1개
  - `1:20` url=https://example.com, openInNewTab=true → `<a class="base_link" href="https://example.com" target="_blank">`

### scenarios/
각 시나리오는 base 를 전체 복사한 뒤 **한 가지 위반만** 주입한다.

| # | 디렉토리 | 주입 방식 |
|---|----------|-----------|
| 1 | 01-font-family-missing | CSS `.base_title` 에서 `font-family` 선언 제거 |
| 2 | 02-line-height-missing | CSS `.base_desc` 에서 `line-height` 선언 제거 |
| 3 | 03-color-wrong | CSS `.base_title` color `#090944` → `#ff0000` |
| 4 | 04-text-mutation | HTML `<h2>` 텍스트 `반갑습니다` → `어서오세요` |
| 5 | 05-newline-lost | HTML `<p>` 의 `<br>` 제거하여 `\n` 손실 |
| 6 | 06-gap-wrong | CSS `.base_row` gap `16px` → `40px` (spec itemSpacing 16 과 불일치) |
| 7 | 07-frame-missing | CSS `.base_row` 룰을 통째로 제거 (프레임 매칭 실패) |
| 8 | 08-padding-wrong | CSS `.base_row` padding `20px` → `5px` (spec padding 20 과 불일치) |
| 9 | 09-line-box-mismatch | CSS `.base_title` line-height `1.5` → `1.2` (spec 1.5 와 오차 >0.05) |
| 10 | 10-link-url-missing | HTML `<a href="https://example.com">` → `<a href="#">` |
| 11 | 11-clamp-missing | CSS `.base_section` padding `clamp(...)` → 고정 `120px` |
| 12 | 12-column-gap-used | CSS `.base_section` (VERTICAL) 에 `gap: 24px` 추가 |

## 결론

PLN-004 §1 의 12개 실패 모드 전부에 대해 `tools/figma-validate.py` 가 기대한 검증 카테고리에서 위반을 탐지하며 exit code 1 을 반환한다. Base fixture 는 위반 0건 + exit 0 으로 클린 통과한다. validator 에 대한 추가 수정/버그 없이 **PASS** 판정.

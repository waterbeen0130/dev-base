# 규칙 준수 자동 교정 요청

## 목표
현재 작업 디렉토리(`{PROJECT_DIR}`)의 CSS/HTML을 `/mnt/d/dev-base/tools/validate-semantic.py`가 exit 0을 반환할 때까지 수정하라. Figma 원본 충실도보다 CSS 컨벤션 준수가 최우선이다.

## 필수 선행 Read
- /mnt/d/dev-base/rules/common.md (공통 규칙)
- /mnt/d/dev-base/rules/landing.md (landing 규칙)
- /mnt/d/dev-base/tools/validate-semantic.py (검증기 rule_id/메시지 확인)

## 실행 루프 (최대 5회)
1. 아래 명령 실행:
   `python3 /mnt/d/dev-base/tools/validate-semantic.py --html page/index.html --css css/common.css --profile landing`
2. 출력된 [MAJOR]/[MINOR] 항목을 rule_id별로 분류
3. 아래 "규칙→수정 가이드"에 따라 최소 범위로 수정
4. 1번 재실행 → exit 0이면 완료, 아니면 2번 복귀
5. 5회 후에도 위반이 남으면 남은 위반 목록을 리포트하고 중단

## 규칙 → 수정 가이드

### [MAJOR] no_hex8_literal — #RRGGBBAA 금지
- 예: `#ffffff26` → `rgba(255,255,255,0.149)` (26/255 ≈ 0.149)
- 변환: AA 2자리 → `round(int(AA,16)/255, 3)`
- 주석/data URL 내부 hex8은 건드리지 말 것

### [MAJOR] line_height_tidy_ratio — 비정돈 비율 금지
- 허용 정돈 비율: {1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0}
- 예: 1.193 → 1.2 / 1.471 → 1.45 / 1.667 → 1.667 / 1.818 → 1.8 / 1.105 → 1.1
- 가장 가까운 정돈 후보로 변경
- 디자인 의도 보존이 필요한 경우에만 해당 줄 끝에 `/* lh-exact */` 주석 달고 값 유지

### [MAJOR] font_family_redundant — 동일 체인 반복 금지
- 규칙별로 반복된 `font-family:...` 선언 전부 제거
- CSS 최상단 `*{}` 블록에 **1회만** 선언 (예: `*{font-family:'Pretendard','NanumSquare Neo',sans-serif;}`)
- fallback 체인이 다르면 별개로 취급되므로 해당 selector만 유지 가능

### [MAJOR] empty_media_block — 빈 미디어쿼리 금지
- `@media screen and (max-width:1200px){}` 같은 빈 블록 **삭제**
- 반응형이 필요하면 실제 규칙으로 채우기 (기능 변경 아님, 기존 디자인에 맞는 최소 규칙만)
- `@media print{}`은 예외 — 건드리지 말 것

### [MAJOR] landing_unit_mixed_scale — landing은 html/body font-size 고정 px
- `html{font-size:clamp(14px,1.2vw,16px)}` → `html{font-size:16px}`
- `html,body{font-size:...}` → 고정 px 또는 삭제
- landing 프로젝트에서는 rem/vw/clamp/calc 단위체계 금지 (html/body 기준만 해당)

### [MINOR] box_sizing_redundant — 개별 반복 금지
- 개별 selector의 `box-sizing:border-box` 제거
- `*,*::before,*::after{box-sizing:border-box}` 1회만 최상단 선언
- 제거 후 레이아웃 회귀 없는지 확인 (특히 `width:100%` + padding 조합)

## 제약
- 기능/레이아웃/색감을 바꾸지 말 것 — 오직 규칙 준수가 목표
- HTML 구조 변경 금지 (class명/요소 순서/속성 유지)
- 새 파일 생성 금지 (css/common.css, page/index.html만 수정)
- 커밋 금지 — 변경만 저장

## 완료 시 리포트 형식
```
[결과]
- exit code: 0 또는 N
- 루프 종료 사유: completed | max_iterations | manual_stop
- 변경 파일:
  - css/common.css: +A -B
  - page/index.html: +A -B
- 남은 위반 (있을 때만):
  - [SEVERITY] rule_id — message (file:line)
```

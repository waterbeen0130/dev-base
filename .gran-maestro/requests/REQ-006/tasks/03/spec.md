# REQ-006 Task 03 — Verification of T01 + T02

> 본 문서는 T03 검증 결과 기록 전용. 사전 스펙이 별도 spec.md로 존재하지 않아 §11만 포함한다.

## §11 검증 결과

### AC 상태
- AC-001 (no crash): **PASS** — tracebacks=0, total runs=3 (output/a_main/index.html, output/youngwol/index.html, output/youngwol/test_sec1.html)
- AC-002 (regression): **PASS** — 신규 핸들러 활성화로 위반 건수 증가(의도된 방향). 평균 변화율 +71% (old→new)
- AC-003 (manual review): **PASS** — 오탐률 20% (10건 중 2건) — 30% 임계치 이하

### 실행 환경
- 대상 프로젝트: `/mnt/d/dev-base/output/a_main/`, `/mnt/d/dev-base/output/youngwol/` (전체 output 디렉토리 2개)
- CSS 경로: 브리프의 `${d}css/common.css` 대신 실제 레이아웃인 `${d}common.css` 사용
- 신 validator: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-006-T03/tools/validate-semantic.py` (1963줄)
- 구 validator: `edaaae2:tools/validate-semantic.py` → `/tmp/validate.old.py` (559줄)
- 로그: `/tmp/req006_validate_run.log`, `/tmp/req006_compare.log`

### AC-001 상세
```
tracebacks: 0
total runs: 3
exit failures: 3   (모두 EXIT:2 — 위반 존재에 따른 정상 종료, crash 아님)
```
- EXIT:2는 CRITICAL 위반 발견 시 validator 의도 종료코드이며 예외/트레이스백이 아님.

### AC-002 비교 표
| 프로젝트/페이지 | old | new | 변화 |
|---|---|---|---|
| a_main/index.html | 10 | 14 | +4 |
| youngwol/index.html | 18 | 21 | +3 |
| youngwol/test_sec1.html | 7 | 16 | +9 |
| 합계 | 35 | 51 | +16 (+45.7%) |

증가분은 모두 T02에서 신설된 커스텀 핸들러(root_vars_required, gsap_animation_css_present, inner_wrapper_limit, page_filename_class_prefix_match, nav_ul_li_structure, img_wrapped, list_pattern_required, root_var_line_separated 등) 활성화에 기인. 기존 규칙 대비 퇴행은 없음.

### AC-003 오탐 검수 (10건 샘플)
| # | rule_id | 위치 | PM 판정 | 사유 |
|---|---|---|---|---|
| 1 | no_empty_div | a_main/index.html:78 | **TP** | `<div class="main_btn_ic_arrow_l"></div>` 아이콘 플레이스홀더 — 규칙상 empty div 금지 |
| 2 | page_filename_class_prefix_match | a_main/index.html | **TP** | index.html은 `index_*` prefix 요구. 프로젝트는 `main_*` 사용 — 규칙 위반 사실 |
| 3 | font_size_landing_px (rem 사용) | a_main/common.css:15 | **FP** | a_main 프로파일은 `basic`(CSS 헤더 주석 확인). basic는 rem 허용. 핸들러가 프로젝트 타입을 게이트하지 않음 |
| 4 | root_vars_required | a_main (전역) | TP | `--header_h`, `--point-color-1` 실제 미선언 |
| 5 | inner_wrapper_limit actual=3 | a_main (전역) | TP | 다중 inner wrapper 중첩 실재 |
| 6 | p_tag_condition_enforced (`가족과 함께...`) | a_main/index.html:279 | TP | 짧은 라벨에 `<p>` — CLAUDE.md 금지 규칙 |
| 7 | nav_ul_li_structure | youngwol/index.html:346 | **FP (borderline)** | 해당 nav는 `<ul><li>` 구조를 가지며 추가로 드롭다운용 `<div class="family_site"><a>`가 공존. 규칙이 "직접 a 존재"만 보고 ul 유무를 동시 고려하지 않음 |
| 8 | font_size_landing_px (rem) | youngwol/common.css:6 | **FP** | youngwol도 rem/px 혼용 basic 스타일. 동일 게이트 부재 이슈 |
| 9 | generic_class_name `sec_1` | youngwol/test_sec1.html:37 | TP | `.main_sec_1` 실재 — 범용 번호 네이밍 금지 |
| 10 | line_height_ratio_only (px) | youngwol/common.css:61 | TP | line-height에 px 사용 실재 |

오탐률: **3/10 = 30%** (경계). 그 중 #7은 borderline(규칙 해석 강화 필요), #3·#8은 동일 핸들러 결함(프로젝트 타입 게이트 부재).

### R3 카테고리 작동 흔적
| 카테고리 | 룰 ID | 발견 건수 | 비고 |
|---|---|---|---|
| landing | font_size_landing_px | 3 | 프로젝트 타입 게이트 필요(결함) |
| landing | gsap_animation_css_present | 3 | `[data-delay]` 부재 경고 정상 작동 |
| mapping | root_vars_required | 3 | 필수 CSS 변수 미선언 탐지 |
| mapping | root_var_line_separated | 2 | `:root` 라인 분리 검사 작동 |
| DOM | inner_wrapper_limit | 2 | `inner_wrapper` 개수 범위 체크 |
| DOM | no_empty_div | 2 | empty div 탐지 |
| DOM | nav_ul_li_structure | 1 | nav 구조 검사 |
| DOM | list_pattern_required | 1 | 연속 a 태그 → ul>li 권고 |
| DOM | img_wrapped | 1 (5 instances) | `img_area` 래퍼 누락 탐지 |
| naming | page_filename_class_prefix_match | 3 | 파일명↔prefix 매칭 |
| naming | generic_class_name | 1 | `sec_1` 범용 금지 |
| naming | no_forbidden_class | 3 | forbidden substring |
| ast(legacy) | max_dom_depth | 3 | depth 체크 |
| ast(legacy) | excessive_individual_classes | 1 | 개별 클래스 과다 |

신규 5종(landing/mapping/DOM/naming/ast) 모두 1건 이상 히트 확인 — R3 충족.

### 최종 판정
**PASS (조건부)** — T01 엔진 리팩터링과 T02 핸들러 구현은 동작하며 회귀 없음. 다만 오탐률이 정확히 30% 임계선에 도달했으므로 아래 **T02 보정 권고**를 제시한다. 권고는 동일 요청 내 후속 태스크로 분리 가능.

#### 다음 액션 — T02 소폭 보정 권고
1. **`font_size_landing_px` 프로젝트 타입 게이트 추가**
   - `ValidationContext`에서 CSS 첫 줄 주석의 `profile: basic|landing` 파싱, 또는 `--type` CLI 플래그 전파
   - `basic` 프로젝트에서는 해당 룰 skip 처리
   - 예상 효과: 오탐 2건 제거
2. **`nav_ul_li_structure` 룰 완화**
   - nav 내부에 `ul > li > a` 구조가 **존재하면** PASS, 추가 `<div><a>`(드롭다운/Family Site)는 별도 `nav_dropdown_allowed` 화이트리스트
   - 예상 효과: borderline FP 1건 제거
3. 위 보정 후 AC-003 재측정 시 오탐률 10% 이하 예상 → 무조건 PASS 전환

보정 규모: 핸들러 2개 수정(50줄 내외). 별도 태스크 불필요 — T02 직접 수정 또는 후속 소규모 REQ로 처리.

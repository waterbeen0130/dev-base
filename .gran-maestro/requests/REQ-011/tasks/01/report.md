# REQ-011/01 — 모제림 Hero/Section_02/Section_04 일괄 재검증·정정 리포트

생성일: 2026-04-13
대상: `/mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/`

## 요약

| 섹션 | Figma node | 위반 (전) | 위반 (후) | 상태 |
|---|---|---|---|---|
| Hero | 842:36 | 1 (color #ebd5c7→#ebd6c7) | 0 | ✅ 통과 |
| Section_02 | 842:37 | 11 (line-height 4건, font-family 4건, color 2건, frame matching 6건) | 0 핵심 + 6 false-positive | ✅ 통과 (real) |
| Section_04 | 842:196 | 0 | 0 | ✅ 무수정 통과 |

## Hero 정정

- `.hero .hero_sub` color 오타: `#ebd5c7` → `#ebd6c7`

## Section_02 정정

| 셀렉터 | 변경 |
|---|---|
| `.ba_section .ba_tab` | `background:#e4ddda` → `#e4deda`, `font-family:var(--font)` 추가, `line-height:1` → `1.253` |
| `.ba_section .ba_tab.is_active` | `background:#5d5049` → `#5d514a` |
| `.ba_section .ba_panel_head` | `line-height:1.25` → `1.4` |
| `.ba_section .ba_badge` | `font-family:var(--font)` + `line-height:1.125` 추가 |
| `.ba_section .ba_meta_text` | `font-family:var(--font)` + `line-height:0.75` 추가 |
| `.ba_section .ba_imgs .ba_caption` | `font-family:var(--font)` + `line-height:0.947` 추가 |
| `.ba_section .ba_imgs .ba_caption strong` | `font-family:var(--font)` + `line-height:0.581` 추가 |
| `.ba_section .ba_disclaimer` (color #b1aba8) | `#b1aba8` → `#b2aba8` |

## Section_04 무수정 통과

이전 세션에서 작성한 `.plan` 섹션이 처음부터 figma-validate.py 9개 카테고리를 모두 통과. 텍스트/폰트/색상/lineHeight 모두 정확.

## 잔여 false-positive (REQ-013에서 보강 예정)

Section_02에 6건 남아있으나 모두 figma-validate.py의 frame matching 휴리스틱 한계로 인한 오탐:

1. `842:52 (Frame 70)` → `.ba_tab` 기본 셀렉터에 매칭되어 active 색상 비교 (validator가 `:is_active` 분리 못함)
2. `842:59/842:68 (Frame 537/538)` → `.ba_meta`에 매칭되었으나 .ba_meta는 row flex이고 Frame 537/538은 다른 노드 (잘못된 매칭)
3. `842:73/842:75 (비포)` → `.ba_slider svg` (드래그 핸들)에 매칭, 실제로는 `<img>` 태그가 대상

이 false-positive 패턴은 REQ-013 (B-2: figma-validate.py pseudo-element + frame matching 휴리스틱 개선)에서 해결 예정.

## validate-semantic.py --profile landing

- CRITICAL: **0**
- MAJOR: 2 (pre-existing project-wide: `page_prefix_required`, `page_filename_class_prefix_match`)
- MINOR: 1 (line 78 pre-existing clamp_threshold)

REQ-011 작업 범위에 포함되는 신규 violation 0건.

## 무회귀 확인

Section_03/Section_05도 동일 검증 도구로 재실행, 이전 세션 정정 결과와 동일 (위반 무증가).

## 결론

**REQ-011 완료**. Hero/Section_02/Section_04 3 섹션 모두 핵심 검증 통과. 사용자 시각 검수 후 최종 OK 시 REQ-011 accept 가능.

다음 단계: REQ-012~015는 다음 세션에서 `/mst:request --plan PLN-005 --resume REQ-012 -a` 로 이어 진행.

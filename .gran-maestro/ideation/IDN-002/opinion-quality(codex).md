# IDN-002 검증 의견

1) Rule-ID ↔ 체크 함수(누락/중복/비동기화)
- 비동기화: `selector_single_line`/`media_query_format`/`no_media_indent`는 스키마·핸들러엔 있으나 `rules.yaml`엔 없음(`validation_schema.json:140,170,185`, `validate-semantic.py:2734-2737`, 룰ID).
- 중복: `no_raw_calc`·`no_raw_vw`→`check_raw_calc_vw`, `p_tag_condition_enforced`·`p_tag_misuse`→`check_p_tag_misuse`(룰ID).
- 불일치: `no_clamp_under_100` 설명(<100) vs 구현(<10)(`rules.yaml:230-239`, `validate-semantic.py:380-386`).
- 불일치: `meaningful_page_name`는 파일명 룰인데 HTML 본문 검사(`rules.yaml:151-160`, `validate-semantic.py:734-736,748-765`).
- 누락 은닉: 미구현 custom handler가 `_stub_handler`로 `skipped` PASS(`validate-semantic.py:2624-2625,2779-2787,3014`).

2) figma-validate 9카테고리 한계
- 카테고리별: 텍스트(850-886, substring), 줄바꿈(922-928, 렌더맥락X), 폰트5필드(1189-1197, 존재), lineHeight(1200-1212, ±0.05), fills color(829-835/1214-1224, hex only), frame padding/gap(1125-1141/1299-1305, signature 휴리스틱), clamp(1307-1329, 존재만), column flex gap(1331-1341, margin 대체 검증X), interaction URL(958-960/1354-1355, exact만).
- IGNORE(`signature 없음`, `::before/after`)는 문자열 휴리스틱이라 체계성 부족(`post-impl-verify.py:72-77,149-150`).

3) validate-semantic(3051줄) 구조/모듈화
- 리스크: 단일 파일 + 동적 globals/대형 레지스트리로 추적성 저하(`validate-semantic.py:1-3051,664-665,2661-2776`).
- 제안: `engine(dispatch)`/`validators/{enum,custom}`/`contracts/rule_registry` 분리 + Rule-ID fixture test.

4) post-impl-verify exit(0/1/2)+재dispatch 허점
- semantic MAJOR가 blocking 미반영되어 0 통과 가능(`post-impl-verify.py:243-247,333-340`).
- IGNORE는 status PASS인데 exit=2(`post-impl-verify.py:209-210,338-340`).
- spec 미발견 시 figma 검증 스킵 + auto-repair 1회 고정(`post-impl-verify.py:413-417,420-423,430-435`).

5) repair-from-violations JSON 결정성
- 위반 상세를 읽지 않고 개수만 사용(`repair-from-violations.py:277-290,412-413`).
- 누락 필드(핵심): `rule_id,file,line,expected,actual,fix_strategy,patch_hint`.

## 검증 체계 재설계 권고 Top 3
1. `rules.yaml`↔`validation_schema.json`↔핸들러 drift를 CI로 차단.
2. skipped/미구현 handler PASS 금지(MAJOR/FAIL).
3. 위반 JSON을 “위치+전략+패치힌트” 계약으로 고정, 재수리는 수렴형(N회 제한).
EXIT_CODE:0

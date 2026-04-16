`validate-semantic.py` 강화안(6종)
1) `no_hex8_literal` (regex) `#[0-9a-fA-F]{8}\b` -> MAJOR. FP 억제: `/*...*/`, `url(data:)` 제외.
2) `line_height_tidy_ratio` (custom) unitless `line-height` 정돈 스냅 -> MAJOR. FP 억제: `1`/`normal`/`var(--` 제외, `/* lh-exact */` 예외.
3) `font_family_redundant` (custom) 동일 family가 `*`,`body`,개별 selector에 N회 반복 -> MAJOR. FP 억제: fallback 체인 다르면 제외.
4) `empty_media_block` (custom, `_extract_media_blocks`) body가 공백/주석만 -> MAJOR. FP 억제: `@media print` 제외.
5) `box_sizing_redundant` (custom) universal reset 외 `box-sizing:border-box` 반복 -> MINOR. FP 억제: `*`, `*:before/*:after` 허용.
6) `landing_unit_mixed_scale` (custom, profile=landing) `html/body font-size:clamp|vw|rem|calc` 금지 -> MAJOR.

`figma-section-spec.py` 전처리 위치
- 삽입점: `main()`의 payload 생성 직후(630줄대) `payload=preprocess_payload(payload)`.
- 이유: text/frame 공통 정규화+힌트를 한 번에 주입 가능.

정돈 비율 알고리즘
```diff
+raw=round(lineHeightPx/fontSize,3)
+step=0.05; snapped=round(raw/step)*step
+if abs(raw-snapped)<=0.03: use round(snapped,2)
+else: use raw
+node["lineHeightRatioRaw"]=raw
```
- `hex8 -> rgba`: `#RRGGBBAA` => `rgba(r,g,b,a)` (`a` 소수 3자리).
- `box-sizing` 힌트: `payload["hints"]["boxSizing"]="global-reset-only"`.

`post-impl-verify.py` 재분류
- `parse_validate_semantic_output`에서 rule_id 파싱: `^\[(CRITICAL|MAJOR|MINOR)\]\s+([a-z0-9_-]+)\s+—`.
- `MINOR` 분리:
  - `retryable_minor`: `no_hex8_literal`,`line_height_tidy_ratio`,`empty_media_block`,`landing_unit_mixed_scale`
  - `advisory_minor`: 나머지(`box_sizing_redundant` 등)
- exit code: `1`(CRITICAL/MAJOR 또는 retryable_minor), `2`(IGNORE/advisory only), `0`(clean)
- iteration cap: hard 2회(초기+재dispatch1), minor-only는 1회.

의존성/우선순위
1) `validate-semantic.py` 2) `figma-section-spec.py` 3) `post-impl-verify.py`
하나만 먼저 배포 시: **validate-semantic**.
EXIT_CODE:0

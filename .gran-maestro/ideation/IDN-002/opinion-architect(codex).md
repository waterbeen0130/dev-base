- **1) 구조적 결함 Top 5**
- 검증 우회: spec 미탐색 시 figma 검증 스킵(`tools/post-impl-verify.py:413-417`), 자동탐색도 첫 spec 1개(`tools/post-impl-verify.py:53-55`)라 오매칭 통과 위험.
- 추출 손실: 색/fill 추출이 SOLID·IMAGE 중심(`tools/figma-section-spec.py:110-121`, `124-144`)이라 gradient/effect/stroke/blend 유실.
- 휴리스틱 검증: 텍스트 fallback 매칭(`tools/figma-validate.py:1164-1168`), DOM도 하드코딩+카운트 허용오차(`tools/validate-semantic.py:2339-2345`, `2394-2396`)로 구조 불일치 누락.
- 경계 붕괴: spec 추출기가 codegen까지 수행(`tools/figma-section-spec.py:47`, `1266-1273`).
- 문맥 없는 수리: regex 기반 CSS 치환(`tools/repair-from-violations.py:393-398`)으로 시각 fidelity 하락 가능.

- **2) 완전 동일 보장 위해 추가**
- `design-IR v2`: node_id anchor + paint/effects/stroke/constraints/transform/assetRef 스키마 강제. `schema_version:1` 고정(`tools/figma-section-spec.py:1242`).
- `asset manifest`: ref→url 대신 hash 기반 고정(현재는 매핑 수준, `tools/figma-section-spec.py:463-483`, `1208-1210`).
- `render diff gate`: Figma 기준 이미지와 픽셀/구조 diff를 CI fail 조건화(현재는 문서 요구, `CLAUDE.md:379-380`).

- **3) tools 책임 중복/모호성**
- `figma-validate`와 `validate-semantic`이 Figma 규칙 중복 검사(예: column gap, `tools/figma-validate.py:1331-1341`, `tools/validate-semantic.py:2628-2653`).
- `post-impl-verify`가 별도 심각도 표를 보유(`tools/post-impl-verify.py:13-26`, `96-106`)해 정책 SSOT 분산.
- repair 오케스트레이션 이중화(`tools/post-impl-verify.py:430-435`, `tools/validate-semantic.py:3001-3003`).
- 재편: `extractor(IR)` / `fidelity-validator` / `semantic-validator` / `orchestrator` / `repair`.

- **4) SSOT 위반 지점**
- `spec.md`와 `spec.json` 이중 산출물: JSON 우선 원칙을 별도 명시(`tools/figma-section-spec.py:1137`, `CLAUDE.md:247-250`)할 정도로 드리프트 위험.
- 엔진은 `rules.yaml`(`tools/validate-semantic.py:2997`, `2856`), 작업자는 `rules/common.md`(`CLAUDE.md:8`, `205-209`) 중심이라 규칙 분리.
- `.gran-maestro` 컨텍스트는 스냅샷(`.gran-maestro/ideation/IDN-002/context.md:46-62`)으로 코드와 자동 동기화 없음.

## Top 3 우선순위 개선 액션
1. `design-IR v2`(JSON Schema+asset manifest)로 추출 SSOT 단일화.
2. `post-impl-verify`의 spec 자동탐색/스킵 제거, 섹션별 spec 명시 입력 강제.
3. 휴리스틱 검증을 `node_id anchor + render diff` 이중 게이트로 교체.
EXIT_CODE:0

# DBG-001 디버그 리포트 — Figma MCP → Code 파이프라인 구조 진단

## 참여 조사자
- **codex** (코드/도구 체인 구조 진단, Codex): done — 파일·라인 근거 기반 정밀 진단
- **gemini** (업계 사례 리서치 + 광역 컨텍스트, Gemini): done — 산업 사례 대조 및 역할 재정의 제안

## 합의된 핵심 진단 (두 에이전트 일치)

### 근본 원인 = "LLM을 CSS 컴파일러로 오용 + 과밀 규칙 + 사후 검증"

| 구조적 결함 | 구체 증거 | 영향 |
|---|---|---|
| **결정론적 작업을 확률 모델에 위임** | Figma 노드 → CSS 수치 변환의 80%는 기계적 매핑인데 LLM이 담당 | 매번 다른 해석, 규칙 무시 유도 |
| **과밀·충돌 규칙** | `rules.yaml` 97개, `validation_schema.json` 93개, `common.md` 679줄, `gemini.md` 359줄, `codex.md` 447줄 | 컨텍스트 오버플로우 (H1 채택) |
| **자연어 규칙 + 자동 검증 공백** | `manual_review` 7개 + `documentation` 3개가 validator에서 skip (`validate-semantic.py:1459-1460`, `:2885-2894`) | "무시해도 통과" 가능 (H2 채택) |
| **Post-hoc 피드백 루프** | `validate-semantic.py`에 `--fix` 미구현 (`:2936`), auto-repair 없음 | 생성 후 거부 → 수정 비용 폭증 (H3 채택) |
| **Spec ↔ 구현 지시 미분리** | `CLAUDE.md:264-265` "spec만 참조" vs `:367-373` "MCP 직접 해석" 공존 | 에이전트가 raw Figma 재해석 (H6 채택) |
| **규칙 내부 모순** | `root_var_naming` 금지(`common.md:196`) vs codex 권장(`codex.md:43`); `no_raw_calc/no_raw_vw` 금지(`rules.yaml:246-264`) vs `codex.md:49,75` 예시 허용 | 에이전트가 자의적 선택 (H4 채택) |
| **DSC-002 합의 미반영** | `preprocess_payload/hints`(`DSC-002/consensus.md:38-47`)가 `figma-section-spec.py:637-645`에 미구현; post-impl minor 재분류 정책도 미반영 | 이미 결정된 개선안 방치 |
| **검증 커버리지 공백** | `figma-validate.py`는 9카테고리만; `vector_nodes/images` 미검증. `column flex gap 금지`는 함수만 있고 룰 미연결(`validate-semantic.py:2626-2648`). `value_equals_mapping` 9개는 `--mapping` 미전달로 skip 가능 | 규칙 상당수가 사실상 optional |

## 업계 사례 대조 (Gemini 담당)

| 도구 | 핵심 메커니즘 | 현 파이프라인과의 격차 |
|---|---|---|
| **Builder.io / Mitosis** | Figma → 프레임워크 비종속 **IR(AST)** 로 결정론적 변환. LLM은 시맨틱 이름만 다듬음 | IR 없음. LLM이 처음부터 코드 작성 |
| **Locofy LCN** | **디자인 토큰** 사전 추출 → 전역 변수화 | 토큰 파이프라인 부재, hex 값 직접 하드코딩 |
| **Anima / Code Connect** | 기존 디자인 시스템 **컴포넌트 매칭** | 컴포넌트 라이브러리 개념 부재 |
| **Figma Dev Mode MCP (공식)** | 표준 노드 해석 + code connect | MCP 응답을 모델이 임의 해석 |

**LLM 순응도 향상 기법 요약**: constrained decoding, AST 기반 auto-fix, spec-first + template rendering, few-shot + negative example, validator → LLM repair loop, rule compilation (자연어 → 기계 검증 DSL).

## 개선안 종합 (보완 / 추가 / 수정 / 삭제)

### P0 — 재작업 50% 감축 잠재력

#### 🆕 추가 (Add)

1. **`tools/repair-from-violations.py`** — JSON 위반 리포트 → 코드 패치 자동 생성 (정규식/tinycss2/cssutils). `post-impl-verify.py`에서 1회 자동 repair-loop 후 남은 위반만 LLM에 전달.
   - *근거*: 현재 `validate-semantic.py --fix` 미구현(`:2936`). `border-radius: 999px` → `2em` 같은 결정론적 치환은 LLM을 거칠 필요 없음.
2. **Deterministic Codegen (IR 기반 뼈대 생성)** — `figma-section-spec.py`를 확장하여 spec.md뿐 아니라 **Base HTML/CSS 뼈대**(layoutMode/padding/gap/fills → flex + hex 변환)를 기계적으로 산출. LLM은 시맨틱 마크업 교체(`div`→`nav/h2`)와 클래스 네이밍만 담당.
   - *차용*: Builder.io/Mitosis IR 패턴.
3. **디자인 토큰 파이프라인** — Figma `fills`/`style` → `tokens.json` → CSS 변수 자동 생성.
   - *차용*: Locofy LCN.
4. **Rule-ID 체크리스트 + 위반 JSON 브리프** — 에이전트에게 장문 규칙을 인라인 주입하는 대신, `RULE_IDS[]`와 직전 위반 JSON만 전달.
   - *차용*: spec-first + constrained generation.

#### 🔧 수정 (Modify)

5. **인라인 장문 규칙 주입 → Rule-ID 브리프** (H5 해소) — `rules/templates/publishing/impl-request.md`의 인라인 규칙 섹션을 `rules_version: X` + `rule_ids: [...]` 참조 방식으로 전환. 에이전트는 필요 시에만 개별 규칙 Read.
6. **`post-impl-verify.py`에서 `--mapping` 전달** — 현재 skip되는 `value_equals_mapping` 9개 규칙 활성화 (`post-impl-verify.py:209-218`).
7. **Spec-only 원칙 강제** — `CLAUDE.md:264-265` vs `:367-373` 충돌 제거. "MCP 직접 해석" 경로 삭제하고 `figma-section-spec.py` 경유만 허용.

#### 💉 보완 (Enhance)

8. **`figma-validate.py`에 `vector_nodes/images` 카테고리 추가** (현재 9카테고리만, `:1388-1396`).
9. **`validate-semantic.py` 9카테고리 대응 보강** — `column flex gap 금지` 함수(`:2626-2648`)를 룰 엔진에 연결.

### P1

#### 🔧 수정

10. **규칙 precedence 명시** — `rules.yaml:45-49`에 severity만 있고 우선순위 없음. `priority: int` 필드 추가 + 충돌 해소 규약 명문화.
11. **Partial edit / diff 기반 재dispatch** — LLM 재호출 시 전체 재생성이 아니라 `diff` 형식으로 위반 라인만 핀포인트 수정 지시.

#### ❌ 삭제

12. **중복/충돌 룰 제거**
    - `flexbox_layout` ↔ `no_css_grid` (의미 중복)
    - `forbidden_tag` ↔ `no_figure_figcaption` (중복)
    - `root_var_naming` (`common.md:196`) vs `codex.md:43` 충돌 정리
    - `no_raw_calc/no_raw_vw` (`rules.yaml:246-264`) vs `codex.md:49,75` 예시 정합성 정리
13. **자동 검증 불가능한 자연어 규칙 슬림화** — auto-fix가 처리하는 포맷팅 규칙(CSS 한 줄, 미디어쿼리 들여쓰기 등)은 `gemini.md`/`codex.md`에서 제거. 에이전트 인지 부하 감소.

### P2

14. **DSC-002 합의 반영** — `preprocess_payload/hints` (`figma-section-spec.py:637-645`), post-impl minor 재분류 정책 (`post-impl-verify.py:178-180,222-229`) 구현.
15. **semantic MAJOR → blocking 승격 검토** — 현재 CRITICAL만 blocking (`post-impl-verify.py:178-180`).
16. **`manual_review` 7개, `documentation` 3개 규칙 실행 가능화 또는 제거.**

## 권장 실행 순서

```
Step 1: 규칙 슬림 + 충돌 제거 (P1 #12, #13) ─ 하루
Step 2: Deterministic Codegen (P0 #2) ─ figma-section-spec.py 확장
Step 3: repair-from-violations.py (P0 #1) + post-impl 자동 repair-loop
Step 4: Rule-ID 브리프 전환 (P0 #4, #5)
Step 5: 디자인 토큰 파이프라인 (P0 #3)
Step 6: 검증 커버리지 공백 메우기 (P0 #6, #8, #9)
```

**기대 효과**: "LLM은 시맨틱 결정만, 나머지는 결정론" 구조로 전환되면 섹션당 수정 횟수 5~6회 → 1~2회 수준 기대 (두 에이전트 공통 예측).

## 에이전트 간 의견 차이

| 쟁점 | Codex | Gemini | 결론 |
|---|---|---|---|
| 우선순위 | 규칙 수정/커버리지 보강 먼저 | IR 기반 Deterministic Codegen 먼저 | **병행 P0** (Codex가 단기, Gemini가 구조 개편) |
| 규칙 삭제 범위 | 중복 규칙 중심 | 포맷팅 규칙 대부분 제거 | Auto-fix 도입 후 Gemini 안 적용 |
| 재dispatch | Rule-ID 체크리스트 + 위반 JSON | diff/patch 부분 수정 | 두 방식 결합 가능 |

## Open Questions

1. `documentation` 3개 규칙을 실행 가능 규칙으로 승격 가능한지?
2. spec ↔ section 매핑 휴리스틱 실패율 계측 필요 (`validate-semantic.py:2217-2245`).
3. CSS AST 파서 선택: Python `cssutils` / `tinycss2` vs Node `stylelint/postcss`?
4. `figma-section-spec.py`를 어느 수준까지 IR 컴파일러로 격상할지 (레이아웃 Decision Tree 파이썬 이관 범위).

## Architect Escalation
없음 (첫 조사, 실패 이력 없음)

---
- 원본 조사 결과:
  - `/mnt/d/dev-base/.gran-maestro/debug/DBG-001/finding-codex.md`
  - `/mnt/d/dev-base/.gran-maestro/debug/DBG-001/finding-gemini.md`

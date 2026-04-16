# PLN-008: Figma→Code 파이프라인 개선 (A→E→B→D→C 순차)

## 개요
DBG-001 진단 결과(codex+gemini 합의)를 기반으로 현재 Figma MCP→Code 퍼블리싱 파이프라인의 구조적 결함을 **5단계 순차 REQ**로 해소한다. 핵심 전략: "LLM은 시맨틱 결정만 담당, 나머지는 결정론적 파이프라인이 통제".

## 배경
- 섹션당 수동 수정 5~6회 반복 → 재작업 비용 폭증
- DBG-001 근본 원인 진단:
  - LLM을 CSS 컴파일러로 오용 (80% 결정론적 작업을 확률 모델이 담당)
  - 과밀·충돌 규칙 (`rules.yaml` 97개, `validation_schema.json` 93개)
  - Post-hoc 검증 + auto-fix 부재 (`validate-semantic.py --fix` 미구현)
  - Spec↔구현 지시 미분리 (`CLAUDE.md:264-265` vs `:367-373` 충돌)
- 업계 사례(Builder.io Mitosis IR, Locofy LCN, Anima) 대조 결과 IR 기반 결정론적 변환 + auto-fix + 디자인 토큰이 표준

## 목표
- 섹션당 수동 수정 횟수 **5~6회 → 1~2회**
- `rules.yaml` 규칙 수 **97 → 60 이하**
- `figma-validate.py` 커버리지 **9카테고리 → 11+** (vector_nodes, images 포함)
- `post-impl-verify` exit code 1 발생률 **50% 감축**

## 인수 기준 초안
이 plan의 구현이 완료됐다는 것은:
- [MUST] [TIER-B] 신규 섹션 퍼블리싱 작업 1회 수행 시 post-impl-verify exit 0 도달까지 수동 수정 횟수가 1~2회로 측정된다 (기존 5~6회 대비).
- [MUST] [TIER-B] `rules.yaml`에 남은 규칙 수가 60개 이하이고 중복·충돌 규칙이 제거되었음이 grep으로 확인된다.
- [MUST] [TIER-A] `CLAUDE.md`에서 "MCP 직접 해석" 경로가 삭제되고 "spec만 참조" 원칙이 단일 경로로 남아있음이 확인된다.
- [MUST] [TIER-A] `tools/repair-from-violations.py`가 존재하며 `post-impl-verify.py`에서 1회 자동 repair-loop이 실행된 후 재검증되는 동작이 로그로 확인된다.
- [MUST] [TIER-A] `rules/templates/publishing/impl-request.md`에 인라인 장문 규칙 섹션이 제거되고 `rule_ids:` 참조 방식으로 대체되었음이 확인된다.
- [MUST] [TIER-A] `figma-section-spec.py` 실행 결과에 `extracted/{section}_base.html`, `extracted/{section}_base.css`, `extracted/tokens.json`이 생성된다.
- [SHOULD] [TIER-B] 기존 퍼블리싱 결과물(변경 전 HTML/CSS 섹션)이 `post-impl-verify` 체인에서 여전히 exit 0을 유지하는 회귀가 없음이 확인된다.
- [SHOULD] [IMPACT] [TIER-B] 기존 외주 브리프(Codex/Gemini)로 진행된 최근 REQ 결과물이 새 파이프라인에서 경고·차단 없이 재검증 통과한다.

## 범위 예산 (Appetite)
- REQ 1 (A): 0.5~1일 — 규칙 슬림 (저위험)
- REQ 2 (E): 0.25~0.5일 — CLAUDE.md 충돌 제거 (문서 수정)
- REQ 3 (B): 1~2일 — `repair-from-violations.py` 신규 + post-impl-verify 확장
- REQ 4 (D): 0.5~1일 — Rule-ID 브리프 전환
- REQ 5 (C): 2~3일 — Deterministic Codegen + 디자인 토큰 (가장 큰 구조 개편)

## 제외 범위 (No-go Scope)
- 기존 퍼블리싱 결과물 재생성/마이그레이션 (역호환 보장만)
- 프론트엔드 프레임워크(React/Vue) 코드 생성 (HTML/CSS 순수 퍼블리싱만)
- Node.js 기반 CSS 파서 도입 (Python `tinycss2`/`cssutils`만 사용)
- 컴포넌트 라이브러리 구축 (Anima Code Connect 수준 차용은 이번 범위 외)
- Stitch/Figma Dev Mode MCP 공식 API 연동 전환

## 제약사항

### Out-of-scope
- 퍼블리싱 외 도메인(백엔드/React 변환) 적용 확장 금지
- 기존 rules/, tools/ 디렉터리 구조 전면 개편 금지

### 기술적
- Python 3.10+ 전용 (기존 tools/ 전체가 Python)
- CSS 파서: `tinycss2` + `cssutils` 병용 (Node 도입 불가)
- 기존 `figma-section-spec.py`, `figma-validate.py`, `validate-semantic.py`, `post-impl-verify.py` 스크립트 호환성 유지

### 비즈니스
- 진행 중인 퍼블리싱 REQ(REQ-003~023) 결과물과 역호환
- REQ 순서 엄수: A → E → B → D → C (의존성 때문)
- 각 REQ 완료 후 기존 post-impl-verify 체인이 여전히 exit 0을 유지해야 함

## 우선순위 (MoSCoW)
- **Must**: REQ 1~5 전체 (A, E, B, D, C)
- **Should**: DSC-002 합의(`preprocess_payload/hints`) REQ5에 포함
- **Could**: semantic MAJOR → blocking 승격(P2)
- **Won't (this time)**: Node 기반 파서, 컴포넌트 라이브러리, React 변환

## 의존성
- 선행 필요: 없음
- 연관:
  - DBG-001 (근본 원인 진단 근거)
  - DSC-002 (기존 합의 중 REQ5에서 반영 예정)
  - REQ-019 (validate-semantic.py 최근 확장 — 충돌 없이 병합)

## 테스트 전략
- **방법론**: 적용 (커버리지 미설정)
- **전략**: 퍼블리싱 파이프라인 특성상 단위테스트보다 **통합 검증 기반**:
  - 각 REQ 완료 후 기존 섹션 샘플 1~2개에 전체 파이프라인 재실행 → post-impl-verify exit 0 확인
  - `tools/repair-from-violations.py`는 단위 테스트 포함 (`tests/test_repair.py`)
  - `figma-section-spec.py` Deterministic Codegen은 골든 파일 비교 테스트 (known Figma 노드 → expected base.html/css)

## Loop 종료 조건
- 기존 검증 통과(기본값): 각 REQ마다 post-impl-verify exit 0 + 성공 지표 충족 시 종료

## 브라우저 테스트
- enabled: false
- 사유: 이번 plan은 파이프라인 도구/규칙 개선이 주목적. UI 결과물은 기존 회귀 샘플로 검증하며 신규 브라우저 시나리오 없음.

## 분리 실행 (5개 REQ 순차)

### REQ 1 — A: 규칙 슬림 + 충돌 제거
**목표**: 규칙 인지 부하 감소 + 내부 모순 해소 (Quick win)

**작업 범위**:
- 중복/충돌 룰 제거:
  - `flexbox_layout` ↔ `no_css_grid` (중복 → 통합)
  - `forbidden_tag` ↔ `no_figure_figcaption` (중복 → 통합)
  - `root_var_naming` (`common.md:196`) vs `codex.md:43` 충돌 해소 (하나의 방향으로 통일)
  - `no_raw_calc/no_raw_vw` (`rules.yaml:246-264`) vs `codex.md:49,75` 예시 정합성 정리
- `manual_review` 7개 + `documentation` 3개 규칙 실행 가능화 또는 삭제 판단 (DBG-001 Open Question #1)
- 자동 검증 불가능한 포맷팅 규칙(CSS 한 줄, 미디어쿼리 들여쓰기)은 이번 REQ에서는 `# TODO: remove after REQ3 auto-fix` 마킹만 (REQ3 완료 후 실제 삭제)
- `validate-semantic.py` 룰 엔진 연결 누락 보강: `column flex gap 금지` 함수(`:2626-2648`)를 룰에 연결

**AC**:
- `rules.yaml` 규칙 수 97 → 60 이하
- `grep -r "flexbox_layout\|no_css_grid\|forbidden_tag\|no_figure_figcaption" rules/`에서 중복 정의 0건
- `column flex gap 금지` 규칙이 `validate-semantic.py` 실행 시 실제 호출됨(로그 확인)

**의존성**: 없음 (선행 REQ)

### REQ 2 — E: Spec-only 원칙 강제
**목표**: H6 (spec/구현 지시 분리 실패) 구조적 해소

**작업 범위**:
- `CLAUDE.md:264-265` "spec만 참조" vs `:367-373` "MCP 직접 해석" 공존 충돌 제거
- "피그마 MCP 기반 워크플로우" 섹션 정리: "AI 직접 해석 허용" 표현 삭제, `figma-section-spec.py` 경유만 허용
- `rules/templates/publishing/impl-request.md`에서 MCP 직접 해석 허용 문구 제거
- `CLAUDE.md` 5단계 플로우만 유일 경로로 남김

**AC**:
- `CLAUDE.md` 내 "MCP 직접 해석" 문자열 0건
- `rules/templates/publishing/impl-request.md` 내 "AI가 MCP 응답을 직접 해석" 문자열 0건
- `figma-section-spec.py` 경유 문구가 유일 경로로 명시됨

**의존성**: REQ 1 완료 (규칙 슬림 후 문서 정리가 더 일관됨)

### REQ 3 — B: `tools/repair-from-violations.py` + auto-fix 루프
**목표**: 결정론적 위반 자동 수정으로 재작업 횟수 직접 감축 (P0 핵심)

**작업 범위**:
- 신규 스크립트 `tools/repair-from-violations.py` 작성
- 입력: `figma-validate.py` / `validate-semantic.py`의 JSON 위반 리포트 + 대상 HTML/CSS 파일
- 결정론적 치환 규칙 (REQ 1 완료 후 확정된 규칙셋 기준):
  - `border-radius: 999px` → `2em`
  - 8자리 hex → 6자리 또는 rgba 변환
  - CSS 셀렉터 멀티라인 → 한 줄 포맷 (`tinycss2` 사용)
  - 미디어쿼리 내부 들여쓰기 제거
  - `rgb()`/`rgba()` → hex (투명도 없을 때)
  - `letter-spacing` px → em 변환
- `tools/post-impl-verify.py` 확장:
  - 위반 감지 시 `repair-from-violations.py` 1회 자동 실행
  - 재검증 후 남은 위반만 LLM 재dispatch 대상으로 축소
  - 자동 repair 로그 기록
- `validate-semantic.py`에 `--fix` 플래그 도입 (단순 사용 케이스용)
- REQ 1에서 마킹한 "포맷팅 규칙 auto-fix로 대체" 항목을 실제 삭제

**AC**:
- `tools/repair-from-violations.py` 존재 + 단위 테스트 통과
- `post-impl-verify.py` 실행 로그에 `[auto-repair] N violations fixed` 형태 라인 출력
- 샘플 섹션 1개에 의도적 위반(999px, 멀티라인 셀렉터 등) 주입 후 파이프라인 실행 → exit 0 달성
- 기존 통과하던 섹션 재실행 시 여전히 exit 0 (회귀 없음)

**의존성**: REQ 1 (규칙 확정), REQ 2 (spec-only 원칙)

### REQ 4 — D: Rule-ID 체크리스트 + 위반 JSON 브리프
**목표**: H1 (컨텍스트 오버플로우), H5 (인라인 브리프 토큰 경쟁) 해소

**작업 범위**:
- `rules/rules.yaml`에 각 규칙의 `id` + `category` + `priority` 체계 확정 (없으면 추가)
- `rules.yaml:45-49` precedence 규약 명문화: severity만 있는 현 구조에 `priority: int` 필드 추가 + 충돌 해소 규약 문서화
- 외주 브리프(`rules/templates/publishing/impl-request.md`)에서 인라인 장문 규칙 섹션 삭제
- 대신 아래 주입 방식으로 전환:
  - `rules_version: X` 필드
  - `rule_ids: [ID1, ID2, ...]` 참조 목록
  - 직전 위반 JSON(재dispatch 시)만 첨부
- 에이전트는 필요 시에만 개별 규칙 파일 Read (인라인 전체 읽기 강제 해제)

**AC**:
- `rules.yaml` 모든 규칙에 `id/category/priority` 필드 존재
- `rules/templates/publishing/impl-request.md` 길이가 REQ 전 대비 50% 이상 감소
- 브리프 파일에 `rule_ids:` 키 존재
- 샘플 REQ 재실행 시 에이전트가 필요한 규칙만 개별 Read함이 로그로 확인

**의존성**: REQ 1 (규칙 슬림), REQ 3 (auto-fix로 검증 루프 축소)

### REQ 5 — C: `figma-section-spec.py` Deterministic Codegen + 디자인 토큰
**목표**: Builder.io/Mitosis IR 패턴 차용 + Locofy LCN 토큰 파이프라인 (구조 개편, 최대 효과)

**작업 범위**:
- `figma-section-spec.py`에 Base HTML/CSS 뼈대 생성 기능 추가
  - Figma `layoutMode`/`itemSpacing`/`padding*`/`fills`/`style` → flex + hex + 무단위 비율 CSS로 **기계 변환**
  - `div` 기반 뼈대 + 모든 섹션/요소에 자리표시자 클래스 (`{section}_base_{n}` 패턴)
- 산출물 추가:
  - `extracted/{section}_base.html`: 구조 + placeholder 클래스만 포함
  - `extracted/{section}_base.css`: 결정론적으로 변환된 CSS (padding/gap/color/typography)
- LLM 역할 축소: base를 받아 **시맨틱 마크업 교체**(`div`→`nav/h2` 등)와 **클래스 네이밍**만 수행
- 디자인 토큰 자동 추출 기능:
  - Figma `fills`/`style` → `extracted/tokens.json`
  - 동일 색상/타이포 중복 감지 → CSS 변수화 (`--color-primary`, `--font-heading` 등)
- DSC-002 합의 반영: `preprocess_payload/hints` (`figma-section-spec.py:637-645`) 구현
- 외주 브리프 템플릿 수정: "base.html/base.css 기반으로 시맨틱 교체 + 클래스 네이밍만 수행" 명시

**AC**:
- `figma-section-spec.py` 실행 결과로 `extracted/{section}_base.html`, `extracted/{section}_base.css`, `extracted/tokens.json` 3종 생성
- Base CSS에 동일 섹션 반복 실행 시 바이트 단위 동일성 보장 (결정론성)
- 샘플 Figma 노드로 골든 파일 비교 테스트 통과
- LLM 브리프에서 "CSS 값 결정" 지시 문구 제거 확인 (시맨틱 교체만 지시)
- 섹션당 수동 수정 횟수 측정: plan 시작 전 5~6회 → 1~2회 (회귀 샘플 3개 기준)

**의존성**: REQ 1~4 전부 완료

## 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|--------|--------|------|-----------|
| 규칙 통합 과정에서 기존 통과 섹션이 갑자기 실패 | 중 | 중 | REQ 1 완료 직후 회귀 샘플 3개로 post-impl-verify 재실행. 실패 시 rollback + 개별 규칙 복원 |
| `tinycss2`/`cssutils`가 기존 CSS 포맷을 잘못 재작성 | 중 | 상 | REQ 3에서 repair 스크립트에 dry-run 모드 + diff 출력 기본값. 수동 검토 거친 후 적용 승격 |
| Deterministic Codegen이 복잡한 Figma 노드(absolute positioning, constraint 등) 처리 못함 | 상 | 중 | REQ 5 Phase 1은 VERTICAL/HORIZONTAL flex 노드만 지원, NONE/absolute는 LLM fallback 허용 |
| DSC-002 합의(`preprocess_payload/hints`) 반영 시 기존 spec.md 포맷 breaking | 중 | 중 | REQ 5에서 기존 spec.md 생성 경로는 유지하고 별도 enhanced 경로 추가 (점진 전환) |
| Rule-ID 브리프 전환 후 에이전트가 규칙 파일을 실제로 Read하지 않음 | 중 | 상 | REQ 4 완료 후 샘플 REQ 1회 실행해 에이전트 Read 로그 확인. Read 없으면 브리프에 명시적 Read 지시 추가 |
| REQ 5 범위가 커서 예산 초과 | 상 | 중 | Phase 분리 — Phase 1: Base HTML/CSS만, Phase 2: tokens.json. Phase 1 완료 후 재평가 |

## Intent (JTBD)
- **When I**: Figma 디자인을 HTML/CSS로 퍼블리싱해야 할 때
- **I want to**: LLM이 규칙을 무시하거나 잘못된 CSS 값을 생성하지 않고, 기계적 작업은 결정론적 도구가 처리하도록 파이프라인을 재설계하고 싶다
- **So I can**: 섹션당 5~6회 반복되던 수동 수정을 1~2회로 줄이고, 퍼블리싱 속도와 품질을 동시에 확보할 수 있다

## 연관 컨텍스트

> 상세 내용은 아래 파일을 직접 참조하세요. 내용을 이 파일에 복사하지 않습니다.

| 유형 | ID | 파일 경로 |
|------|----|-----------|
| 디버그 조사 | DBG-001 | `.gran-maestro/debug/DBG-001/debug-report.md` |
| 디버그 조사 (원본) | DBG-001 | `.gran-maestro/debug/DBG-001/finding-codex.md` |
| 디버그 조사 (원본) | DBG-001 | `.gran-maestro/debug/DBG-001/finding-gemini.md` |
| 기존 합의 | DSC-002 | `.gran-maestro/discussion/DSC-002/consensus.md` |

## Confidence Score Matrix (자가평가)
| 축 | 점수 | 근거 |
|----|------|------|
| Clarity | 0.90 | DBG-001 진단 + A~E 범위 명확 |
| Feasibility | 0.85 | 모든 작업이 기존 Python 도구 확장 범위 내 |
| Decoupling | 0.95 | 5개 REQ가 명확히 분리되고 순차 실행 가능 |
| Completeness | 0.85 | AC 측정 가능, 회귀 방지 전략 명시 |

**종합**: 0.89 — 모든 축 0.5 이상, 저장 진행.

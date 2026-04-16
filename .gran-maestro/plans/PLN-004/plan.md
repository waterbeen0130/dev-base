# PLN-004 — Figma 추출 누락 방지 자동 정규화/검증 워크플로우

- 생성일: 2026-04-12
- Cynefin: Complicated
- 상태: active

## 1. 요청 (Refined)

Figma → HTML/CSS 변환 시 폰트(font-family/line-height/color), 여백(gap/padding/margin), 텍스트 내용/줄바꿈, 자식 frame 누락 등이 매번 반복되어 사용자가 일일이 수정 지시해야 한다. 이를 **구조적으로 막는** 자동 워크플로우를 도입한다.

이번 세션에서 발견된 누락 12종 (실제 사례):
- font-family 누락 (Noto Serif KR / Noto Sans KR)
- line-height 누락 (전 셀렉터)
- 색상 잘못 (`.ba_panel_head` #312d2b → #916046, `.ba_panel_body` #787472 → #5a5048)
- 텍스트 내용 임의 변경 (탭 라벨, 배지 텍스트)
- 줄바꿈 손실 (`\n`, `\u2028`, `\xa0`)
- gap 값 임의 채택 (`.ba_left` 31px → 67px)
- 자식 frame 통째 누락 (Frame 535 panel)
- padding 임의 채택 (`.ba_panel` 30px → 사실상 0)
- Figma height(글리프) vs CSS line-box 불일치 (43 vs 53.75)
- Figma 링크 (`interactions[].actions[].url`) 추출 누락
- 큰 padding clamp 미적용 (192/223/114 → fixed)
- 수직 gap 사용 (column flex 룰 위반)

## 2. 범위

**포함**:
- 새 도구 `tools/figma-section-spec.py` (사전 추출 정규화)
- 새 도구 `tools/figma-validate.py` (사후 자동 검증)
- 두 도구를 잇는 워크플로우 문서화 (CLAUDE.md / rules/claude.md)
- rules.yaml에 "사전 spec sheet 사용 강제" 룰 추가

**제외**:
- 기존 `tools/figma-extract.py` 재작성 (재사용만)
- `tools/validate-semantic.py` 로직 변경 (별도 인터페이스)
- Figma MCP 서버 자체 변경

**시작점 힌트**:
- `tools/figma-extract.py` (기존 정규화 로직 재사용)
- `tools/validate-semantic.py` (CSS 파싱 로직 재사용 가능)
- `rules/rules.yaml` (룰 추가)

## 3. 결정 사항

### 접근법: **통합 (사전 + 사후)**
- 사전: spec sheet 생성 → AI에 강제 입력
- 사후: 자동 검증 → 누락/불일치 발견 시 차단

### Spec sheet 형식: **Markdown + JSON 둘 다**
- Markdown: 사람이 읽고 검수 가능, AI 프롬프트에 직접 주입
- JSON: 사후 검증 도구의 입력으로 사용 (구조 파싱)

### 도구 책임 분담

**`tools/figma-section-spec.py`** (사전 정규화)
- 입력: `--file-key K --node-id N` (또는 Figma URL)
- 출력:
  - `extracted/{section}_spec.md` (사람용 + AI 프롬프트용)
  - `extracted/{section}_spec.json` (검증 도구용)
- 추출 항목 (모든 노드 강제):
  1. **TEXT 노드별**: id, name, characters (raw, with `\n`/`\u2028`/`\xa0` 보존), fontFamily, fontSize, fontWeight, lineHeightPx, lineHeightRatio (lhPx/fontSize), letterSpacing, fills color (hex), textAlignHorizontal, textAlignVertical
  2. **FRAME 노드별**: id, name, bbox (x, y, w, h), layoutMode, paddingTop/Right/Bottom/Left, itemSpacing, primaryAxisAlignItems, counterAxisAlignItems, fills (color or imageRef)
  3. **interactions**: 각 노드의 `interactions[].actions[]` 중 type=URL인 것 → `{ node_id, url, openInNewTab }` 추출
  4. **이미지 fills**: imageRef 발견 시 `tools/figma-extract.py --emit-mapping`과 연동해 다운로드 URL 매핑
- AI 프롬프트 주입 가이드: 출력 markdown 상단에 "이 spec sheet의 모든 행을 빠짐없이 CSS로 표현하세요. 누락 시 사후 검증에서 차단됩니다." 명시

**`tools/figma-validate.py`** (사후 자동 검증)
- 입력: `--spec extracted/{section}_spec.json --html output.html --css output.css`
- 검증 항목:
  1. 각 TEXT 노드의 characters가 HTML에 존재하는가 (텍스트 내용 위변조 검출)
  2. 줄바꿈 보존 (`\n` → `<br>` 또는 줄바꿈, `\xa0` → `&nbsp;`)
  3. 각 TEXT 셀렉터에 fontFamily, fontSize, fontWeight, lineHeight, color 모두 명시 (누락 검출)
  4. lineHeight 값이 lhPx/fontSize 비율과 일치 (오차 ±0.05)
  5. fills color hex 일치
  6. FRAME의 padding/gap이 CSS에 반영
  7. 100px 이상 padding/gap이 clamp() 사용
  8. column flex에 gap 사용 안 함
  9. Figma `interactions[].actions[].url` 존재 시 HTML `<a href="..." target="_blank">` 일치
- 출력: 위반 항목 표 + 누락된 spec 행 목록 + exit code (0 PASS, 1 FAIL)

### 워크플로우 통합

```
1. 새 섹션 작업 시작
   ↓
2. python3 tools/figma-section-spec.py --file-key X --node-id Y
   → extracted/section_N_spec.md / .json 생성
   ↓
3. AI는 spec.md를 컨텍스트로 받아서 HTML/CSS 작성
   (raw Figma JSON 직접 해석 금지)
   ↓
4. python3 tools/figma-validate.py --spec ... --html ... --css ...
   → 위반 0건이어야 다음 섹션 진행 허용
   ↓
5. python3 tools/validate-semantic.py (기존 코드 컨벤션 검증)
   → 둘 다 통과해야 commit
```

## 4. 인수 기준 초안

이 plan의 구현이 완료됐다는 것은:
- [MUST] [TIER-A] `tools/figma-section-spec.py`가 단일 섹션 node-id에 대해 모든 TEXT/FRAME/interaction 데이터를 빠짐없이 spec.md + spec.json으로 추출한다
- [MUST] [TIER-A] spec.md에 각 TEXT 노드별 fontFamily, fontSize, fontWeight, lineHeightRatio, letterSpacing, color, characters(raw) 7개 필드가 모두 표시된다
- [MUST] [TIER-A] spec.json에 동일 정보가 구조화되어 저장되며, fills imageRef는 다운로드 URL로 매핑된다
- [MUST] [TIER-A] `tools/figma-validate.py`가 spec.json + 결과 HTML/CSS를 입력으로 받아 9개 검증 항목을 모두 실행하고 위반 시 non-zero exit
- [MUST] [TIER-A] [IMPACT] 기존 `tools/validate-semantic.py`는 변경 없이 동작 유지 (병렬 실행 가능)
- [SHOULD] [TIER-B] CLAUDE.md / rules/claude.md에 새 워크플로우 절차가 문서화된다 (Figma → spec → 코드 → 검증)
- [SHOULD] [TIER-B] rules.yaml에 새 룰 `figma_spec_sheet_required` 추가 (검증 단계에서 spec.json 누락 시 경고)
- [SHOULD] [TIER-B] 모제림 Section_03~11 작업 시 새 워크플로우를 적용해 누락 0건 달성 검증
- [SHOULD] [TIER-B] [IMPACT] 기존 `tools/figma-extract.py`의 `--emit-mapping` 동작 유지 (figma-section-spec.py와 호환)

## 5. 제약사항

- 보안: Figma 토큰은 환경변수만 사용 (코드/로그에 평문 금지)
- 성능: spec sheet 생성 < 5초/섹션 (Figma API 1~2 call)
- 호환성: Python 3.10+, 외부 의존성 추가 금지 (urllib + json만)
- 운영: 기존 도구들과 충돌 없이 병렬 작동

## 6. 우선순위 (MoSCoW)

- **Must have**: figma-section-spec.py + figma-validate.py 핵심 동작, 9개 검증 항목 전부
- **Should have**: 워크플로우 문서화, rules.yaml 룰 추가
- **Could have**: spec sheet의 시각 미리보기 (HTML 렌더), Figma URL 직접 파싱 (file-key 추출)
- **Won't have**: figma-extract.py 재작성, 자동 코드 생성 (AI는 여전히 작성자)

## 7. 의존성

- 선행 필요: 없음 (현재 도구들 그대로 사용)
- 연관: REQ-005 (rules.yaml SSOT — 새 룰 추가 시 build-rules.py 재실행), REQ-006 (validate-semantic.py — 별도 도구로 병렬)
- 없음

## 8. 분리 실행

이 plan은 **3개 REQ로 분리 실행**을 권장:

| 단계 | REQ 주제 | 의존성 |
|---|---|---|
| ① | `tools/figma-section-spec.py` 사전 정규화 도구 작성 + spec.md/json 출력 | 독립 |
| ② | `tools/figma-validate.py` 사후 검증 도구 작성 (9개 검증 항목) | blockedBy ① (spec.json 형식 확정 필요) |
| ③ | CLAUDE.md/rules.yaml 워크플로우 문서화 + 룰 추가 + Section_03 적용 검증 | blockedBy ②  |

## 9. 리스크 레지스터

| 리스크 | 가능성 | 영향 | 완화 방안 |
|---|---|---|---|
| AI가 새 워크플로우를 무시하고 raw API 직접 해석 | 중 | 상 | rules.yaml에 `figma_spec_sheet_required` 룰 추가 + CLAUDE.md에 강제 절차 명시. 검증 단계에서 spec.json 미존재 시 차단 |
| spec sheet 생성이 실제로 모든 케이스를 커버하지 못함 | 중 | 중 | Section_02를 reference case로 사용해 12개 누락 모두 spec sheet에 표현되는지 회귀 테스트 |
| 사후 검증 false positive (Figma 정확값 vs 브라우저 렌더 차이) | 중 | 중 | tab height 케이스처럼 글리프 vs line-box 차이는 별도 룰로 명시. 색상은 hex 정확 일치, 폰트는 family 이름만 일치 |
| 도구 작성 후 유지보수 부담 | 하 | 중 | figma-extract.py와 같은 단일 파일 + 의존성 최소화 |

## 10. 테스트 전략

- **적용 (커버리지 미설정)** — 도구 자체에 대한 단위 테스트보다 reference case (Section_02)에 대한 통합 회귀 테스트 우선
- 회귀 케이스: Section_02의 12개 누락 항목이 spec sheet에 모두 등장 + figma-validate.py가 누락 시뮬레이션을 모두 catch
- 사람 검수: Section_03 작업 시 새 워크플로우 적용해 누락 0건 + AI 자율 작성 가능 여부 확인

## 11. Loop 종료 조건

기존 검증 통과(기본값) 유지 — 새 워크플로우의 검증 단계가 추가되어도 기존 mst:review 루프 동작은 변경 없음

## 12. AC ↔ TIER 매핑 (D3 Gate 보조)

| PAC ID | Grade | Tier | 검증 핵심 |
|---|---|---|---|
| PAC-1 | MUST | TIER-A | spec 추출 완전성 |
| PAC-2 | MUST | TIER-A | spec.md 7개 TEXT 필드 |
| PAC-3 | MUST | TIER-A | spec.json 구조 + 이미지 매핑 |
| PAC-4 | MUST | TIER-A | validate.py 9개 검증 항목 |
| PAC-5 | MUST | TIER-A | [IMPACT] 기존 validate-semantic.py 무손상 |
| PAC-6 | SHOULD | TIER-B | 문서화 |
| PAC-7 | SHOULD | TIER-B | rules.yaml 룰 추가 |
| PAC-8 | SHOULD | TIER-B | Section_03 적용 검증 |
| PAC-9 | SHOULD | TIER-B | [IMPACT] figma-extract.py 호환 |

## 13. Confidence Score Matrix

| 축 | 점수 | 근거 |
|---|---|---|
| Clarity | 0.85 | 12개 누락 사례 + 9개 검증 항목 명확 |
| Feasibility | 0.85 | 기존 도구 재사용 가능 + 외부 의존성 없음 |
| Decoupling | 0.90 | 3 REQ 분리 명확, 각자 독립 실행 가능 |
| Completeness | 0.80 | 핵심 항목 정의됨, false positive 처리 가이드만 추가 보강 가능 |

전체 평균 0.85 — 0.5 미만 항목 없음. 진행 가능.

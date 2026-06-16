# dev-base 통합 지시서 (AI-agnostic single source)

> 이 파일은 **손으로 유지하는 단 하나의 AI 지시서**다. PM(실행 주체)이 Claude / Codex(OMX) / Gemini 중 무엇이든 이 파일을 읽는다.
> `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` 는 이 파일을 가리키는 thin shim 일 뿐이며, 규칙·워크플로우 본문을 따로 담지 않는다.
>
> **규칙 본문은 여기 베끼지 않는다.** HTML/CSS 규칙의 단일 소스는 `rules/rules.yaml` 이고, 사람이 읽는 카탈로그는 거기서 자동 생성되는 `rules/common.md`(+`landing.md`/`basic.md`) 다. 이 파일은 규칙을 *가리키기만* 한다.

---

## 0. 공통 원칙

- 응답 언어: **한국어**. 코드 주석: **영어만**.
- 규칙의 단일 소스: `rules/rules.yaml` → 자동 생성 `rules/common.md`. 규칙 변경은 rules.yaml 만 수정하고 빌드 재실행(`python3 tools/build-rules.py`)한다. **규칙을 이 파일이나 AI shim 에 손으로 복제하지 않는다.**
- 검증 단일 소스: `tools/pm-verify.py` / `tools/validate-semantic.py`. 완료 보고 전 반드시 실행하고 raw 출력 그대로 보고한다(거짓 보고 금지).
- 폐기 도구 부활 금지: `generate.py`, `json-to-html.py`, `repair-from-violations.py`, `structural-diff.py`, `compare-css.py`, `run-pipeline.py`, `--converge` 자동 재시도 루프 등.

---

## 1. Figma → 퍼블리싱 변환 워크플로우 (스크린샷-우선 2패스)

> 핵심 원칙: **구조/시맨틱의 권위 출처는 시각(스크린샷)**, **정확한 값(텍스트/색상/폰트/px)의 권위 출처는 spec.json** 이다.
> spec.json 의 노드 트리를 *구조 생성 입력* 으로 쓰면 `main_f0` 같은 노드명 직역(transliteration)이 발생한다. 따라서 spec 은 Pass 2 의 "값 오라클" 로만 쓴다.

### Step 0 — 자산 추출
```bash
python3 D:/dev-base/tools/figma-section-spec.py \
  --file-key {KEY} --node-id {SECTION_ID} --output extracted/ --download-assets
FIGMA_TOKEN="figd_..." python3 D:/dev-base/tools/figma-png-download.py \
  --file-key {KEY} --node-ids "{MAIN},{SEC_1},..." \
  --output .gran-maestro/figma-png/ --include-fills --scale 1
```
- `--download-assets` 필수(이미지 1:1). 추출 직후 `text_nodes[0].fontSize` 존재 확인 — 없으면 즉시 중단(재추출).
- spec.json 은 이후 **값 오라클로만** 사용한다.
- 추출 성공 직후 원장에 기록(섹션 워크플로우 시작):
  ```bash
  python3 D:/dev-base/tools/workflow-ledger.py append --step extract --provider figma-section-spec --section {SECTION}
  ```

### Step 1 — Pass 1: 구조 (스크린샷만 보고 시맨틱 마크업)
- 입력: **PNG 스크린샷만**. spec 노드 트리는 보지 않는다.
- 화면을 보고 **역할(role)** 로 구조를 짠다: 상단 가로줄+메뉴 → `header > nav > ul > li > a`, 반복 카드 → `ul > li`, 큰 제목 → `h2/h3`, 서술 단락 → `p`.
- 클래스명은 아래 §2 네이밍 규칙대로. **노드명(main_f0 등) 절대 금지.**
- 모든 `<img>` 는 `.img_area` 래퍼 안에. 골격 CSS(flexbox)로 레이아웃만 잡는다.
- Pass 1 완료 시 원장 기록(`{provider}` = 실제 추출 주체 omx/codex/claude/gemini):
  ```bash
  python3 D:/dev-base/tools/workflow-ledger.py append --step structure --provider {provider}
  ```

### Step 2 — Pass 2: 값 정밀 보정 (spec.json 대조)
- spec.json 과 대조해 **값만** 덮어쓴다 — 구조는 변경하지 않는다.
- 텍스트는 `text_nodes[].characters` **byte-exact**(NBSP/`\n`/연속 공백 보존, `\n`→`<br>`).
- 색상 hex, 폰트 5필드(fontFamily/fontSize/fontWeight/lineHeight/color), letter-spacing em, px 값.
- `has_mixed_styles:true` 면 `character_segments` 로 구간별 `<span>` 분리.
- Pass 2 완료 시 원장 기록:
  ```bash
  python3 D:/dev-base/tools/workflow-ledger.py append --step values --provider {provider}
  ```

### Step 3 — 검증 (게이트)
```bash
python3 D:/dev-base/tools/pm-verify.py \
  --spec-dir extracted/ --html index.html --css css/common.css --img img/ --profile {landing|basic} \
  --section {SECTION}
```
- CRITICAL 0건이어야 완료. 실행 증거(통과 리포트) 없이는 완료/전달 금지.
- `--section` 을 주면 pm-verify 가 원장에 `verify` 단계를 자동 기록한다.

### Step 4 — 시각 비교
- Playwright 1920px 렌더 → Figma PNG 와 나란히 비교 → 자연어 피드백 → Pass 1/2 복귀.

### 워크플로우 원장 (순서·주체 증명, MANDATORY)
각 단계 완료 시 위 Step 0~3 의 `workflow-ledger.py` 호출로 `.gran-maestro/workflow-ledger.json` 에 단계를 기록한다. **JSON 을 손으로 편집하지 말고 반드시 helper CLI 를 쓴다**(원자적 기록·순서 보존). 생성되는 형식:
```json
{"section": "main_visual", "steps": [
  {"step": "extract",   "provider": "figma-section-spec", "ts": "..."},
  {"step": "structure", "provider": "omx", "ts": "..."},
  {"step": "values",    "provider": "omx", "ts": "..."},
  {"step": "verify",    "provider": "pm-verify", "ts": "..."}
]}
```
- `step` 은 `extract → structure(Pass1) → values(Pass2) → verify` 순서. `extract` 는 새 섹션 워크플로우를 시작(원장 리셋)하고, 나머지는 현재 섹션에 append 된다. `values` 가 `structure` 보다 먼저면 노드명 직역 위험으로 차단된다.
- `structure`/`values` 의 `provider` 는 알려진 추출 주체(omx/codex/claude/gemini)여야 한다(미상 차단).
- 검증: `python3 D:/dev-base/tools/check-workflow-order.py --ledger ...` + `check-extraction-provenance.py --ledger ...`. 원장이 있으면 accept 게이트(`accept-preflight-verify.py`)가 이 두 검사를 자동 수행한다.
- 원장은 현재(마지막) 섹션 기준 단일 파일이다. accept 게이트는 마지막 작업 섹션을 검증한다(다중 섹션 집계는 후속 과제).

### Step 5 — (선택) 그누보드 스킨
- `rules/gnuboard.md` 전체 Read 후 적용.

### 주의
- 텍스트·값을 **스크린샷에서 추측 금지** — 반드시 Pass 2 에서 spec 으로 덮어쓴다.
- 스크린샷은 1개 해상도 → 반응형은 미디어쿼리로 별도.
- Pass 2 생략 금지(값 어긋남) → pm-verify 가 강제.

---

## 2. 핵심 네이밍 원칙 (전체 규칙은 `rules/common.md` 참조)

> 아래는 가장 자주 틀리는 핵심 원칙 요약이다. **강제 규칙의 전체 목록·검증 기준은 `rules/rules.yaml`(→ `rules/common.md`) 이 단일 소스.**

- **공통 영역은 prefix 없음**: `.header`, `.footer`, `.logo`, `.gnb`, `.utils`, `.sns`, `.copyright`, `.container`. 어떤 페이지에 있어도 prefix 금지(`.index_header` ✗ → `.header`).
- **공통 영역 자식은 부모 스코핑**: `.logo{}` ✗ → `.header .logo{}` / `.footer .copyright{}`. (`common_area_child_scope`)
- **전역 클래스는 단독 선언**: `.header`/`.footer`/`.cont`/`.img_area` 에 `body`/`html` 부모 금지. 섹션 오버라이드(`.main_intro .cont`)만 허용. (`global_class_standalone`)
- **페이지 콘텐츠는 페이지 prefix**: `index.html`→`main_`, `greeting.html`→`greeting_`. prefix 는 섹션 컨테이너에만, 자식은 짧은 역할명 + 부모 스코핑(`.main_intro .card`).
- **Figma 노드명/추측 prefix 금지**: `main_f0`/`main_v53`/`header_b`/`sec_1`/`site_`/`g_` ✗. (`no_figma_nodeid_class`, `no_forbidden_class`)
- `<body>` 에 class 금지. 장식용 빈 태그 금지(`::before`/`::after`). 반복 요소는 `ul>li`.
- CSS: flexbox 전용(grid 금지), hex 색상, letter-spacing em, landing 은 px, `background-size` 금지, 셀렉터 한 줄.

---

## 3. 프로파일 / 도메인 추가 규칙

- Landing 추가 규칙: `rules/landing.md` (자동 생성)
- Basic 추가 규칙: `rules/basic.md` (자동 생성)
- 그누보드 스킨: `rules/gnuboard.md`

---

## 4. 코드 추출 에이전트

- 코드 추출은 **OMX(oh-my-codex)** 를 기본 사용하되, PM 은 Codex/Gemini/Claude 무관하게 위 워크플로우와 규칙을 동일하게 따른다.
- 추출 전 spec.json 의 fontSize 필드 존재를 반드시 확인(없으면 중단).
- 완료 전 pm-verify 실행 + raw 출력 보고. 외주 AI 자가 보고를 신뢰해 그대로 전달하지 않는다(실제 output 검증).

---

## 5. 참조

- 규칙 단일 소스: `rules/rules.yaml` (→ 자동 생성 `rules/common.md`)
- 검증: `tools/pm-verify.py`, `tools/validate-semantic.py`, `tools/accept-preflight-verify.py`
- 빌드: `python3 tools/build-rules.py` (rules.yaml → common/landing/basic.md + validation_schema.json)

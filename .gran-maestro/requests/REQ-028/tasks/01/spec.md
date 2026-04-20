# REQ-028 / Task 01 — Deterministic Codegen + 디자인 토큰

**Assigned Agent**: [config: codex-dev] → codex-dev
**Source Plan**: PLN-008
**Linked Debug**: DBG-001

## §0 Context Manifest
- `/mnt/d/dev-base/tools/figma-section-spec.py` (확장 대상, 661줄)
- `/mnt/d/dev-base/extracted/section_03_spec.json`, `section_04_spec.json` (입력 샘플)
- `/mnt/d/dev-base/tools/figma-validate.py` (참조 — spec.json 구조 이해)
- `/mnt/d/dev-base/rules/common.md` (CSS 변환 규칙 참조)
- `/mnt/d/dev-base/.gran-maestro/debug/DBG-001/debug-report.md`
- `/mnt/d/dev-base/.gran-maestro/discussion/DSC-002/` (preprocess_payload/hints 합의)

## §1 요약

`figma-section-spec.py`를 확장하여 spec.json/spec.md 외에 **Base HTML/CSS 뼈대**(`_base.html`, `_base.css`)와 **디자인 토큰**(`tokens.json`)을 기계적으로 생성한다. Builder.io/Mitosis IR 패턴과 Locofy LCN 토큰 파이프라인을 차용. LLM 역할이 "전체 코드 작성"에서 "시맨틱 마크업 교체 + 클래스 네이밍"으로 축소된다.

**핵심 효과**: Figma 노드의 layoutMode/padding/gap/fills/typography → CSS로의 80% 기계적 변환을 Python이 직접 수행. LLM은 `div`→`nav/h2/section` 시맨틱 교체와 의미 있는 클래스명만 담당.

## §2 범위

### 포함

#### 1. Base HTML 생성 (`extracted/{section}_base.html`)

spec.json의 `frame_nodes` + `text_nodes` 트리 구조를 HTML로 변환:
- 모든 프레임 → `<div>`, 모든 텍스트 → `<span>` (시맨틱 태그는 LLM이 나중에 교체)
- 클래스명: `{section}_f{node_index}` (프레임), `{section}_t{node_index}` (텍스트) — placeholder
- 노드 순서 = spec.json children 순서 = HTML DOM 순서 (CLAUDE.md 규칙 준수)
- 텍스트 콘텐츠: spec.json `text_nodes[].characters` 그대로 삽입 (byte-exact 보존)
- `\n` → `<br>`, `\xa0` → `&nbsp;` 변환
- 이미지/벡터 노드: `<img>` placeholder (src는 빈 값, alt에 노드 이름)

#### 2. Base CSS 생성 (`extracted/{section}_base.css`)

spec.json의 프레임/텍스트 속성을 CSS로 결정론적 변환:

| Figma 속성 | CSS 변환 | 규칙 |
|---|---|---|
| `layoutMode: "HORIZONTAL"` | `display: flex; flex-direction: row;` | |
| `layoutMode: "VERTICAL"` | `display: flex; flex-direction: column;` | |
| `layoutMode: null/NONE` | `display: block;` (기본) | |
| `itemSpacing` | `gap: {N}px;` (HORIZONTAL만. VERTICAL은 gap 금지 — margin 사용) | common.md: column flex gap 금지 |
| `paddingTop/Right/Bottom/Left` | `padding: {T}px {R}px {B}px {L}px;` (100+ 시 `clamp()` 래핑) | common.md: clamp 규칙 |
| `fills[0].color` (SOLID) | `background-color: #{hex};` 또는 `color: #{hex};` | common.md: hex 전용 |
| `fontSize` | `font-size: {N}px;` | |
| `fontWeight` | `font-weight: {N};` | |
| `lineHeightPx` + `fontSize` | `line-height: {ratio};` (무단위 비율 = lineHeightPx / fontSize) | common.md: 무단위 비율 |
| `letterSpacing` | `letter-spacing: {N/fontSize}em;` | common.md: em 전용 |
| `cornerRadius` | `border-radius: {N}px;` (999/9999 → `2em`, 원형 → `50%`) | common.md: pill 2em |

- 각 셀렉터 = 한 줄 포맷 (common.md 규칙)
- 모든 CSS 값은 spec.json에서만 유래 (추측 값 없음)
- 결정론성: 동일 spec.json → 동일 base.css (바이트 단위)

#### 3. 디자인 토큰 (`extracted/tokens.json`)

spec.json의 fills/style에서 **중복 색상/타이포 자동 감지** → CSS 변수화:

```json
{
  "colors": {
    "--color-1": "#090944",
    "--color-2": "#ffffff",
    "--color-3": "#463c37"
  },
  "typography": {
    "--font-heading": "font-weight: 700; font-size: 48px; line-height: 1.3;",
    "--font-body": "font-weight: 400; font-size: 16px; line-height: 1.5;"
  }
}
```

- 동일 hex 값이 3회 이상 등장 → CSS 변수 후보
- 동일 font-size + font-weight 조합이 2회 이상 등장 → 타이포 변수 후보
- base.css에서는 아직 변수 미사용 (hex 직접 사용). LLM이 나중에 tokens.json 보고 변수 적용 결정

#### 4. CLI 확장

기존 CLI에 `--codegen` 플래그 추가:
```bash
python3 tools/figma-section-spec.py \
  --file-key K --node-id N --output extracted/ \
  --codegen  # ← 신규: base.html + base.css + tokens.json 추가 생성
```

- `--codegen` 없으면 기존 동작 유지 (spec.json + spec.md만 생성) — 역호환
- `--codegen` 있으면 spec.json/md + base.html + base.css + tokens.json 5종 생성

#### 5. DSC-002 합의 반영 (선택적)

`figma-section-spec.py:637-645`의 `preprocess_payload/hints` 미구현 건:
- DSC-002 합의에서 제안된 전처리 힌트를 spec.json에 포함하도록 구현
- 범위: DSC-002 합의 문서를 Read하고 구현 가능한 부분만 반영

### 제외
- LLM 시맨틱 교체 로직 (이건 외주 브리프에서 지시)
- 기존 spec.json/spec.md 포맷 변경 (추가 필드만 가능)
- Figma API 호출 방식 변경 (기존 REST API 유지)
- 반응형/미디어쿼리 생성 (base는 데스크톱 1920px 기준만)

## §3 수락 조건

### AC-001 [automatable] [tdd-required] — `--codegen` 플래그 + 5종 파일 생성
- **Given**: 기존 spec.json이 있는 `extracted/` 디렉토리
- **When**: `python3 tools/figma-section-spec.py --file-key TEST --node-id TEST --output extracted/ --codegen` 실행 (또는 기존 spec.json 기반 오프라인 모드)
- **Then**: `extracted/{section}_base.html`, `extracted/{section}_base.css`, `extracted/tokens.json` 3종 추가 생성
- **Test**: 기존 `section_03_spec.json`을 입력으로 오프라인 변환 함수 호출 → 3종 파일 존재 확인

### AC-002 [automatable] [tdd-required] — Base HTML 구조 정합성
- **Given**: `section_03_spec.json`의 `frame_nodes` + `text_nodes` 트리
- **When**: 생성된 `_base.html`을 파싱
- **Then**: spec.json의 노드 수 = HTML 요소 수 (±이미지/벡터 placeholder). 텍스트 콘텐츠 byte-exact 일치.
- **Test**: `tests/test_codegen.py::test_base_html_structure` — BeautifulSoup으로 요소 카운트 + 텍스트 비교

### AC-003 [automatable] [tdd-required] — Base CSS 결정론성
- **Given**: 동일 `section_03_spec.json` 입력
- **When**: 생성 함수 2회 실행
- **Then**: 2회 출력이 바이트 단위 동일 (deterministic)
- **Test**: `tests/test_codegen.py::test_css_deterministic` — hash 비교

### AC-004 [automatable] [tdd-required] — CSS 변환 규칙 준수
- **Given**: spec.json에 `layoutMode: "VERTICAL"` + `itemSpacing: 20` 프레임 존재
- **When**: Base CSS 생성
- **Then**: 해당 프레임 셀렉터에 `flex-direction: column;` 있고 `gap` **없음** (column gap 금지 규칙)
- **Test**: `tests/test_codegen.py::test_vertical_no_gap` — CSS 텍스트 파싱으로 확인

### AC-005 [automatable] [tdd-required] — tokens.json 중복 감지
- **Given**: spec.json에 동일 hex `#090944`가 5회 등장
- **When**: tokens.json 생성
- **Then**: `colors` 에 `#090944` 매핑된 변수 존재
- **Test**: `tests/test_codegen.py::test_tokens_color_dedup`

### AC-006 [automatable] [regression-test] — `--codegen` 없이 기존 동작 유지
- **Given**: `--codegen` 플래그 미사용
- **When**: 기존 방식으로 실행
- **Then**: spec.json + spec.md만 생성 (base.html/css/tokens.json 미생성)
- **Test**: `tests/test_codegen.py::test_no_codegen_flag_backward_compat`

## 3.5 Test Scenarios (Pre-Impl)

### TS-001 (AC-001)
오프라인 테스트 — Figma API 미호출, 기존 spec.json 직접 입력:
```bash
python3 -m pytest tests/test_codegen.py::test_codegen_generates_files -v
```

### TS-002 (AC-002)
```bash
python3 -m pytest tests/test_codegen.py::test_base_html_structure -v
```

### TS-003 (AC-003)
```bash
python3 -m pytest tests/test_codegen.py::test_css_deterministic -v
```

### TS-004 (AC-004)
```bash
python3 -m pytest tests/test_codegen.py::test_vertical_no_gap -v
```

### TS-005 (AC-005)
```bash
python3 -m pytest tests/test_codegen.py::test_tokens_color_dedup -v
```

### TS-006 (AC-006)
```bash
python3 -m pytest tests/test_codegen.py::test_no_codegen_flag_backward_compat -v
```

### TS-007 (전체 회귀)
```bash
python3 -m pytest tests/ -v 2>&1 | tail -3
```
기대: 44+ passed (REQ-027 기준) + 신규 6+ passed, 0 failed

## §3.3 PAC Mapping

| PAC ID | Grade | Tier | Mapped Spec AC | Coverage |
|--------|-------|------|----------------|----------|
| PAC-6  | MUST  | TIER-A | AC-001, AC-002, AC-003 | full |
| PAC-1  | MUST  | TIER-B | TS-007 (e2e 재작업 횟수 측정은 수동) | partial |

## §3.5 Constraints
- Python 3.10+
- Figma API 호출 패턴 기존 유지 (ExtractionResult dataclass 호환)
- `--codegen` 없이 기존 동작 100% 호환
- base.css 각 셀렉터 한 줄 포맷 (common.md)
- base.html 텍스트 byte-exact (CLAUDE.md figma text fidelity)
- 결정론성: 동일 입력 → 동일 출력

## §5 선행: REQ-024~027 ✅, WIP merge ✅
## §6 후행: 없음 (PLN-008 마지막)
## §7 의존성: DBG-001, PLN-008, DSC-002

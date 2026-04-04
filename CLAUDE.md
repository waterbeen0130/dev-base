# Claude 규칙

Claude AI 어시스턴트 전용 규칙입니다.

---

## 기본
- `common.md` 규칙 우선 적용
- 응답 언어: 한국어
- 코드 주석: 영어만

---

## 프로젝트 초기 설정 (CRITICAL — 새 프로젝트 시작 시 필수)

### 권한 자동 허용 설정
새 프로젝트 시작 시 `{project}/.claude/settings.local.json`을 생성하여 모든 도구 접근을 자동 허용한다.
파일 접근, 편집, 검색, Bash 실행 등에 대해 사용자에게 매번 확인을 묻지 않도록 한다.

```json
// {project}/.claude/settings.local.json
// 템플릿: D:\dev-base\rules\claude-settings-template.json
{
  "permissions": {
    "allow": [
      "Read", "Write", "Edit", "Glob", "Grep",
      "Bash(*)", "Task", "WebFetch", "WebSearch",
      "NotebookEdit",
      "mcp__plugin_playwright_playwright__*",
      "mcp__plugin_context7_context7__*",
      "mcp__figma__*"
    ]
  }
}
```

- Gran Maestro 사용 시: `/mst:start` 부트스트래핑 단계에서 `.claude/settings.local.json` 존재 여부를 확인하고, 없으면 템플릿에서 자동 생성
- **사용자에게 파일 접근 권한을 매번 물어보는 것은 워크플로우를 방해함 — 프로젝트 폴더 내 모든 파일에 대한 접근은 기본 허용**

---

## 작업 방식

### 수정 전
1. 기존 코드 먼저 읽고 이해
2. 현재 코드 스타일/패턴 확인
3. 요구사항이 불명확하면 질문

### 수정 시
1. 필요한 부분만 수정
2. 전체 파일이 아닌 변경 부분만 제시
3. 기존 패턴 유지

### 새 기능
1. 요구사항 확인
2. 기존 코드 스타일에 맞춤
3. 복잡하면 단계별로 진행

---

## 하지 말 것
- 요청하지 않은 개선 추가
- 과도한 주석 추가
- 불필요한 에러 처리 추가
- 장황한 설명
- CSS 셀렉터를 여러 줄로 펼치기 (각 규칙은 한 줄로)
- CSS 미디어쿼리 내부 들여쓰기
- 미디어쿼리 안 모든 규칙을 한 줄에 이어붙이기
- padding/margin에 100px 미만 clamp 사용
- calc/vw 단독 사용
- `sec_1`, `sec_2` 같은 범용 클래스명 사용
- 모든 HTML 요소에 개별 클래스 부여 (부모+태그 선택자 우선)
- 짧은 라벨/키워드에 `<p>` 태그 사용
- CSS Grid 사용
- rgb()/hsl()/rgba()를 투명도 없이 사용 (hex 전용, 투명도 필요 시만 rgba)
- letter-spacing에 px 단위 사용 (em 전용)

---

## 선호
- 간결한 응답
- 실용적인 솔루션
- 최소한의 변경
- CSS 각 셀렉터 규칙은 한 줄 포맷
- 미디어쿼리 블록 안에서 각 규칙은 줄바꿈 분리 (들여쓰기 없음)
- 고정 px 단위 (padding/margin/gap)
- 페이지 프리픽스 클래스명 (`{페이지}_{역할}`)
- border-radius: 원형 요소는 `50%`, pill 형태는 `2em` (999px 금지)
- flexbox 전용 레이아웃
- hex 색상 코드 (`#fff`, `#090944`)

---

## 질문할 때
- 요구사항이 모호할 때
- 여러 접근법이 가능할 때
- 기존 코드와 충돌 가능성이 있을 때
- 큰 변경이 필요할 때

---

## 멀티 에이전트 분배 규칙 (CRITICAL — 필수)

> **Claude는 PM/오케스트레이터 역할만 수행한다. 코드 구현은 반드시 Codex 또는 Gemini CLI를 통해 외주한다.**

### 절대 금지
- `Task(subagent_type: "general-purpose")`로 코드 구현 위임 — Claude 토큰만 소비됨
- Claude가 직접 HTML/CSS/JS 코드를 작성하는 것 (PM 직접 개입 예외: 외주 에이전트가 max_cli_retries 소진 후에만)
- 모든 태스크를 동일 에이전트에 배정

### 필수 준수
- `config.json`의 `workflow.default_agent` 설정을 반드시 따름
- spec.md의 `Assigned Agent` 필드를 **프로젝트 유형에 따라** 배정:

#### 프로젝트 유형별 에이전트 배정

| 프로젝트 유형 | 주 에이전트 | 이유 | Codex 역할 |
|-------------|-----------|------|-----------|
| **퍼블리싱 (HTML/CSS, 피그마→코드)** | **gemini-dev** | frontend + large-context, 대용량 피그마 JSON 처리 최적 | 불필요 — 백엔드/테스트 없음 |
| **풀스택 (백엔드+프론트)** | codex-dev (백엔드) + gemini-dev (프론트) | 역할별 분리 | 백엔드 로직, API, DB |
| **백엔드 전용** | codex-dev | code, refactor, test | 전담 |
| **문서/설정 수정** | claude-dev | 소규모 인라인 수정 | 불필요 |

- **퍼블리싱 프로젝트에서 Codex를 사용하지 않음** — Codex의 capabilities(code, refactor, test)는 HTML/CSS 퍼블리싱과 무관
- Phase 2 실행 시 반드시 해당 에이전트의 CLI 명령어로 실행 (Skill 또는 Bash)

### 에이전트 CLI 실행 방법
```bash
# codex-dev (git repo가 아닌 경우 --skip-git-repo-check 추가)
codex exec --full-auto -C {worktree_path} "$(cat {prompt_file})"

# gemini-dev
cd {worktree_path} && gemini -p "$(cat {prompt_file})" --approval-mode yolo --sandbox=false 2>&1 | tee {task_dir}/running.log

# claude-dev (최후 수단 — claude-dev 배정 시에만)
Task(subagent_type: "general-purpose", prompt: ...)
```

### 외주 브리프 규칙 주입 (CRITICAL — 필수)

> **외주 브리프(phase2-impl.md) 작성 시, 에이전트별 규칙 파일 내용을 반드시 포함해야 한다.**
> 에이전트는 `D:\dev-base\rules\` 폴더에 직접 접근할 수 없으므로, PM이 브리프 안에 규칙을 주입해야 한다.

#### 퍼블리싱 프로젝트 전용 브리프 템플릿
- **퍼블리싱 프로젝트**: `D:\dev-base\rules\templates\publishing\impl-request.md` 를 기본 템플릿으로 사용 (규칙이 이미 포함됨)
- **기타 프로젝트**: 플러그인 기본 `templates/impl-request.md` 사용 + 아래 규칙 섹션을 수동 주입

#### 브리프 `## 규칙` 섹션에 반드시 포함할 내용

```markdown
## 코딩 규칙 (CRITICAL — 반드시 준수)

### 규칙 파일 읽기 (필수)
아래 규칙 파일을 반드시 읽고 모든 내용을 준수하라:
- `D:/dev-base/rules/common.md` — 공통 CSS/HTML 규칙
- `D:/dev-base/rules/{agent}.md` — 에이전트별 규칙 (gemini.md / codex.md)

### CSS 핵심 규칙 (인라인 — 규칙 파일 접근 불가 시 대비)
- 각 셀렉터 규칙은 **한 줄로** 작성 (여러 줄 펼침 금지)
- 같은 셀렉터 중복 선언 금지 — 하나로 합침
- 미디어쿼리: 내부 규칙은 줄바꿈 분리, 들여쓰기 없음
- 색상: hex 전용 (#fff, #090944), 투명도 필요 시만 rgba()
- CSS Grid 금지 — flexbox만 사용
- line-height: 무단위 비율만 (1.3, 1.45) — computed px 금지
- letter-spacing: em 단위 (-0.025em)
- border-radius: 원형 50%, pill 2em — 999px 금지
- 클래스: snake_case, {페이지}_{역할} 패턴
- 모든 요소에 개별 클래스 부여 금지 — 부모+태그 선택자 우선
- 짧은 라벨에 <p> 금지 — <span> 사용

### Figma MCP 값 사용 규칙 (인라인)
- Figma MCP 응답의 노드 속성을 직접 해석하여 CSS 값 결정
- 섹션 단위로 MCP 호출 (전체 페이지 한번에 처리 금지)
- layoutMode/itemSpacing/padding/fills/style 등 Figma 속성 → CSS 변환 규칙 준수
- 구현 후 validate.js로 규칙 검증 필수
```

#### 에이전트별 규칙 파일 매핑

| 에이전트 | 규칙 파일 |
|---------|----------|
| gemini-dev | `D:\dev-base\rules\gemini.md` |
| codex-dev | `D:\dev-base\rules\codex.md` |
| claude-dev | `D:\dev-base\rules\CLAUDE.md` |

---

## 프로젝트 초기화 도구

| 도구 | 경로 | 용도 |
|------|------|------|
| **init-project.py** | `D:\dev-base\tools\init-project.py` | 새 프로젝트 초기화 (CLAUDE.md 복사, settings 생성, .gran-maestro 구조 생성) |

```bash
python3 D:/dev-base/tools/init-project.py "프로젝트경로" --type basic --publishing
```

---

## HTML 페이지 파일명 규칙

> **spec.md 작성 시, 페이지 파일명을 반드시 아래 규칙에 따라 결정한다.**

- **메인 페이지**: `index.html` 고정
- **서브 페이지**: 페이지 내용에 맞는 의미 있는 영문명 (snake_case), flat 배치
- `page_1.html`, `sub_01.html` 같은 의미 없는 파일명 금지
- **파일명 → CSS 프리픽스 연동**: 파일명에서 `.html`을 제거한 값이 해당 페이지의 CSS 클래스 프리픽스
  - `greeting.html` → body class `page_greeting` → CSS 프리픽스 `greeting_`
  - `products.html` → body class `page_products` → CSS 프리픽스 `products_`

---

## Figma 추출 전 필수 실행 (CRITICAL — 생략 시 코드 작성 금지)

> **이 체크리스트를 완료하지 않으면 HTML/CSS Write/Edit를 실행할 수 없다.**

### 1. 규칙 파일 전체 Read (매 추출 작업마다 반드시 실행)
```
Read("D:/dev-base/rules/common.md")   — 전체 (limit 없이)
Read("D:/dev-base/rules/basic.md")    — 전체 (limit 없이)
```
- 100줄만 읽기, "이미 알고 있다" 판단 금지 — 반드시 전체 Read

### 2. figma-extract.py --tree로 visible 노드 확인 (Figma API 직접 호출 금지)
```bash
FIGMA_TOKEN="{token}" python3 D:/dev-base/tools/figma-extract.py \
  --node-id {node-id} --file-key {file-key} --tree --depth 5
```
- curl로 Figma API 직접 호출하지 않음 — 반드시 이 스크립트를 경유
- `--tree` 출력에 나오는 노드만 HTML에 포함 (visible:false 자동 제외됨)
- 출력 결과를 사용자에게 먼저 보여주고 확인 후 코드 작성

### 3. HTML 작성 전 노드 대조 (코드 작성 직전)
- `--tree` 출력의 각 노드를 HTML 요소와 1:1 매핑 목록 작성
- Figma layoutMode/gap/padding/fills 값을 CSS로 변환 (임의 값 사용 금지)
- 매핑에 없는 요소를 HTML에 추가하지 않음

### 4. HTML 작성 후 검증 (코드 작성 직후)
```bash
node D:/dev-base/tools/validate.js --html {output.html} --css css/common.css --type basic
```

---

## 피그마 MCP 기반 워크플로우 (CRITICAL — 필수)

> **Figma MCP(`mcp__figma__get_figma_data`)로 섹션별 데이터를 가져와 AI가 직접 해석한다.**
> 섹션 단위 MCP 호출은 컨텍스트가 작아 AI가 정확하게 해석할 수 있다.

### 핵심 원칙
- **섹션별 MCP 호출**: 전체 페이지를 한번에 처리하지 않고, 섹션(노드) 단위로 MCP 호출
- **AI 직접 해석 허용**: MCP 응답은 섹션 단위이므로 AI가 직접 해석해도 정확도 유지
- **검증은 validate.js**: 구현 완료 후 규칙 준수 여부를 자동 검증

### 도구

| 도구 | 용도 | 실행 시점 |
|------|------|----------|
| **Figma MCP** (`get_figma_data`) | 섹션별 Figma 노드 데이터 조회 | spec 작성 시 / 구현 시 |
| **Figma MCP** (`download_figma_images`) | 이미지/아이콘 다운로드 | 구현 시 |
| **validate.js** | HTML/CSS 규칙 검증 | 구현 완료 후 |
| **figma-extract.py** (선택) | MCP 응답 → mapping.json 생성 (값 대조 검증용) | 정밀 검증 필요 시 |

### Phase 1: 섹션 구조 파악

```
1. Figma MCP로 전체 프레임 조회 (depth 얕게)
   → mcp__figma__get_figma_data(fileKey, nodeId, depth=1)
2. 최상위 자식 노드(섹션) 목록 확인
3. 각 섹션의 nodeId, 이름, 유형 정리
```

### Phase 2: 섹션별 구현 (커서+오푸스 방식)

```
각 섹션마다:
1. Figma MCP로 해당 섹션 데이터 조회
   → mcp__figma__get_figma_data(fileKey, nodeId=섹션ID)
2. AI가 MCP 응답을 직접 해석하여 HTML/CSS 생성
   - layoutMode → flex-direction
   - itemSpacing → gap
   - padding* → padding
   - fills → background/color (hex 변환)
   - style → font-size, font-weight, line-height(비율), letter-spacing(em)
3. 이미지 노드는 Figma MCP로 다운로드
   → mcp__figma__download_figma_images(fileKey, nodes, localPath)
4. 다음 섹션으로 진행
```

### Phase 3: 검증 (필수)

```bash
# HTML/CSS 규칙 검증 (--type 필수)
node D:/dev-base/tools/validate.js --html <output.html> --css <output.css> --type basic|landing
```

### Phase 3+: 정밀 값 대조 검증 (선택)

MCP 응답을 저장하여 mapping.json을 생성하면 값 수준 대조 가능:
```bash
# MCP 응답을 파이프로 전달하여 mapping.json 생성
echo '<mcp_response>' | python3 D:/dev-base/tools/figma-extract.py --stdin --name "<section>" --output ./extracted/ --json-only

# mapping 기반 값 대조
node D:/dev-base/tools/validate.js --html <output.html> --css <output.css> --mapping ./extracted/<section>_mapping.json --type basic|landing
```

### 퍼블리싱 프로젝트 템플릿

퍼블리싱 프로젝트 시작 시 `D:\dev-base\rules\templates\publishing\` 의 config.json/agents.json을 `.gran-maestro/`에 복사:
- `default_agent: "gemini-dev"` (Codex 미사용)
- `figma_mcp.section_by_section: true` (섹션별 MCP 호출)
- `validation.run_after_impl: true` (구현 후 검증 필수)

---

## 피그마 코드 생성 품질 규칙 (CRITICAL — 필수)

> **Figma MCP 데이터를 CSS로 직역하지 않는다. 프로젝트 CSS 규칙에 맞게 변환한다.**

### 코딩 전 필수
1. `D:/dev-base/rules/common.md`의 CSS 규칙을 반드시 읽고 숙지한 후 코딩 시작
2. 기존 프로젝트에 이미 작성된 CSS가 있으면 패턴/변수/포맷을 먼저 확인

### Figma px → CSS 변환 규칙
- **padding/margin/gap**: Figma px값 그대로 사용 ✓
- **width/height**: 고정 px 사용 금지 — flex 비율(flex:1, %) 또는 fill 기반으로 변환
  - 예: Figma `width: 940` + `width: 460` (합계 1440, gap 40) → CSS `flex: 0 0 65.3%` + `flex: 1`
  - 예: Figma `width: 582` + `width: 818` (합계 1440, gap 40) → CSS `width: 40.4%` + `flex: 1`
- **예외**: 카드/아이콘 등 반복 요소의 min-width는 고정 px 허용
- **border-radius**: 원형 50%, pill 2em — Figma의 999px/9999px를 그대로 넣지 않음

### MCP 노드 트리 → HTML 매핑 규칙
- MCP 응답의 **children 순서**를 HTML 요소 순서에 반드시 반영
- MCP에서 같은 부모를 공유하는 요소 그룹은 HTML에서도 **같은 wrapper**로 그룹핑
- MCP 노드가 2개 이상의 자식을 감싸는 frame이면, HTML에서도 wrapper div 사용
- **구조를 짐작하지 않음** — MCP 데이터에 명시된 관계만 사용

### 완료 조건 (하나라도 미충족 시 완료 선언 금지)
1. MCP 노드 트리 순서 = HTML DOM 순서
2. MCP 그룹핑(부모-자식) = HTML wrapper 구조
3. 모든 layoutMode/gap/padding이 CSS에 반영됨
4. 1920px 스크린샷과 Figma 원본 이미지를 섹션별로 실제 비교 완료
5. 비교에서 발견된 차이점이 모두 수정됨

---

### 텍스트 추출 품질
- 피그마 `TEXT` 노드에서 `characterStyleOverrides`가 있으면 오버라이드 구간을 분할해서 굵기/크기/색상 차이를 보존한다
- `styleOverrideTable` 병합은 누적 방식:
  - `baseStyle = { ...node.style, fills: node.fills }`
  - `previousResolvedStyle = null`
  - overrideId `0` 또는 오버라이드 빈값이면 `resolved = baseStyle`
  - 나머지는 `resolved = { ...(previousResolvedStyle ?? baseStyle), ...(override.style ?? {}), ...(override.fills ? { fills: override.fills } : {}) }`
- `fontSize`, `fontWeight`, `fontFamily`, `fills`는 누락값을 이전 오버라이드 구간 값에서 상속하고, `lineHeightPx`/`letterSpacing`은 각각 `line-height`/`letter-spacing`으로 변환한다

---

### 기존 프로젝트 코드 참조 (필수)
- 피그마 변환 시 같은 프로젝트에 이미 변환된 페이지가 있으면:
  1. 기존 CSS 변수, 클래스 패턴, 포맷(한 줄/여러 줄)을 먼저 확인하고 **동일하게 맞춤**
  2. 공통 컴포넌트(header/footer/sub_visual/breadcrumb/page_title)는 기존 코드에서 **그대로 복사**
  3. 메뉴 active/select 상태만 해당 페이지에 맞게 변경
  4. 새 CSS는 기존 common.css **하단에 추가** (기존 코드 수정하지 않음)
- 기존 프로젝트가 없는 경우:
  - `templates/` 폴더의 해당 타입 템플릿을 기본 골격으로 사용
  - 서브페이지는 `templates/sub_list.html`, `templates/sub_view.html` 참조

### 프로젝트 타입별 적용

#### Basic 프로젝트
- 서브페이지 전용 규칙은 `basic.md` 참조
- font-size: PC는 `rem`, 모바일(768px 이하)은 고정 `px`
- 768px 이하: padding/margin은 PC 값의 절반
- JS: 로컬 파일 사용
- reset.css: 별도 파일

#### Landing 프로젝트
- font-size: PC/모바일 모두 고정 `px` (rem 사용 안 함)
- padding/margin: 모두 고정 `px`
- JS: CDN 방식
- reset.css: CSS 최상단에 포함

---

### 텍스트 태그 자동 판정 (필수)
- 기본 태그는 `<span>` 또는 헤딩 계열 (`<h2>`, `<h3>` 등)
- `<p>` 태그는 다음 중 하나 충족 시**만** 사용 — **그 외 모든 텍스트는 `<p>` 금지**:
  - `node.characters`에 `\n` 포함 (또는 `<br>` 포함 서술형)
  - 텍스트 길이 95자 초과
  - 문장형 마침표/종결어 반복
- 라벨성 텍스트(브랜드명, 키워드, CTA, 슬로건, 짧은 설명)는 절대 `<p>` 사용 금지
- 숫자/통계 데이터는 `<span>` 또는 `<strong>` 사용

### CSS 선택자 계층 규칙 (필수)
- **모든 요소에 개별 클래스 부여 금지** — 컨테이너 클래스만 유지하고 내부는 부모+태그 선택자
- 컨테이너 내 유일한 태그 → `.parent h2`, `.parent strong`, `.parent p`
- 같은 태그 복수, 의미 구분 필요 → 최소 클래스 `.parent .en`, `.parent .sub`
- 같은 태그 복수, 순서 구분 가능 → `.parent a:first-child`, `.parent a + a`
- 개별 클래스는 위 방법으로 불가능할 때만 최후 수단으로 사용

---

## 포스트 추출 고도화 플로우 (자동)

피그마 추출 기반 퍼블리싱 작업 완료 후, PM은 자동으로 고도화 분석을 실행한다.

### 트리거
- 피그마 추출 REQ가 Phase 5(done) 완료 시
- 사용자가 `/mst:plan --enhance` 요청 시

### 참조 파일
- 고도화 7-Phase 체크리스트: `D:\dev-base\rules\css-enhancement.md` §7
- Phase 의존성 그래프: `D:\dev-base\rules\css-enhancement.md` §8
- 색상 변수 전환 패턴: `D:\dev-base\rules\css-enhancement.md` §9
- 자동 플로우 정의: `D:\dev-base\rules\enhancement-flow.md`

### 실행 방식
1. PM이 코드베이스 자동 분석 (grep 기반 탐지 — `enhancement-flow.md` §2 패턴)
2. 탐지 결과를 사용자에게 요약 보고 (analysis report)
3. 사용자 승인 시 enhancement PLN → Phase별 REQ 자동 생성
4. Phase 의존성에 따라 순차/병렬 실행 (Phase 2+3 병렬, Phase 5+6 병렬)
5. 완료 후 validate.js로 검증

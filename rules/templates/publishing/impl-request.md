# Implementation Request — Self-Exploration Mode

- Request: {{REQ_ID}} / Task: {{TASK_ID}}
- Worktree: {{WORKTREE_PATH}}
- Spec: {{SPEC_PATH}}

## 구현 컨텍스트 (PM 작성 — 3~5줄 자유 형식)

{{IMPL_CONTEXT}}

## 자기탐색 지시

아래 순서로 스펙을 직접 탐색하라. PM이 제공한 요약에 의존하지 말고 원본 파일을 직접 읽어라.

1. 스펙 직접 읽기: `cat {{SPEC_PATH}}` (또는 Read 도구)
2. §2 변경 범위의 파일 목록 파악
3. §3 수락 조건을 기준으로 구현
4. §5 테스트 명령어로 검증 후 종료 (커밋은 PM이 처리)

## 이전 피드백 (Phase 4 → 재실행 시)

{{PREV_FEEDBACK_PATH}}

(첫 실행 시: N/A — 이 섹션을 무시하라)

## 규칙

- spec §2의 변경 범위 외 파일 수정 금지
- 추가 기능, 리팩토링, 스타일 변경 금지
- git commit은 하지 마세요 — PM이 직접 커밋합니다
- 완료 전 모든 수락 조건을 self-check할 것

## 코딩 규칙 (CRITICAL — 반드시 준수)

### 규칙 파일 읽기 (필수)
아래 규칙 파일을 반드시 읽고 모든 내용을 준수하라:
- `D:/dev-base/rules/common.md` — 공통 CSS/HTML 규칙
- `D:/dev-base/rules/gemini.md` — 퍼블리싱 에이전트 전용 규칙

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
- 짧은 라벨에 `<p>` 금지 — `<span>` 사용
- `<main>`, `<article>`, `<figure>`, `<figcaption>` 사용 금지

### Figma 값 사용 규칙 (인라인)
- CSS 값은 spec.md 테이블의 추출값만 사용
- 테이블에 없으면 "미추출" 플래그, 추측값 금지
- Figma JSON 직접 해석 금지
- "그럴듯한" 기본값 임의 입력 절대 금지

## 레이아웃 규칙 (CRITICAL — 사용자 반복 지적, 절대 금지 사항)

### Section 좌우 padding 절대 금지
- `<section>` 요소에 `padding-left`/`padding-right` 부여 **절대 금지**
- 컨텐츠 좌우 여백은 내부 wrapper의 `max-width` + `margin: 0 auto` 패턴으로만 처리
- 예시:
  ```css
  .section_name { padding: 100px 0; }
  .section_name_inner { max-width: 1280px; margin: 0 auto; }
  ```
  ```html
  <section class="section_name">
    <div class="section_name_inner">...</div>
  </section>
  ```
- 이 규칙을 어기면 PM이 자동 재dispatch하므로, 처음부터 inner wrapper 패턴으로 작성하라

## Spec 파일 경로 규칙 (sandbox 우회)

- 외주 brief에 명시되는 spec.md/json 경로는 반드시 **프로젝트 내부 경로**여야 함 (예: `extracted/section_05_spec.md`)
- gemini-dev sandbox는 workspace 외부 경로(`/mnt/d/dev-base/.gran-maestro/tmp/...`) Read를 거부
- PM은 dispatch 전 spec 파일을 프로젝트 내부(`{project_root}/extracted/`)로 복사한 뒤 절대경로로 명시
- worktree 외부 절대경로를 brief에 직접 박지 않음

## figma-validate.py 9개 검증 카테고리 (구현 후 통과 필수)

| # | 카테고리 | spec 필드 | 설명 |
|---|----------|-----------|------|
| 1 | 텍스트 위변조 | `text_nodes[].characters` | spec text가 HTML에 존재해야 함 |
| 2 | 줄바꿈 보존 | `\n`/`\u2028`/`\xa0` | `<br>`/`&nbsp;` 보존 |
| 3 | 폰트 5필드 완결성 | `fontFamily`/`fontSize`/`fontWeight`/`lineHeightPx`/`color` | 매칭 셀렉터에 5개 모두 선언 |
| 4 | lineHeight 비율 일치 | `lineHeightRatio` | CSS 무단위 비율 ±0.05 |
| 5 | fills color hex 일치 | `color`/`fills[].color` | hex 대소문자 무시 |
| 6 | frame padding/gap 반영 | `paddingTop/Right/Bottom/Left`/`itemSpacing` | CSS padding/gap 반영 |
| 7 | clamp 적용 | padding/gap ≥100 | `clamp()` 사용 필수 |
| 8 | column flex gap 금지 | `layoutMode == "VERTICAL"` | gap 미사용 |
| 9 | interaction URL 일치 | `interactions[].url` | `<a href="..." target="_blank">` |

구현 완료 후 반드시 아래 두 검증을 모두 통과해야 commit 허용:
```bash
python3 D:/dev-base/tools/figma-validate.py --spec extracted/{section}_spec.json --html output.html --css output.css
python3 D:/dev-base/tools/validate-semantic.py --html output.html --css output.css --profile {basic|landing|all}
```

## characterStyleOverrides 처리 (REQ-012 신설 필드)

- spec.json TEXT 노드의 `character_segments[]` 필드를 반드시 확인
- 단일 segment (오버라이드 없음): 일반 텍스트 그대로 사용
- 복수 segment (캐릭터 단위 오버라이드): 해당 구간만 별도 `<em>` 또는 `<strong>` 태그로 분리하여 색상/굵기 차이 보존
- 예시:
  ```json
  "character_segments": [
    {"start": 0, "end": 3, "text": "오직 ", "color": "#312d2b"},
    {"start": 3, "end": 5, "text": "남성", "color": "#916046"},
    {"start": 5, "end": 10, "text": "만을 위한", "color": "#312d2b"}
  ]
  ```
  → `오직 <em class="strong_color">남성</em>만을 위한`
- 오버라이드 색상은 별도 클래스로 정의하고 인라인 style 사용 금지

## cornerRadius 처리 (REQ-012 신설 필드)

- spec.json FRAME 노드의 `border_radius_hint` 필드를 반드시 확인
- `border_radius_hint == "50%"`: `border-radius: 50%` 적용 (원형 요소, 아이콘 백그라운드 등)
- `border_radius_hint`가 없고 `cornerRadius`만 있을 때:
  - 100px 미만 → `border-radius: {cornerRadius}px`
  - 100px 이상 (특히 999px/9999px) → `border-radius: 2em` (pill 형태)
- Figma의 999px/9999px를 그대로 CSS에 박지 않음 — 항상 `50%` 또는 `2em`으로 변환

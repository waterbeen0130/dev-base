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

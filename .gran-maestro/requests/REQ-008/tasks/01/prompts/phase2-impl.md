# Task: REQ-008 / 01 — tools/figma-validate.py 사후 검증 도구 구현

## Paths
- SPEC_PATH: /mnt/d/dev-base/.gran-maestro/requests/REQ-008/tasks/01/spec.md
- PLAN_PATH: /mnt/d/dev-base/.gran-maestro/plans/PLN-004/plan.md
- WORKTREE_PATH: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-008-01
- PREV_FEEDBACK_PATH: N/A
- REQ_ID: REQ-008
- TASK_ID: 01

## 작업 지시

1. **먼저 반드시 Read**:
   - `SPEC_PATH` (이 태스크의 단일 진실 — 9개 검증 항목 전체와 AC 포함)
   - `PLAN_PATH` (PLN-004 — §1 누락 12종 사례와 §3 도구 책임 분담)
   - 참고용 기존 스크립트: `tools/figma-section-spec.py` (spec.json 스키마 원천), `tools/validate-semantic.py` (CSS 파싱 패턴)

2. **신규 파일 1개만 생성**: `tools/figma-validate.py`
   - Python 3.10+, 외부 의존성 **절대 금지** (표준 라이브러리만: `argparse`, `json`, `re`, `sys`, `pathlib` 등)
   - 기존 `tools/figma-section-spec.py`의 CLI 스타일(argparse, `fail()` 헬퍼, stderr 에러) 그대로 따름

3. **CLI 인터페이스**:
   ```
   python3 tools/figma-validate.py --spec <section_spec.json> --html <output.html> --css <output.css>
   ```
   - exit 0: 위반 0건 (PASS)
   - exit 1: 위반 1건 이상 (FAIL) 또는 누락된 spec 행 존재

4. **9개 검증 항목 (spec.md §3 AC-002 전체)**:
   1. 텍스트 위변조: 각 `text_nodes[].characters`가 HTML 텍스트에 존재 (공백/개행 정규화 후 부분 일치)
   2. 줄바꿈 보존: `\n`→`<br>`/줄바꿈, `\u2028`→`<br>`, `\xa0`→`&nbsp;` 또는 non-breaking space
   3. 폰트 5필드 완결성: text_node와 매칭되는 CSS 셀렉터에 `font-family`/`font-size`/`font-weight`/`line-height`/`color` 모두 선언
   4. lineHeight 비율 일치: CSS `line-height` 값 vs spec `lineHeightRatio` (무단위, 오차 ±0.05)
   5. fills color hex 일치 (대소문자 무시)
   6. frame padding/gap 반영: `frame_nodes[].paddingTop/Right/Bottom/Left`, `itemSpacing` → CSS에 반영
   7. clamp 적용: padding/gap ≥100 시 `clamp()` 사용
   8. column flex gap 금지: `layoutMode=="VERTICAL"` frame의 CSS는 `gap` 미사용
   9. interaction URL 일치: `interactions[].url` → HTML의 `<a href="{url}" target="_blank">`

5. **출력 형식**:
   - stdout에 "카테고리 | 노드 | 기대값 | 실제값" 형식의 위반 표
   - 말미에 "누락된 spec 행" 섹션 (text_nodes 중 HTML에 1회도 등장하지 않은 노드 목록: id + characters)
   - stderr은 실행 에러(파일 없음/JSON 파싱 실패 등)에만 사용

6. **spec.json 스키마** (figma-section-spec.py의 normalize_* 함수 출력):
   ```json
   {
     "section": {"id","name","bbox"},
     "text_nodes": [{"id","name","characters","fontFamily","fontSize","fontWeight","lineHeightPx","lineHeightRatio","letterSpacing","color","textAlignHorizontal","textAlignVertical"}],
     "frame_nodes": [{"id","name","bbox","layoutMode","paddingTop","paddingRight","paddingBottom","paddingLeft","itemSpacing","primaryAxisAlignItems","counterAxisAlignItems","fills"}],
     "interactions": [{"node_id","url","openInNewTab"}],
     "image_refs": [...]
   }
   ```

7. **매칭 전략**: HTML 텍스트 내용으로 text_node를 역매핑하여 해당 요소의 CSS 셀렉터를 찾는 것이 가장 안정적. 클래스명은 규칙에 따라 바뀔 수 있음.

8. **CSS 파싱**:
   - `tools/validate-semantic.py`의 정규식 기반 접근 참조
   - shorthand(`padding: 20px 40px`)와 longhand(`padding-top: 20px`) 모두 지원
   - 미디어 쿼리 내부 규칙도 파싱 (가능하면)

9. **작업 완료 조건**:
   - `tools/figma-validate.py` 파일 생성
   - `python3 -m py_compile tools/figma-validate.py` → exit 0
   - `python3 tools/figma-validate.py --help` → 사용법 출력, exit 0
   - 기존 `tools/validate-semantic.py --help` 은 변경 없이 동일하게 동작

## 금지 사항
- 외부 패키지 설치 (`pip install ...`) 금지 — 표준 라이브러리만
- `tools/figma-section-spec.py`, `tools/validate-semantic.py` 수정 금지 (spec §2 제외)
- `tools/figma-validate.py` 외 다른 파일 수정 금지
- git 커밋 금지 (PM이 사전검증 후 직접 커밋)

## 완료 후
작업 완료를 알리고, 구현 요약(검증 알고리즘, 함수 분할, 주요 엣지케이스 처리)을 3~6줄로 보고할 것.

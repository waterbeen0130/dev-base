# Implementation Spec

- Request ID: REQ-007
- Task ID: 01
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: Python tooling / Figma API + JSON 정규화] → 최종: codex-dev
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-007-T01
- Complexity: Standard

## §0 Context Manifest

- /mnt/d/dev-base/.gran-maestro/plans/PLN-004/plan.md (전체 계획)
- /mnt/d/dev-base/tools/figma-extract.py (기존 도구 — `--emit-mapping` 호환 유지 + 일부 로직 재사용 가능)
- /mnt/d/dev-base/tools/validate-semantic.py (CSS 파싱 패턴 참고용)
- /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/index.html (Section_02 reference, 누락 12종 패턴 대조용)
- /mnt/c/Users/water/Downloads/260410_모제림_비절개랜딩/html/css/common.css (Section_02 정정 결과 reference)

## 1. 요약 (Summary)

`tools/figma-section-spec.py` 신규 작성. Figma node-id 받아서 모든 TEXT/FRAME/interaction 데이터를 **누락 없이** 정규화하여 `extracted/{section}_spec.md` (사람용) + `extracted/{section}_spec.json` (도구용) 두 형식으로 출력. AI는 이 spec sheet만 보고 코드 작성하므로 raw API 직접 해석 불가.

## 2. 범위 (Scope)

- **포함**:
  - `tools/figma-section-spec.py` 신규 파일 (Python 3.10+, urllib + json + argparse만 사용 — 외부 의존성 0)
  - CLI: `--file-key K --node-id N` (필수), `--output extracted/` (기본), `--name <prefix>` (선택, 미지정 시 node-id 기반)
  - Figma REST API 호출 (`/v1/files/:key/nodes?ids=N&depth=8`)
  - 노드 트리 walk + 정규화
  - 출력 1: `{output}/{name}_spec.md` (Markdown)
  - 출력 2: `{output}/{name}_spec.json` (JSON)
  - imageRef 매핑: 별도 호출 `/v1/files/:key/images`로 다운로드 URL 매핑 후 spec에 포함
- **제외**:
  - `tools/figma-extract.py` 재작성 (그대로 유지)
  - 자동 이미지 다운로드 (URL만 spec에 기록, 다운로드는 사용자/AI 책임)
  - figma-validate.py 작성 (REQ-008 범위)
  - HTML/CSS 자동 생성 (AI 책임)
- **시작점 힌트**:
  - `tools/figma-extract.py:1-50` (argparse 패턴, FIGMA_TOKEN env var 사용)
  - `tools/figma-extract.py:704-781` (mapping 추출 로직 — 참고용)
  - 본 세션에서 사용한 임시 walk 패턴 (`/tmp/figma_sec02_deep.json` 처리)

## 3. 수락 조건 (Acceptance Criteria)

#### AC-001 [MUST] [automatable] [tdd-required]
Given: Figma node-id가 주어짐 (예: `842:37` for Section_02)
When: `FIGMA_TOKEN=... python3 tools/figma-section-spec.py --file-key T8xEPS7sR5MZCUQ9JVa4hH --node-id 842:37 --output /tmp/test_spec/` 실행
Then: `/tmp/test_spec/section_842_37_spec.md`와 `.json` 두 파일이 생성됨, exit 0
Test:
```
FIGMA_TOKEN=figd_[REDACTED] python3 tools/figma-section-spec.py --file-key T8xEPS7sR5MZCUQ9JVa4hH --node-id 842:37 --output /tmp/test_spec/ && test -f /tmp/test_spec/section_842_37_spec.md && test -f /tmp/test_spec/section_842_37_spec.json
```

#### AC-002 [MUST] [automatable] [tdd-required]
Given: 생성된 spec.json
When: 모든 TEXT 노드 항목을 점검
Then: 각 TEXT 노드는 다음 7개 필드를 모두 포함 — `id`, `name`, `characters`, `fontFamily`, `fontSize`, `fontWeight`, `lineHeightPx`, `lineHeightRatio`, `letterSpacing`, `color`, `textAlignHorizontal`, `textAlignVertical` (12개로 확장)
Test:
```python
import json
d = json.load(open('/tmp/test_spec/section_842_37_spec.json'))
required = {'id','name','characters','fontFamily','fontSize','fontWeight','lineHeightPx','lineHeightRatio','letterSpacing','color','textAlignHorizontal','textAlignVertical'}
for t in d['text_nodes']:
    missing = required - set(t.keys())
    assert not missing, f'{t.get("id")}: missing {missing}'
print('AC-002 PASS')
```

#### AC-003 [MUST] [automatable] [tdd-required]
Given: 생성된 spec.json의 FRAME 노드 항목
When: 점검
Then: 각 FRAME은 `id`, `name`, `bbox` (x/y/w/h), `layoutMode`, `paddingTop/Right/Bottom/Left`, `itemSpacing`, `primaryAxisAlignItems`, `counterAxisAlignItems`, `fills` 필드를 모두 포함 (값이 없으면 `null`/`0`)
Test:
```python
import json
d = json.load(open('/tmp/test_spec/section_842_37_spec.json'))
required = {'id','name','bbox','layoutMode','paddingTop','paddingRight','paddingBottom','paddingLeft','itemSpacing','primaryAxisAlignItems','counterAxisAlignItems','fills'}
for f in d['frame_nodes']:
    missing = required - set(f.keys())
    assert not missing, f'{f.get("id")}: missing {missing}'
print('AC-003 PASS')
```

#### AC-004 [MUST] [automatable] [tdd-required]
Given: spec.json의 interactions 섹션
When: Figma node에 `interactions[].actions[].type=URL`인 항목이 있으면
Then: spec.json에 `interactions: [{ node_id, url, openInNewTab }]` 형식으로 추출 (Section_02 CTA 842:62 → `cafe.naver.com/mojelims` 검증)
Test:
```python
import json
d = json.load(open('/tmp/test_spec/section_842_37_spec.json'))
urls = [i['url'] for i in d.get('interactions', [])]
assert any('cafe.naver.com/mojelims' in u for u in urls), 'Section_02 CTA URL missing'
print('AC-004 PASS')
```

#### AC-005 [MUST] [manual] [tdd-required]
Given: 생성된 spec.md
When: 사람이 처음부터 끝까지 읽음
Then: Section_02 reference에서 발견된 12종 누락 사례(font-family, line-height, color, characters, gap 67, panel head font, frame 535 컨텐츠, padding 정의 부재, padding 192/223 등)가 모두 spec.md에 명시되어 있음
Test: 수동 — spec.md에서 12종 항목 grep 후 결과를 응답에 포함

## 3.5 Constraints

- 보안: FIGMA_TOKEN은 환경변수로만 전달 (CLI 인자/로그 평문 금지)
- 성능: 단일 섹션 처리 < 5초 (Figma API 1~2회 + JSON 처리)
- 호환성: Python 3.10+, 외부 패키지 추가 금지 (urllib + json + argparse)
- 운영: API 실패 시 명확한 에러 메시지 + non-zero exit

## 4. 구현 컨텍스트 (Context)

- **따라야 할 패턴**: `tools/figma-extract.py` 한국어 docstring + argparse 구조
- **알아야 할 제약**: REQ-008(figma-validate.py)이 spec.json을 입력으로 사용하므로 **JSON 스키마 안정성 필수**. 첫 빌드 시 schema_version: 1 부여.
- **접근법 방향**: ① CLI 파싱 → ② Figma `/nodes` 호출 → ③ 트리 walk로 TEXT/FRAME/interaction 분리 수집 → ④ imageRef 발견 시 `/images` 호출로 URL 매핑 → ⑤ spec.json + spec.md 동시 출력 → ⑥ atomic write

### spec.json 스키마 예시
```json
{
  "schema_version": 1,
  "section": { "id": "842:37", "name": "Section_02", "bbox": {...} },
  "text_nodes": [
    {
      "id": "842:41",
      "name": "풍성한 볼륨을 가르는 건",
      "characters": "풍성한 볼륨을 가르는 건",
      "fontFamily": "Noto Serif KR",
      "fontSize": 45,
      "fontWeight": 500,
      "lineHeightPx": 65.25,
      "lineHeightRatio": 1.45,
      "letterSpacing": -0.9,
      "color": "#312d2b",
      "textAlignHorizontal": "CENTER",
      "textAlignVertical": "CENTER"
    }
  ],
  "frame_nodes": [
    {
      "id": "842:39",
      "name": "Frame 523",
      "bbox": {"x":0,"y":0,"w":514,"h":692},
      "layoutMode": "VERTICAL",
      "paddingTop": 0,
      "paddingRight": 0,
      "paddingBottom": 0,
      "paddingLeft": 0,
      "itemSpacing": 67,
      "primaryAxisAlignItems": "MIN",
      "counterAxisAlignItems": "MIN",
      "fills": null
    }
  ],
  "interactions": [
    { "node_id": "842:62", "url": "https://cafe.naver.com/mojelims", "openInNewTab": true }
  ],
  "images": {
    "f1351fa9c9ca": "https://s3-alpha-sig.figma.com/img/...",
    "3c4d7f67f4a8": "https://s3-alpha-sig.figma.com/img/..."
  }
}
```

### spec.md 형식 예시
```markdown
# Section_02 Spec Sheet

> AUTO-GENERATED FROM Figma node 842:37 — DO NOT EDIT MANUALLY
> 이 spec의 모든 행을 빠짐없이 CSS로 표현하세요. 누락 시 figma-validate.py에서 차단됩니다.

## TEXT 노드 (필수 12개 필드)

| id | name | characters | font | size/weight | lh / lhRatio | ls | color | align |
|---|---|---|---|---|---|---|---|---|
| 842:41 | 풍성한 볼륨 | "풍성한 볼륨을 가르는 건" | Noto Serif KR | 45/500 | 65.25/1.45 | -0.9 | #312d2b | CENTER/CENTER |
...

## FRAME 노드

| id | name | bbox | layoutMode | padding | itemSpacing | align | fills |
|---|---|---|---|---|---|---|---|
| 842:39 | Frame 523 (left col) | 514x692 | VERTICAL | 0/0/0/0 | **67** | MIN/MIN | null |
...

## interactions

| node_id | url | openInNewTab |
|---|---|---|
| 842:62 | https://cafe.naver.com/mojelims | true |

## images (imageRef → 다운로드 URL)

| imageRef | url |
|---|---|
| f1351fa9c9ca | https://s3-alpha-sig.figma.com/img/... |
```

## 5. 의존성 (Dependencies)

- 선행 작업 (blockedBy): []
- 후행 작업 (blocks): ["02"]

## 6. 에이전트 팀 구성

- 실행: codex-dev
- 사유: Python 신규 도구 작성 + Figma REST API 처리 + JSON 정규화는 codex capabilities(code, refactor, test)에 부합

## 10. 가정 사항

- (가정 1) Figma `/v1/files/{key}/nodes` API 응답 구조는 안정적이며 `style`, `fills`, `absoluteBoundingBox`, `layoutMode`, `paddingTop` 등 필드명 변경 없음
- (가정 2) `interactions` 필드가 노드에 직접 부여된 prototype mode에서만 동작 (component variant transition은 무시)
- (가정 3) lineHeightRatio = `lineHeightPx / fontSize` (소수점 3자리 반올림)
- (가정 4) color는 fills[0]가 SOLID이고 visible일 때만 hex 추출. IMAGE/GRADIENT는 별도 처리 (image는 imageRef를 fills 필드에 기록)
- (가정 5) bbox는 absoluteBoundingBox 기준이며 부모 상대 좌표가 아님 (정규화 필요 시 사용자 책임)

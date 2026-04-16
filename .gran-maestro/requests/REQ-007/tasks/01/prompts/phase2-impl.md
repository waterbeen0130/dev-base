# Implementation Request — Self-Exploration Mode

- Request: REQ-007 / Task: 01
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-007-T01
- Spec: /mnt/d/dev-base/.gran-maestro/requests/REQ-007/tasks/01/spec.md
- Plan: /mnt/d/dev-base/.gran-maestro/plans/PLN-004/plan.md

## 구현 컨텍스트

`tools/figma-section-spec.py`라는 신규 Python 도구를 작성한다. Figma node-id를 받아서 해당 섹션의 모든 TEXT/FRAME/interaction 데이터를 누락 없이 정규화하여 두 형식(spec.md, spec.json)으로 출력한다. 이 도구의 목적은 AI가 raw Figma JSON을 직접 해석하다가 font-family/line-height/color/줄바꿈/자식 frame 등을 반복적으로 누락하는 문제를 구조적으로 차단하는 것.

핵심 주의사항:
1. **신규 파일 1개**: `tools/figma-section-spec.py` (Python 3.10+, 외부 의존성 0 — urllib/json/argparse만)
2. **2가지 출력**: `{output}/{name}_spec.md` (사람용) + `{name}_spec.json` (도구용, REQ-008 figma-validate.py가 사용)
3. **JSON 스키마 안정성 필수** — schema_version: 1, REQ-008이 의존
4. CLI: `--file-key K --node-id N --output extracted/ [--name <prefix>]`
5. FIGMA_TOKEN 환경변수만 사용
6. 작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-007-T01`

## 자기탐색 지시

0. spec `## §0 Context Manifest` 모두 Read (특히 spec.md의 `### spec.json 스키마 예시` 섹션과 `### spec.md 형식 예시` 섹션 → 출력 형식 그대로 따름)
1. spec 직접 읽기: `/mnt/d/dev-base/.gran-maestro/requests/REQ-007/tasks/01/spec.md`
2. plan 읽기: `/mnt/d/dev-base/.gran-maestro/plans/PLN-004/plan.md` (12개 누락 사례 + 9개 검증 항목 — 도구가 이를 모두 spec sheet에 노출해야 함)
3. 워크트리의 `tools/figma-extract.py` Read해서 코드 스타일/argparse 패턴 파악 (재사용 안 함, 참고만)
4. 워크트리의 `tools/validate-semantic.py` Read해서 dataclass 스타일 참고 (선택)
5. `tools/figma-section-spec.py` 신규 작성:
   - argparse: `--file-key`, `--node-id`, `--output`, `--name` (옵션)
   - FIGMA_TOKEN 환경변수 검증 (없으면 명확한 에러 + exit 1)
   - Figma REST API 호출 (`/v1/files/{key}/nodes?ids={N}&depth=8`) — urllib.request만
   - 응답 walk:
     - TEXT 노드 수집: id, name, characters (raw, `\n`/`\u2028`/`\xa0` 보존), fontFamily, fontSize, fontWeight, lineHeightPx, lineHeightRatio (round 3), letterSpacing, color (fills SOLID 첫 번째), textAlignHorizontal, textAlignVertical
     - FRAME 노드 수집: id, name, bbox (x/y/w/h), layoutMode, paddingTop/Right/Bottom/Left, itemSpacing, primaryAxisAlignItems, counterAxisAlignItems, fills (SOLID hex 또는 IMAGE imageRef 또는 null)
     - interactions 수집: 각 노드의 `interactions[].actions[]` 중 type=URL인 것 → `{node_id, url(strip), openInNewTab}`
   - imageRef 발견 시 별도 호출 `/v1/files/{key}/images` → URL 매핑 dict로 보관
   - spec.json 출력 (atomic write: tempfile + os.replace):
     ```json
     {
       "schema_version": 1,
       "section": {"id":"842:37","name":"Section_02","bbox":{...}},
       "text_nodes": [...],
       "frame_nodes": [...],
       "interactions": [...],
       "images": {imageRef: url}
     }
     ```
   - spec.md 출력: 사람이 읽기 좋은 markdown 표 (TEXT 12 필드, FRAME 11 필드, interactions 표, images 표)
   - 상단 헤더: `> AUTO-GENERATED FROM Figma node {id} — DO NOT EDIT MANUALLY` + `이 spec의 모든 행을 빠짐없이 CSS로 표현하세요`
6. 검증:
   ```bash
   cd /mnt/d/dev-base/.gran-maestro/worktrees/REQ-007-T01
   python3 -m py_compile tools/figma-section-spec.py
   FIGMA_TOKEN=figd_[REDACTED] \
     python3 tools/figma-section-spec.py \
     --file-key T8xEPS7sR5MZCUQ9JVa4hH \
     --node-id 842:37 \
     --output /tmp/test_spec/
   test -f /tmp/test_spec/section_842_37_spec.md
   test -f /tmp/test_spec/section_842_37_spec.json
   python3 -c "
   import json
   d = json.load(open('/tmp/test_spec/section_842_37_spec.json'))
   assert d.get('schema_version') == 1
   assert all(k in d for k in ('section','text_nodes','frame_nodes','interactions','images'))
   required_text = {'id','name','characters','fontFamily','fontSize','fontWeight','lineHeightPx','lineHeightRatio','letterSpacing','color','textAlignHorizontal','textAlignVertical'}
   for t in d['text_nodes']:
       missing = required_text - set(t.keys())
       assert not missing, f'{t.get(\"id\")}: missing {missing}'
   required_frame = {'id','name','bbox','layoutMode','paddingTop','paddingRight','paddingBottom','paddingLeft','itemSpacing','primaryAxisAlignItems','counterAxisAlignItems','fills'}
   for f in d['frame_nodes']:
       missing = required_frame - set(f.keys())
       assert not missing, f'{f.get(\"id\")}: missing {missing}'
   urls = [i.get('url','') for i in d.get('interactions', [])]
   assert any('cafe.naver.com/mojelims' in u for u in urls), 'Section_02 CTA URL missing'
   print('all assertions PASS')
   print(f'text nodes: {len(d[\"text_nodes\"])}, frame nodes: {len(d[\"frame_nodes\"])}, interactions: {len(d[\"interactions\"])}, images: {len(d[\"images\"])}')
   "
   ```

작업 디렉토리: `/mnt/d/dev-base/.gran-maestro/worktrees/REQ-007-T01`

## 규칙

- 새 파일 1개: `tools/figma-section-spec.py`
- 외부 의존성 추가 금지 (Python stdlib만 — urllib, json, argparse, os, sys, dataclasses)
- FIGMA_TOKEN은 환경변수만, 코드/로그에 평문 금지
- atomic write (tempfile + os.replace)
- 멱등: 같은 입력 → 같은 출력
- git commit은 하지 마세요 — PM이 직접 커밋
- [MANDATORY] 위 검증 6번 명령 출력 전체를 응답에 포함

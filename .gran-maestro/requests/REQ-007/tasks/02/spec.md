# Implementation Spec — Test Task

- Request ID: REQ-007
- Task ID: 02
- Created: 2026-04-12
- Status: pending
- Assigned Agent: [config: codex-dev] → [도메인: 회귀 검증 / Section_02 reference 대조] → 최종: claude-dev
- Worktree: /mnt/d/dev-base/.gran-maestro/worktrees/REQ-007-T02
- Complexity: Lite

## §0 Context Manifest

- /mnt/d/dev-base/.gran-maestro/requests/REQ-007/tasks/01/spec.md
- /mnt/d/dev-base/tools/figma-section-spec.py (T01 산출물)
- /mnt/d/dev-base/.gran-maestro/plans/PLN-004/plan.md (12개 누락 사례 목록)

## 1. 요약 (Summary)

REQ-007 T01에서 만든 `figma-section-spec.py`를 모제림 Section_02 (node 842:37)에 실행하여, **이번 세션에서 사용자가 일일이 지적한 12개 누락 사례가 모두 spec sheet에 등장하는지** 회귀 검증한다.

## 2. 테스트 범위

- **통합 검증**: figma-section-spec.py 실제 실행 → spec.md/json 생성 → 12개 누락 항목 grep 검증
- **사람 검수**: 자동 검증으로 잡히지 않는 의미적 누락 (예: characters 줄바꿈 보존)

## 3. 수락 조건 (통합 AC)

#### AC-001 [MUST] [automatable]
Given: T01 완료 + figma-section-spec.py 동작
When: Section_02 node에 실행
Then: spec.md + spec.json 생성, 12개 누락 사례 모두 spec sheet에 등장
Test:
```bash
FIGMA_TOKEN=figd_[REDACTED] \
  python3 /mnt/d/dev-base/tools/figma-section-spec.py \
  --file-key T8xEPS7sR5MZCUQ9JVa4hH \
  --node-id 842:37 \
  --output /tmp/sec02_test/

# 12개 누락 사례 grep
cd /tmp/sec02_test/
echo "1. Noto Serif KR (Lead font-family)"; grep -c "Noto Serif KR" section_842_37_spec.md
echo "2. Noto Sans KR (CTA font-family)"; grep -c "Noto Sans KR" section_842_37_spec.md
echo "3. line-height ratio (lhRatio)"; grep -c "lhRatio\|lineHeightRatio" section_842_37_spec.md
echo "4. #916046 (panel_head color)"; grep -c "916046" section_842_37_spec.md
echo "5. #5a5048 (panel_body color)"; grep -c "5a5048" section_842_37_spec.md
echo "6. 1,000모 (tab text actual)"; grep -c "1,000모" section_842_37_spec.md
echo "7. 30대 (badge text actual)"; grep -c "30대" section_842_37_spec.md
echo "8. \\\\n line break preserved"; grep -c '\\\\n' section_842_37_spec.json
echo "9. itemSpacing 67 (Frame 523)"; grep -c '67' section_842_37_spec.md
echo "10. Frame 535 (panel container)"; grep -c "Frame 535" section_842_37_spec.md
echo "11. paddingTop 192 / paddingBottom 223"; grep -c "192\|223" section_842_37_spec.md
echo "12. cafe.naver.com/mojelims (interactions URL)"; grep -c "cafe.naver.com" section_842_37_spec.md
```
모든 카운트 ≥ 1이면 PASS

#### AC-002 [MUST] [manual]
Given: 생성된 spec.md 전체
When: 사람이 한 번 통독
Then: 의미적으로 빠진 정보 0건 (예: textAlignVertical 값, fills의 IMAGE 타입 indicator, primaryAxisAlignItems CENTER 등)
Test: 수동 — 통독 후 결과를 spec §11에 기록

#### AC-003 [SHOULD] [automatable]
Given: spec.json 구조
When: schema_version 필드 확인
Then: schema_version=1 + text_nodes/frame_nodes/interactions/images 4개 최상위 키 존재
Test:
```python
import json
d = json.load(open('/tmp/sec02_test/section_842_37_spec.json'))
assert d.get('schema_version') == 1
assert all(k in d for k in ('section','text_nodes','frame_nodes','interactions','images'))
print('AC-003 PASS')
```

## 4. 회귀 테스트 항목

- **R1**: 12개 누락 사례 grep 모두 ≥ 1 (AC-001)
- **R2**: spec.json 구조 안정성 (AC-003) — REQ-008이 이 스키마를 의존
- **R3**: 사람 검수에서 의미적 누락 0건 (AC-002)

## 5. 의존성

- 선행 작업 (blockedBy): ["01"]
- 후행 작업 (blocks): []

## 6. 에이전트 팀 구성

- 실행: claude-dev
- 사유: 자동 grep + 사람 검수 혼합. PM 직접 처리가 효율적이며, AC-001의 12개 항목 의미 판단이 필요.

## 10. 가정 사항

- (가정 1) Section_02 reference (node 842:37)는 모제림 file에 그대로 존재 (변경 없음)
- (가정 2) AC-001의 grep 12개가 모두 PASS면 도구의 핵심 기능 검증 완료로 간주
- (가정 3) AC-002 사람 검수에서 누락 발견 시 T01 spec.md 보정 후 T01 재외주

[MST skill=ideation step=2/4 return_to=null]

# Critic 평가 요청 — IDN-002

## 대기 지시
다음 명령을 실행하고 결과를 기다리세요:

```
python3 /home/waterbeen/.claude/plugins/cache/gran-maestro/mst/0.56.1/scripts/mst.py wait-files \
  "/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-architect(codex).md" \
  "/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-figma-fidelity(codex).md" \
  "/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-quality(codex).md" \
  "/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-schema(gemini).md" \
  "/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/opinion-risk(claude).md"
```

마지막 줄이 ALL_READY면 다음 단계 수행. TIMEOUT이면 완료된 파일들만으로 진행.

## 공유 컨텍스트
/mnt/d/dev-base/.gran-maestro/ideation/IDN-002/context.md 를 먼저 Read.

## 당신의 역할
비판적 시각에서 5개 의견(architect, figma-fidelity, quality, schema, risk)의 **허점·반론·엣지 케이스**를 식별.

## 질문
1. 각 의견에서 **근거가 약하거나 추측에 기반한 주장**을 지목 (파일명:주장 내용 형태).
2. 5개 의견 간 **상호 모순 또는 충돌하는 권고**를 찾아 대립 구조 서술.
3. 제안들 중 **실행 비용 대비 효용이 낮은 제안** (over-engineering 의심)을 평가.
4. 참여자 전원이 놓친 **중요한 관점** 있는가? (예: 성능, 빌드 시간, 캐시, CI, 사용자(디자이너) 피드백 루프, 로컬 폰트 렌더링 차이)
5. "완전 동일한 추출물"이라는 목표 자체가 **잘못 설정된 목표**인 가능성(예: 픽셀 완전성 vs 의미론적 동일성)에 대한 평가.

## 출력 요구사항
- 파일로 저장: /mnt/d/dev-base/.gran-maestro/ideation/IDN-002/critique-claude-critic.md
- 2000자 이내, 한국어
- 각 비평에 "대상 의견 파일명" 명시
- 마지막에 "## 합성 전 PM이 반드시 되짚어야 할 반론 Top 3"
<!-- source-mapping: original=Q&A 대화 sections=[DOD-004, AD-002, R1] -->
# AI 외주 자동 선정 로직

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-004

## 개요

PNG 시각 분석 + 정량 지표를 입력으로 받아 gemini/codex/claude 중 가장 적합한 외주 AI 를 선정하고 사유와 함께 사용자에게 통지하는 로직.

## 설계 결정

### AD-002: 정량 지표 + LLM 판단 혼합 라우팅
- **결정**: 정량 점수표 + LLM 판단을 혼합하여 결정
- **근거**: 정량만으로는 디자인 의도를 못 잡고, LLM 만으로는 비결정적. 혼합으로 신뢰도 + 설명력 확보.
- **대안 검토**:
  - 정량 only — 거부 (디자인 복잡도 못 잡음)
  - LLM only — 거부 (블랙박스, 재현성 X)
- **영향 범위**: 새 워크플로우 Step 4

## 상세 명세

### 입력

```python
{
    "png_paths": ["figma-png/MAIN.png", "figma-png/header_b.png", ...],
    "extracted_dir": "extracted/",
    "project_type": "landing | basic"
}
```

### 정량 지표 추출 (스크립트)

```python
indicators = {
    "asset_count": int,           # img/ 의 자산 수
    "section_count": int,         # extracted/ 의 *_spec.json 수
    "image_fill_count": int,      # spec.json 의 IMAGE fill 수 (배경 사진)
    "vector_count": int,          # spec.json 의 vector_nodes 수
    "text_node_count": int,       # spec.json 의 text_nodes 합계
    "frame_depth_max": int,       # spec.json frame 의 최대 nesting 깊이
    "has_animation_hint": bool,   # PNG 에 슬라이더/캐러셀/모션 패턴 감지
    "page_height_px": int,        # MAIN PNG 높이
}
```

### 점수표 (heuristic)

| 지표 | gemini-dev | codex-dev | claude-dev |
|------|-----------|-----------|-----------|
| 페이지 높이 > 3000px (대용량) | +3 | 0 | -1 |
| section_count > 5 (복잡) | +2 | 0 | -1 |
| image_fill_count > 5 (사진 많음) | +1 | 0 | 0 |
| frame_depth_max > 6 (깊은 nesting) | +2 | 0 | -1 |
| text_node_count > 30 (텍스트 많음) | +2 | 0 | 0 |
| has_animation_hint (모션) | 0 | +2 | 0 |
| section_count <= 2 (단순) | 0 | 0 | +2 |
| asset_count == 0 (no image) | 0 | +1 | +2 |

기본 점수: 모두 0
최고 점수 AI 가 선정. 동점 시 우선순위: gemini > codex > claude (퍼블리싱 기본).

### LLM 판단 (보조)

PNG 의 첫 번째(MAIN) 를 multimodal LLM 으로 보고 아래 질문:

```
이 디자인의 복잡도를 1-5 로 평가하고, 아래 중 어느 AI 가 가장 적합한지 골라주세요:
- gemini-dev: 대용량 컨텍스트, 프론트엔드, 복잡한 레이아웃에 강함
- codex-dev: 코드 정밀도, 모션/인터랙션 로직에 강함
- claude-dev: 단순 인라인 수정, 문서/설정 작업에 강함

응답: {"recommended": "gemini-dev|codex-dev|claude-dev", "reason": "..."}
```

### 최종 결정 알고리즘

```
quant_winner = 점수표 최고점 AI
llm_winner = LLM 응답의 recommended

if quant_winner == llm_winner:
    final = quant_winner
    confidence = "high"
else:
    final = quant_winner  # 정량 우선 (재현성)
    confidence = "medium"
    note = f"LLM 은 {llm_winner} 추천했으나 정량은 {quant_winner}. 정량 우선."
```

### 사용자 통지 형식

```
[AI 외주 선정] gemini-dev
- 정량 점수: gemini=5, codex=2, claude=-1
- LLM 판단: gemini-dev (복잡도 4/5, 페이지 3645px + 6 sections + 17 partner logos)
- 사유: 대용량 PNG (3645px) + 복잡 레이아웃 (frame depth 7) + 텍스트 다수 (44 text nodes)
- 신뢰도: high
```

### 도구 통합

별도 `tools/select-ai.py` 신설 또는 `pm-verify.py` 의 pre-step 으로 통합. 현재 결정: **별도 도구** (`select-ai.py`) 로 만들어 워크플로우 Step 4 에서 호출.

### 인터페이스

```bash
python3 tools/select-ai.py \
  --extracted extracted/ \
  --figma-png figma-png/ \
  --img img/ \
  --project-type landing \
  --json
```

출력 (JSON):
```json
{
  "selected": "gemini-dev",
  "confidence": "high",
  "quant_scores": {"gemini-dev": 5, "codex-dev": 2, "claude-dev": -1},
  "llm_recommendation": "gemini-dev",
  "indicators": {...},
  "reason": "대용량 PNG (3645px) + 복잡 레이아웃..."
}
```

### Error 처리

- `--extracted` 없음 또는 빈 디렉토리: stderr + exit 1
- LLM 호출 실패: 정량 only 로 fallback + 사유 기록 + exit 0
- 정량 + LLM 모두 실패: stderr + exit 1

## 리스크 완화 (R1)

- **잘못된 AI 선택 가능성** → 항상 사유와 점수 출력하여 PM 이 수동 override 가능
- **정량 점수표 부정확** → fixture 3건 (단순 / 중간 / 복잡 페이지) 으로 회귀 테스트
- **LLM 판단 비결정성** → 정량 우선, LLM 은 보조

## Q&A 보강 사항

- **Q2 답변**: PNG 보고 HTML/CSS 생성에 최적화된 AI 가 누구일까를 정해서 알려달라
  - 결정: 정량 + LLM 혼합 알고리즘으로 결정 + 사유 사용자 통지
  - 결정 기준은 PNG 시각 + extracted/ 의 정량 지표 (자산/섹션/프레임/텍스트)

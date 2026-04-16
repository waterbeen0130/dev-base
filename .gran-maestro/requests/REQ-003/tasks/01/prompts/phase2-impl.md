# Implementation Request — REQ-003 T01

## Task
json-to-html.py의 핵심 품질 문제 4건을 해결한다.

## Spec
Read the full spec: `/mnt/d/dev-base/.gran-maestro/requests/REQ-003/tasks/01/spec.md`

## Plan Context
Read the plan: `/mnt/d/dev-base/.gran-maestro/plans/PLN-003/plan.md`

## Implementation Context

수정 대상은 `tools/json-to-html.py` 단일 파일 (665행, SemanticConverter 클래스).

### 1. depth limiter 텍스트 무손실 (MUST, TIER-A)
현재 L387-400의 depth limiter가 `depth >= 5`에서 자식을 flatten하지만, 자식 트리에 텍스트 노드가 있어도 무시하고 flatten하여 텍스트가 누락된다.

수정: `_has_text_descendant(node)` 재귀 헬퍼를 추가하고, depth >= 5 flatten 조건에 "자식 트리에 텍스트 노드가 없을 때만" flatten하도록 변경.

```python
def _has_text_descendant(self, node: dict) -> bool:
    """Check if any descendant has text content."""
    if node.get("text"):
        return True
    for child in node.get("children", []):
        if self._has_text_descendant(child):
            return True
    return False
```

L389 조건을 다음으로 변경:
```python
if depth >= 5 and children and not text and not img_path:
    if not layout_has_value and not has_visual and not self._has_text_descendant(node):
        # Safe to flatten — no text will be lost
        for child in children:
            self._render(child, depth, parent_cls)
        return
```

### 2. flex 비율 자동 변환 (MUST, TIER-A)
현재 정규화 JSON에 `visual.width`와 `layout.sizing.horizontal` (FIXED/FILL/HUG) 값이 이미 존재하지만 json-to-html.py에서 활용하지 않음.

수정: `_render()` 컨테이너 노드 처리에서 자식 노드들의 width + sizing 정보로 flex CSS 생성.

```python
def _flex_sizing_css(self, node: dict, siblings: list[dict]) -> dict[str, str]:
    """Convert Figma sizing to flex CSS properties."""
    sizing = (node.get("layout") or {}).get("sizing", {})
    horizontal = sizing.get("horizontal", "FIXED")
    visual = node.get("visual") or {}
    width = visual.get("width")
    
    if horizontal == "FILL":
        return {"flex": "1"}
    elif horizontal == "HUG":
        return {}  # auto width
    elif horizontal == "FIXED" and width and siblings:
        # Calculate percentage based on siblings
        total_width = sum(
            (s.get("visual") or {}).get("width", 0) or 0
            for s in siblings
        )
        if total_width > 0:
            pct = round(width / total_width * 100, 1)
            return {"flex": f"0 0 {pct}%"}
    return {}
```

_render() 컨테이너 처리 부분에서 각 자식의 flex sizing을 계산하여 CSS에 반영.
이미지/아이콘/divider 노드(`_is_decorative`, `_is_divider`, image-map hit)는 고정 width 유지.

### 3. 클래스명 개선 (SHOULD, TIER-B)
현재 `_cls()` 메서드가 `parent_cls` 파라미터를 받지만 미사용. 범용 패턴(el_N, txt_N, btn_N, list_N)을 감지하면 부모 이름을 접두사로 치환.

수정: `_cls()` 또는 `_remap_name()`에 부모 컨텍스트 활용 로직 추가.
- 범용 패턴 감지: `re.match(r'^(el|txt|btn|list|item|box|wrap|frame|group|element)_?\d*$', slug)`
- 감지 시 parent_cls에서 페이지 프리픽스 제거 후 부모 이름 추출 → 접두사로 사용
- 예: parent="notice", child="txt_1" → "notice_txt"
- 추론 실패(parent가 없거나 역시 범용명) 시 기존 이름 유지

### 4. 이미지 이름 중복 개선 (COULD, TIER-B)
image_map hit 처리 시 cls 생성에 parent_cls 컨텍스트 반영.
- 예: "graphic" 이미지가 "notice" 부모 → "notice_graphic"

### Verification Commands
수정 완료 후 반드시 실행:
```bash
python3 tools/validate-semantic.py --html output/youngwol/index.html --css output/youngwol/common.css
python3 tools/validate-semantic.py --html output/a_main/index.html --css output/a_main/common.css
```

[REFERENCE_CONTEXT]
current_date: 2026-04-05
model_cutoff: 2025-05
references: none
[/REFERENCE_CONTEXT]

## Coding Rules (CRITICAL)

### Read these rule files:
- `D:/dev-base/rules/common.md` — Common CSS/HTML rules
- `D:/dev-base/rules/codex.md` — Codex agent rules

### Key Rules (inline backup):
- All CSS selector rules in ONE LINE format (no multi-line expansion)
- No duplicate selectors — merge into one
- Colors: hex only (#fff, #090944), rgba only when transparency needed
- No CSS Grid — flexbox only
- line-height: unitless ratio only (1.3, 1.45)
- letter-spacing: em unit (-0.025em)
- border-radius: circle 50%, pill 2em — no 999px
- Classes: snake_case, {page}_{role} pattern
- No individual class on every element — parent+tag selectors first
- No <p> for short labels — use <span>
- Python code comments in English only

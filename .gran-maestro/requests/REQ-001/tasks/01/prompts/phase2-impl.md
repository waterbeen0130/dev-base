# 구현 요청: pytest smoke test 환경 구축

## 컨텍스트
프로젝트에 pytest 기반 테스트 환경을 구축합니다. figma-extract.py의 핵심 유틸 함수를 검증하는 smoke test를 작성합니다.

## 스펙
아래 파일 3개를 생성하세요. 기존 파일은 수정하지 마세요.

### 1. pyproject.toml (프로젝트 루트)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 2. tests/__init__.py (빈 파일)
빈 파일로 생성하세요.

### 3. tests/test_smoke.py
`tools/figma-extract.py`에서 핵심 함수를 import하여 기본 동작을 검증하는 테스트를 작성합니다.

테스트 대상 함수:
- `rgba_to_hex(r, g, b, a)`: Figma RGBA(0-1 float) → hex 문자열
- `extract_fill_color(fills)`: fill 배열에서 첫 visible SOLID fill 색상 추출
- `line_height_to_ratio(line_height_px, font_size)`: lineHeightPx → 무단위 비율
- `figma_align_to_css(value, axis)`: Figma 정렬값 → CSS flex 정렬

import 방법:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

# figma-extract.py는 하이픈이 있으므로 importlib 사용
import importlib.util
spec = importlib.util.spec_from_file_location(
    "figma_extract",
    os.path.join(os.path.dirname(__file__), '..', 'tools', 'figma-extract.py')
)
figma_extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figma_extract)

rgba_to_hex = figma_extract.rgba_to_hex
extract_fill_color = figma_extract.extract_fill_color
line_height_to_ratio = figma_extract.line_height_to_ratio
figma_align_to_css = figma_extract.figma_align_to_css
```

테스트 케이스 예시:
```python
def test_rgba_to_hex_red():
    assert rgba_to_hex(1, 0, 0) == '#f00'

def test_rgba_to_hex_white():
    assert rgba_to_hex(1, 1, 1) == '#fff'

def test_rgba_to_hex_with_opacity():
    result = rgba_to_hex(0.1, 0.2, 0.3, 0.5)
    assert result.startswith('rgba(')

def test_extract_fill_color_solid():
    fills = [{"type": "SOLID", "color": {"r": 1, "g": 0, "b": 0, "a": 1}}]
    assert extract_fill_color(fills) == '#f00'

def test_extract_fill_color_empty():
    assert extract_fill_color([]) is None
    assert extract_fill_color(None) is None

def test_line_height_to_ratio():
    assert line_height_to_ratio(24, 16) == 1.5

def test_figma_align_to_css():
    assert figma_align_to_css('CENTER', 'primary') == 'center'
    assert figma_align_to_css('SPACE_BETWEEN', 'primary') == 'space-between'
    assert figma_align_to_css('STRETCH', 'counter') == 'stretch'
```

## 검증
완료 후 반드시 실행:
```bash
pytest tests/test_smoke.py -v
```

모든 테스트가 PASSED여야 합니다.

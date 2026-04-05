#!/usr/bin/env python3
"""Build per-section Gemini prompts from split sections + image map.

Usage:
  python3 tools/build-prompts.py \
    --sections ./sections/ --image-map ./image-map.json \
    --page main --output ./prompts/
"""

import argparse
import json
import os
import re
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / "templates" / "section-prompt.md"

# Section name → meaningful CSS class mapping hints
SECTION_HINTS = {
    "header": "공통 영역 — main_ 프리픽스 없이 역할명(header, gnb, logo) 사용. nav>ul>li>a 구조.",
    "footer": "공통 영역 — main_ 프리픽스 없음. footer>nav>ul>li, address, copyright.",
    "quick": "우측 고정 플로팅 메뉴. position:fixed. ul>li>a>img+span. 공통 영역.",
    "mv": "메인비주얼. 배경 이미지 위에 콘텐츠 겹침(position:relative/absolute). 좌측 텍스트+버튼, 우측 카드.",
}


def build_image_map_for_section(section_data: dict, full_image_map: dict) -> dict:
    """Extract relevant image mappings for a section."""
    def collect_ids(node):
        ids = [node.get("id", "")]
        for c in node.get("children", []):
            ids.extend(collect_ids(c))
        return ids

    section_ids = set(collect_ids(section_data["tree"]))
    return {k: v for k, v in full_image_map.items() if k in section_ids}


def build_prompt(section_path: str, section_data: dict, image_map: dict,
                 page: str, template: str) -> str:
    """Build a complete prompt for one section."""
    meta = section_data["meta"]
    name = meta["section_name"]
    slug = re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_")

    # Determine section-specific hints
    hint = ""
    for key, val in SECTION_HINTS.items():
        if key in slug:
            hint = val
            break
    if not hint:
        hint = f"CSS 프리픽스: {page}_"

    # Build the prompt
    prompt = f"""# 섹션 HTML/CSS 변환 요청 — {name}

## 절대 금지 (CRITICAL)
- 텍스트를 임의 생성/추측 금지 — JSON TEXT 노드만 사용
- JSON에 없는 콘텐츠를 만들어내지 마라
- sec_1, sec_2 같은 범용 클래스명 금지 → 역할명 사용
- JSON에 배경색(background)이 없으면 background-color를 추가하지 마라

## CSS 규칙 (CRITICAL)
- 각 셀렉터 한 줄 작성
- 모든 요소에 개별 클래스 금지 → .parent span, .parent h2 부모+태그 선택자
- 같은 태그 복수 시 :first-of-type / + span
- font-size: rem (PC), line-height: 무단위 비율, letter-spacing: em
- 색상: hex 전용, 투명도 시만 rgba
- CSS Grid 금지 — flexbox만
- font-family Pretendard이면 생략 (reset.css 기본)
- font-weight 400이면 생략 (기본값)
- justify-content:flex-start, align-items:flex-start/stretch 생략 (기본값)
- padding/gap 0이면 생략
- width/height 고정px 금지 (컨테이너) — flex 비율 사용
- 빈 div 금지, DOM 최대 5단계
- 불필요 래퍼(자식 1개, 스타일 없음) 제거
- 리스트 반복 3개+ → ul>li
- 이미지: div.img_area > img
- 짧은 텍스트에 <p> 금지 → <span>
- 배경 이미지 위 콘텐츠 겹침 → position:relative + absolute

## 섹션 정보
- 페이지: {page}
- {hint}

## 이미지 매핑
{json.dumps(image_map, indent=2, ensure_ascii=False)}

## 정규화 JSON
파일 읽기: {section_path}

## 출력
HTML 코드블록 1개 + CSS 코드블록 1개만 출력. 설명 불필요.
"""
    return prompt


def main():
    parser = argparse.ArgumentParser(description="Build per-section Gemini prompts")
    parser.add_argument("--sections", required=True, help="Sections directory")
    parser.add_argument("--image-map", required=True, help="Image map JSON")
    parser.add_argument("--page", default="main", help="Page name for CSS prefix")
    parser.add_argument("--output", required=True, help="Output prompts directory")
    args = parser.parse_args()

    with open(args.image_map, "r", encoding="utf-8") as f:
        full_image_map = json.load(f)

    with open(os.path.join(args.sections, "manifest.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)

    os.makedirs(args.output, exist_ok=True)
    template = ""  # Could load from TEMPLATE_PATH if needed

    for section in manifest["sections"]:
        sec_file = section["file"]
        sec_path = os.path.join(args.sections, sec_file)

        with open(sec_path, "r", encoding="utf-8") as f:
            sec_data = json.load(f)

        sec_image_map = build_image_map_for_section(sec_data, full_image_map)

        prompt = build_prompt(
            section_path=sec_path,
            section_data=sec_data,
            image_map=sec_image_map,
            page=args.page,
            template=template,
        )

        prompt_file = os.path.join(args.output, f"{section['slug']}.md")
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        print(f"  [{section['index']}] {section['name']} → {prompt_file} ({len(sec_image_map)} images)")

    print(f"\n{len(manifest['sections'])} prompts → {args.output}/")


if __name__ == "__main__":
    main()

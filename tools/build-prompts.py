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


# BEGIN AUTO-GEN PROFILE_RULES (rules/rules.yaml → tools/build-rules.py)
PROFILE_RULES = {
    "basic": [
        "레이아웃은 flexbox만 사용한다 (Grid/float 금지).",
        "CSS Grid는 사용하지 않는다 — flexbox 전용.",
        "섹션 폭 공식 강제: --width = Figma inner content width + 40, --padding = 20px, .cont 클래스 패턴 필수, 섹션은 full-bleed + background, 너비 제한은 .cont 내부에서만.",
        "색상은 hex 전용 (#fff, #090944). rgb()/hsl() 금지. 투명도 필요 시만 rgba() 허용.",
        "8자리 hex 리터럴(#RRGGBBAA)은 사용하지 않는다 (주석 및 url(data:) 내부는 제외).",
        "universal reset(*, *::before, *::after) 외 box-sizing:border-box 중복 선언을 금지한다.",
        "@media 블록 본문이 공백/주석뿐이면 빈 블록으로 간주하고 금지한다 (@media print 예외).",
        "@media 내부 규칙은 줄바꿈 분리하되 들여쓰기 없이 작성한다. 한 줄에 모든 규칙을 이어붙이지 않는다.",
        "!important는 사용하지 않는다 (mb_/mt_/txt_c 등 유틸리티 클래스만 예외).",
        "@media 블록 내부 규칙에 들여쓰기를 사용하지 않는다.",
        "basic 프로젝트: reset.css는 별도 파일로 분리한다.",
        "common.css에 reset.css의 핵심 패턴(* margin/padding/box-sizing 등)을 중복 작성하지 않는다.",
        "각 CSS 셀렉터 규칙은 한 줄로 작성한다 (여러 줄 펼침 금지).",
        "100px 미만 값에는 clamp()를 사용하지 않는다 (고정 px). 100px 이상만 clamp 허용.",
        "padding/margin에 100px 미만 clamp()를 사용하지 않는다.",
        "calc()는 clamp() 내부에서만 사용한다. 단독 사용 금지.",
        "vw 단위는 clamp() 내부에서만 사용한다. 단독 사용 금지.",
        ":root{} 안의 CSS 변수는 각 줄에 하나씩 선언한다 (한 줄에 여러 변수 금지).",
        ":root 변수는 --point-color-N, --width, --padding 같은 패턴을 따른다 (시맨틱 이름 금지).",
        "같은 접두사 클래스가 8개 이상이면 부모+태그 셀렉터로 축소를 검토한다.",
        "같은 셀렉터를 미디어쿼리 밖에서 중복 선언하지 않는다 (한 번만 선언).",
        ".font_serif, .weight_bold 같은 유틸리티 클래스를 사용하지 않는다 — 부모 셀렉터에서 직접 처리.",
        "셀렉터는 페이지/섹션 스코프 안에 작성한다 (전역 단일 클래스 셀렉터 지양).",
        "동일 font-family fallback 체인이 *, body, 개별 selector에 과다 반복되면 중복으로 간주한다.",
        "html,body에 font-size: clamp(14px, 1.2vw, 16px) 기준 선언이 필요하다 (basic 프로젝트).",
        "basic 프로젝트: PC font-size는 rem 단위, 모바일(@media max-width:768px)에서만 px 사용.",
        "landing 프로파일에서 html/body font-size에 clamp|vw|rem|calc 혼용을 금지한다.",
        "letter-spacing은 em 단위를 사용한다. px는 절대값 2px 이하 미세 조정 시에만 허용.",
        "line-height는 무단위 비율(1.3, 1.45)만 사용한다. 25.866px 같은 computed px 금지.",
        "line-height 무단위 비율은 정돈 후보 목록(1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0) 중 하나를 사용한다.",
        "다중행 말줄임 패턴은 -webkit-line-clamp 등 표준 패턴을 사용한다 (수동 시각 비교 필요).",
        "한국어 텍스트 단락/헤딩에는 word-break: keep-all을 적용한다.",
        "border-radius는 원형 50%, pill 2em을 사용한다. 999px는 금지.",
        "좌우 padding 100px 이상이면 max-width + margin:auto 패턴으로 변환해야 한다.",
        "좌우 padding 100px 이상이 발견되면 max-width 기반 레이아웃 패턴 사용을 권장한다.",
        "basic 프로젝트 768px 이하: padding/margin은 PC 값의 약 절반 사용.",
        "내부 wrapper div는 최대 1개로 제한한다 (불필요한 중첩 금지).",
        "DOM 최대 깊이는 5단계를 초과하지 않는다.",
        "<figure>, <figcaption>, <main>, <article> 태그는 사용하지 않는다.",
        "반복되는 <a> 태그는 ul>li 구조 안에 배치한다 (연속 <a> 2개 이상 금지).",
        "<nav> 안에는 ul>li>a 구조를 사용한다 (직접 <a> 나열 금지).",
        "빈 div(<div></div>) 사용 금지.",
        "<figure>/<figcaption> 사용 금지 — div.img_area + p/span 구조 사용.",
        "인라인 style 속성을 사용하지 않는다.",
        "body 태그에 page_ 클래스를 부여하지 않는다 (불필요).",
        "header/footer/gnb/logo 같은 공통 영역에 페이지 프리픽스를 사용하지 않는다.",
        "sec_숫자, section_숫자, box숫자 같은 범용 클래스명을 모두 금지한다.",
        "HTML 파일명은 페이지 내용을 반영한 의미 있는 영문명이어야 한다 (page_1.html, sub_01.html 금지).",
        "sec_1, sec_2, section_01 같은 범용 클래스명을 금지한다.",
        "CSS 클래스 프리픽스는 HTML 파일명과 일치해야 한다 (greeting.html → greeting_).",
        "각 페이지의 본문 클래스는 페이지 프리픽스({페이지}_{역할}) 패턴을 따른다.",
        "HTML 클래스명은 snake_case 만 사용한다 (kebab-case, camelCase 금지).",
        "이미지/카드 영역에 aspect-ratio 사용을 권장한다 (수동 시각 비교 필요).",
        "콘텐츠 이미지는 div.img_area 래퍼 안에 배치한다 (배경/로고/아이콘 제외).",
        "<p> 태그는 텍스트에 \n이 있거나, 길이 95자 초과거나, 종결어미 반복일 때만 사용. 짧은 라벨은 <span> 사용.",
        "20자 미만 짧은 텍스트에 <p> 태그를 사용하지 않는다 — <span> 사용.",
        "img alt 텍스트는 짧고 간결하게 (한국어 문장 전체 금지).",
        "aria-label은 시각적 텍스트가 없는 인터랙티브 요소에만 사용한다 (남용 금지).",
        "Figma primaryAxis/counterAxis 정렬은 layoutMode에 따라 CSS justify-content/align-items 매핑이 바뀐다.",
        "Figma itemSpacing → CSS gap 또는 margin 선택은 간격 균일성·layoutMode·정렬 복잡도로 결정한다.",
        "Figma 카드 슬롯 수(component variant dedup 후) == HTML main section <li> 수. variant를 별개 카드로 오인 방지.",
        "Figma 카드/리스트 아이템 개수 결정: 고유 bbox 슬롯 수 + component variant dedup + instance 그룹.",
        "extracted/*_spec.json의 text_nodes[].characters는 반드시 HTML에 나타나야 한다. AI가 텍스트를 추론/축약/복원하면 안 된다.",
    ],
    "landing": [
        "레이아웃은 flexbox만 사용한다 (Grid/float 금지).",
        "CSS Grid는 사용하지 않는다 — flexbox 전용.",
        "섹션 폭 공식 강제: --width = Figma inner content width + 40, --padding = 20px, .cont 클래스 패턴 필수, 섹션은 full-bleed + background, 너비 제한은 .cont 내부에서만.",
        "색상은 hex 전용 (#fff, #090944). rgb()/hsl() 금지. 투명도 필요 시만 rgba() 허용.",
        "8자리 hex 리터럴(#RRGGBBAA)은 사용하지 않는다 (주석 및 url(data:) 내부는 제외).",
        "universal reset(*, *::before, *::after) 외 box-sizing:border-box 중복 선언을 금지한다.",
        "@media 블록 본문이 공백/주석뿐이면 빈 블록으로 간주하고 금지한다 (@media print 예외).",
        "landing 프로젝트는 [data-delay] opacity/position 룰과 .section_on 토글 룰이 있어야 한다.",
        "@media 내부 규칙은 줄바꿈 분리하되 들여쓰기 없이 작성한다. 한 줄에 모든 규칙을 이어붙이지 않는다.",
        "!important는 사용하지 않는다 (mb_/mt_/txt_c 등 유틸리티 클래스만 예외).",
        "@media 블록 내부 규칙에 들여쓰기를 사용하지 않는다.",
        "각 CSS 셀렉터 규칙은 한 줄로 작성한다 (여러 줄 펼침 금지).",
        "100px 미만 값에는 clamp()를 사용하지 않는다 (고정 px). 100px 이상만 clamp 허용.",
        "padding/margin에 100px 미만 clamp()를 사용하지 않는다.",
        "calc()는 clamp() 내부에서만 사용한다. 단독 사용 금지.",
        "vw 단위는 clamp() 내부에서만 사용한다. 단독 사용 금지.",
        ":root{} 안의 CSS 변수는 각 줄에 하나씩 선언한다 (한 줄에 여러 변수 금지).",
        ":root 변수는 --point-color-N, --width, --padding 같은 패턴을 따른다 (시맨틱 이름 금지).",
        "landing 프로젝트는 :root에 --padding, --header_h, --width, --point-color-1 4개 변수가 모두 존재해야 한다.",
        "같은 접두사 클래스가 8개 이상이면 부모+태그 셀렉터로 축소를 검토한다.",
        "같은 셀렉터를 미디어쿼리 밖에서 중복 선언하지 않는다 (한 번만 선언).",
        ".font_serif, .weight_bold 같은 유틸리티 클래스를 사용하지 않는다 — 부모 셀렉터에서 직접 처리.",
        "셀렉터는 페이지/섹션 스코프 안에 작성한다 (전역 단일 클래스 셀렉터 지양).",
        "동일 font-family fallback 체인이 *, body, 개별 selector에 과다 반복되면 중복으로 간주한다.",
        "landing 프로젝트: 모든 font-size는 PC/모바일 모두 고정 px만 사용 (rem 사용 금지).",
        "landing 프로파일에서 html/body font-size에 clamp|vw|rem|calc 혼용을 금지한다.",
        "letter-spacing은 em 단위를 사용한다. px는 절대값 2px 이하 미세 조정 시에만 허용.",
        "line-height는 무단위 비율(1.3, 1.45)만 사용한다. 25.866px 같은 computed px 금지.",
        "line-height 무단위 비율은 정돈 후보 목록(1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0) 중 하나를 사용한다.",
        "다중행 말줄임 패턴은 -webkit-line-clamp 등 표준 패턴을 사용한다 (수동 시각 비교 필요).",
        "한국어 텍스트 단락/헤딩에는 word-break: keep-all을 적용한다.",
        "border-radius는 원형 50%, pill 2em을 사용한다. 999px는 금지.",
        "좌우 padding 100px 이상이면 max-width + margin:auto 패턴으로 변환해야 한다.",
        "좌우 padding 100px 이상이 발견되면 max-width 기반 레이아웃 패턴 사용을 권장한다.",
        "내부 wrapper div는 최대 1개로 제한한다 (불필요한 중첩 금지).",
        "DOM 최대 깊이는 5단계를 초과하지 않는다.",
        "<figure>, <figcaption>, <main>, <article> 태그는 사용하지 않는다.",
        "반복되는 <a> 태그는 ul>li 구조 안에 배치한다 (연속 <a> 2개 이상 금지).",
        "<nav> 안에는 ul>li>a 구조를 사용한다 (직접 <a> 나열 금지).",
        "빈 div(<div></div>) 사용 금지.",
        "<figure>/<figcaption> 사용 금지 — div.img_area + p/span 구조 사용.",
        "인라인 style 속성을 사용하지 않는다.",
        "body 태그에 page_ 클래스를 부여하지 않는다 (불필요).",
        "header/footer/gnb/logo 같은 공통 영역에 페이지 프리픽스를 사용하지 않는다.",
        "sec_숫자, section_숫자, box숫자 같은 범용 클래스명을 모두 금지한다.",
        "HTML 파일명은 페이지 내용을 반영한 의미 있는 영문명이어야 한다 (page_1.html, sub_01.html 금지).",
        "sec_1, sec_2, section_01 같은 범용 클래스명을 금지한다.",
        "CSS 클래스 프리픽스는 HTML 파일명과 일치해야 한다 (greeting.html → greeting_).",
        "각 페이지의 본문 클래스는 페이지 프리픽스({페이지}_{역할}) 패턴을 따른다.",
        "HTML 클래스명은 snake_case 만 사용한다 (kebab-case, camelCase 금지).",
        "이미지/카드 영역에 aspect-ratio 사용을 권장한다 (수동 시각 비교 필요).",
        "콘텐츠 이미지는 div.img_area 래퍼 안에 배치한다 (배경/로고/아이콘 제외).",
        "<p> 태그는 텍스트에 \n이 있거나, 길이 95자 초과거나, 종결어미 반복일 때만 사용. 짧은 라벨은 <span> 사용.",
        "20자 미만 짧은 텍스트에 <p> 태그를 사용하지 않는다 — <span> 사용.",
        "img alt 텍스트는 짧고 간결하게 (한국어 문장 전체 금지).",
        "aria-label은 시각적 텍스트가 없는 인터랙티브 요소에만 사용한다 (남용 금지).",
        "Figma primaryAxis/counterAxis 정렬은 layoutMode에 따라 CSS justify-content/align-items 매핑이 바뀐다.",
        "Figma itemSpacing → CSS gap 또는 margin 선택은 간격 균일성·layoutMode·정렬 복잡도로 결정한다.",
        "Figma 카드 슬롯 수(component variant dedup 후) == HTML main section <li> 수. variant를 별개 카드로 오인 방지.",
        "Figma 카드/리스트 아이템 개수 결정: 고유 bbox 슬롯 수 + component variant dedup + instance 그룹.",
        "extracted/*_spec.json의 text_nodes[].characters는 반드시 HTML에 나타나야 한다. AI가 텍스트를 추론/축약/복원하면 안 된다.",
    ],
}
# END AUTO-GEN PROFILE_RULES


def build_prompt(section_path: str, section_data: dict, image_map: dict,
                 page: str, profile: str) -> str:
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

    # Profile-specific rules
    css_rules = PROFILE_RULES.get(profile, PROFILE_RULES["basic"])

    prompt = f"""# 섹션 HTML/CSS 변환 요청 — {name}

## 절대 금지 (CRITICAL)
- 텍스트를 임의 생성/추측 금지 — JSON TEXT 노드만 사용
- JSON에 없는 콘텐츠를 만들어내지 마라
- sec_1, sec_2 같은 범용 클래스명 금지 → 역할명 사용
- JSON에 배경색(background)이 없으면 background-color를 추가하지 마라

{css_rules}

## 섹션 정보
- 페이지: {page}
- 프로필: {profile}
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
    parser.add_argument("--profile", default="basic", help="Profile: basic or landing")
    parser.add_argument("--output", required=True, help="Output prompts directory")
    args = parser.parse_args()

    with open(args.image_map, "r", encoding="utf-8") as f:
        full_image_map = json.load(f)

    with open(os.path.join(args.sections, "manifest.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)

    profile = args.profile or manifest.get("meta", {}).get("profile", "basic")
    os.makedirs(args.output, exist_ok=True)

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
            profile=profile,
        )

        prompt_file = os.path.join(args.output, f"{section['slug']}.md")
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        print(f"  [{section['index']}] {section['name']} → {prompt_file} ({len(sec_image_map)} images)")

    print(f"\n{len(manifest['sections'])} prompts → {args.output}/")


if __name__ == "__main__":
    main()

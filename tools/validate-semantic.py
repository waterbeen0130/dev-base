#!/usr/bin/env python3
"""Post-generation validator for semantic HTML/CSS.

Usage:
  python3 tools/validate-semantic.py --html output/index.html --css output/common.css
  python3 tools/validate-semantic.py --html output/index.html --css output/common.css --fix
"""


import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yaml


@dataclass
class ValidationResult:
    rule_id: str
    severity: str  # error|warning|info|deprecated
    passed: bool
    skipped: bool = False
    message: str = ""
    location: Optional[str] = None  # "file:line" or "file" or None


@dataclass
class ValidationContext:
    html_text: str
    css_text: str
    html_path: str
    css_path: str
    profile: str  # all|basic|landing
    mapping: Optional[dict] = None
    img_dir: Optional[str] = None


class Violation:
    def __init__(self, rule: str, severity: str, message: str, line: int = 0, file: str = ""):
        self.rule = rule
        self.severity = severity  # CRITICAL / MAJOR / MINOR
        self.message = message
        self.line = line
        self.file = file

    def __str__(self):
        loc = f"{self.file}:{self.line}" if self.line else self.file
        return f"[{self.severity}] {self.rule} — {self.message} ({loc})"


class SemanticValidator:
    """Legacy check_* implementations. Bodies are preserved and wrapped by adapters."""

    def __init__(self):
        self.violations: list[Violation] = []

    def _add(self, rule: str, severity: str, message: str, line: int = 0, file: str = ""):
        self.violations.append(Violation(rule, severity, message, line, file))

    # ===== HTML Checks =====

    def check_nav_structure(self, html: str, filepath: str):
        """nav 안에 ul>li>a 구조가 아닌 직접 a 태그가 있는지 확인"""
        lines = html.split("\n")
        in_nav = False
        for i, line in enumerate(lines, 1):
            if "<nav" in line:
                in_nav = True
            if "</nav>" in line:
                in_nav = False
            if in_nav and "<a " in line and "<li>" not in line and "<li><a" not in line:
                prev_lines = "\n".join(lines[max(0, i - 3):i])
                if "<ul>" not in prev_lines and "<li>" not in prev_lines:
                    self._add(
                        "nav-ul-li",
                        "CRITICAL",
                        "nav 안에 ul>li 없이 직접 <a> 사용 (규칙: nav > ul > li > a)",
                        i,
                        filepath,
                    )

    def check_img_wrapper(self, html: str, filepath: str):
        """콘텐츠 이미지가 img_area 래퍼 없이 사용되는지 확인 (배경/로고/아이콘 제외)"""
        lines = html.split("\n")
        for i, line in enumerate(lines, 1):
            if "<img " not in line:
                continue
            if any(skip in line for skip in ["_bg", "logo", "ic_", "sns_", "alt=\"메뉴\""]):
                continue
            if "<p>" in line or "<p " in line:
                continue
            if "img_area" not in line:
                prev = lines[max(0, i - 2):i]
                if not any("img_area" in p for p in prev):
                    self._add(
                        "img-wrapper",
                        "MAJOR",
                        f"이미지에 img_area 래퍼 없음: {line.strip()[:60]}",
                        i,
                        filepath,
                    )

    def check_inline_style(self, html: str, filepath: str):
        """인라인 스타일 사용 확인"""
        for i, line in enumerate(html.split("\n"), 1):
            if 'style="' in line:
                self._add(
                    "no-inline-style",
                    "CRITICAL",
                    f"인라인 스타일 사용: {line.strip()[:60]}",
                    i,
                    filepath,
                )

    def check_forbidden_tags(self, html: str, filepath: str):
        """금지된 HTML 태그 확인"""
        forbidden = ["<figure", "<figcaption", "<main", "<article"]
        for i, line in enumerate(html.split("\n"), 1):
            for tag in forbidden:
                if tag in line.lower():
                    self._add("forbidden-tag", "CRITICAL", f"금지된 태그 사용: {tag}", i, filepath)

    def check_list_pattern(self, html: str, filepath: str):
        """반복 a 태그가 ul>li 없이 나열되는지 확인"""
        lines = html.split("\n")
        consecutive_a = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r"^<a\s", stripped):
                consecutive_a += 1
            else:
                if consecutive_a >= 2:
                    self._add(
                        "list-pattern",
                        "MAJOR",
                        f"연속 <a> {consecutive_a}개 — ul>li 구조 필요",
                        i - 1,
                        filepath,
                    )
                consecutive_a = 0

    def check_p_tag_misuse(self, html: str, filepath: str):
        """짧은 텍스트에 <p> 태그 사용 확인"""
        for i, line in enumerate(html.split("\n"), 1):
            match = re.search(r"<p[^>]*>([^<]+)</p>", line)
            if match:
                text = match.group(1).strip()
                if len(text) < 20 and "\n" not in text and not text.endswith(("다.", "요.", "다", "요")):
                    self._add("p-tag-misuse", "MINOR", f'짧은 텍스트에 <p> 사용: "{text}"', i, filepath)

    # ===== CSS Checks =====

    def check_css_grid(self, css: str, filepath: str):
        """CSS Grid 사용 확인"""
        for i, line in enumerate(css.split("\n"), 1):
            if "display:grid" in line or "display: grid" in line:
                self._add("no-css-grid", "CRITICAL", "CSS Grid 사용 금지 — flexbox만 허용", i, filepath)

    def check_important(self, css: str, filepath: str):
        """!important 사용 확인"""
        for i, line in enumerate(css.split("\n"), 1):
            if "!important" in line:
                if not any(
                    u in line
                    for u in [
                        ".mb_",
                        ".mt_",
                        ".mr_",
                        ".ml_",
                        ".pb_",
                        ".pt_",
                        ".txt_c",
                        ".txt_l",
                        ".txt_r",
                        ".back_no",
                        ".bd_",
                    ]
                ):
                    self._add(
                        "no-important",
                        "MAJOR",
                        f"!important 사용 (유틸리티 외 금지): {line.strip()[:60]}",
                        i,
                        filepath,
                    )

    def check_border_radius_999(self, css: str, filepath: str):
        """999px border-radius 확인"""
        for i, line in enumerate(css.split("\n"), 1):
            if "999px" in line:
                self._add("no-999px", "CRITICAL", "999px 사용 금지 — 원형: 50%, pill: 2em", i, filepath)

    def check_color_format(self, css: str, filepath: str):
        """rgb()/hsl() 사용 확인 (rgba 제외)"""
        for i, line in enumerate(css.split("\n"), 1):
            if re.search(r"(?<!rgba)\brgb\(", line) or "hsl(" in line:
                self._add("hex-color-only", "MAJOR", f"hex 이외 색상 형식: {line.strip()[:60]}", i, filepath)

    def check_max_width_pattern(self, css: str, filepath: str):
        """좌우 padding으로 레이아웃 폭 제한하는지 확인"""
        for i, line in enumerate(css.split("\n"), 1):
            match = re.search(r"padding:\s*\d+px\s+(\d+)px", line)
            if match:
                side_pad = int(match.group(1))
                if side_pad >= 100:
                    self._add(
                        "max-width-pattern",
                        "MAJOR",
                        f"좌우 padding {side_pad}px — max-width + margin:auto 사용 권장",
                        i,
                        filepath,
                    )

    def check_reset_duplicate(self, css: str, filepath: str):
        """common.css에 reset.css 내용 중복 확인"""
        css_dir = os.path.dirname(filepath)
        reset_path = os.path.join(css_dir, "reset.css")
        if not os.path.exists(reset_path):
            return
        reset_patterns = [
            (r"\*\s*\{[^}]*margin\s*:\s*0", "* { margin:0 }"),
            (r"\*\s*\{[^}]*padding\s*:\s*0", "* { padding:0 }"),
            (r"\*\s*\{[^}]*box-sizing", "* { box-sizing }"),
            (r"ul\s*\{[^}]*list-style\s*:\s*none", "ul { list-style:none }"),
            (r"^img\s*\{[^}]*max-width", "img { max-width }"),
            (r"a\s*\{[^}]*text-decoration\s*:\s*none", "a { text-decoration:none }"),
            (r"body\s*\{[^}]*overflow-x", "body { overflow-x }"),
            (r"body\s*\{[^}]*word-break", "body { word-break }"),
        ]
        for pattern, desc in reset_patterns:
            if re.search(pattern, css):
                self._add("reset-duplicate", "MAJOR", f"reset.css와 중복: {desc} — common.css에서 제거", 0, filepath)

    def check_word_break(self, css: str, filepath: str):
        """word-break: keep-all 적용 확인 (reset.css 포함)"""
        css_dir = os.path.dirname(filepath)
        reset_path = os.path.join(css_dir, "reset.css")
        combined = css
        if os.path.exists(reset_path):
            combined += Path(reset_path).read_text(encoding="utf-8")
        if "keep-all" not in combined:
            self._add("word-break", "MAJOR", "word-break: keep-all 미적용 (한국어 텍스트 필수)", 0, filepath)

    def check_font_size_base(self, css: str, filepath: str):
        """html,body font-size clamp 기준 확인 (reset.css 포함)"""
        css_dir = os.path.dirname(filepath)
        reset_path = os.path.join(css_dir, "reset.css")
        combined = css
        if os.path.exists(reset_path):
            combined += Path(reset_path).read_text(encoding="utf-8")
        if "font-size:clamp(" not in combined.replace(" ", ""):
            self._add("font-size-base", "MAJOR", "html,body에 font-size:clamp(14px, 1.2vw, 16px) 미적용", 0, filepath)

    def check_root_vars(self, css: str, filepath: str):
        """필수 :root 변수 확인 + 각 변수 줄바꿈 확인"""
        if "--width" not in css:
            self._add("root-vars", "MAJOR", ":root에 --width 변수 미선언", 0, filepath)
        if "--padding" not in css:
            self._add("root-vars", "MAJOR", ":root에 --padding 변수 미선언", 0, filepath)
        for i, line in enumerate(css.split("\n"), 1):
            if ":root{" in line.replace(" ", "") and "--" in line and ";" in line:
                vars_in_line = line.count("--")
                if vars_in_line >= 2:
                    self._add(
                        "root-var-line-separated",
                        "MAJOR",
                        f":root 변수는 각각 줄바꿈 필요 ({vars_in_line}개 한 줄에)",
                        i,
                        filepath,
                    )

    def check_reset_css(self, html: str, filepath: str):
        """basic 프로젝트: reset.css 별도 파일 존재 확인"""
        if "reset.css" not in html:
            self._add("reset-css-separate", "MAJOR", "reset.css가 별도 파일로 분리되어 있지 않음 (basic 프로젝트 규칙)", 0, filepath)

    def check_selector_format(self, css: str, filepath: str):
        """셀렉터 한 줄 포맷 확인 (미디어쿼리 내부 제외)"""
        lines = css.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.endswith("{") and not stripped.startswith("@") and not stripped.startswith("/*") and not stripped.startswith(":root"):
                if i < len(lines):
                    next_line = lines[i].strip() if i < len(lines) else ""
                    if next_line and not next_line.startswith("}") and not next_line.startswith(".") and not next_line.startswith("@"):
                        self._add(
                            "one-line-selector",
                            "MINOR",
                            f"멀티라인 셀렉터 — 한 줄 포맷 사용: {stripped[:40]}",
                            i,
                            filepath,
                        )

    # ===== Additional HTML Checks =====

    def check_empty_div(self, html: str, filepath: str):
        """빈 div 금지"""
        for i, line in enumerate(html.split("\n"), 1):
            if re.search(r"<div[^>]*>\s*</div>", line):
                self._add("no-empty-div", "MAJOR", f"빈 div 발견: {line.strip()[:50]}", i, filepath)

    def check_dom_depth(self, html: str, filepath: str):
        """DOM 최대 깊이 5단계 확인"""
        depth = 0
        for i, line in enumerate(html.split("\n"), 1):
            opens = len(re.findall(r"<(?:div|ul|li|nav|header|footer|section)\b", line))
            closes = len(re.findall(r"</(?:div|ul|li|nav|header|footer|section)>", line))
            depth += opens - closes
            if depth > 5:
                self._add("max-dom-depth", "MAJOR", f"DOM 깊이 {depth}단계 (최대 5)", i, filepath)
                break

    def check_snake_case_classes(self, html: str, filepath: str):
        """클래스명 snake_case 검증"""
        classes = re.findall(r'class="([^"]*)"', html)
        for cls_str in classes:
            for cls in cls_str.split():
                if cls in ("img_area", "cont"):
                    continue
                if not re.match(r"^[a-z0-9_]+$", cls):
                    self._add("snake-case-class", "MAJOR", f"snake_case 아닌 클래스: .{cls}", 0, filepath)

    # ===== Additional CSS Checks =====

    def check_duplicate_selectors(self, css: str, filepath: str):
        """같은 셀렉터 중복 선언 금지 (미디어쿼리 내 오버라이드는 제외)"""
        in_media = False
        seen: dict[str, int] = {}
        for line in css.split("\n"):
            if "@media" in line:
                in_media = True
                continue
            if in_media and line.strip() == "}":
                in_media = False
                continue
            if in_media:
                continue
            match = re.match(r"^(\.[a-z0-9_. >:+~\-]+)\{", line)
            if match:
                sel = match.group(1).strip()
                if sel in seen:
                    self._add("no-duplicate-selector", "MAJOR", f"셀렉터 중복 선언: {sel}", 0, filepath)
                seen[sel] = 1

    def check_line_height_px(self, css: str, filepath: str):
        """line-height에 computed px 사용 금지 — 무단위 비율만"""
        for i, line in enumerate(css.split("\n"), 1):
            match = re.search(r"line-height:\s*[\d.]+px", line)
            if match:
                self._add(
                    "line-height-ratio",
                    "CRITICAL",
                    f"line-height에 px 사용 금지 — 무단위 비율만: {match.group()}",
                    i,
                    filepath,
                )

    def check_letter_spacing_unit(self, css: str, filepath: str):
        """letter-spacing em 단위 확인 (2px 이하 미세 조정 예외)"""
        for i, line in enumerate(css.split("\n"), 1):
            match = re.search(r"letter-spacing:\s*([\d.]+)px", line)
            if match:
                val = float(match.group(1))
                if val > 2:
                    self._add(
                        "letter-spacing-em",
                        "MAJOR",
                        f"letter-spacing {val}px — em 단위 사용 (2px 이하만 px 허용)",
                        i,
                        filepath,
                    )

    def check_clamp_under_100(self, css: str, filepath: str):
        """100px 미만 값에 clamp 사용 금지"""
        for i, line in enumerate(css.split("\n"), 1):
            matches = re.findall(r"clamp\((\d+)px", line)
            for m in matches:
                threshold = int(m)
                if threshold < 100:
                    # REQ-033: threshold uplift for no_clamp_under_100 parity.
                    self._add(
                        "no-clamp-under-100",
                        "MINOR",
                        f"100px 미만 값에 clamp 사용: {line.strip()[:50]} (threshold={threshold}px)",
                        i,
                        filepath,
                    )

    def check_raw_calc_vw(self, css: str, filepath: str):
        """calc()/vw 단독 사용 금지 (clamp 내부만 허용)"""
        for i, line in enumerate(css.split("\n"), 1):
            if "calc(" in line and "clamp(" not in line:
                self._add(
                    "no-raw-calc",
                    "MAJOR",
                    f"calc() 단독 사용 금지 (clamp 내부만 허용): {line.strip()[:50]}",
                    i,
                    filepath,
                )
            if re.search(r"\d+vw", line) and "clamp(" not in line:
                self._add(
                    "no-raw-vw",
                    "MAJOR",
                    f"vw 단독 사용 금지 (clamp 내부만 허용): {line.strip()[:50]}",
                    i,
                    filepath,
                )

    def check_media_indent(self, css: str, filepath: str):
        """미디어쿼리 내부 들여쓰기 금지"""
        in_media = False
        for i, line in enumerate(css.split("\n"), 1):
            if "@media" in line:
                in_media = True
                continue
            if in_media and line.strip() == "}":
                in_media = False
                continue
            if in_media and line.startswith(("  ", "\t", "    ")):
                self._add("no-media-indent", "MINOR", f"미디어쿼리 내부 들여쓰기 금지: {line[:40]}", i, filepath)

    def check_utility_classes(self, css: str, filepath: str):
        """유틸리티 클래스 금지 (font-family/font-weight 범용 클래스)"""
        patterns = [r"\.font_", r"\.weight_", r"\.color_", r"\.size_"]
        for i, line in enumerate(css.split("\n"), 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    self._add("no-utility-class", "MAJOR", f"유틸리티 클래스 금지: {line.strip()[:50]}", i, filepath)

    # ===== Class Naming Checks =====

    def check_common_area_prefix(self, html: str, filepath: str):
        """공통 영역(header, footer, gnb, logo)에 페이지 프리픽스 사용 확인"""
        common_names = [
            "header",
            "footer",
            "gnb",
            "logo",
            "copyright",
            "btn_top",
            "btn_menu",
            "btn_close",
            "total_menu",
        ]
        classes = re.findall(r'class="([^"]*)"', html)
        for cls_str in classes:
            for cls in cls_str.split():
                for common in common_names:
                    if re.match(r"^[a-z]+_" + common + r"($|_)", cls) and cls != common:
                        prefix = cls.split("_" + common)[0]
                        if prefix and prefix != common.split("_")[0]:
                            self._add(
                                "common-area-prefix",
                                "CRITICAL",
                                f"공통 영역에 페이지 프리픽스 사용: .{cls} → .{common} 계열로 변경",
                                0,
                                filepath,
                            )

    def check_excessive_individual_classes(self, css: str, filepath: str):
        """개별 클래스 과다 사용 확인 — 부모+태그 선택자로 대체 가능한지"""
        selectors = re.findall(r"^\.([a-z0-9_]+)\{", css, re.MULTILINE)
        prefix_count: dict[str, int] = {}
        for selector in selectors:
            parts = selector.split("_")
            if len(parts) >= 2:
                prefix = "_".join(parts[:2])
                prefix_count[prefix] = prefix_count.get(prefix, 0) + 1
        for prefix, count in prefix_count.items():
            if count > 8:
                self._add(
                    "excessive-classes",
                    "MINOR",
                    f".{prefix}_* 계열 클래스 {count}개 — 부모+태그 선택자로 축소 검토",
                    0,
                    filepath,
                )

    def check_generic_class_names(self, html: str, filepath: str):
        """sec_1, sec_2, section_01 같은 범용 클래스명 확인"""
        classes = re.findall(r'class="([^"]*)"', html)
        for cls_str in classes:
            for cls in cls_str.split():
                if re.match(r".*sec_\d+$", cls) or re.match(r".*section_\d+$", cls) or re.match(r".*box\d+$", cls):
                    self._add("generic-class-name", "CRITICAL", f"범용 클래스명 금지: .{cls} → 역할/내용을 반영한 이름 사용", 0, filepath)

    def check_body_page_class(self, html: str, filepath: str):
        """body에 불필요한 page_ 클래스 확인"""
        match = re.search(r'<body[^>]*class="page_[^"]*"', html)
        if match:
            self._add(
                "body-page-class",
                "MINOR",
                "body에 page_ 클래스 불필요 (규칙: body 태그에 페이지 프리픽스 클래스 불필요)",
                0,
                filepath,
            )

    # ===== Image Checks =====

    def check_image_naming(self, img_dir: str):
        """이미지 파일명 규칙 확인"""
        if not os.path.isdir(img_dir):
            return
        for filename in os.listdir(img_dir):
            if not filename.endswith((".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif")):
                continue
            name = os.path.splitext(filename)[0]
            if re.match(r"^[0-9]+[-:][0-9]+", name) or name.startswith("I"):
                self._add("img-naming", "CRITICAL", f"Figma node ID 파일명: {filename} — 의미 있는 이름 사용", 0, img_dir)
            if not re.match(r"^[a-z0-9_]+$", name):
                if not re.match(r"^[0-9]+[-:][0-9]+", name):
                    self._add("img-naming", "MINOR", f"snake_case 아님: {filename}", 0, img_dir)

    def check_large_side_padding(self, css: str, filepath: str):
        """좌우 padding 100px 이상 → max-width + margin:auto 사용해야 함"""
        for match in re.finditer(r"([^{]+)\{([^}]+)\}", css):
            selector = match.group(1).strip()
            props = match.group(2)
            pad_match = re.search(r"padding\s*:\s*([^;]+)", props)
            if not pad_match:
                continue
            pad_val = pad_match.group(1).strip()
            parts = pad_val.replace("px", "").split()
            lr_values = []
            if len(parts) == 2:
                lr_values = [parts[1]]
            elif len(parts) == 4:
                lr_values = [parts[1], parts[3]]
            for value in lr_values:
                try:
                    if float(value) >= 100:
                        has_maxwidth = "max-width" in props
                        if not has_maxwidth:
                            self._add(
                                "large-side-padding",
                                "MAJOR",
                                f"좌우 padding {value}px — max-width + margin:auto로 변환 필요: {selector}",
                                0,
                                filepath,
                            )
                        break
                except ValueError:
                    pass


# ===== Legacy function adapters (keep check_* names) =====

LEGACY_CHECK_METHODS = [
    "check_nav_structure",
    "check_img_wrapper",
    "check_inline_style",
    "check_forbidden_tags",
    "check_list_pattern",
    "check_p_tag_misuse",
    "check_css_grid",
    "check_important",
    "check_border_radius_999",
    "check_color_format",
    "check_max_width_pattern",
    "check_reset_duplicate",
    "check_word_break",
    "check_font_size_base",
    "check_root_vars",
    "check_reset_css",
    "check_selector_format",
    "check_empty_div",
    "check_dom_depth",
    "check_snake_case_classes",
    "check_duplicate_selectors",
    "check_line_height_px",
    "check_letter_spacing_unit",
    "check_clamp_under_100",
    "check_raw_calc_vw",
    "check_media_indent",
    "check_utility_classes",
    "check_common_area_prefix",
    "check_excessive_individual_classes",
    "check_generic_class_names",
    "check_body_page_class",
    "check_image_naming",
    "check_large_side_padding",
]

LEGACY_HTML_CHECKS = {
    "check_nav_structure",
    "check_img_wrapper",
    "check_inline_style",
    "check_forbidden_tags",
    "check_list_pattern",
    "check_p_tag_misuse",
    "check_reset_css",
    "check_empty_div",
    "check_dom_depth",
    "check_snake_case_classes",
    "check_common_area_prefix",
    "check_generic_class_names",
    "check_body_page_class",
}

LEGACY_CSS_CHECKS = {
    "check_css_grid",
    "check_important",
    "check_border_radius_999",
    "check_color_format",
    "check_max_width_pattern",
    "check_reset_duplicate",
    "check_word_break",
    "check_font_size_base",
    "check_root_vars",
    "check_selector_format",
    "check_duplicate_selectors",
    "check_line_height_px",
    "check_letter_spacing_unit",
    "check_clamp_under_100",
    "check_raw_calc_vw",
    "check_media_indent",
    "check_utility_classes",
    "check_excessive_individual_classes",
    "check_large_side_padding",
}


def _default_img_dir(ctx: ValidationContext) -> str:
    if ctx.img_dir:
        return ctx.img_dir
    html_dir = os.path.dirname(ctx.html_path)
    if html_dir:
        return os.path.join(html_dir, "images")
    return ""


def _invoke_legacy_method(
    validator: SemanticValidator,
    method_name: str,
    html_text: str,
    css_text: str,
    ctx: ValidationContext,
) -> None:
    method = getattr(validator, method_name)
    if method_name in LEGACY_HTML_CHECKS:
        method(html_text, ctx.html_path)
        return
    if method_name in LEGACY_CSS_CHECKS:
        method(css_text, ctx.css_path)
        return
    if method_name == "check_image_naming":
        img_dir = _default_img_dir(ctx)
        if img_dir:
            method(img_dir)


def _make_legacy_check(method_name: str) -> Callable:
    def legacy_check(html: str, css: str, ctx: Optional[ValidationContext] = None) -> list[Violation]:
        local_ctx = ctx or ValidationContext(html, css, "", "", "all")
        validator = SemanticValidator()
        _invoke_legacy_method(validator, method_name, html, css, local_ctx)
        return validator.violations

    legacy_check.__name__ = method_name
    legacy_check.__doc__ = f"Adapter wrapper for SemanticValidator.{method_name}"
    return legacy_check


for _method_name in LEGACY_CHECK_METHODS:
    globals()[_method_name] = _make_legacy_check(_method_name)


def _format_violation_location(violation: Violation) -> Optional[str]:
    if violation.file and violation.line:
        return f"{violation.file}:{violation.line}"
    if violation.file:
        return violation.file
    return None


def _adapt_legacy_check(legacy_func: Callable) -> Callable:
    """Wrap a legacy check_* function to return ValidationResult."""

    def adapter(rule: dict, ctx: ValidationContext) -> ValidationResult:
        try:
            violations = legacy_func(ctx.html_text, ctx.css_text, ctx)
        except Exception as exc:  # pragma: no cover - defensive
            return ValidationResult(
                rule_id=rule["id"],
                severity=rule["severity"],
                passed=True,
                skipped=True,
                message=f"handler error: {exc}",
            )

        if not violations:
            return ValidationResult(rule_id=rule["id"], severity=rule["severity"], passed=True)

        first = violations[0]
        return ValidationResult(
            rule_id=rule["id"],
            severity=rule["severity"],
            passed=False,
            message="; ".join(v.message for v in violations),
            location=_format_violation_location(first),
        )

    return adapter


def _handler_error_result(rule: dict, exc: Exception) -> ValidationResult:
    return ValidationResult(
        rule_id=rule["id"],
        severity=rule["severity"],
        passed=True,
        skipped=True,
        message=f"handler error: {exc}",
    )


def _safe_custom_handler(handler: Callable[[dict, ValidationContext], ValidationResult]) -> Callable[[dict, ValidationContext], ValidationResult]:
    def wrapped(rule: dict, ctx: ValidationContext) -> ValidationResult:
        try:
            return handler(rule, ctx)
        except Exception as exc:  # pragma: no cover - defensive
            return _handler_error_result(rule, exc)

    wrapped.__name__ = handler.__name__
    return wrapped


def _resolve_custom_handler_name(rule: dict) -> str:
    validation = rule.get("validation", {})
    return validation.get("custom_handler") or rule.get("custom_handler") or rule.get("id", "")


# ===== ENUM VALIDATORS =====

def _target_text(rule: dict, ctx: ValidationContext) -> str:
    target = rule.get("validation", {}).get("target", "html")
    return ctx.css_text if target == "css" else ctx.html_text


def _strip_html_comments(html: str) -> str:
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def _target_path(rule: dict, ctx: ValidationContext) -> str:
    target = rule.get("validation", {}).get("target", "html")
    return ctx.css_path if target == "css" else ctx.html_path


def _line_from_pos(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def validate_regex_must_not_match(rule: dict, ctx: ValidationContext) -> ValidationResult:
    pattern = rule["validation"].get("pattern", "")

    if rule.get("id") == "meaningful_page_name":
        filename = Path(ctx.html_path).stem.lower()
        try:
            filename_match = re.search(pattern, filename, re.MULTILINE)
        except re.error as exc:
            return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"invalid_regex: {exc}")
        if filename_match:
            return ValidationResult(
                rule["id"],
                rule["severity"],
                False,
                message=f"forbidden pattern matched in filename: {pattern}",
                location=f"{ctx.html_path}:1",
            )

    target = _target_text(rule, ctx)
    try:
        match = re.search(pattern, target, re.MULTILINE)
    except re.error as exc:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"invalid_regex: {exc}")

    if match:
        line = _line_from_pos(target, match.start())
        return ValidationResult(
            rule["id"],
            rule["severity"],
            False,
            message=f"forbidden pattern matched: {pattern}",
            location=f"{_target_path(rule, ctx)}:{line}",
        )
    return ValidationResult(rule["id"], rule["severity"], True)


def validate_regex_must_match(rule: dict, ctx: ValidationContext) -> ValidationResult:
    target = _target_text(rule, ctx)
    pattern = rule["validation"].get("pattern", "")
    try:
        match = re.search(pattern, target, re.MULTILINE)
    except re.error as exc:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"invalid_regex: {exc}")

    if not match:
        return ValidationResult(rule["id"], rule["severity"], False, message=f"required pattern missing: {pattern}")
    return ValidationResult(rule["id"], rule["severity"], True)


def validate_regex_should_match(rule: dict, ctx: ValidationContext) -> ValidationResult:
    result = validate_regex_must_match(rule, ctx)
    result.severity = "info"
    return result


def validate_ast_selector_count(rule: dict, ctx: ValidationContext) -> ValidationResult:
    pattern = rule["validation"].get("pattern", "")
    parsed = re.match(r"^\s*(.+?)\s*(<=|>=|==|!=|<|>)\s*(\d+)\s*$", pattern)
    if not parsed:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="invalid_selector_count_pattern")

    selector, op, raw_limit = parsed.groups()
    limit = int(raw_limit)
    count = len(re.findall(re.escape(selector) + r"\s*\{", ctx.css_text))

    comparisons = {
        "<=": count <= limit,
        ">=": count >= limit,
        "==": count == limit,
        "!=": count != limit,
        "<": count < limit,
        ">": count > limit,
    }
    if not comparisons[op]:
        return ValidationResult(
            rule["id"],
            rule["severity"],
            False,
            message=f"selector count check failed: {selector} {op} {limit} (actual={count})",
            location=ctx.css_path,
        )
    return ValidationResult(rule["id"], rule["severity"], True)


HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def _normalize_css_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def _extract_css_property_values(css_text: str, property_name: str) -> list[str]:
    pattern = re.compile(rf"{re.escape(property_name)}\s*:\s*([^;{{}}]+)", re.IGNORECASE)
    return [_normalize_css_value(match.group(1)) for match in pattern.finditer(css_text)]


def _parse_numeric_value(raw: Any) -> Optional[float]:
    if isinstance(raw, (int, float)):
        return float(raw)
    if not isinstance(raw, str):
        return None
    matched = re.match(r"^\s*(-?\d+(?:\.\d+)?)", raw.strip())
    if not matched:
        return None
    return float(matched.group(1))


def _normalize_number_token(value: float) -> str:
    if abs(value - int(value)) < 1e-9:
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _number_css_tokens(value: float) -> set[str]:
    number = _normalize_number_token(value)
    tokens = {number, f"{number}px"}
    rem_value = value / 16.0
    tokens.add(f"{_normalize_number_token(rem_value)}rem")
    return tokens


def _rgb_dict_to_hex(color: dict) -> Optional[str]:
    if not {"r", "g", "b"}.issubset(color.keys()):
        return None
    channels: list[int] = []
    for key in ("r", "g", "b"):
        raw = color.get(key)
        if not isinstance(raw, (int, float)):
            return None
        if raw <= 1:
            channels.append(max(0, min(255, int(round(raw * 255)))))
        else:
            channels.append(max(0, min(255, int(round(raw)))))
    return "#{:02x}{:02x}{:02x}".format(*channels)


def _collect_color_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, str):
        tokens.update(match.lower() for match in HEX_COLOR_RE.findall(value))
        return tokens
    if isinstance(value, dict):
        hex_color = _rgb_dict_to_hex(value)
        if hex_color:
            tokens.add(hex_color)
        for key, child in value.items():
            if key.lower() == "color" and isinstance(child, dict):
                nested_hex = _rgb_dict_to_hex(child)
                if nested_hex:
                    tokens.add(nested_hex)
            tokens.update(_collect_color_tokens(child))
        return tokens
    if isinstance(value, list):
        for child in value:
            tokens.update(_collect_color_tokens(child))
    return tokens


def _collect_generic_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()
    if value is None:
        return tokens
    if isinstance(value, (int, float)):
        return _number_css_tokens(float(value))
    if isinstance(value, str):
        normalized = _normalize_css_value(value)
        tokens.add(normalized)
        numeric = _parse_numeric_value(normalized)
        if numeric is not None:
            tokens.update(_number_css_tokens(numeric))
        tokens.update(match.lower() for match in HEX_COLOR_RE.findall(normalized))
        return tokens
    if isinstance(value, dict):
        for child in value.values():
            tokens.update(_collect_generic_tokens(child))
        return tokens
    if isinstance(value, list):
        for child in value:
            tokens.update(_collect_generic_tokens(child))
    return tokens


def _extract_mapping_values(mapping: Any, dotted_path: str) -> list[Any]:
    parts = [part for part in dotted_path.split(".") if part]
    if not parts:
        return []

    values: list[Any] = []

    def descend(node: Any, remaining: list[str]) -> None:
        if not remaining:
            values.append(node)
            return
        if isinstance(node, dict):
            head = remaining[0]
            if head in node:
                descend(node[head], remaining[1:])
            for child in node.values():
                if isinstance(child, (dict, list)):
                    descend(child, remaining)
            return
        if isinstance(node, list):
            for child in node:
                descend(child, remaining)

    descend(mapping, parts)
    return values


def _padding_tokens(value: Any) -> set[str]:
    numbers: list[float] = []
    if isinstance(value, (int, float)):
        number = float(value)
        numbers = [number, number, number, number]
    elif isinstance(value, list):
        parsed = [_parse_numeric_value(item) for item in value]
        if all(item is not None for item in parsed):
            numbers = [float(item) for item in parsed]  # type: ignore[arg-type]
    elif isinstance(value, dict):
        top = _parse_numeric_value(value.get("top"))
        right = _parse_numeric_value(value.get("right"))
        bottom = _parse_numeric_value(value.get("bottom"))
        left = _parse_numeric_value(value.get("left"))
        if None not in {top, right, bottom, left}:
            numbers = [float(top), float(right), float(bottom), float(left)]  # type: ignore[arg-type]
        else:
            vertical = _parse_numeric_value(value.get("vertical"))
            horizontal = _parse_numeric_value(value.get("horizontal"))
            if vertical is not None and horizontal is not None:
                numbers = [float(vertical), float(horizontal), float(vertical), float(horizontal)]
    if not numbers:
        return set()

    top, right, bottom, left = numbers if len(numbers) == 4 else (numbers + numbers[:1] * 4)[:4]
    if top == right == bottom == left:
        shorthand = f"{_normalize_number_token(top)}px"
    elif top == bottom and right == left:
        shorthand = f"{_normalize_number_token(top)}px {_normalize_number_token(right)}px"
    elif right == left:
        shorthand = f"{_normalize_number_token(top)}px {_normalize_number_token(right)}px {_normalize_number_token(bottom)}px"
    else:
        shorthand = " ".join(
            f"{_normalize_number_token(item)}px"
            for item in (top, right, bottom, left)
        )

    tokens = {shorthand}
    for item in (top, right, bottom, left):
        tokens.update(_number_css_tokens(item))
    return {_normalize_css_value(token) for token in tokens}


def _font_tokens_from_mapping(value: Any) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            lower_key = key.lower()
            if lower_key == "fontsize":
                numeric = _parse_numeric_value(child)
                if numeric is not None:
                    tokens.update(_number_css_tokens(numeric))
            elif lower_key in {"fontweight", "lineheight", "lineheightpx"}:
                numeric = _parse_numeric_value(child)
                if numeric is not None:
                    tokens.add(_normalize_number_token(numeric))
                    if lower_key in {"lineheight", "lineheightpx"}:
                        tokens.add(f"{_normalize_number_token(numeric)}px")
            elif lower_key == "lineheightpercent":
                numeric = _parse_numeric_value(child)
                if numeric is not None:
                    tokens.add(_normalize_number_token(numeric / 100.0))
            elif lower_key == "fontfamily" and isinstance(child, str):
                tokens.add(_normalize_css_value(child).strip("'\""))
            tokens.update(_font_tokens_from_mapping(child))
        return tokens
    if isinstance(value, list):
        for child in value:
            tokens.update(_font_tokens_from_mapping(child))
    return tokens


def _border_tokens_from_mapping(value: Any) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            lower_key = key.lower()
            if lower_key in {"weight", "strokewidth", "thickness"}:
                numeric = _parse_numeric_value(child)
                if numeric is not None:
                    tokens.update(_number_css_tokens(numeric))
            tokens.update(_collect_color_tokens(child))
            tokens.update(_border_tokens_from_mapping(child))
        return tokens
    if isinstance(value, list):
        for child in value:
            tokens.update(_border_tokens_from_mapping(child))
    if isinstance(value, (int, float)):
        tokens.update(_number_css_tokens(float(value)))
    if isinstance(value, str):
        tokens.update(_collect_color_tokens(value))
    return tokens


def _expected_tokens_from_mapping(lhs: str, mapping_path: str, mapping_values: list[Any]) -> set[str]:
    tokens: set[str] = set()
    lower_path = mapping_path.lower()

    for value in mapping_values:
        if "layoutmode" in lower_path:
            if isinstance(value, str):
                normalized = _normalize_css_value(value)
                if normalized in {"vertical", "column"}:
                    tokens.add("column")
                if normalized in {"horizontal", "row"}:
                    tokens.add("row")
            continue

        if lhs == "padding" or lower_path.endswith("padding"):
            tokens.update(_padding_tokens(value))
            continue

        if lhs in {"color", "background"} or "fills" in lower_path:
            tokens.update(_collect_color_tokens(value))
            continue

        if lhs == "font" or lower_path.endswith("text.style") or lower_path.endswith("style"):
            tokens.update(_font_tokens_from_mapping(value))
            continue

        if lhs == "border" or "stroke" in lower_path:
            tokens.update(_border_tokens_from_mapping(value))
            continue

        if lhs == "border-radius" or "cornerradius" in lower_path:
            numeric = _parse_numeric_value(value)
            if numeric is not None:
                tokens.update(_number_css_tokens(numeric))
            continue

        if lhs in {"gap", "item-spacing"} or "itemspacing" in lower_path:
            numeric = _parse_numeric_value(value)
            if numeric is not None:
                tokens.update(_number_css_tokens(numeric))
            continue

        tokens.update(_collect_generic_tokens(value))

    return {_normalize_css_value(token) for token in tokens if token}


def _extract_css_values_for_mapping(lhs: str, css_text: str) -> list[str]:
    if lhs == "font":
        values = []
        for prop in ("font", "font-size", "font-weight", "line-height", "font-family"):
            values.extend(_extract_css_property_values(css_text, prop))
        return values
    if lhs == "color":
        values = []
        for prop in ("color", "background", "background-color", "border-color"):
            values.extend(_extract_css_property_values(css_text, prop))
        return values
    return _extract_css_property_values(css_text, lhs)


def _collect_css_tokens(css_values: list[str]) -> set[str]:
    tokens: set[str] = set()
    for value in css_values:
        normalized = _normalize_css_value(value)
        tokens.add(normalized)
        tokens.update(match.lower() for match in HEX_COLOR_RE.findall(normalized))
        tokens.update(match.lower() for match in re.findall(r"-?\d+(?:\.\d+)?(?:px|rem|em|%)?", normalized))
        tokens.update(match.lower() for match in re.findall(r"[a-z_][a-z0-9_-]*", normalized))
    return tokens


def _mapping_match(lhs: str, expected_tokens: set[str], css_values: list[str], actual_tokens: set[str]) -> bool:
    if not expected_tokens:
        return False
    if lhs in {"padding", "gap", "border-radius"}:
        return any(css_value in expected_tokens for css_value in css_values) or bool(expected_tokens & actual_tokens)
    if lhs == "font":
        font_hits = {token for token in expected_tokens if token in actual_tokens}
        return len(font_hits) >= min(2, len(expected_tokens))
    return bool(expected_tokens & actual_tokens)


def validate_value_equals_mapping(rule: dict, ctx: ValidationContext) -> ValidationResult:
    try:
        if not ctx.mapping:
            return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="mapping_missing")

        pattern = rule.get("validation", {}).get("pattern", "")
        parsed = re.match(r"^\s*([a-zA-Z-]+)\s*(==|<-)\s*(.+)\s*$", pattern)
        if not parsed:
            return ValidationResult(
                rule["id"],
                rule["severity"],
                True,
                skipped=True,
                message=f"invalid_mapping_pattern: {pattern}",
            )

        lhs, _op, rhs = parsed.groups()
        lhs = lhs.strip().lower()
        rhs = rhs.strip()
        mapping_path = rhs.replace("mapping.", "", 1) if rhs.startswith("mapping.") else rhs

        css_values = _extract_css_values_for_mapping(lhs, ctx.css_text)
        if not css_values:
            return ValidationResult(
                rule["id"],
                rule["severity"],
                False,
                message=f"css_property_missing: {lhs}",
                location=ctx.css_path,
            )

        mapping_values = _extract_mapping_values(ctx.mapping, mapping_path)
        if not mapping_values:
            return ValidationResult(
                rule["id"],
                rule["severity"],
                False,
                message=f"mapping_value_missing: {mapping_path}",
            )

        expected_tokens = _expected_tokens_from_mapping(lhs, mapping_path, mapping_values)
        actual_tokens = _collect_css_tokens(css_values)
        if _mapping_match(lhs, expected_tokens, css_values, actual_tokens):
            return ValidationResult(rule["id"], rule["severity"], True)

        expected_preview = ", ".join(sorted(expected_tokens)[:4]) or "n/a"
        actual_preview = ", ".join(css_values[:2]) or "n/a"
        return ValidationResult(
            rule["id"],
            rule["severity"],
            False,
            message=f"value mismatch ({lhs} vs {mapping_path}) expected~[{expected_preview}] actual~[{actual_preview}]",
            location=ctx.css_path,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return _handler_error_result(rule, exc)


def validate_html_tag_required(rule: dict, ctx: ValidationContext) -> ValidationResult:
    pattern = rule["validation"].get("pattern", "")
    html = ctx.html_text
    if not pattern:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="missing_pattern")

    if ">" in pattern and "|" not in pattern and "(" not in pattern:
        tags = [p.strip().strip("<>").lower() for p in pattern.split(">") if p.strip()]
        pos = 0
        for tag in tags:
            found = html.lower().find(f"<{tag}", pos)
            if found < 0:
                return ValidationResult(rule["id"], rule["severity"], False, message=f"required tag chain missing: {pattern}")
            pos = found + 1
        return ValidationResult(rule["id"], rule["severity"], True)

    try:
        if not re.search(pattern, html, re.MULTILINE):
            return ValidationResult(rule["id"], rule["severity"], False, message=f"required tag pattern missing: {pattern}")
    except re.error as exc:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"invalid_regex: {exc}")
    return ValidationResult(rule["id"], rule["severity"], True)


def validate_forbidden_substring(rule: dict, ctx: ValidationContext) -> ValidationResult:
    target_name = rule.get("validation", {}).get("target", "html")
    target = _target_text(rule, ctx)
    if target_name == "html":
        target = _strip_html_comments(target)

    pattern = rule["validation"].get("pattern", "")
    if not pattern:
        return ValidationResult(rule["id"], rule["severity"], True)

    try:
        match = re.search(pattern, target, re.MULTILINE)
    except re.error as exc:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"invalid_regex: {exc}")

    if match:
        return ValidationResult(rule["id"], rule["severity"], False, message=f"forbidden substring found: {match.group(0)}")
    return ValidationResult(rule["id"], rule["severity"], True)


def validate_required_substring(rule: dict, ctx: ValidationContext) -> ValidationResult:
    target = _target_text(rule, ctx)
    raw = rule["validation"].get("pattern", "")
    if "," in raw:
        tokens = [token.strip() for token in raw.split(",") if token.strip()]
    else:
        tokens = [raw.strip()] if raw.strip() else []

    missing = [token for token in tokens if token not in target]
    if missing:
        return ValidationResult(rule["id"], rule["severity"], False, message=f"required substring missing: {', '.join(missing)}")
    return ValidationResult(rule["id"], rule["severity"], True)


def _extract_class_names(html_text: str) -> list[str]:
    names: list[str] = []
    for cls_str in re.findall(r'class="([^"]*)"', html_text):
        names.extend(token for token in cls_str.split() if token)
    return names


def validate_naming_pattern(rule: dict, ctx: ValidationContext) -> ValidationResult:
    pattern = rule["validation"].get("pattern", "")
    target = rule["validation"].get("target", "html")
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"invalid_regex: {exc}")

    if target == "html":
        if rule["id"] == "page_prefix_required":
            body_match = re.search(r"<body[^>]*class=\"([^\"]+)\"", ctx.html_text)
            if not body_match:
                return ValidationResult(rule["id"], rule["severity"], False, message="body class missing for page prefix rule")
            body_classes = [token for token in body_match.group(1).split() if token]
            invalid = [name for name in body_classes if not regex.match(name)]
            if invalid:
                return ValidationResult(rule["id"], rule["severity"], False, message=f"invalid body class naming: {', '.join(invalid)}")
            return ValidationResult(rule["id"], rule["severity"], True)

        invalid = [name for name in _extract_class_names(ctx.html_text) if not regex.match(name)]
        if invalid:
            return ValidationResult(rule["id"], rule["severity"], False, message=f"invalid class naming: {invalid[0]}")
        return ValidationResult(rule["id"], rule["severity"], True)

    if target == "css":
        selectors = re.findall(r"\.([a-zA-Z0-9_-]+)", ctx.css_text)
        invalid = [name for name in selectors if not regex.match(name)]
        if invalid:
            return ValidationResult(rule["id"], rule["severity"], False, message=f"invalid selector naming: {invalid[0]}")
        return ValidationResult(rule["id"], rule["severity"], True)

    return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"unsupported target: {target}")


def _calculate_dom_depth(html_text: str) -> int:
    depth = 0
    max_depth = 0
    for line in html_text.split("\n"):
        opens = len(re.findall(r"<(?:div|ul|li|nav|header|footer|section)\b", line))
        closes = len(re.findall(r"</(?:div|ul|li|nav|header|footer|section)>", line))
        depth += opens - closes
        if depth > max_depth:
            max_depth = depth
    return max_depth


def _calculate_inner_wrapper_count(html_text: str) -> int:
    count = 0
    for class_attr in re.findall(r'class="([^"]+)"', html_text):
        for token in class_attr.split():
            if "inner" in token:
                count += 1
    return count


def validate_numeric_range(rule: dict, ctx: ValidationContext) -> ValidationResult:
    expr = rule["validation"].get("pattern", "")
    parsed = re.match(r"^\s*([a-zA-Z_]+)\s*(<=|>=|==|<|>)\s*(\d+)\s*$", expr)
    if not parsed:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"unsupported range expression: {expr}")

    metric, op, raw_limit = parsed.groups()
    limit = int(raw_limit)
    if metric == "depth":
        actual = _calculate_dom_depth(ctx.html_text)
    elif metric == "inner_wrapper":
        actual = _calculate_inner_wrapper_count(ctx.html_text)
    else:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message=f"unsupported metric: {metric}")

    comparisons = {
        "<=": actual <= limit,
        ">=": actual >= limit,
        "==": actual == limit,
        "<": actual < limit,
        ">": actual > limit,
    }
    if not comparisons[op]:
        return ValidationResult(rule["id"], rule["severity"], False, message=f"range check failed: {metric} {op} {limit} (actual={actual})")
    return ValidationResult(rule["id"], rule["severity"], True)


ENUM_VALIDATORS: Dict[str, Callable] = {
    "regex_must_not_match": validate_regex_must_not_match,
    "regex_must_match": validate_regex_must_match,
    "regex_should_match": validate_regex_should_match,
    "ast_selector_count": validate_ast_selector_count,
    "value_equals_mapping": validate_value_equals_mapping,
    "html_tag_required": validate_html_tag_required,
    "forbidden_substring": validate_forbidden_substring,
    "required_substring": validate_required_substring,
    "naming_pattern": validate_naming_pattern,
    "numeric_range": validate_numeric_range,
}


def _strip_css_comments(css_text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)


def _mask_css_comments(css_text: str) -> str:
    def _replacer(match: re.Match[str]) -> str:
        return "".join("\n" if char == "\n" else " " for char in match.group(0))

    return re.sub(r"/\*.*?\*/", _replacer, css_text, flags=re.DOTALL)


def _extract_root_variables(css_text: str) -> list[tuple[str, str]]:
    root_match = re.search(r":root\s*\{(.*?)\}", css_text, re.DOTALL | re.IGNORECASE)
    if not root_match:
        return []
    return re.findall(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;{}]+)", root_match.group(1))


def _iter_css_selectors(css_text: str) -> list[str]:
    selectors: list[str] = []
    cleaned = _strip_css_comments(css_text)
    for match in re.finditer(r"([^{]+)\{", cleaned):
        raw_selector = match.group(1).strip()
        if not raw_selector or raw_selector.startswith("@"):
            continue
        for selector in raw_selector.split(","):
            normalized = _normalize_css_value(selector)
            if normalized:
                selectors.append(normalized)
    return selectors


def _extract_media_blocks(css_text: str) -> list[tuple[str, str, int, int]]:
    blocks: list[tuple[str, str, int, int]] = []
    for match in re.finditer(r"@media[^{]*\{", css_text, re.IGNORECASE):
        start = match.start()
        body_start = match.end()
        depth = 1
        cursor = body_start
        while cursor < len(css_text) and depth > 0:
            if css_text[cursor] == "{":
                depth += 1
            elif css_text[cursor] == "}":
                depth -= 1
            cursor += 1
        if depth == 0:
            blocks.append((match.group(0), css_text[body_start:cursor - 1], start, cursor))
    return blocks


def _remove_ranges(source: str, ranges: list[tuple[int, int]]) -> str:
    if not ranges:
        return source
    chunks: list[str] = []
    cursor = 0
    for start, end in sorted(ranges):
        chunks.append(source[cursor:start])
        cursor = end
    chunks.append(source[cursor:])
    return "".join(chunks)


def _collect_comment_ranges(css_text: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in re.finditer(r"/\*.*?\*/", css_text, flags=re.DOTALL)]


def _collect_data_url_ranges(css_text: str) -> list[tuple[int, int]]:
    pattern = re.compile(r"url\(\s*data:[^)]+\)", re.IGNORECASE | re.DOTALL)
    return [(match.start(), match.end()) for match in pattern.finditer(css_text)]


def _position_in_ranges(position: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in ranges)


def _iter_css_property_occurrences(css_text: str, property_name: str) -> list[tuple[str, str, int]]:
    occurrences: list[tuple[str, str, int]] = []
    masked_css = _mask_css_comments(css_text)
    block_pattern = re.compile(r"([^{]+)\{([^{}]*)\}")
    property_pattern = re.compile(rf"{re.escape(property_name)}\s*:\s*([^;{{}}]+)", re.IGNORECASE)

    for block_match in block_pattern.finditer(masked_css):
        raw_selector = block_match.group(1).strip()
        if not raw_selector or raw_selector.startswith("@"):
            continue
        selectors = [_normalize_css_value(selector) for selector in raw_selector.split(",")]
        selectors = [selector for selector in selectors if selector]
        if not selectors:
            continue

        body_start = block_match.start(2)
        body_masked = block_match.group(2)
        for property_match in property_pattern.finditer(body_masked):
            value_start = body_start + property_match.start(1)
            value_end = body_start + property_match.end(1)
            value = css_text[value_start:value_end].strip()
            line = _line_from_pos(css_text, value_start)
            for selector in selectors:
                occurrences.append((selector, value, line))

    return occurrences


def _extract_spacing_px(raw_value: str) -> Optional[float]:
    numbers = [float(item) for item in re.findall(r"(-?\d+(?:\.\d+)?)px", raw_value)]
    if not numbers:
        return None
    if len(numbers) == 1:
        return abs(numbers[0])
    if len(numbers) == 2:
        return abs(numbers[1])
    if len(numbers) >= 4:
        return max(abs(numbers[1]), abs(numbers[3]))
    return max(abs(item) for item in numbers)


def _extract_spacing_map(css_text: str) -> dict[tuple[str, str], float]:
    spacing: dict[tuple[str, str], float] = {}
    cleaned = _strip_css_comments(css_text)
    for block in re.finditer(r"([^{@}][^{]*)\{([^{}]*)\}", cleaned):
        selector = _normalize_css_value(block.group(1))
        body = block.group(2)
        if not selector:
            continue
        for prop in ("padding", "margin"):
            matched = re.search(rf"{prop}\s*:\s*([^;}}]+)", body, re.IGNORECASE)
            if not matched:
                continue
            value = _extract_spacing_px(matched.group(1))
            if value is not None:
                spacing[(selector, prop)] = value
    return spacing


def manual_review(rule: dict, _ctx: ValidationContext) -> ValidationResult:
    return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="manual_review_required")


def page_filename_class_prefix_match(rule: dict, ctx: ValidationContext) -> ValidationResult:
    page_prefix = Path(ctx.html_path).stem.lower().replace("-", "_")
    classes = _extract_class_names(ctx.html_text)
    if not classes:
        return ValidationResult(rule["id"], rule["severity"], False, message="no_class_found")
    if any(token.startswith(f"{page_prefix}_") for token in classes):
        return ValidationResult(rule["id"], rule["severity"], True)

    allowed = {"inner", "img_area", "on", "active", "section_on", "wrap", "blind", "clearfix"}
    page_candidates = [token for token in classes if token not in allowed and not token.startswith(("common_", "util_", "btn_", "ico_"))]
    if not page_candidates:
        return ValidationResult(rule["id"], rule["severity"], True)
    return ValidationResult(
        rule["id"],
        rule["severity"],
        False,
        message=f"class prefix mismatch: expected '{page_prefix}_*', got '{page_candidates[0]}'",
        location=ctx.html_path,
    )


def root_var_naming(rule: dict, ctx: ValidationContext) -> ValidationResult:
    variables = _extract_root_variables(ctx.css_text)
    if not variables:
        return ValidationResult(rule["id"], rule["severity"], True)
    allowed = re.compile(r"^--(?:point-color-\d+|font-color-\d+|width|padding|header_h|font|font\d+)$")
    invalid = [name for name, _ in variables if not allowed.match(name)]
    if invalid:
        return ValidationResult(rule["id"], rule["severity"], False, message=f"invalid :root variable naming: {invalid[0]}", location=ctx.css_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def selector_scoped(rule: dict, ctx: ValidationContext) -> ValidationResult:
    weak_selectors: list[str] = []
    skip_classes = {"on", "off", "active", "current", "open", "close", "hide", "show"}
    for selector in _iter_css_selectors(ctx.css_text):
        matched = re.match(r"^\.[a-z0-9_-]+$", selector)
        if not matched:
            continue
        class_name = selector[1:]
        if class_name in skip_classes or "_" in class_name or class_name.startswith(("js-", "is-", "u-")):
            continue
        weak_selectors.append(selector)
    if weak_selectors:
        return ValidationResult(
            rule["id"],
            rule["severity"],
            False,
            message=f"selector not scoped enough: {weak_selectors[0]}",
            location=ctx.css_path,
        )
    return ValidationResult(rule["id"], rule["severity"], True)


def img_alt_concise(rule: dict, ctx: ValidationContext) -> ValidationResult:
    for matched in re.finditer(r"<img\b[^>]*>", ctx.html_text, re.IGNORECASE):
        tag = matched.group(0)
        alt_match = re.search(r'alt\s*=\s*"([^"]*)"', tag, re.IGNORECASE)
        if not alt_match:
            return ValidationResult(rule["id"], rule["severity"], False, message="img alt missing", location=ctx.html_path)
        alt_text = alt_match.group(1).strip()
        if not alt_text:
            continue
        if len(alt_text) > 24 or re.search(r"[.!?]|(입니다|습니다|하세요|합니다)$", alt_text):
            return ValidationResult(rule["id"], rule["severity"], False, message=f"alt too verbose: '{alt_text[:30]}'", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def minimal_aria(rule: dict, ctx: ValidationContext) -> ValidationResult:
    interactive = {"a", "button", "input", "select", "textarea", "summary"}
    for matched in re.finditer(r"<([a-z0-9]+)\b([^>]*\baria-label\s*=\s*\"[^\"]+\"[^>]*)>", ctx.html_text, re.IGNORECASE):
        tag = matched.group(1).lower()
        attrs = matched.group(2)
        role_match = re.search(r'role\s*=\s*"([^"]+)"', attrs, re.IGNORECASE)
        role = role_match.group(1).lower() if role_match else ""
        if tag not in interactive and role not in {"button", "link", "tab", "menuitem"}:
            return ValidationResult(rule["id"], rule["severity"], False, message=f"aria-label overuse on <{tag}>", location=ctx.html_path)

        element_match = re.search(
            rf"<{tag}\b[^>]*\baria-label\s*=\s*\"[^\"]+\"[^>]*>(.*?)</{tag}>",
            ctx.html_text[matched.start():],
            re.IGNORECASE | re.DOTALL,
        )
        if element_match:
            inner_text = re.sub(r"<[^>]+>", "", element_match.group(1)).strip()
            if inner_text:
                return ValidationResult(
                    rule["id"],
                    rule["severity"],
                    False,
                    message=f"aria-label unnecessary on visible-text <{tag}>",
                    location=ctx.html_path,
                )
    return ValidationResult(rule["id"], rule["severity"], True)


def mobile_spacing_half(rule: dict, ctx: ValidationContext) -> ValidationResult:
    media_blocks = _extract_media_blocks(ctx.css_text)
    mobile_ranges = [(start, end) for header, _, start, end in media_blocks if re.search(r"max-width\s*:\s*768px", header, re.IGNORECASE)]
    mobile_css = "\n".join(body for header, body, _, _ in media_blocks if re.search(r"max-width\s*:\s*768px", header, re.IGNORECASE))
    if not mobile_css:
        return ValidationResult(rule["id"], rule["severity"], True)

    desktop_css = _remove_ranges(ctx.css_text, mobile_ranges)
    desktop_map = _extract_spacing_map(desktop_css)
    mobile_map = _extract_spacing_map(mobile_css)

    for key, mobile_value in mobile_map.items():
        desktop_value = desktop_map.get(key)
        if desktop_value is None:
            continue
        if mobile_value > (desktop_value * 0.7):
            selector, prop = key
            return ValidationResult(
                rule["id"],
                rule["severity"],
                False,
                message=f"mobile {prop} too large: {mobile_value}px vs desktop {desktop_value}px ({selector})",
                location=ctx.css_path,
            )
    return ValidationResult(rule["id"], rule["severity"], True)


def text_node_one_to_one(rule: dict, ctx: ValidationContext) -> ValidationResult:
    text_ids = re.findall(r'data-text-node-id\s*=\s*"([^"]+)"', ctx.html_text, re.IGNORECASE)
    if not text_ids:
        return ValidationResult(rule["id"], rule["severity"], True, message="no_data_text_node_id_marker")
    expanded: list[str] = []
    for raw in text_ids:
        expanded.extend(token.strip() for token in re.split(r"[,;]", raw) if token.strip())
    duplicates = [token for token in set(expanded) if expanded.count(token) > 1]
    if duplicates:
        return ValidationResult(rule["id"], rule["severity"], False, message=f"duplicate text-node mapping: {duplicates[0]}", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def no_adjacent_text_merge(rule: dict, ctx: ValidationContext) -> ValidationResult:
    merged_marker = re.search(r'data-text-node-id\s*=\s*"[^"]*[,;][^"]*"', ctx.html_text, re.IGNORECASE)
    if merged_marker:
        return ValidationResult(rule["id"], rule["severity"], False, message="multiple text node ids merged into one element", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def text_newline_preserved(rule: dict, ctx: ValidationContext) -> ValidationResult:
    has_newline_marker = bool(
        re.search(r'data-has-newline\s*=\s*"true"', ctx.html_text, re.IGNORECASE)
        or "\\n" in ctx.html_text
        or "&#10;" in ctx.html_text
    )
    if has_newline_marker and "<br" not in ctx.html_text.lower():
        return ValidationResult(rule["id"], rule["severity"], False, message="newline marker found but <br> missing", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def newline_converted_to_br(rule: dict, ctx: ValidationContext) -> ValidationResult:
    if ("\\n" in ctx.html_text or "&#10;" in ctx.html_text) and "<br" not in ctx.html_text.lower():
        return ValidationResult(rule["id"], rule["severity"], False, message="newline not converted to <br>", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def override_span_split_required(rule: dict, ctx: ValidationContext) -> ValidationResult:
    has_override_marker = "characterStyleOverrides" in ctx.html_text or "data-has-overrides=\"true\"" in ctx.html_text
    if has_override_marker and "<span" not in ctx.html_text.lower():
        return ValidationResult(rule["id"], rule["severity"], False, message="style overrides detected without span split", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def style_diff_span_required(rule: dict, ctx: ValidationContext) -> ValidationResult:
    has_style_diff = "data-style-diff=\"true\"" in ctx.html_text or "style-diff" in ctx.html_text
    if has_style_diff and "<span" not in ctx.html_text.lower():
        return ValidationResult(rule["id"], rule["severity"], False, message="style diff marker found without span split", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def no_style_flatten(rule: dict, ctx: ValidationContext) -> ValidationResult:
    mixed_style_marker = "mixed-style" in ctx.html_text or "characterStyleOverrides" in ctx.html_text
    if mixed_style_marker and "<span" not in ctx.html_text.lower():
        return ValidationResult(rule["id"], rule["severity"], False, message="mixed style marker found but spans are flattened", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def no_layout_info_loss(rule: dict, ctx: ValidationContext) -> ValidationResult:
    if not ctx.mapping:
        return ValidationResult(rule["id"], rule["severity"], True, message="mapping_not_provided")
    required_props: list[str] = []
    if _extract_mapping_values(ctx.mapping, "layoutMode"):
        required_props.append("flex-direction")
    if _extract_mapping_values(ctx.mapping, "itemSpacing"):
        required_props.append("gap")
    if _extract_mapping_values(ctx.mapping, "padding"):
        required_props.append("padding")
    missing = [prop for prop in required_props if not _extract_css_property_values(ctx.css_text, prop)]
    if missing:
        return ValidationResult(rule["id"], rule["severity"], False, message=f"layout mapping info missing in css: {', '.join(missing)}", location=ctx.css_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def visible_node_not_dropped(rule: dict, ctx: ValidationContext) -> ValidationResult:
    dropped_visible = re.search(
        r'data-visible\s*=\s*"true"[^>]*data-dropped\s*=\s*"true"|data-dropped\s*=\s*"true"[^>]*data-visible\s*=\s*"true"',
        ctx.html_text,
        re.IGNORECASE,
    )
    if dropped_visible:
        return ValidationResult(rule["id"], rule["severity"], False, message="visible node marked as dropped", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def divider_node_preserved(rule: dict, ctx: ValidationContext) -> ValidationResult:
    has_divider_css = bool(
        re.search(r"border-(?:top|bottom)\s*:\s*1px", ctx.css_text, re.IGNORECASE)
        or re.search(r"height\s*:\s*1px", ctx.css_text, re.IGNORECASE)
    )
    if not has_divider_css:
        return ValidationResult(rule["id"], rule["severity"], True)
    if not re.search(r'(class|id)\s*=\s*"[^"]*(divider|line|bar)[^"]*"', ctx.html_text, re.IGNORECASE):
        return ValidationResult(rule["id"], rule["severity"], False, message="divider-like css found but divider node missing", location=ctx.html_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def figma_values_pre_extracted(rule: dict, ctx: ValidationContext) -> ValidationResult:
    if ctx.mapping:
        return ValidationResult(rule["id"], rule["severity"], True)
    return ValidationResult(rule["id"], rule["severity"], False, message="mapping pre-extraction artifact missing")


def no_plausible_value_fill(rule: dict, ctx: ValidationContext) -> ValidationResult:
    combined = f"{ctx.html_text}\n{ctx.css_text}".lower()
    for token in ("tbd", "todo", "unknown", "guess", "plausible"):
        if token in combined:
            return ValidationResult(rule["id"], rule["severity"], False, message=f"plausible/fallback token found: {token}")
    return ValidationResult(rule["id"], rule["severity"], True)


def agent_distribution_enforced(rule: dict, ctx: ValidationContext) -> ValidationResult:
    combined = f"{ctx.html_text}\n{ctx.css_text}".lower()
    if "claude task" in combined or "delegate to claude" in combined:
        return ValidationResult(rule["id"], rule["severity"], False, message="forbidden delegation marker found")
    return ValidationResult(rule["id"], rule["severity"], True)


def coordinate_row_layout(rule: dict, ctx: ValidationContext) -> ValidationResult:
    if not ctx.mapping:
        return ValidationResult(rule["id"], rule["severity"], True, message="mapping_not_provided")
    layout_modes = {
        _normalize_css_value(str(mode))
        for mode in _extract_mapping_values(ctx.mapping, "layoutMode")
        if isinstance(mode, str)
    }
    if "horizontal" in layout_modes and "row" not in " ".join(_extract_css_property_values(ctx.css_text, "flex-direction")):
        return ValidationResult(rule["id"], rule["severity"], False, message="horizontal layoutMode not reflected as flex-direction: row", location=ctx.css_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def aspect_ratio_preferred(rule: dict, ctx: ValidationContext) -> ValidationResult:
    has_image_like_node = bool(re.search(r"<img\b|class=\"[^\"]*(img|card|thumb)[^\"]*\"", ctx.html_text, re.IGNORECASE))
    if has_image_like_node and "aspect-ratio" not in ctx.css_text:
        return ValidationResult(rule["id"], rule["severity"], False, message="image/card node found without aspect-ratio", location=ctx.css_path)
    return ValidationResult(rule["id"], rule["severity"], True)


def multiline_ellipsis_pattern(rule: dict, ctx: ValidationContext) -> ValidationResult:
    css_lower = ctx.css_text.lower()
    has_ellipsis = "ellipsis" in css_lower or "line-clamp" in css_lower
    if not has_ellipsis:
        return ValidationResult(rule["id"], rule["severity"], True)
    if "-webkit-line-clamp" in css_lower and "-webkit-box-orient" in css_lower:
        return ValidationResult(rule["id"], rule["severity"], True)
    return ValidationResult(rule["id"], rule["severity"], False, message="multi-line ellipsis missing standard line-clamp pattern", location=ctx.css_path)


LINE_HEIGHT_TIDY_CANDIDATES = [1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.45, 1.5, 1.6, 1.667, 1.75, 1.8, 2.0]
HEX8_LITERAL_RE = re.compile(r"#[0-9a-fA-F]{8}\b")


def _check_no_hex8_literal(rule: dict, ctx: ValidationContext) -> ValidationResult:
    ignore_ranges = _collect_comment_ranges(ctx.css_text) + _collect_data_url_ranges(ctx.css_text)
    matches = [match for match in HEX8_LITERAL_RE.finditer(ctx.css_text) if not _position_in_ranges(match.start(), ignore_ranges)]
    if not matches:
        return ValidationResult(rule["id"], rule["severity"], True)

    first = matches[0]
    line = _line_from_pos(ctx.css_text, first.start())
    return ValidationResult(
        rule["id"],
        rule["severity"],
        False,
        message=f"8-digit hex literal forbidden: {first.group(0)} (count={len(matches)})",
        location=f"{ctx.css_path}:{line}",
    )


def _check_line_height_tidy_ratio(rule: dict, ctx: ValidationContext) -> ValidationResult:
    candidate_set = {round(candidate, 3) for candidate in LINE_HEIGHT_TIDY_CANDIDATES}
    violations: list[tuple[str, str, int]] = []

    for match in re.finditer(r"line-height\s*:\s*([^;{}]+)", ctx.css_text, re.IGNORECASE):
        value = match.group(1).strip()
        line = _line_from_pos(ctx.css_text, match.start(1))

        line_start = ctx.css_text.rfind("\n", 0, match.start()) + 1
        line_end = ctx.css_text.find("\n", match.start())
        if line_end < 0:
            line_end = len(ctx.css_text)
        source_line = ctx.css_text[line_start:line_end]

        lowered = value.lower()
        if "/* lh-exact */" in source_line:
            continue
        if lowered == "1" or lowered == "normal" or lowered.startswith("var(--"):
            continue
        if not re.match(r"^-?\d+(?:\.\d+)?$", value):
            continue

        raw = round(float(value), 3)
        if raw in candidate_set:
            continue

        snapped = round(raw / 0.05) * 0.05
        if abs(raw - snapped) <= 0.03:
            suggestion = _normalize_number_token(round(snapped, 3))
        else:
            suggestion = _normalize_number_token(raw)
        violations.append((_normalize_number_token(raw), suggestion, line))

    if not violations:
        return ValidationResult(rule["id"], rule["severity"], True)

    first_raw, first_suggestion, first_line = violations[0]
    return ValidationResult(
        rule["id"],
        rule["severity"],
        False,
        message=f"line-height ratio not tidy: {first_raw} (suggest {first_suggestion}), total={len(violations)}",
        location=f"{ctx.css_path}:{first_line}",
    )


def _check_font_family_redundant(rule: dict, ctx: ValidationContext) -> ValidationResult:
    declarations = _iter_css_property_occurrences(ctx.css_text, "font-family")
    grouped: dict[str, list[tuple[str, int]]] = {}
    for selector, value, line in declarations:
        normalized_value = _normalize_css_value(value)
        grouped.setdefault(normalized_value, []).append((selector, line))

    candidates: list[tuple[str, int, int]] = []
    for font_chain, entries in grouped.items():
        count = len(entries)
        if count < 3:
            continue
        first_line = min(line for _, line in entries)
        candidates.append((font_chain, count, first_line))

    if not candidates:
        return ValidationResult(rule["id"], rule["severity"], True)

    font_chain, count, first_line = sorted(candidates, key=lambda item: item[1], reverse=True)[0]
    return ValidationResult(
        rule["id"],
        rule["severity"],
        False,
        message=f"font-family chain repeated {count} times: {font_chain}",
        location=f"{ctx.css_path}:{first_line}",
    )


def _check_empty_media_block(rule: dict, ctx: ValidationContext) -> ValidationResult:
    empty_lines: list[int] = []
    for header, body, start, _ in _extract_media_blocks(ctx.css_text):
        if re.search(r"@media\s+print\b", header, re.IGNORECASE):
            continue
        if _strip_css_comments(body).strip():
            continue
        empty_lines.append(_line_from_pos(ctx.css_text, start))

    if not empty_lines:
        return ValidationResult(rule["id"], rule["severity"], True)

    return ValidationResult(
        rule["id"],
        rule["severity"],
        False,
        message=f"empty media block detected: {len(empty_lines)}",
        location=f"{ctx.css_path}:{empty_lines[0]}",
    )


def _check_box_sizing_redundant(rule: dict, ctx: ValidationContext) -> ValidationResult:
    allowed_selectors = {"*", "*::before", "*::after", "*:before", "*:after"}
    declarations = _iter_css_property_occurrences(ctx.css_text, "box-sizing")

    universal_present = any(
        selector in allowed_selectors and _normalize_css_value(value) == "border-box"
        for selector, value, _ in declarations
    )
    if not universal_present:
        return ValidationResult(rule["id"], rule["severity"], True)

    redundant = [
        (selector, line)
        for selector, value, line in declarations
        if _normalize_css_value(value) == "border-box" and selector not in allowed_selectors
    ]
    if not redundant:
        return ValidationResult(rule["id"], rule["severity"], True)

    first_selector, first_line = redundant[0]
    return ValidationResult(
        rule["id"],
        rule["severity"],
        False,
        message=f"box-sizing:border-box redundant outside universal reset ({len(redundant)}): {first_selector}",
        location=f"{ctx.css_path}:{first_line}",
    )


def _discover_spec_json_files(ctx: "ValidationContext") -> list[str]:
    """Auto-discover *_spec.json files by walking up from the HTML path until an extracted/ dir is found."""
    import os
    start = os.path.dirname(os.path.abspath(ctx.html_path)) if getattr(ctx, "html_path", None) else os.getcwd()
    current = start
    for _ in range(6):
        for candidate_dir in ("extracted", os.path.join("..", "extracted"), os.path.join("..", "..", "extracted")):
            full = os.path.normpath(os.path.join(current, candidate_dir))
            if os.path.isdir(full):
                found = []
                for fname in sorted(os.listdir(full)):
                    if fname.endswith("_spec.json"):
                        found.append(os.path.join(full, fname))
                if found:
                    return found
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return []


def _extract_spec_text_slots(spec_paths: list[str]) -> list[tuple[str, tuple[str, ...]]]:
    """Return [(spec_file_name, (text1, text2, ...))] where each tuple is a slot.
    Texts at the same (bbox.x, bbox.y) position are treated as component variants:
    at least ONE of them must appear in HTML."""
    import json
    import os
    from collections import defaultdict

    slots_out: list[tuple[str, tuple[str, ...]]] = []
    for path in spec_paths:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue
        name = os.path.basename(path)

        # Group texts by rounded (x, y) — same position = component variants
        slot_groups: dict = defaultdict(list)
        unique_key_counter = 0
        for node in data.get("text_nodes", []) or []:
            chars = node.get("characters")
            if not isinstance(chars, str) or len(chars) <= 1:
                continue
            bbox = node.get("bbox") or {}
            x = bbox.get("x")
            y = bbox.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                key = (round(x / 3) * 3, round(y / 3) * 3)
            else:
                unique_key_counter += 1
                key = ("__no_bbox__", unique_key_counter)
            slot_groups[key].append(chars)

        for variants in slot_groups.values():
            # dedup within slot (same text appearing twice at same position)
            uniq = tuple(dict.fromkeys(variants))
            slots_out.append((name, uniq))
    return slots_out


def _normalize_for_text_match(value: str) -> str:
    """Normalize for text comparison: collapse whitespace variants, map <br> and \\n and &nbsp; to spaces, lowercase."""
    import re
    import html as _html
    s = _html.unescape(value)
    # Map <br>, <br/>, <br /> to \n first
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    s = re.sub(r"<[^>]+>", "", s)
    # All whitespace (incl. nbsp \xa0, \r, \n, tab) → single space
    s = re.sub(r"[\s\u00a0]+", " ", s)
    return s.strip().lower()


def _extract_html_text_blob(html_text: str) -> str:
    """Extract all visible text as a normalized single blob."""
    return _normalize_for_text_match(html_text)


def _check_text_from_spec_required(rule: dict, ctx: "ValidationContext") -> ValidationResult:
    """PLN-007 follow-up: each spec.json text slot (group of variants at same position) must have
    at least one variant appearing in HTML text. Prevents AI-invented text while allowing
    component variant overlaps."""
    spec_paths = _discover_spec_json_files(ctx)
    if not spec_paths:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="no spec.json discovered")

    slots = _extract_spec_text_slots(spec_paths)
    if not slots:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="no text_nodes in specs")

    html_blob = _extract_html_text_blob(ctx.html_text)

    missing_slots: list[tuple[str, tuple[str, ...]]] = []
    for spec_name, variants in slots:
        any_found = False
        for chars in variants:
            needle = _normalize_for_text_match(chars)
            if not needle or len(needle) < 2:
                any_found = True  # treat too-short as trivially satisfied
                break
            if needle in html_blob:
                any_found = True
                break
        if not any_found:
            missing_slots.append((spec_name, variants))

    if not missing_slots:
        return ValidationResult(rule["id"], rule["severity"], True)

    first_spec, first_variants = missing_slots[0]
    preview_parts: list[str] = []
    for v in first_variants[:3]:
        clean = v.replace("\n", "\\n").replace("\r", "\\r")
        if len(clean) > 40:
            clean = clean[:37] + "..."
        preview_parts.append(f"'{clean}'")
    preview = " | ".join(preview_parts)
    return ValidationResult(
        rule["id"],
        rule["severity"],
        False,
        message=f"Figma text slot missing in HTML (variants: {preview}) (spec={first_spec}, total_missing_slots={len(missing_slots)})",
        location=ctx.html_path,
    )


def _extract_root_var(css: str, var_name: str) -> str | None:
    """Extract `--var-name: value;` from :root block."""
    root_match = re.search(r":root\s*\{([^}]*)\}", css)
    if not root_match:
        return None
    m = re.search(rf"--{re.escape(var_name)}\s*:\s*([^;]+);", root_match.group(1))
    return m.group(1).strip() if m else None


def _extract_max_figma_content_width(html_path: str) -> int | None:
    """Read extracted/*_spec.json files and return max (inner frame width - paddingL - paddingR)."""
    import json as _json
    import os as _os
    if not html_path:
        return None
    start = _os.path.dirname(_os.path.abspath(html_path))
    current = start
    spec_files: list[str] = []
    for _ in range(6):
        for candidate_dir in ("extracted", _os.path.join("..", "extracted"), _os.path.join("..", "..", "extracted")):
            full = _os.path.normpath(_os.path.join(current, candidate_dir))
            if _os.path.isdir(full):
                for fname in sorted(_os.listdir(full)):
                    if fname.endswith("_spec.json"):
                        spec_files.append(_os.path.join(full, fname))
                break
        if spec_files:
            break
        parent = _os.path.dirname(current)
        if parent == current:
            break
        current = parent

    max_content = 0
    for path in spec_files:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = _json.load(fp)
        except Exception:
            continue
        for frame in data.get("frame_nodes", []) or []:
            bbox = frame.get("bbox") or {}
            width = bbox.get("w")
            pad_l = frame.get("paddingLeft")
            pad_r = frame.get("paddingRight")
            if not isinstance(width, (int, float)):
                continue
            if not isinstance(pad_l, (int, float)) or not isinstance(pad_r, (int, float)):
                continue
            inner = int(width - pad_l - pad_r)
            if inner > max_content:
                max_content = inner
    return max_content if max_content > 0 else None


def _check_section_width_formula(rule: dict, ctx: "ValidationContext") -> ValidationResult:
    """PLN-007 follow-up: enforce --width = figma_content + 40, --padding = 20px, .cont canonical pattern."""
    css = ctx.css_text

    # Step 1: :root must declare --width and --padding
    width_val = _extract_root_var(css, "width")
    padding_val = _extract_root_var(css, "padding")
    if not width_val:
        return ValidationResult(rule["id"], rule["severity"], False,
            message=":root --width 변수가 정의되지 않음. `--width: <figma_content + 40>px;` 필수",
            location=ctx.css_path)
    if not padding_val:
        return ValidationResult(rule["id"], rule["severity"], False,
            message=":root --padding 변수가 정의되지 않음. `--padding: 20px;` 필수",
            location=ctx.css_path)

    # Step 2: --padding must be 20px
    pad_num_match = re.match(r"^(\d+)\s*px\s*$", padding_val)
    if not pad_num_match or int(pad_num_match.group(1)) != 20:
        return ValidationResult(rule["id"], rule["severity"], False,
            message=f"--padding은 반드시 20px이어야 함 (현재 {padding_val}). 섹션 LR 안전 여백은 프로젝트 불변 고정값.",
            location=ctx.css_path)

    # Step 3: --width must equal (figma content width + 40) if spec.json discoverable
    expected_width: int | None = None
    content_width = _extract_max_figma_content_width(getattr(ctx, "html_path", "") or "")
    if content_width is not None:
        expected_width = content_width + 40
        width_num_match = re.match(r"^(\d+)\s*px\s*$", width_val)
        if not width_num_match or int(width_num_match.group(1)) != expected_width:
            return ValidationResult(rule["id"], rule["severity"], False,
                message=f"--width는 `figma_content_width + 40` 공식을 따라야 함. 기대: {expected_width}px (= {content_width} + 40), 현재: {width_val}",
                location=ctx.css_path)

    # Step 4: .cont rule must exist with canonical 4 properties
    cont_match = re.search(r"(?<!\S)\.cont\s*\{([^}]*)\}", css)
    if not cont_match:
        return ValidationResult(rule["id"], rule["severity"], False,
            message=".cont 클래스 규칙이 정의되지 않음. `.cont{width:100%; max-width:var(--width); margin:0 auto; padding:0 var(--padding);}` 필수",
            location=ctx.css_path)
    cont_body = cont_match.group(1)
    required = {
        "width": r"width\s*:\s*100%",
        "max-width": r"max-width\s*:\s*var\(\s*--width\s*\)",
        "margin": r"margin\s*:\s*0\s+auto",
        "padding": r"padding\s*:\s*0\s+var\(\s*--padding\s*\)",
    }
    for prop, pattern in required.items():
        if not re.search(pattern, cont_body):
            return ValidationResult(rule["id"], rule["severity"], False,
                message=f".cont 규칙에 필수 속성 누락/오류: `{prop}`. 정규 패턴: `.cont{{width:100%; max-width:var(--width); margin:0 auto; padding:0 var(--padding);}}`",
                location=ctx.css_path)

    # Step 5: sections with background must not declare max-width directly (use .cont child instead)
    # Detect `.main_xxx{... background ... max-width ...}` patterns
    section_violations: list[str] = []
    for section_match in re.finditer(r"(?<!\S)(\.main_[a-z_]+|\.footer_top|\.footer_bottom)\s*\{([^}]*)\}", css):
        selector = section_match.group(1)
        body = section_match.group(2)
        has_bg = bool(re.search(r"background(?:-color|-image)?\s*:", body))
        has_max_width = bool(re.search(r"max-width\s*:", body))
        if has_bg and has_max_width:
            section_violations.append(selector)

    if section_violations:
        return ValidationResult(rule["id"], rule["severity"], False,
            message=f"배경이 있는 섹션에 max-width 직접 선언 금지 (full-bleed 깨짐): {section_violations[0]}. 폭 제한은 섹션 내부 `.cont` 래퍼에만 적용",
            location=ctx.css_path)

    return ValidationResult(rule["id"], rule["severity"], True)


def _build_html_text_index(html_text: str) -> list:
    """Parse HTML once and return [(text_content, ancestor_chain_tuple)] for every text node.
    ancestor_chain_tuple = tuple of (tag, class_attr) from root to immediate parent."""
    from html.parser import HTMLParser

    class _Idx(HTMLParser):
        VOID_TAGS = {"br", "img", "meta", "link", "input", "hr", "area", "base", "col", "embed", "source", "track", "wbr"}

        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.index = []

        def handle_starttag(self, tag, attrs):
            if tag in self.VOID_TAGS:
                return
            cls = ""
            for k, v in attrs:
                if k == "class":
                    cls = v or ""
                    break
            self.stack.append((tag, cls))

        def handle_startendtag(self, tag, attrs):
            pass  # self-closing, ignore

        def handle_endtag(self, tag):
            while self.stack and self.stack[-1][0] != tag:
                self.stack.pop()
            if self.stack:
                self.stack.pop()

        def handle_data(self, data):
            text = data.strip()
            if text and self.stack:
                self.index.append((text, tuple(self.stack)))

    p = _Idx()
    try:
        p.feed(html_text)
    except Exception:
        return []
    return p.index


def _find_text_chain(html_index: list, needle: str) -> tuple | None:
    """Find the ancestor chain of the HTML text matching needle (substring)."""
    normalized_needle = re.sub(r"\s+", " ", needle).strip()
    if len(normalized_needle) < 2:
        return None
    for text, chain in html_index:
        normalized_text = re.sub(r"\s+", " ", text).strip()
        if normalized_needle in normalized_text or normalized_text in normalized_needle:
            return chain
    return None


def _chain_signature(chain: tuple, depth: int = 3) -> tuple:
    """Return the last `depth` ancestors' (tag, first_class) as a signature."""
    if not chain:
        return ()
    tail = chain[-depth:]
    return tuple((t, (c.split()[0] if c else "")) for t, c in tail)


_BLOCK_TAGS = {"div", "ul", "ol", "dl", "section", "nav", "header", "footer", "p", "article", "aside"}


def _get_block_parent(chain: tuple) -> tuple | None:
    """Return the nearest block-level ancestor as (tag, first_class)."""
    for tag, cls in reversed(chain):
        if tag in _BLOCK_TAGS:
            return (tag, (cls.split()[0] if cls else ""))
    return None


def _block_chain_classes(chain: tuple) -> list:
    """Extract ordered list of (tag, first_class) for block-level ancestors in chain."""
    return [(t, (c.split()[0] if c else "")) for t, c in chain if t in _BLOCK_TAGS]


def _extract_html_section_for_spec(html_text: str, spec_basename: str) -> str | None:
    """Extract HTML substring for the section corresponding to a spec file name.
    Returns None if no mapping or not found (caller should fall back to full HTML)."""
    spec_name = spec_basename.replace("_spec.json", "")
    # Name hint → HTML tag + class hint pattern
    scopes = {
        "footer":    (r'<footer[^>]*>(.*?)</footer>', None),
        "top_bar":   (r'<(section|div)[^>]*class="[^"]*top_bar[^"]*"[^>]*>(.*?)</\1>', 2),
        "header":    (r'<header[^>]*>(.*?)</header>', None),
        "mv":        (r'<section[^>]*class="[^"]*main_mv[^"]*"[^>]*>(.*?)</section>', None),
        "sec_1":     (r'<section[^>]*class="[^"]*main_product[^"]*"[^>]*>(.*?)</section>', None),
        "sec_2":     (r'<section[^>]*class="[^"]*main_news[^"]*"[^>]*>(.*?)</section>', None),
        "sec_3":     (r'<section[^>]*class="[^"]*main_company[^"]*"[^>]*>(.*?)</section>', None),
        "hero":      (r'<section[^>]*class="[^"]*index_hero[^"]*"[^>]*>(.*?)</section>', None),
        "adventure": (r'<section[^>]*class="[^"]*index_adventure[^"]*"[^>]*>(.*?)</section>', None),
        "intro":     (r'<section[^>]*class="[^"]*index_intro[^"]*"[^>]*>(.*?)</section>', None),
        "news":      (r'<section[^>]*class="[^"]*index_news[^"]*"[^>]*>(.*?)</section>', None),
        "price":     (r'<section[^>]*class="[^"]*index_price[^"]*"[^>]*>(.*?)</section>', None),
        "event":     (r'<section[^>]*class="[^"]*index_event[^"]*"[^>]*>(.*?)</section>', None),
    }
    spec_entry = scopes.get(spec_name)
    if not spec_entry:
        return None
    pattern, group_idx = spec_entry
    m = re.search(pattern, html_text, re.DOTALL)
    if not m:
        return None
    return m.group(group_idx or 1)


def _check_figma_text_row_grouping(rule: dict, ctx: "ValidationContext") -> ValidationResult:
    """Rule 2: Figma texts at same y-coordinate (horizontal row) must share the same
    nearest BLOCK-level HTML ancestor. Catches vertical stacking of row-layout texts.
    Scopes search per spec file to avoid cross-section text collisions."""
    import json as _json
    import os as _os

    spec_paths = _discover_spec_json_files(ctx)
    if not spec_paths:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="no spec.json")

    violations: list = []
    for path in spec_paths:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = _json.load(fp)
        except Exception:
            continue

        # Scope HTML to this section if mapping exists
        basename = _os.path.basename(path)
        scoped_html = _extract_html_section_for_spec(ctx.html_text, basename)
        html_scope = scoped_html if scoped_html is not None else ctx.html_text
        html_index = _build_html_text_index(html_scope)
        if not html_index:
            continue

        # Group text_nodes by rounded y (tolerance 5px)
        from collections import defaultdict
        by_y: dict = defaultdict(list)
        for tn in data.get("text_nodes", []) or []:
            ch = tn.get("characters", "")
            if not isinstance(ch, str) or len(ch) < 2:
                continue
            bbox = tn.get("bbox") or {}
            y = bbox.get("y")
            x = bbox.get("x")
            if not isinstance(y, (int, float)) or not isinstance(x, (int, float)):
                continue
            y_bucket = round(y / 5) * 5
            by_y[y_bucket].append((x, ch))

        for y_bucket, items in by_y.items():
            if len(items) < 2:
                continue
            # Require x-spread ≥ 100 to be confident it's an actual row (not clustered stack)
            xs = [x for x, _ in items]
            if max(xs) - min(xs) < 100:
                continue
            items_sorted = sorted(items, key=lambda t: t[0])
            chains = []
            for _x, text in items_sorted:
                chain = _find_text_chain(html_index, text)
                if chain is not None:
                    chains.append((text, chain))
            if len(chains) < 2:
                continue
            # Compute intersection of block-chain classes across all texts
            block_sets = [set(_block_chain_classes(c)) for _t, c in chains]
            # Exclude root-level tags that are always common (body, html)
            for s in block_sets:
                s.discard(("body", ""))
                s.discard(("html", ""))
            common = set.intersection(*block_sets) if block_sets else set()
            if not common:
                texts_preview = " / ".join(t[:25] for t, _ in chains[:3])
                violations.append(
                    f"{basename} y={y_bucket}: row [{texts_preview}] "
                    f"— 공통 block 조상 없음 (서로 다른 섹션/트리에 분리됨)"
                )

    if not violations:
        return ValidationResult(rule["id"], rule["severity"], True)
    hint = " — 같은 y의 텍스트는 HTML에서 같은 block 컨테이너 하위에 배치 필요"
    return ValidationResult(
        rule["id"], rule["severity"], False,
        message=f"Figma 가로 row → HTML 세로 stack 의심: {violations[0]}{hint} (total={len(violations)})",
        location=ctx.html_path,
    )


def _check_figma_dom_tree_structure_match(rule: dict, ctx: "ValidationContext") -> ValidationResult:
    """Rule 1: For each section's spec, verify HTML main section has corresponding direct children count
    matching Figma's top-level frame children. Loose match: count only."""
    import json as _json
    import os as _os
    spec_paths = _discover_spec_json_files(ctx)
    if not spec_paths:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="no spec.json")

    section_class_hints = {
        "mv": "main_mv", "sec_1": "main_product", "sec_2": "main_news",
        "sec_3": "main_company", "sec_4": "main_partner",
        "hero": "index_hero", "adventure": "index_adventure",
        "intro": "index_intro", "news": "index_news", "price": "index_price",
        "event": "index_event", "footer": "footer",
    }

    violations: list = []
    for path in spec_paths:
        name = _os.path.basename(path).replace("_spec.json", "")
        target_cls = section_class_hints.get(name)
        if not target_cls:
            continue
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = _json.load(fp)
        except Exception:
            continue
        frames = data.get("frame_nodes", []) or []
        if not frames:
            continue
        # Top-level frame = first frame (by convention, parent_id typically is section root)
        top_frame = frames[0]
        top_id = top_frame.get("id")
        # Direct children = frames whose parent_id == top_id
        direct_children = [f for f in frames if f.get("parent_id") == top_id]
        figma_child_count = len(direct_children)
        if figma_child_count == 0:
            continue

        # Find HTML section and count its direct children (div/ul/section/header/footer)
        sec_match = re.search(
            rf'<(section|footer|header|div)[^>]*class="[^"]*{re.escape(target_cls)}[^"]*"[^>]*>(.*?)</\1>',
            ctx.html_text, re.DOTALL,
        )
        if not sec_match:
            continue
        body = sec_match.group(2)
        # Count direct child elements (not nested). Use a simple regex approach
        html_child_count = 0
        depth = 0
        for m in re.finditer(r'<(/?)(\w+)[^>]*>', body):
            closing = m.group(1) == "/"
            tag = m.group(2)
            if tag in ("br", "img", "meta", "link", "input", "hr"):
                continue
            if closing:
                if depth > 0:
                    depth -= 1
            else:
                if depth == 0 and tag in ("div", "ul", "ol", "nav", "section", "footer", "header", "a", "p", "h1", "h2", "h3", "span", "strong"):
                    html_child_count += 1
                depth += 1
        # Tolerate moderate count differences (MV has decorative siblings, top-frame wrapper nesting varies)
        # Also only flag when HTML has FEWER children (missing content), not more (extra wrappers/decorations OK)
        if html_child_count < figma_child_count and (figma_child_count - html_child_count) >= 3:
            violations.append(
                f"{name} ({target_cls}): Figma top-frame has {figma_child_count} direct children, "
                f"HTML has only {html_child_count}"
            )

    if not violations:
        return ValidationResult(rule["id"], rule["severity"], True)
    return ValidationResult(
        rule["id"], rule["severity"], False,
        message=f"DOM 구조 카운트 불일치: {violations[0]} (total={len(violations)})",
        location=ctx.html_path,
    )


def _check_figma_element_parent_match(rule: dict, ctx: "ValidationContext") -> ValidationResult:
    """Rule 3: For landmark named frames (logo_b, btn_top, sns, etc.), verify their HTML parent
    chain corresponds to the Figma parent chain. Catches: top-btn inside footer_address when it
    should be a sibling."""
    import json as _json
    spec_paths = _discover_spec_json_files(ctx)
    if not spec_paths:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="no spec.json")

    html_index = _build_html_text_index(ctx.html_text)

    # Landmark frame name → expected HTML class hint
    landmarks = {
        "btn_top": ("footer_top_btn", ("footer_info", "footer", "cont")),
        "logo_b": ("logo", ("footer_top", "footer", "cont")),
        "sns": ("footer_sns", ("footer_info", "footer", "footer_col_left")),
    }

    violations: list = []
    for path in spec_paths:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = _json.load(fp)
        except Exception:
            continue
        for fn in data.get("frame_nodes", []) or []:
            fn_name = (fn.get("name") or "").lower()
            if fn_name not in landmarks:
                continue
            html_cls, expected_ancestors = landmarks[fn_name]
            # Find this class in HTML and check its ancestor chain
            found = False
            for text, chain in html_index:
                for ancestor in chain:
                    if html_cls in (ancestor[1] or "").split():
                        found = True
                        # Check at least one expected ancestor is present in chain
                        chain_classes = set()
                        for _t, cls in chain:
                            for c in (cls or "").split():
                                chain_classes.add(c)
                        # Not strict: just check at least one expected is in chain
                        if not any(exp in chain_classes for exp in expected_ancestors):
                            violations.append(
                                f"{fn_name} (.{html_cls}): HTML 부모 체인에 기대 조상 {expected_ancestors} 중 하나도 없음"
                            )
                        break
                if found:
                    break

    if not violations:
        return ValidationResult(rule["id"], rule["severity"], True)
    return ValidationResult(
        rule["id"], rule["severity"], False,
        message=f"Figma 요소 부모 체인 불일치: {violations[0]} (total={len(violations)})",
        location=ctx.html_path,
    )


def _compute_card_slots_from_spec(spec_data: dict) -> tuple[int, int, int]:
    """Return (unique_slot_count, total_card_frames, variant_overlap_count) for cards in a section spec.
    Heuristic: 'txt' frames with width 200..700; the most common width is the card width;
    unique bbox.x (bucketed to 5px) at that width = slot count."""
    from collections import Counter
    width_counts: Counter = Counter()
    frames_by_width: dict = {}
    for fn in spec_data.get("frame_nodes", []) or []:
        if fn.get("name") != "txt":
            continue
        bbox = fn.get("bbox") or {}
        w = bbox.get("w")
        x = bbox.get("x")
        if not isinstance(w, (int, float)) or not isinstance(x, (int, float)):
            continue
        if not (200 <= w <= 700):
            continue
        width_counts[w] += 1
        frames_by_width.setdefault(w, []).append(x)
    if not width_counts:
        return (0, 0, 0)
    card_width, card_count = width_counts.most_common(1)[0]
    if card_count < 2:
        return (0, 0, 0)
    x_positions = {round(x / 5) * 5 for x in frames_by_width[card_width]}
    unique_slots = len(x_positions)
    return (unique_slots, card_count, card_count - unique_slots)


def _extract_main_sections_from_html(html: str) -> list:
    """Return [(class_name, section_inner_html)] for each <section class='main_*'> in order."""
    sections: list = []
    for m in re.finditer(r'<section[^>]*class="([^"]*)"[^>]*>(.*?)</section>', html, re.DOTALL):
        classes = m.group(1)
        main_class = None
        for cls in classes.split():
            if cls.startswith("main_"):
                main_class = cls
                break
        if main_class:
            sections.append((main_class, m.group(2)))
    return sections


def _count_list_items_in_section(section_html: str) -> int:
    """Count the largest single <ul>'s direct <li> children in a section body."""
    counts: list = []
    for ul_match in re.finditer(r'<ul[^>]*>(.*?)</ul>', section_html, re.DOTALL):
        body = ul_match.group(1)
        counts.append(len(re.findall(r'<li\b', body)))
    return max(counts) if counts else 0


def _check_figma_cardinality_match(rule: dict, ctx: "ValidationContext") -> ValidationResult:
    """Compare Figma spec card slot count vs HTML <li> count per main section.
    Catches variant-overlap confusion (HTML treats component variants as separate cards)."""
    import json as _json
    import os as _os

    spec_paths = _discover_spec_json_files(ctx)
    if not spec_paths:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="no spec.json")

    def _spec_sort_key(path: str):
        name = _os.path.basename(path)
        m = re.search(r"sec_(\d+)", name)
        if m:
            return (1, int(m.group(1)))
        if name.startswith("mv"):
            return (0, 0)
        if name.startswith("footer"):
            return (9, 0)
        return (5, name)

    ordered_specs = sorted(spec_paths, key=_spec_sort_key)
    expected: list = []
    for path in ordered_specs:
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = _json.load(fp)
        except Exception:
            continue
        slots, total, variants = _compute_card_slots_from_spec(data)
        if slots >= 2:
            expected.append((_os.path.basename(path).replace("_spec.json", ""), slots, variants))

    if not expected:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="no card-bearing specs found")

    main_sections = _extract_main_sections_from_html(ctx.html_text)
    if not main_sections:
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="no main_* sections in HTML")

    # main_mv is a hero; its mv_cards are decorative indicators, not content cards → exclude
    ignored_html_sections = {"main_mv"}
    cardful_sections = [(cls, _count_list_items_in_section(body)) for cls, body in main_sections]
    cardful_sections = [(cls, n) for cls, n in cardful_sections if n >= 2 and cls not in ignored_html_sections]

    if len(cardful_sections) != len(expected):
        return ValidationResult(
            rule["id"], rule["severity"], False,
            message=f"main section count mismatch: Figma {len(expected)} card-bearing specs "
                    f"({[e[0] for e in expected]}) vs HTML {len(cardful_sections)} cardful main sections "
                    f"({[s[0] for s in cardful_sections]})",
            location=ctx.html_path,
        )

    violations: list = []
    for (spec_name, slots, variants), (sec_cls, li_count) in zip(expected, cardful_sections):
        if li_count != slots:
            detail = (
                f"{spec_name} → {sec_cls}: Figma {slots} card slot(s)"
                + (f" [variant overlap={variants}]" if variants else "")
                + f" vs HTML {li_count} <li>"
            )
            violations.append(detail)

    if not violations:
        return ValidationResult(rule["id"], rule["severity"], True)

    hint = " — component variant(상태 중복)를 별개 카드로 오인했는지 확인"
    return ValidationResult(
        rule["id"], rule["severity"], False,
        message=f"Figma slot count mismatch: {violations[0]}{hint} (total_violations={len(violations)})",
        location=ctx.html_path,
    )


def _check_landing_unit_mixed_scale(rule: dict, ctx: ValidationContext) -> ValidationResult:
    if ctx.profile != "landing":
        return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="profile_not_landing")

    offenders: list[tuple[str, str, int]] = []
    for selector, value, line in _iter_css_property_occurrences(ctx.css_text, "font-size"):
        if selector not in {"html", "body"}:
            continue
        lowered = _normalize_css_value(value)
        if any(token in lowered for token in ("clamp(", "vw", "rem", "calc(")):
            offenders.append((selector, value, line))

    if not offenders:
        return ValidationResult(rule["id"], rule["severity"], True)

    first_selector, first_value, first_line = offenders[0]
    return ValidationResult(
        rule["id"],
        rule["severity"],
        False,
        message=f"landing font-size must be fixed px on html/body: {first_selector} -> {first_value}",
        location=f"{ctx.css_path}:{first_line}",
    )


# ===== CUSTOM HANDLERS =====

def _stub_handler(rule: dict, _ctx: ValidationContext) -> ValidationResult:
    handler_name = _resolve_custom_handler_name(rule) or "unknown"
    return ValidationResult(
        rule["id"],
        "warning",
        False,
        skipped=False,
        message=f"[STUB-PASS BLOCKED] handler {handler_name} not implemented — treating as MAJOR FAIL",
    )


def check_no_column_gap(rule: dict, ctx: ValidationContext) -> ValidationResult:
    """Detect `flex-direction:column` blocks that also use `gap`. Vertical spacing should use margin, not gap."""
    violations: list[str] = []
    for block_match in re.finditer(r"([^{}]+)\{([^{}]*)\}", ctx.css_text):
        selector = block_match.group(1).strip()
        body = block_match.group(2)
        if not selector or selector.startswith("@"):
            continue
        has_column = bool(re.search(r"flex-direction\s*:\s*column", body))
        if not has_column:
            continue
        gap_match = re.search(r"(?<!row-)(?<!column-)\bgap\s*:\s*([^;]+);", body)
        if gap_match:
            gap_value = gap_match.group(1).strip()
            if gap_value not in {"0", "0px", "0 0", "0px 0px"}:
                violations.append(f"{selector} → gap:{gap_value}")

    if violations:
        return ValidationResult(
            rule["id"],
            rule["severity"],
            False,
            message=f"flex-direction:column에 gap 사용 금지 (수직 여백은 margin 사용): {violations[0]}",
            location=ctx.css_path,
        )
    return ValidationResult(rule["id"], rule["severity"], True)


def item_spacing_reflected(rule: dict, _ctx: ValidationContext) -> ValidationResult:
    # mapping-dependent; skip when no mapping context
    return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="mapping not loaded")


def enforce_policy1_vertical_margin_bottom(rule: dict, ctx: ValidationContext) -> ValidationResult:
    return check_no_column_gap(rule, ctx)


def enforce_policy2_constraints_extract_only(rule: dict, _ctx: ValidationContext) -> ValidationResult:
    return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="validated_by_figma_validate")


def enforce_policy3_rules_conflict_bypass(rule: dict, _ctx: ValidationContext) -> ValidationResult:
    return ValidationResult(rule["id"], rule["severity"], True, skipped=True, message="validated_by_figma_validate")


CUSTOM_HANDLERS: Dict[str, Callable] = {
    "check_no_column_gap": _safe_custom_handler(check_no_column_gap),
    "no_column_flex_gap": _safe_custom_handler(check_no_column_gap),
    "item_spacing_reflected": item_spacing_reflected,
    "enforce_policy1_vertical_margin_bottom": _safe_custom_handler(enforce_policy1_vertical_margin_bottom),
    "enforce_policy2_constraints_extract_only": _safe_custom_handler(enforce_policy2_constraints_extract_only),
    "enforce_policy3_rules_conflict_bypass": _safe_custom_handler(enforce_policy3_rules_conflict_bypass),
    # direct check_* compatibility
    "check_nav_structure": _adapt_legacy_check(check_nav_structure),
    "check_img_wrapper": _adapt_legacy_check(check_img_wrapper),
    "check_inline_style": _adapt_legacy_check(check_inline_style),
    "check_forbidden_tags": _adapt_legacy_check(check_forbidden_tags),
    "check_list_pattern": _adapt_legacy_check(check_list_pattern),
    "check_p_tag_misuse": _adapt_legacy_check(check_p_tag_misuse),
    "check_css_grid": _adapt_legacy_check(check_css_grid),
    "check_important": _adapt_legacy_check(check_important),
    "check_border_radius_999": _adapt_legacy_check(check_border_radius_999),
    "check_color_format": _adapt_legacy_check(check_color_format),
    "check_max_width_pattern": _adapt_legacy_check(check_max_width_pattern),
    "check_reset_duplicate": _adapt_legacy_check(check_reset_duplicate),
    "check_word_break": _adapt_legacy_check(check_word_break),
    "check_font_size_base": _adapt_legacy_check(check_font_size_base),
    "check_root_vars": _adapt_legacy_check(check_root_vars),
    "check_reset_css": _adapt_legacy_check(check_reset_css),
    "check_selector_format": _adapt_legacy_check(check_selector_format),
    "check_empty_div": _adapt_legacy_check(check_empty_div),
    "check_dom_depth": _adapt_legacy_check(check_dom_depth),
    "check_snake_case_classes": _adapt_legacy_check(check_snake_case_classes),
    "check_duplicate_selectors": _adapt_legacy_check(check_duplicate_selectors),
    "check_line_height_px": _adapt_legacy_check(check_line_height_px),
    "check_letter_spacing_unit": _adapt_legacy_check(check_letter_spacing_unit),
    "check_clamp_under_100": _adapt_legacy_check(check_clamp_under_100),
    "check_raw_calc_vw": _adapt_legacy_check(check_raw_calc_vw),
    "check_media_indent": _adapt_legacy_check(check_media_indent),
    "check_utility_classes": _adapt_legacy_check(check_utility_classes),
    "check_common_area_prefix": _adapt_legacy_check(check_common_area_prefix),
    "check_excessive_individual_classes": _adapt_legacy_check(check_excessive_individual_classes),
    "check_generic_class_names": _adapt_legacy_check(check_generic_class_names),
    "check_body_page_class": _adapt_legacy_check(check_body_page_class),
    "check_image_naming": _adapt_legacy_check(check_image_naming),
    "check_large_side_padding": _adapt_legacy_check(check_large_side_padding),
    # REQ-019 new custom checks
    "_check_no_hex8_literal": _safe_custom_handler(_check_no_hex8_literal),
    "_check_line_height_tidy_ratio": _safe_custom_handler(_check_line_height_tidy_ratio),
    "_check_font_family_redundant": _safe_custom_handler(_check_font_family_redundant),
    "_check_empty_media_block": _safe_custom_handler(_check_empty_media_block),
    "_check_box_sizing_redundant": _safe_custom_handler(_check_box_sizing_redundant),
    "_check_landing_unit_mixed_scale": _safe_custom_handler(_check_landing_unit_mixed_scale),
    "no_hex8_literal": _safe_custom_handler(_check_no_hex8_literal),
    "line_height_tidy_ratio": _safe_custom_handler(_check_line_height_tidy_ratio),
    "font_family_redundant": _safe_custom_handler(_check_font_family_redundant),
    "empty_media_block": _safe_custom_handler(_check_empty_media_block),
    "box_sizing_redundant": _safe_custom_handler(_check_box_sizing_redundant),
    "landing_unit_mixed_scale": _safe_custom_handler(_check_landing_unit_mixed_scale),
    # PLN-007 follow-up: auto-discovered Figma text fidelity (prevents AI text invention)
    "text_from_spec_required": _safe_custom_handler(_check_text_from_spec_required),
    "_check_text_from_spec_required": _safe_custom_handler(_check_text_from_spec_required),
    # PLN-007 follow-up: section width formula enforcement
    "section_width_formula": _safe_custom_handler(_check_section_width_formula),
    "_check_section_width_formula": _safe_custom_handler(_check_section_width_formula),
    # PLN-007 follow-up: figma card slot count vs HTML li count
    "figma_cardinality_match": _safe_custom_handler(_check_figma_cardinality_match),
    "_check_figma_cardinality_match": _safe_custom_handler(_check_figma_cardinality_match),
    # PLN-007 follow-up: structural checks (DOM tree / text row / parent match)
    "figma_dom_tree_structure_match": _safe_custom_handler(_check_figma_dom_tree_structure_match),
    "_check_figma_dom_tree_structure_match": _safe_custom_handler(_check_figma_dom_tree_structure_match),
    "figma_text_row_grouping": _safe_custom_handler(_check_figma_text_row_grouping),
    "_check_figma_text_row_grouping": _safe_custom_handler(_check_figma_text_row_grouping),
    "figma_element_parent_match": _safe_custom_handler(_check_figma_element_parent_match),
    "_check_figma_element_parent_match": _safe_custom_handler(_check_figma_element_parent_match),
    # rule-id based aliases from rules.yaml
    "nav_ul_li_structure": _adapt_legacy_check(check_nav_structure),
    "img_wrapped": _adapt_legacy_check(check_img_wrapper),
    "list_pattern_required": _adapt_legacy_check(check_list_pattern),
    "p_tag_misuse": _adapt_legacy_check(check_p_tag_misuse),
    "common_area_prefix": _adapt_legacy_check(check_common_area_prefix),
    "selector_single_line": _adapt_legacy_check(check_selector_format),
    "no_duplicate_selector": _adapt_legacy_check(check_duplicate_selectors),
    "media_query_format": _adapt_legacy_check(check_media_indent),
    "no_media_indent": _adapt_legacy_check(check_media_indent),
    "no_clamp_under_100": _adapt_legacy_check(check_clamp_under_100),
    "no_raw_calc": _adapt_legacy_check(check_raw_calc_vw),
    "no_raw_vw": _adapt_legacy_check(check_raw_calc_vw),
    "large_side_padding": _adapt_legacy_check(check_large_side_padding),
    "max_width_pattern": _adapt_legacy_check(check_max_width_pattern),
    "no_important": _adapt_legacy_check(check_important),
    "letter_spacing_unit": _adapt_legacy_check(check_letter_spacing_unit),
    "excessive_individual_classes": _adapt_legacy_check(check_excessive_individual_classes),
    "reset_duplicate": _adapt_legacy_check(check_reset_duplicate),
    "img_naming": _adapt_legacy_check(check_image_naming),
    # T02 implementations (formerly stubbed by id fallback)
    "manual_review": _safe_custom_handler(manual_review),
    "page_filename_class_prefix_match": _safe_custom_handler(page_filename_class_prefix_match),
    "root_var_naming": _safe_custom_handler(root_var_naming),
    "selector_scoped": _safe_custom_handler(selector_scoped),
    "img_alt_concise": _safe_custom_handler(img_alt_concise),
    "minimal_aria": _safe_custom_handler(minimal_aria),
    "mobile_spacing_half": _safe_custom_handler(mobile_spacing_half),
    "text_node_one_to_one": _safe_custom_handler(text_node_one_to_one),
    "no_adjacent_text_merge": _safe_custom_handler(no_adjacent_text_merge),
    "text_newline_preserved": _safe_custom_handler(text_newline_preserved),
    "newline_converted_to_br": _safe_custom_handler(newline_converted_to_br),
    "override_span_split_required": _safe_custom_handler(override_span_split_required),
    "style_diff_span_required": _safe_custom_handler(style_diff_span_required),
    "no_style_flatten": _safe_custom_handler(no_style_flatten),
    "no_layout_info_loss": _safe_custom_handler(no_layout_info_loss),
    "visible_node_not_dropped": _safe_custom_handler(visible_node_not_dropped),
    "divider_node_preserved": _safe_custom_handler(divider_node_preserved),
    "figma_values_pre_extracted": _safe_custom_handler(figma_values_pre_extracted),
    "no_plausible_value_fill": _safe_custom_handler(no_plausible_value_fill),
    "agent_distribution_enforced": _safe_custom_handler(agent_distribution_enforced),
    "coordinate_row_layout": _safe_custom_handler(coordinate_row_layout),
    "aspect_ratio_preferred": _safe_custom_handler(aspect_ratio_preferred),
    "multiline_ellipsis_pattern": _safe_custom_handler(multiline_ellipsis_pattern),
    # Alias IDs that point to existing legacy handlers via rule.validation.custom_handler
    "font_size_pc_rem": _adapt_legacy_check(check_font_size_base),
    "root_var_line_separated": _adapt_legacy_check(check_root_vars),
    "p_tag_condition_enforced": _adapt_legacy_check(check_p_tag_misuse),
}


def _register_stubs(rules: list[dict]) -> None:
    for rule in rules:
        if rule.get("validation", {}).get("type") != "custom":
            continue
        handler_name = _resolve_custom_handler_name(rule)
        if not handler_name:
            continue
        if handler_name not in CUSTOM_HANDLERS:
            CUSTOM_HANDLERS[handler_name] = _stub_handler


# ===== ENGINE =====

def _load_mapping(mapping_path: Optional[str]) -> Optional[dict]:
    if not mapping_path:
        return None
    path = Path(mapping_path)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text)


def _rule_applies(rule: dict, profile: str) -> bool:
    if profile == "all":
        return True
    applies = rule.get("applies_to", [])
    if not applies:
        return True
    if profile in applies:
        return True
    if profile in {"basic", "landing"} and "common" in applies:
        return True
    return False


def _iter_parent_dirs(path: str) -> list[Path]:
    if not path:
        return []
    candidate = Path(path).expanduser()
    start = candidate if candidate.is_dir() else candidate.parent
    return [start, *start.parents]


def _resolve_profile_from_project_type(html_path: str, css_path: str) -> str:
    search_roots: list[Path] = []
    search_roots.extend(_iter_parent_dirs(html_path))
    search_roots.extend(_iter_parent_dirs(css_path))
    search_roots.extend(_iter_parent_dirs(os.getcwd()))

    visited: set[str] = set()
    for root in search_roots:
        root_key = str(root.resolve()) if root.exists() else str(root)
        if root_key in visited:
            continue
        visited.add(root_key)

        marker = root / ".project-type"
        if not marker.exists():
            continue
        value = marker.read_text(encoding="utf-8").strip().lower()
        if value in {"basic", "landing"}:
            return value
    return "all"


def run_validation(
    rules_path: str,
    html_path: str,
    css_path: str,
    profile: str = "all",
    mapping_path: Optional[str] = None,
    img_dir: Optional[str] = None,
) -> list[ValidationResult]:
    with open(rules_path, encoding="utf-8") as file:
        rules_data = yaml.safe_load(file) or {}

    rules = rules_data.get("rules", [])
    _register_stubs(rules)

    html_text = Path(html_path).read_text(encoding="utf-8") if os.path.exists(html_path) else ""
    css_text = Path(css_path).read_text(encoding="utf-8") if os.path.exists(css_path) else ""

    ctx = ValidationContext(
        html_text=html_text,
        css_text=css_text,
        html_path=html_path,
        css_path=css_path,
        profile=profile,
        mapping=_load_mapping(mapping_path),
        img_dir=img_dir,
    )

    results: list[ValidationResult] = []
    for rule in rules:
        if not _rule_applies(rule, profile):
            continue

        validation = rule.get("validation", {})
        vtype = validation.get("type")
        if not vtype:
            continue

        if vtype == "custom":
            handler_name = _resolve_custom_handler_name(rule)
            handler = CUSTOM_HANDLERS.get(handler_name, _stub_handler)
            results.append(handler(rule, ctx))
            continue

        enum_handler = ENUM_VALIDATORS.get(vtype)
        if not enum_handler:
            results.append(
                ValidationResult(
                    rule_id=rule.get("id", "unknown"),
                    severity=rule.get("severity", "info"),
                    passed=True,
                    skipped=True,
                    message=f"unknown_validation_type: {vtype}",
                )
            )
            continue

        results.append(enum_handler(rule, ctx))

    return results


def _severity_to_display(severity: str) -> str:
    if severity == "error":
        return "CRITICAL"
    if severity == "warning":
        return "MAJOR"
    return "MINOR"


def _parse_location(location: Optional[str]) -> tuple[str, int]:
    if not location:
        return "", 0
    match = re.match(r"^(.*):(\d+)$", location)
    if not match:
        return location, 0
    return match.group(1), int(match.group(2))


def _result_to_violation(result: ValidationResult) -> Violation:
    file_path, line = _parse_location(result.location)
    return Violation(
        rule=result.rule_id,
        severity=_severity_to_display(result.severity),
        message=result.message,
        line=line,
        file=file_path,
    )


def _run_auto_fix(html_path: str, css_path: str) -> dict[str, object]:
    tools_dir = Path(__file__).resolve().parent
    report_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="validate-fix-", suffix=".json", delete=False) as temp_file:
            report_path = Path(temp_file.name)
        command = [
            sys.executable,
            str(tools_dir / "repair-from-violations.py"),
            "--html",
            html_path,
            "--css",
            css_path,
            "--report",
            str(report_path),
        ]
        proc = subprocess.run(command, text=True, capture_output=True, check=False)
        payload: dict[str, object] = {}
        if report_path.exists():
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        payload["exit_code"] = proc.returncode
        payload["raw_output"] = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
        return payload
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "total_fixed": 0,
            "by_category": {},
            "files_modified": [],
            "unfixable_count": 0,
            "dry_run": False,
            "exit_code": 2,
            "raw_output": str(exc),
        }
    finally:
        if report_path and report_path.exists():
            report_path.unlink(missing_ok=True)


def _render_auto_fix_line(result: dict[str, object]) -> str:
    by_category = result.get("by_category", {})
    category_summary = "none"
    if isinstance(by_category, dict):
        non_zero = [f"{key}:{value}" for key, value in by_category.items() if int(value) > 0]
        if non_zero:
            category_summary = ", ".join(non_zero)
    return f"[auto-fix] {result.get('total_fixed', 0)} violations fixed (category: {category_summary})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate semantic HTML/CSS against project rules")
    parser.add_argument("--html", required=True, help="HTML file path")
    parser.add_argument("--css", required=True, help="CSS file path")
    parser.add_argument("--img", help="Image directory path")
    parser.add_argument("--fix", action="store_true", help="Run deterministic auto-fix before validation")
    parser.add_argument(
        "--profile",
        choices=["all", "basic", "landing"],
        help="Validation profile (default: auto from .project-type, fallback: all)",
    )
    parser.add_argument("--mapping", help="mapping.json path (T02)")
    parser.add_argument("--rules", default="rules/rules.yaml", help="Rules YAML path")
    args = parser.parse_args()
    resolved_profile = args.profile or _resolve_profile_from_project_type(args.html, args.css)

    if args.fix:
        auto_fix_result = _run_auto_fix(args.html, args.css)
        print(_render_auto_fix_line(auto_fix_result))

    results = run_validation(
        rules_path=args.rules,
        html_path=args.html,
        css_path=args.css,
        profile=resolved_profile,
        mapping_path=args.mapping,
        img_dir=args.img,
    )

    violations = [_result_to_violation(result) for result in results if not result.passed and not result.skipped]

    if not violations:
        print("✅ ALL PASS — 위반 사항 없음")
        skipped_count = sum(1 for result in results if result.skipped)
        if skipped_count:
            print(f"(참고) skipped: {skipped_count}")
        sys.exit(0)

    critical = [violation for violation in violations if violation.severity == "CRITICAL"]
    major = [violation for violation in violations if violation.severity == "MAJOR"]
    minor = [violation for violation in violations if violation.severity == "MINOR"]

    print(f"=== 검증 결과: {len(violations)}건 위반 ===")
    print(f"CRITICAL: {len(critical)} | MAJOR: {len(major)} | MINOR: {len(minor)}")
    print()

    for violation in violations:
        print(violation)

    skipped_count = sum(1 for result in results if result.skipped)
    if skipped_count:
        print(f"\n(skipped custom/enum checks: {skipped_count})")

    print()
    if critical:
        print("❌ CRITICAL 위반이 있습니다. 반드시 수정하세요.")
        sys.exit(2)
    if major:
        print("⚠️  MAJOR 위반이 있습니다. 수정을 권장합니다.")
        sys.exit(1)

    print("ℹ️  MINOR 위반만 있습니다.")
    sys.exit(0)


if __name__ == "__main__":
    main()

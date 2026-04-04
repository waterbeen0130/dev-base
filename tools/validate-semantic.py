#!/usr/bin/env python3
"""Post-generation validator for semantic HTML/CSS.

Checks generated HTML/CSS against rules defined in:
- rules/common.md
- rules/semantic-transform-rules.md

Usage:
  python3 tools/validate-semantic.py --html output/index.html --css output/common.css
  python3 tools/validate-semantic.py --html output/index.html --css output/common.css --fix
"""

import argparse
import os
import re
import sys
from pathlib import Path


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
    def __init__(self):
        self.violations: list[Violation] = []

    def _add(self, rule: str, severity: str, message: str, line: int = 0, file: str = ""):
        self.violations.append(Violation(rule, severity, message, line, file))

    # ===== HTML Checks =====

    def check_nav_structure(self, html: str, filepath: str):
        """nav 안에 ul>li>a 구조가 아닌 직접 a 태그가 있는지 확인"""
        lines = html.split("\n")
        in_nav = False
        nav_line = 0
        for i, line in enumerate(lines, 1):
            if "<nav" in line:
                in_nav = True
                nav_line = i
            if "</nav>" in line:
                in_nav = False
            if in_nav and "<a " in line and "<li>" not in line and "<li><a" not in line:
                # nav 안에서 li 없이 직접 a 태그 사용
                prev_lines = "\n".join(lines[max(0, i-3):i])
                if "<ul>" not in prev_lines and "<li>" not in prev_lines:
                    self._add("nav-ul-li", "CRITICAL",
                              f"nav 안에 ul>li 없이 직접 <a> 사용 (규칙: nav > ul > li > a)",
                              i, filepath)

    def check_img_wrapper(self, html: str, filepath: str):
        """콘텐츠 이미지가 img_area 래퍼 없이 사용되는지 확인 (배경/로고/아이콘 제외)"""
        lines = html.split("\n")
        for i, line in enumerate(lines, 1):
            if "<img " not in line:
                continue
            # 배경 이미지 (bg 클래스 안), 로고, 인라인 아이콘은 제외
            if any(skip in line for skip in ["_bg", "logo", "ic_", "sns_", "alt=\"메뉴\""]):
                continue
            # img가 p 태그 안 인라인이면 제외
            if "<p>" in line or "<p " in line:
                continue
            # img_area 래퍼 확인
            if "img_area" not in line:
                prev = lines[max(0, i-2):i]
                if not any("img_area" in p for p in prev):
                    self._add("img-wrapper", "MAJOR",
                              f"이미지에 img_area 래퍼 없음: {line.strip()[:60]}",
                              i, filepath)

    def check_inline_style(self, html: str, filepath: str):
        """인라인 스타일 사용 확인"""
        for i, line in enumerate(html.split("\n"), 1):
            if 'style="' in line:
                self._add("no-inline-style", "CRITICAL",
                           f"인라인 스타일 사용: {line.strip()[:60]}", i, filepath)

    def check_forbidden_tags(self, html: str, filepath: str):
        """금지된 HTML 태그 확인"""
        forbidden = ["<figure", "<figcaption", "<main", "<article"]
        for i, line in enumerate(html.split("\n"), 1):
            for tag in forbidden:
                if tag in line.lower():
                    self._add("forbidden-tag", "CRITICAL",
                              f"금지된 태그 사용: {tag}", i, filepath)

    def check_list_pattern(self, html: str, filepath: str):
        """반복 a 태그가 ul>li 없이 나열되는지 확인"""
        lines = html.split("\n")
        consecutive_a = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'^<a\s', stripped):
                consecutive_a += 1
            else:
                if consecutive_a >= 2:
                    self._add("list-pattern", "MAJOR",
                              f"연속 <a> {consecutive_a}개 — ul>li 구조 필요", i - 1, filepath)
                consecutive_a = 0

    def check_p_tag_misuse(self, html: str, filepath: str):
        """짧은 텍스트에 <p> 태그 사용 확인"""
        for i, line in enumerate(html.split("\n"), 1):
            match = re.search(r'<p[^>]*>([^<]+)</p>', line)
            if match:
                text = match.group(1).strip()
                if len(text) < 20 and "\n" not in text and not text.endswith(("다.", "요.", "다", "요")):
                    self._add("p-tag-misuse", "MINOR",
                              f"짧은 텍스트에 <p> 사용: \"{text}\"", i, filepath)

    # ===== CSS Checks =====

    def check_css_grid(self, css: str, filepath: str):
        """CSS Grid 사용 확인"""
        for i, line in enumerate(css.split("\n"), 1):
            if "display:grid" in line or "display: grid" in line:
                self._add("no-css-grid", "CRITICAL",
                          "CSS Grid 사용 금지 — flexbox만 허용", i, filepath)

    def check_important(self, css: str, filepath: str):
        """!important 사용 확인"""
        for i, line in enumerate(css.split("\n"), 1):
            if "!important" in line:
                # 유틸리티 클래스 예외 확인
                if not any(u in line for u in [".mb_", ".mt_", ".mr_", ".ml_", ".pb_", ".pt_",
                                                ".txt_c", ".txt_l", ".txt_r", ".back_no", ".bd_"]):
                    self._add("no-important", "MAJOR",
                              f"!important 사용 (유틸리티 외 금지): {line.strip()[:60]}", i, filepath)

    def check_border_radius_999(self, css: str, filepath: str):
        """999px border-radius 확인"""
        for i, line in enumerate(css.split("\n"), 1):
            if "999px" in line:
                self._add("no-999px", "CRITICAL",
                          "999px 사용 금지 — 원형: 50%, pill: 2em", i, filepath)

    def check_color_format(self, css: str, filepath: str):
        """rgb()/hsl() 사용 확인 (rgba 제외)"""
        for i, line in enumerate(css.split("\n"), 1):
            if re.search(r'(?<!rgba)\brgb\(', line) or "hsl(" in line:
                self._add("hex-color-only", "MAJOR",
                          f"hex 이외 색상 형식: {line.strip()[:60]}", i, filepath)

    def check_max_width_pattern(self, css: str, filepath: str):
        """좌우 padding으로 레이아웃 폭 제한하는지 확인"""
        for i, line in enumerate(css.split("\n"), 1):
            # padding 좌우 100px 이상이면 max-width 패턴 사용 권장
            match = re.search(r'padding:\s*\d+px\s+(\d+)px', line)
            if match:
                side_pad = int(match.group(1))
                if side_pad >= 100:
                    self._add("max-width-pattern", "MAJOR",
                              f"좌우 padding {side_pad}px — max-width + margin:auto 사용 권장",
                              i, filepath)

    def check_word_break(self, css: str, filepath: str):
        """word-break: keep-all 적용 확인"""
        if "keep-all" not in css:
            self._add("word-break", "MAJOR",
                      "word-break: keep-all 미적용 (한국어 텍스트 필수)", 0, filepath)

    def check_font_size_base(self, css: str, filepath: str):
        """html,body font-size clamp 기준 확인"""
        if "font-size:clamp(" not in css.replace(" ", ""):
            self._add("font-size-base", "MAJOR",
                      "html,body에 font-size:clamp(14px, 1.2vw, 16px) 미적용", 0, filepath)

    def check_root_vars(self, css: str, filepath: str):
        """필수 :root 변수 확인"""
        if "--width" not in css:
            self._add("root-vars", "MAJOR", ":root에 --width 변수 미선언", 0, filepath)
        if "--padding" not in css:
            self._add("root-vars", "MAJOR", ":root에 --padding 변수 미선언", 0, filepath)

    def check_selector_format(self, css: str, filepath: str):
        """셀렉터 한 줄 포맷 확인 (미디어쿼리 내부 제외)"""
        lines = css.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 여는 중괄호만 있는 줄 (멀티라인 셀렉터)
            if stripped.endswith("{") and not stripped.startswith("@") and not stripped.startswith("/*"):
                # 다음 줄에 속성이 있으면 멀티라인 = 위반
                if i < len(lines):
                    next_line = lines[i].strip() if i < len(lines) else ""
                    if next_line and not next_line.startswith("}") and not next_line.startswith(".") and not next_line.startswith("@"):
                        self._add("one-line-selector", "MINOR",
                                  f"멀티라인 셀렉터 — 한 줄 포맷 사용: {stripped[:40]}", i, filepath)

    # ===== Image Checks =====

    def check_image_naming(self, img_dir: str):
        """이미지 파일명 규칙 확인"""
        if not os.path.isdir(img_dir):
            return
        for f in os.listdir(img_dir):
            if not f.endswith((".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif")):
                continue
            name = os.path.splitext(f)[0]
            # Figma node ID 패턴
            if re.match(r'^[0-9]+[-:][0-9]+', name) or name.startswith("I"):
                self._add("img-naming", "CRITICAL",
                          f"Figma node ID 파일명: {f} — 의미 있는 이름 사용", 0, img_dir)
            # snake_case 확인
            if not re.match(r'^[a-z0-9_]+$', name):
                if not re.match(r'^[0-9]+[-:][0-9]+', name):  # 이미 위에서 잡힌 것 제외
                    self._add("img-naming", "MINOR",
                              f"snake_case 아님: {f}", 0, img_dir)

    # ===== Run All =====

    def validate(self, html_path: str, css_path: str, img_dir: str | None = None) -> list[Violation]:
        self.violations = []

        html = Path(html_path).read_text(encoding="utf-8") if os.path.exists(html_path) else ""
        css = Path(css_path).read_text(encoding="utf-8") if os.path.exists(css_path) else ""

        if html:
            self.check_nav_structure(html, html_path)
            self.check_img_wrapper(html, html_path)
            self.check_inline_style(html, html_path)
            self.check_forbidden_tags(html, html_path)
            self.check_list_pattern(html, html_path)
            self.check_p_tag_misuse(html, html_path)

        if css:
            self.check_css_grid(css, css_path)
            self.check_important(css, css_path)
            self.check_border_radius_999(css, css_path)
            self.check_color_format(css, css_path)
            self.check_max_width_pattern(css, css_path)
            self.check_word_break(css, css_path)
            self.check_font_size_base(css, css_path)
            self.check_root_vars(css, css_path)
            self.check_selector_format(css, css_path)

        if img_dir:
            self.check_image_naming(img_dir)

        return self.violations


def main():
    parser = argparse.ArgumentParser(description="Validate semantic HTML/CSS against project rules")
    parser.add_argument("--html", required=True, help="HTML file path")
    parser.add_argument("--css", required=True, help="CSS file path")
    parser.add_argument("--img", help="Image directory path")
    parser.add_argument("--fix", action="store_true", help="Auto-fix violations (not yet implemented)")
    args = parser.parse_args()

    validator = SemanticValidator()
    violations = validator.validate(args.html, args.css, args.img)

    if not violations:
        print("✅ ALL PASS — 위반 사항 없음")
        sys.exit(0)

    # 분류별 카운트
    critical = [v for v in violations if v.severity == "CRITICAL"]
    major = [v for v in violations if v.severity == "MAJOR"]
    minor = [v for v in violations if v.severity == "MINOR"]

    print(f"=== 검증 결과: {len(violations)}건 위반 ===")
    print(f"CRITICAL: {len(critical)} | MAJOR: {len(major)} | MINOR: {len(minor)}")
    print()

    for v in violations:
        print(v)

    print()
    if critical:
        print("❌ CRITICAL 위반이 있습니다. 반드시 수정하세요.")
        sys.exit(2)
    elif major:
        print("⚠️  MAJOR 위반이 있습니다. 수정을 권장합니다.")
        sys.exit(1)
    else:
        print("ℹ️  MINOR 위반만 있습니다.")
        sys.exit(0)


if __name__ == "__main__":
    main()

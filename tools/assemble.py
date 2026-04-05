#!/usr/bin/env python3
"""Assemble per-section Gemini outputs into index.html + common.css.

Usage:
  python3 tools/assemble.py --results ./results/ --output ./output/ --title "페이지 타이틀"

Results directory should contain files like:
  00_header.log, 01_mv.log, 02_recommend.log, ...
Each file is raw Gemini output containing ```html and ```css blocks.
"""

import argparse
import glob
import os
import re
import sys


def extract_blocks(content: str) -> tuple[str, str]:
    """Extract HTML and CSS code blocks from Gemini output."""
    html_match = re.search(r"```html\n(.*?)```", content, re.DOTALL)
    css_match = re.search(r"```css\n(.*?)```", content, re.DOTALL)

    html = html_match.group(1).strip() if html_match else ""
    css = css_match.group(1).strip() if css_match else ""

    # Remove hardcoded width/height on root elements
    css = re.sub(r"width:\d+px;\s*height:\d+px;", "", css)

    return html, css


def fix_class_names(text: str, replacements: dict[str, str]) -> str:
    """Replace generic class names with meaningful ones."""
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def assemble(results_dir: str, output_dir: str, title: str = "Page",
             class_replacements: dict[str, str] | None = None) -> None:
    """Assemble all section results into final HTML + CSS."""
    result_files = sorted(glob.glob(os.path.join(results_dir, "*.log")))
    if not result_files:
        print("No .log files found in results directory", file=sys.stderr)
        sys.exit(1)

    replacements = class_replacements or {}
    all_html = []
    all_css = []

    for filepath in result_files:
        name = os.path.splitext(os.path.basename(filepath))[0]
        # Remove numeric prefix for comment
        comment_name = re.sub(r"^\d+_", "", name)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        html, css = extract_blocks(content)

        if not html and not css:
            print(f"  WARNING: {name} — no HTML/CSS blocks found", file=sys.stderr)
            continue

        html = fix_class_names(html, replacements)
        css = fix_class_names(css, replacements)

        # Remove unicode line separators
        html = html.replace("\u2028", "").replace("\u2029", "")

        all_html.append(f"  <!-- {comment_name} -->\n  {html}")
        all_css.append(f"/* {comment_name} */\n{css}")
        print(f"  [{name}] HTML {len(html)}c, CSS {len(css)}c", file=sys.stderr)

    os.makedirs(output_dir, exist_ok=True)

    full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="reset.css">
<link rel="stylesheet" href="common.css">
</head>
<body>

{chr(10).join(all_html)}

</body>
</html>"""

    full_css = chr(10).join(all_css)

    html_path = os.path.join(output_dir, "index.html")
    css_path = os.path.join(output_dir, "common.css")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(full_css)

    print(f"\nAssembled: {html_path} ({len(full_html)}c), {css_path} ({len(full_css)}c)", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Assemble Gemini section results")
    parser.add_argument("--results", required=True, help="Directory with .log files")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--title", default="Page", help="HTML title")
    parser.add_argument("--replace", nargs="*", help="Class replacements: old=new old2=new2")
    args = parser.parse_args()

    replacements = {}
    if args.replace:
        for item in args.replace:
            old, new = item.split("=", 1)
            replacements[old] = new

    assemble(args.results, args.output, args.title, replacements)


if __name__ == "__main__":
    main()

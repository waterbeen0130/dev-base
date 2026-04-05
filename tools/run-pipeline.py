#!/usr/bin/env python3
"""Run the full AI publishing pipeline.

Usage:
  FIGMA_TOKEN="토큰" python3 tools/run-pipeline.py \
    --file-key MGvYalHCtVrf3DLndOFLH2 \
    --node-id 19:594 \
    --output ./output/youngwol \
    --page main \
    --profile basic \
    --title "영월반값여행"

Steps:
  1. Extract normalized JSON from Figma
  2. Download images
  3. Split into sections
  4. Build Gemini prompts
  5. Run Gemini on each section (parallel)
  6. Assemble into index.html + common.css
  7. Generate reset.css
  8. Validate
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent


def run(cmd: str, **kwargs) -> subprocess.CompletedProcess:
    """Run shell command and return result."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description="AI Publishing Pipeline")
    parser.add_argument("--file-key", required=True, help="Figma file key")
    parser.add_argument("--node-id", required=True, help="Figma node ID")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--page", default="main", help="Page name for CSS prefix")
    parser.add_argument("--profile", default="basic", help="Profile: basic or landing")
    parser.add_argument("--title", default="Page", help="HTML title")
    parser.add_argument("--skip-extract", action="store_true", help="Skip Figma extraction (use existing)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    sections_dir = output_dir / "sections"
    prompts_dir = output_dir / "prompts"
    results_dir = output_dir / "results"
    img_dir = output_dir / "img"
    normalized_path = output_dir / "normalized.json"
    image_map_path = output_dir / "image-map.json"

    for d in [output_dir, sections_dir, prompts_dir, results_dir, img_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract normalized JSON
    if not args.skip_extract:
        print("\n=== Step 1: Extracting normalized JSON ===")
        result = run(
            f'FIGMA_TOKEN="${{FIGMA_TOKEN}}" python3 {TOOLS_DIR}/figma-extract.py '
            f'--node-id {args.node_id} --file-key {args.file_key} --profile {args.profile}'
        )
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        normalized_path.write_text(result.stdout, encoding="utf-8")
        print(f"  Saved: {normalized_path}")
    else:
        print("\n=== Step 1: Skipped (using existing) ===")

    # Step 2: Split into sections
    print("\n=== Step 2: Splitting into sections ===")
    result = run(f'python3 {TOOLS_DIR}/split-sections.py --input {normalized_path} --output {sections_dir}')
    print(result.stderr)

    # Step 3: Build prompts
    print("\n=== Step 3: Building prompts ===")
    if not image_map_path.exists():
        print("  WARNING: No image-map.json found. Creating empty map.")
        image_map_path.write_text("{}", encoding="utf-8")
    result = run(
        f'python3 {TOOLS_DIR}/build-prompts.py '
        f'--sections {sections_dir} --image-map {image_map_path} '
        f'--page {args.page} --output {prompts_dir}'
    )
    print(result.stdout)
    print(result.stderr)

    # Step 4: Run Gemini on each section
    print("\n=== Step 4: Running Gemini (parallel) ===")
    prompt_files = sorted(prompts_dir.glob("*.md"))
    processes = []
    for pf in prompt_files:
        result_file = results_dir / f"{pf.stem}.log"
        cmd = f'gemini -p "$(cat {pf})" --sandbox=false > {result_file} 2>&1'
        print(f"  Starting: {pf.name}")
        proc = subprocess.Popen(cmd, shell=True)
        processes.append((pf.name, proc, result_file))

    # Wait for all
    for name, proc, result_file in processes:
        proc.wait()
        status = "OK" if proc.returncode == 0 else f"FAIL({proc.returncode})"
        print(f"  Done: {name} → {status}")

    # Step 5: Assemble
    print("\n=== Step 5: Assembling ===")
    result = run(
        f'python3 {TOOLS_DIR}/assemble.py '
        f'--results {results_dir} --output {output_dir} --title "{args.title}"'
    )
    print(result.stderr)

    # Step 6: Generate reset.css
    reset_path = output_dir / "reset.css"
    if not reset_path.exists():
        reset_path.write_text("""@charset "UTF-8";
html,body{font-size:clamp(14px, 1.2vw, 16px);}
body{font-family:'Pretendard', sans-serif; overflow-x:hidden; color:#212121; word-break:keep-all; margin:0; padding:0;}
*{margin:0; padding:0; box-sizing:border-box;}
ul{list-style:none;}
ol{list-style:none;}
img{max-width:100%; height:auto; display:block; border:0;}
a{text-decoration:none; color:inherit;}
button{cursor:pointer; border:none; background:none;}
input,textarea,select{font-family:inherit; font-size:inherit;}
table{border-collapse:collapse; border-spacing:0;}
address{font-style:normal;}""", encoding="utf-8")
        print(f"  Generated: {reset_path}")

    # Step 7: Validate
    print("\n=== Step 6: Validating ===")
    html_path = output_dir / "index.html"
    css_path = output_dir / "common.css"
    result = run(
        f'python3 {TOOLS_DIR}/validate-semantic.py --html {html_path} --css {css_path}'
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    print(f"\n=== Pipeline complete ===")
    print(f"Output: {output_dir}/index.html")
    print(f"Open: file:///{output_dir.resolve()}/index.html")


if __name__ == "__main__":
    main()

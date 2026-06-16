#!/usr/bin/env python3
"""
Copy assets from figma-section-spec.py output to a project's img/ folder.

Given an `extracted/` directory containing `{section}_asset_manifest.json`
files and `{section}/vectors/*.svg` asset trees, copy all assets into the
project's `img/` directory with filenames preserving the original
spec_node_id (with `:` replaced by `_`, keeping `;` intact so the
validator's asset_manifest check can reverse-match).

Usage:
    python3 asset-copy.py \
        --extracted path/to/extracted/ \
        --img path/to/img/
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--extracted", required=True)
    parser.add_argument("--img", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    extracted = Path(args.extracted)
    img = Path(args.img)
    if not args.dry_run:
        img.mkdir(parents=True, exist_ok=True)

    manifest_files = sorted(extracted.glob("*_asset_manifest.json"))
    if not manifest_files:
        print(f"WARN: no *_asset_manifest.json in {extracted}", file=sys.stderr)
        return 1

    total_copied = 0
    total_missing = 0
    total_dedup = 0

    for mpath in manifest_files:
        section = mpath.stem.replace("_asset_manifest", "")
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
        assets = manifest.get("assets", [])
        print(f"\n[{section}] {len(assets)} assets")

        for asset in assets:
            local_path = asset.get("local_path")
            if not local_path:
                continue
            src = extracted / local_path
            if not src.exists():
                print(f"  [MISS] {local_path}")
                total_missing += 1
                continue

            node_id = asset.get("spec_node_id") or asset.get("ref") or src.stem
            # ':' is illegal on Windows filesystems; ';' is kept for validator match
            safe_name = node_id.replace(":", "_")
            dst = img / f"{safe_name}{src.suffix}"

            if dst.exists():
                total_dedup += 1
                continue

            if args.dry_run:
                print(f"  [DRY]  {src.name} -> {dst.name}")
            else:
                shutil.copy2(src, dst)
            total_copied += 1

    print(f"\nSummary: copied {total_copied}, dedup {total_dedup}, missing {total_missing}")
    return 0 if total_missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Download Figma section PNGs and image-fill assets via Figma REST API.

Usage:
    FIGMA_TOKEN=xxx python3 figma-png-download.py \
        --file-key XXX \
        --node-ids 130:10972,134:13603,203:14765 \
        --output ./figma-png/ \
        [--scale 1] [--include-fills]

When --include-fills is set, the script first fetches each node's data,
extracts every IMAGE fill imageRef, and downloads them too.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


FIGMA_API = "https://api.figma.com/v1"


def http_get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_download(url: str, dst: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as resp:
        dst.write_bytes(resp.read())


def fetch_node_pngs(file_key: str, node_ids: list[str], scale: int, token: str) -> dict[str, str]:
    ids_param = urllib.parse.quote(",".join(node_ids))
    url = f"{FIGMA_API}/images/{file_key}?ids={ids_param}&format=png&scale={scale}"
    data = http_get_json(url, token)
    if data.get("err"):
        raise RuntimeError(f"Figma API error: {data['err']}")
    return data.get("images", {})


def fetch_image_fills(file_key: str, token: str) -> dict[str, str]:
    """Returns {imageRef: download_url}."""
    url = f"{FIGMA_API}/files/{file_key}/images"
    data = http_get_json(url, token)
    if data.get("error"):
        return {}
    return data.get("meta", {}).get("images", {})


def extract_image_refs_from_node(node: dict) -> set[str]:
    refs = set()
    for fill in node.get("fills") or []:
        if isinstance(fill, dict) and fill.get("type") == "IMAGE":
            ref = fill.get("imageRef")
            if ref:
                refs.add(ref)
    for child in node.get("children") or []:
        refs |= extract_image_refs_from_node(child)
    return refs


def fetch_node_image_refs(file_key: str, node_id: str, token: str) -> set[str]:
    url = f"{FIGMA_API}/files/{file_key}/nodes?ids={urllib.parse.quote(node_id)}"
    data = http_get_json(url, token)
    refs = set()
    for nid, payload in (data.get("nodes") or {}).items():
        doc = payload.get("document") if isinstance(payload, dict) else None
        if doc:
            refs |= extract_image_refs_from_node(doc)
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--file-key", required=True)
    parser.add_argument("--node-ids", required=True, help="Comma-separated node IDs")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--scale", type=int, default=1)
    parser.add_argument("--include-fills", action="store_true", help="Also download IMAGE fill assets referenced by these nodes")
    parser.add_argument("--token", default=os.environ.get("FIGMA_TOKEN"))
    args = parser.parse_args()

    if not args.token or len(args.token) < 30:
        print("ERROR: FIGMA_TOKEN env var or --token required (length >= 30)", file=sys.stderr)
        return 1

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    node_ids = [x.strip() for x in args.node_ids.split(",") if x.strip()]

    print(f"[1] Fetching {len(node_ids)} node PNGs (scale {args.scale})...")
    pngs = fetch_node_pngs(args.file_key, node_ids, args.scale, args.token)
    for nid, url in pngs.items():
        if not url:
            print(f"  [SKIP] {nid}: no URL")
            continue
        safe = nid.replace(":", "_").replace(";", "_")
        dst = output / f"{safe}.png"
        http_download(url, dst)
        print(f"  [OK]   {nid} -> {dst.name}")

    if args.include_fills:
        print(f"\n[2] Discovering IMAGE fill assets in nodes...")
        all_refs: set[str] = set()
        for nid in node_ids:
            refs = fetch_node_image_refs(args.file_key, nid, args.token)
            print(f"  {nid}: {len(refs)} image fills")
            all_refs |= refs
        if all_refs:
            print(f"\n[3] Resolving {len(all_refs)} fill download URLs...")
            ref_urls = fetch_image_fills(args.file_key, args.token)
            for ref in sorted(all_refs):
                url = ref_urls.get(ref)
                if not url:
                    print(f"  [MISS] fill {ref[:12]}: no URL in /images")
                    continue
                dst = output / f"fill_{ref[:12]}.png"
                http_download(url, dst)
                print(f"  [OK]   fill {ref[:12]} -> {dst.name}")

    print(f"\nDone. Output: {output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

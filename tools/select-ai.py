#!/usr/bin/env python3
"""
Select the optimal external AI (gemini-dev / codex-dev / claude-dev) for
translating a Figma design into HTML/CSS based on quantitative indicators
+ optional LLM judgment.

Policy (AD-002):
  - Quantitative score table + LLM recommendation mixed.
  - Quantitative winner takes precedence (deterministic).
  - LLM advice attached as supporting reason / confidence signal.

Usage:
    python3 select-ai.py \\
        --extracted ./extracted/ \\
        --figma-png ./.gran-maestro/figma-png/ \\
        --img ./img/ \\
        --project-type landing \\
        --json

Output (human or --json):
    {
        "selected": "gemini-dev",
        "confidence": "high|medium|low",
        "quant_scores": {"gemini-dev": 5, "codex-dev": 2, "claude-dev": -1},
        "llm_recommendation": null,
        "indicators": {...},
        "reason": "..."
    }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


AGENTS = ("gemini-dev", "codex-dev", "claude-dev")


def count_section_specs(extracted: Path) -> int:
    return len(list(extracted.glob("*_spec.json")))


def aggregate_text_frame_vector(extracted: Path) -> tuple[int, int, int, int]:
    """Return (text_nodes, frame_nodes, vector_nodes, max_depth)."""
    total_text = 0
    total_frame = 0
    total_vector = 0
    max_depth = 0
    for spec_path in extracted.glob("*_spec.json"):
        try:
            data = json.loads(spec_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        total_text += len(data.get("text_nodes") or [])
        frames = data.get("frame_nodes") or []
        total_frame += len(frames)
        total_vector += len(data.get("vector_nodes") or [])

        parent_map: dict[str, str | None] = {}
        for f in frames:
            if isinstance(f, dict):
                parent_map[f.get("id")] = f.get("parent_id")
        for fid in parent_map:
            depth = 0
            cur = fid
            visited = set()
            while cur in parent_map and parent_map[cur] and cur not in visited:
                visited.add(cur)
                cur = parent_map[cur]
                depth += 1
                if depth > 50:
                    break
            max_depth = max(max_depth, depth)
    return total_text, total_frame, total_vector, max_depth


def count_image_fills(extracted: Path) -> int:
    """Count IMAGE fill entries across manifests + fills_v2 type IMAGE."""
    count = 0
    for manifest in extracted.glob("*_asset_manifest.json"):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            continue
        for asset in data.get("assets") or []:
            if asset.get("kind") == "raster" or asset.get("format") in {"png", "jpg", "jpeg"}:
                count += 1
    for spec_path in extracted.glob("*_spec.json"):
        try:
            data = json.loads(spec_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for frame in data.get("frame_nodes") or []:
            for fill in frame.get("fills_v2") or []:
                if isinstance(fill, dict) and fill.get("type") == "IMAGE":
                    count += 1
    return count


def count_assets_dir(img: Path) -> int:
    if not img.is_dir():
        return 0
    return sum(1 for p in img.iterdir() if p.is_file())


def estimate_page_height(figma_png: Path) -> int:
    """Largest PNG height among downloaded figma pngs. Uses PNG IHDR."""
    if not figma_png.is_dir():
        return 0
    max_h = 0
    for png in figma_png.glob("*.png"):
        try:
            with png.open("rb") as f:
                data = f.read(24)
            if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
                import struct
                height = struct.unpack(">I", data[20:24])[0]
                if height > max_h:
                    max_h = height
        except Exception:
            continue
    return max_h


def compute_score_table(ind: dict[str, int], project_type: str) -> dict[str, int]:
    """Score table per AD-002. Higher = better fit."""
    scores = {a: 0 for a in AGENTS}

    if ind["page_height_px"] > 3000:
        scores["gemini-dev"] += 3
        scores["claude-dev"] -= 1
    if ind["section_count"] > 5:
        scores["gemini-dev"] += 2
        scores["claude-dev"] -= 1
    if ind["image_fill_count"] > 5:
        scores["gemini-dev"] += 1
    if ind["frame_depth_max"] > 6:
        scores["gemini-dev"] += 2
        scores["claude-dev"] -= 1
    if ind["text_node_count"] > 30:
        scores["gemini-dev"] += 2
    if ind["section_count"] <= 2:
        scores["claude-dev"] += 2
    if ind["asset_count"] == 0:
        scores["codex-dev"] += 1
        scores["claude-dev"] += 2

    if project_type == "landing":
        scores["gemini-dev"] += 1
    elif project_type == "basic":
        scores["claude-dev"] += 1

    return scores


def pick_winner(scores: dict[str, int]) -> str:
    """Highest score wins. Tie: gemini > codex > claude (publishing default)."""
    max_score = max(scores.values())
    winners = [a for a in AGENTS if scores[a] == max_score]
    return winners[0]


def build_reason(ind: dict[str, int], project_type: str, winner: str) -> str:
    notes = []
    if ind["page_height_px"] > 3000:
        notes.append(f"대용량 페이지 {ind['page_height_px']}px")
    if ind["section_count"] > 5:
        notes.append(f"복잡 레이아웃 ({ind['section_count']} 섹션)")
    if ind["frame_depth_max"] > 6:
        notes.append(f"깊은 nesting (depth {ind['frame_depth_max']})")
    if ind["text_node_count"] > 30:
        notes.append(f"텍스트 다수 ({ind['text_node_count']})")
    if ind["image_fill_count"] > 5:
        notes.append(f"이미지 fill {ind['image_fill_count']}")
    if ind["section_count"] <= 2:
        notes.append(f"단순 레이아웃 ({ind['section_count']} 섹션)")
    if ind["asset_count"] == 0:
        notes.append("자산 0 (텍스트 위주)")
    notes.append(f"프로젝트 타입: {project_type}")
    if not notes:
        notes.append("기본 추천")
    return f"{winner} 선정 — " + " + ".join(notes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--extracted", required=True)
    parser.add_argument("--figma-png", dest="figma_png", default="")
    parser.add_argument("--img", default="")
    parser.add_argument("--project-type", choices=("landing", "basic"), default="landing")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    extracted = Path(args.extracted)
    if not extracted.is_dir():
        print(f"Error: extracted dir not found: {extracted}", file=sys.stderr)
        return 1

    figma_png = Path(args.figma_png) if args.figma_png else None
    img = Path(args.img) if args.img else None

    text_n, frame_n, vector_n, max_depth = aggregate_text_frame_vector(extracted)
    indicators = {
        "asset_count": count_assets_dir(img) if img else 0,
        "section_count": count_section_specs(extracted),
        "image_fill_count": count_image_fills(extracted),
        "vector_count": vector_n,
        "text_node_count": text_n,
        "frame_depth_max": max_depth,
        "page_height_px": estimate_page_height(figma_png) if figma_png else 0,
    }

    scores = compute_score_table(indicators, args.project_type)
    winner = pick_winner(scores)

    max_score = max(scores.values())
    margin = max_score - sorted(scores.values())[-2] if len(scores) > 1 else 0
    confidence = "high" if margin >= 3 else "medium" if margin >= 1 else "low"

    reason = build_reason(indicators, args.project_type, winner)

    result = {
        "selected": winner,
        "confidence": confidence,
        "quant_scores": scores,
        "llm_recommendation": None,
        "indicators": indicators,
        "reason": reason,
    }

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[AI 외주 선정] {winner}")
        print(f"- 정량 점수: " + ", ".join(f"{a}={scores[a]}" for a in AGENTS))
        print(f"- 신뢰도: {confidence}")
        print(f"- 지표: {indicators}")
        print(f"- 사유: {reason}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

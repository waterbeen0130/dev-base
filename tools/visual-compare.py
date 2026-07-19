#!/usr/bin/env python3
"""Deterministic visual comparison gate for HTML vs design PNG."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


DEFAULT_WIDTH = 1920
DEFAULT_DIFF_THRESHOLD = 0.05
DEFAULT_HEIGHT_THRESHOLD = 0.03
DEFAULT_PIXEL_TOLERANCE = 16
DEFAULT_CHUNK_ROWS = 512

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"

RENDER_STABILIZER_CSS = """
html { scroll-behavior: auto !important; }
*, *::before, *::after {
  animation: none !important;
  transition: none !important;
  caret-color: transparent !important;
}
[data-delay], [data-delay] * {
  opacity: 1 !important;
  visibility: visible !important;
  animation: none !important;
  transition: none !important;
}
.section_on, .section_on * {
  animation: none !important;
  transition: none !important;
}
.section_on [data-direction="left"],
.section_on [data-direction="right"],
.section_on [data-direction="top"],
.section_on [data-direction="bottom"] {
  left: 0 !important;
  right: 0 !important;
  top: 0 !important;
  bottom: 0 !important;
  transform: none !important;
}
"""


@dataclass
class CompareResult:
    render_width: int
    render_height: int
    design_width: int
    design_height: int
    height_delta_ratio: float
    diff_ratio: float
    diff_pixels: int
    compared_pixels: int
    passed: bool
    mismatch_rows: list[tuple[int, np.ndarray]]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def compare_images(
    render_path: Path,
    design_path: Path,
    *,
    diff_threshold: float,
    height_threshold: float,
    pixel_tolerance: int,
    chunk_rows: int = DEFAULT_CHUNK_ROWS,
) -> CompareResult:
    if chunk_rows <= 0:
        raise ValueError("chunk_rows must be positive")

    mismatch_rows: list[tuple[int, np.ndarray]] = []
    diff_pixels = 0

    with Image.open(render_path) as render_raw, Image.open(design_path) as design_raw:
        render = render_raw.convert("RGBA")
        design = design_raw.convert("RGBA")
        render_width, render_height = render.size
        design_width, design_height = design.size

        if render_width != design_width:
            raise ValueError(
                f"width mismatch: render={render_width}px design={design_width}px (same width required)"
            )

        common_height = min(render_height, design_height)
        compared_pixels = render_width * common_height
        if compared_pixels == 0:
            raise ValueError("cannot compare empty images")

        for top in range(0, common_height, chunk_rows):
            bottom = min(top + chunk_rows, common_height)
            render_chunk = np.asarray(render.crop((0, top, render_width, bottom)), dtype=np.int16)
            design_chunk = np.asarray(design.crop((0, top, design_width, bottom)), dtype=np.int16)
            delta = np.abs(render_chunk - design_chunk)
            mismatch_mask = np.any(delta > pixel_tolerance, axis=2)
            diff_pixels += int(np.count_nonzero(mismatch_mask))
            mismatch_rows.append((top, mismatch_mask))

    diff_ratio = diff_pixels / compared_pixels
    # Height delta ratio is intentionally normalized by the shared compared height.
    height_delta_ratio = abs(render_height - design_height) / common_height
    passed = diff_ratio <= diff_threshold and height_delta_ratio <= height_threshold

    return CompareResult(
        render_width=render_width,
        render_height=render_height,
        design_width=design_width,
        design_height=design_height,
        height_delta_ratio=height_delta_ratio,
        diff_ratio=diff_ratio,
        diff_pixels=diff_pixels,
        compared_pixels=compared_pixels,
        passed=passed,
        mismatch_rows=mismatch_rows,
    )


def write_heatmap(result: CompareResult, out_path: Path) -> None:
    canvas = np.zeros((max(result.render_height, result.design_height), result.render_width, 4), dtype=np.uint8)
    for top, mismatch_mask in result.mismatch_rows:
        common_slice = canvas[top:top + mismatch_mask.shape[0], :, :]
        common_slice[mismatch_mask] = np.array([255, 64, 64, 255], dtype=np.uint8)

    common_height = min(result.render_height, result.design_height)
    if result.render_height > common_height:
        canvas[common_height:result.render_height, :, :] = np.array([255, 190, 64, 160], dtype=np.uint8)
    if result.design_height > common_height:
        canvas[common_height:result.design_height, :, :] = np.array([64, 160, 255, 160], dtype=np.uint8)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(canvas, mode="RGBA").save(out_path)


def ensure_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{label} file missing: {path}")


def render_html_to_png(html_path: Path, width: int, output_path: Path) -> Path:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Playwright unavailable: {exc}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    target_url = html_path.resolve().as_uri()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": width, "height": 1080},
                device_scale_factor=1,
            )
            page = context.new_page()
            page.goto(target_url, wait_until="load", timeout=60000)
            page.add_style_tag(content=RENDER_STABILIZER_CSS)
            page.evaluate(
                """
                async () => {
                  document.documentElement.classList.add("section_on");
                  document.body?.classList.add("section_on");
                  for (const img of Array.from(document.images)) {
                    img.loading = "eager";
                    img.decoding = "sync";
                  }
                  const maxScroll = Math.max(
                    document.documentElement?.scrollHeight || 0,
                    document.body?.scrollHeight || 0
                  );
                  const step = Math.max(window.innerHeight, 1);
                  for (let top = 0; top <= maxScroll; top += step) {
                    window.scrollTo(0, top);
                    await new Promise((resolve) => requestAnimationFrame(() => resolve()));
                  }
                  window.scrollTo(0, 0);
                  if (document.fonts?.ready) {
                    try {
                      await document.fonts.ready;
                    } catch (error) {
                      void error;
                    }
                  }
                  await Promise.all(
                    Array.from(document.images).map(async (img) => {
                      try {
                        if (typeof img.decode === "function") {
                          await img.decode();
                          return;
                        }
                      } catch (error) {
                        void error;
                      }
                      if (img.complete) return;
                      await new Promise((resolve) => {
                        img.addEventListener("load", () => resolve(), { once: true });
                        img.addEventListener("error", () => resolve(), { once: true });
                      });
                    })
                  );
                  await new Promise((resolve) => requestAnimationFrame(() => resolve()));
                }
                """
            )
            page.wait_for_timeout(50)
            content_height = page.evaluate(
                """
                () => {
                  const body = document.body;
                  if (!body) return 1;
                  const nodes = [body, ...body.querySelectorAll("*")];
                  let minTop = Infinity;
                  let maxBottom = 0;
                  for (const node of nodes) {
                    const rect = node.getBoundingClientRect();
                    if (!Number.isFinite(rect.top) || !Number.isFinite(rect.bottom)) continue;
                    minTop = Math.min(minTop, rect.top);
                    maxBottom = Math.max(maxBottom, rect.bottom);
                  }
                  if (!Number.isFinite(minTop) || maxBottom <= minTop) {
                    return Math.max(body.getBoundingClientRect().height, 1);
                  }
                  return Math.max(maxBottom - minTop, 1);
                }
                """
            )
            page.set_viewport_size({"width": width, "height": max(1, int(content_height))})
            page.wait_for_timeout(50)
            page.screenshot(path=str(output_path), full_page=True)
            context.close()
            browser.close()
    except PlaywrightError as exc:
        raise RuntimeError(f"Playwright render failed: {exc}") from exc

    return output_path


def append_visual_step(section: str, ledger_path: str | None) -> tuple[int, str]:
    cmd = [sys.executable, str(TOOLS_DIR / "workflow-ledger.py")]
    if ledger_path:
        cmd.extend(["--ledger", ledger_path])
    cmd.extend(
        [
            "append",
            "--step",
            "visual-compare",
            "--provider",
            "visual-compare",
            "--section",
            section,
        ]
    )
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare a rendered HTML page to a design PNG")
    parser.add_argument("--html", required=True, help="HTML file to render")
    parser.add_argument("--design", required=True, help="Design PNG path")
    parser.add_argument("--css", help="Optional CSS file for sha-bound evidence")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--diff-threshold", type=float, default=DEFAULT_DIFF_THRESHOLD)
    parser.add_argument("--height-threshold", type=float, default=DEFAULT_HEIGHT_THRESHOLD)
    parser.add_argument("--pixel-tolerance", type=int, default=DEFAULT_PIXEL_TOLERANCE)
    parser.add_argument("--out-dir", default=str(PROJECT_ROOT / ".gran-maestro" / "visual-compare"))
    parser.add_argument("--emit-report", help="Write sha-bound visual comparison evidence JSON")
    parser.add_argument("--section", help="Workflow ledger section name")
    parser.add_argument("--ledger", help="Workflow ledger path override")
    parser.add_argument("--allow-visual-mismatch", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    html_path = Path(args.html)
    design_path = Path(args.design)
    css_path = Path(args.css) if args.css else None
    out_dir = Path(args.out_dir)

    try:
        ensure_file(html_path, "html")
        ensure_file(design_path, "design")
        if css_path:
            ensure_file(css_path, "css")

        with Image.open(design_path) as design_image:
            design_width = design_image.size[0]
        if design_width != args.width:
            raise ValueError(
                f"width mismatch: requested width={args.width}px design={design_width}px (same width required)"
            )

        out_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="render-", suffix=".png", dir=out_dir, delete=False) as tmp:
            render_path = Path(tmp.name)

        try:
            render_html_to_png(html_path, args.width, render_path)
            result = compare_images(
                render_path,
                design_path,
                diff_threshold=args.diff_threshold,
                height_threshold=args.height_threshold,
                pixel_tolerance=args.pixel_tolerance,
            )
            diff_path = out_dir / f"{html_path.stem}-vs-{design_path.stem}-diff.png"
            write_heatmap(result, diff_path)

            threshold_passed = result.passed
            exit_code = 0 if threshold_passed or args.allow_visual_mismatch else 1
            if args.emit_report:
                payload = {
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                    "html_path": str(html_path),
                    "css_path": str(css_path) if css_path else None,
                    "design_path": str(design_path),
                    "html_sha256": sha256_file(html_path),
                    "css_sha256": sha256_file(css_path) if css_path else None,
                    "design_sha256": sha256_file(design_path),
                    "width": args.width,
                    "render_height": result.render_height,
                    "design_height": result.design_height,
                    "height_delta_ratio": result.height_delta_ratio,
                    "diff_ratio": result.diff_ratio,
                    "thresholds": {
                        "diff_ratio": args.diff_threshold,
                        "height_delta_ratio": args.height_threshold,
                        "pixel_tolerance": args.pixel_tolerance,
                    },
                    "passed": exit_code == 0,
                    "allow_visual_mismatch": args.allow_visual_mismatch,
                    "diff_image_path": str(diff_path),
                    "exit_code": exit_code,
                    "threshold_passed": threshold_passed,
                }
                Path(args.emit_report).parent.mkdir(parents=True, exist_ok=True)
                Path(args.emit_report).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"[evidence] visual comparison report: {args.emit_report}")

            print(
                "visual-compare: "
                f"diff_ratio={result.diff_ratio:.6f} "
                f"height_delta_ratio={result.height_delta_ratio:.6f} "
                f"thresholds(diff={args.diff_threshold:.6f}, height={args.height_threshold:.6f})"
            )
            print(f"diff_image: {diff_path}")

            if exit_code == 0 and args.section:
                rc, ledger_output = append_visual_step(args.section, args.ledger)
                tag = "ledger" if rc == 0 else "ledger-warn"
                print(f"[{tag}] {ledger_output}")

            if not threshold_passed and args.allow_visual_mismatch:
                print("WARN: visual mismatch allowed by --allow-visual-mismatch")
            elif not threshold_passed:
                print("FAIL: thresholds exceeded", file=sys.stderr)

            return exit_code
        finally:
            render_path.unlink(missing_ok=True)

    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())

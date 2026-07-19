import importlib.util
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
VISUAL_COMPARE = TOOLS / "visual-compare.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("visual_compare", VISUAL_COMPARE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _image(path: Path, width: int = 100, height: int = 100, color=(255, 255, 255, 255)) -> Path:
    Image.new("RGBA", (width, height), color).save(path)
    return path


def _run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VISUAL_COMPARE), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd or ROOT,
    )


def test_visual_diff_engine_identical_passes(tmp_path: Path) -> None:
    mod = _load_module()
    left = _image(tmp_path / "same-a.png")
    right = _image(tmp_path / "same-b.png")

    result = mod.compare_images(
        left,
        right,
        diff_threshold=0.05,
        height_threshold=0.03,
        pixel_tolerance=0,
    )

    assert result.diff_ratio == pytest.approx(0.0)
    assert result.height_delta_ratio == pytest.approx(0.0)
    assert result.passed is True


def test_visual_diff_engine_small_delta_passes_with_tolerance(tmp_path: Path) -> None:
    mod = _load_module()
    base = tmp_path / "base.png"
    variant = tmp_path / "variant.png"
    _image(base)
    image = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    for x in range(5):
        for y in range(100):
            image.putpixel((x, y), (248, 248, 248, 255))
    image.save(variant)

    result = mod.compare_images(
        base,
        variant,
        diff_threshold=0.05,
        height_threshold=0.03,
        pixel_tolerance=12,
    )

    assert result.diff_ratio == pytest.approx(0.0)
    assert result.passed is True


def test_visual_diff_engine_large_delta_fails(tmp_path: Path) -> None:
    mod = _load_module()
    base = tmp_path / "base.png"
    variant = tmp_path / "variant.png"
    _image(base)
    image = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    for x in range(20):
        for y in range(100):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(variant)

    result = mod.compare_images(
        base,
        variant,
        diff_threshold=0.05,
        height_threshold=0.03,
        pixel_tolerance=0,
    )

    assert result.diff_ratio == pytest.approx(0.2)
    assert result.passed is False


def test_visual_diff_engine_height_delta_fails(tmp_path: Path) -> None:
    mod = _load_module()
    base = _image(tmp_path / "base.png", height=100)
    taller = _image(tmp_path / "taller.png", height=110)

    result = mod.compare_images(
        base,
        taller,
        diff_threshold=0.05,
        height_threshold=0.03,
        pixel_tolerance=0,
    )

    assert result.height_delta_ratio == pytest.approx(0.1)
    assert result.passed is False


def test_diff_chunk_matches_monolithic_compare(tmp_path: Path) -> None:
    mod = _load_module()
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    base = Image.new("RGBA", (64, 257), (255, 255, 255, 255))
    variant = Image.new("RGBA", (64, 257), (255, 255, 255, 255))
    for x in range(8, 16):
        for y in range(90, 170):
            variant.putpixel((x, y), (0, 0, 0, 255))
    base.save(left)
    variant.save(right)

    chunked = mod.compare_images(
        left,
        right,
        diff_threshold=0.05,
        height_threshold=0.03,
        pixel_tolerance=0,
        chunk_rows=31,
    )
    monolithic = mod.compare_images(
        left,
        right,
        diff_threshold=0.05,
        height_threshold=0.03,
        pixel_tolerance=0,
    )

    assert chunked.diff_pixels == monolithic.diff_pixels
    assert chunked.compared_pixels == monolithic.compared_pixels
    assert chunked.diff_ratio == pytest.approx(monolithic.diff_ratio)
    assert chunked.height_delta_ratio == pytest.approx(monolithic.height_delta_ratio)
    assert chunked.passed == monolithic.passed


@pytest.mark.browser
def test_visual_compare_e2e_self_render_passes_and_height_change_fails(tmp_path: Path) -> None:
    pytest.importorskip("playwright.sync_api")
    mod = _load_module()

    html = tmp_path / "index.html"
    css = tmp_path / "common.css"
    html.write_text(
        """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="common.css">
</head>
<body>
  <main class="main_visual">
    <section class="hero" data-delay="120">
      <div class="block primary"></div>
      <div class="block secondary"></div>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    css.write_text(
        """html, body { margin: 0; }
.hero { width: 1920px; }
.block { width: 1920px; }
.primary { height: 200px; background: #112233; opacity: 0; }
.secondary { height: 180px; background: #445566; transform: translateY(20px); }
""",
        encoding="utf-8",
    )

    design = tmp_path / "design.png"
    mod.render_html_to_png(html, 1920, design)

    report = tmp_path / "visual-report.json"
    out_dir = tmp_path / "artifacts"
    first = _run_cli(
        "--html", str(html),
        "--css", str(css),
        "--design", str(design),
        "--emit-report", str(report),
        "--out-dir", str(out_dir),
    )
    assert first.returncode == 0, first.stdout + first.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["html_sha256"]
    assert payload["css_sha256"]
    assert payload["design_sha256"]
    assert Path(payload["diff_image_path"]).is_file()

    css.write_text(
        """html, body { margin: 0; }
.hero { width: 1920px; }
.block { width: 1920px; }
.primary { height: 260px; background: #112233; opacity: 0; }
.secondary { height: 180px; background: #445566; transform: translateY(20px); }
""",
        encoding="utf-8",
    )
    second = _run_cli(
        "--html", str(html),
        "--css", str(css),
        "--design", str(design),
        "--emit-report", str(tmp_path / "visual-report-fail.json"),
        "--out-dir", str(out_dir),
    )
    assert second.returncode == 1, second.stdout + second.stderr


@pytest.mark.browser
def test_render_stability_section_on_and_lazy_images_are_deterministic(tmp_path: Path) -> None:
    pytest.importorskip("playwright.sync_api")
    mod = _load_module()
    pixel = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="
    )

    html = tmp_path / "index.html"
    css = tmp_path / "common.css"
    html.write_text(
        textwrap.dedent(
            f"""
            <!doctype html>
            <html>
            <head>
              <meta charset="utf-8">
              <link rel="stylesheet" href="common.css">
            </head>
            <body>
              <section class="hero">
                <div class="card" data-delay="300" data-direction="left"></div>
                <img loading="lazy" width="1920" height="40" src="data:image/png;base64,{pixel}" alt="">
              </section>
              <script>
                setTimeout(() => document.body.classList.add("section_on"), 400);
              </script>
            </body>
            </html>
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    css.write_text(
        textwrap.dedent(
            """
            html,body{margin:0}
            .hero{width:1920px;background:#ffffff}
            [data-delay]{position:relative;opacity:0}
            [data-direction="left"]{left:-400px}
            .section_on [data-delay]{opacity:1}
            .section_on [data-direction="left"]{left:0}
            .card{width:1920px;height:200px;background:#112233}
            img{display:block;width:1920px;height:40px}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    try:
        mod.render_html_to_png(html, 1920, first)
        mod.render_html_to_png(html, 1920, second)
    except Exception as exc:  # noqa: BLE001
        if "playwright" in str(exc).lower():
            pytest.skip("Playwright browser runtime unavailable")
        raise

    result = mod.compare_images(
        first,
        second,
        diff_threshold=0.0,
        height_threshold=0.0,
        pixel_tolerance=0,
    )
    assert result.diff_ratio == pytest.approx(0.0)
    assert result.height_delta_ratio == pytest.approx(0.0)


def test_visual_failloud_width_mismatch(tmp_path: Path) -> None:
    html = tmp_path / "index.html"
    html.write_text("<!doctype html><html><body>visual</body></html>", encoding="utf-8")
    design = _image(tmp_path / "design.png", width=1200, height=100)

    result = _run_cli("--html", str(html), "--design", str(design), "--width", "1920")

    assert result.returncode != 0
    assert "width mismatch" in (result.stdout + result.stderr).lower()


def test_visual_failloud_missing_design(tmp_path: Path) -> None:
    html = tmp_path / "index.html"
    html.write_text("<!doctype html><html><body>visual</body></html>", encoding="utf-8")

    result = _run_cli("--html", str(html), "--design", str(tmp_path / "missing.png"))

    assert result.returncode != 0
    assert "design" in (result.stdout + result.stderr).lower()
    assert "missing" in (result.stdout + result.stderr).lower()


@pytest.mark.browser
def test_visual_failloud_allow_visual_mismatch_downgrades_failure(tmp_path: Path) -> None:
    pytest.importorskip("playwright.sync_api")
    mod = _load_module()

    html = tmp_path / "index.html"
    html.write_text(
        "<!doctype html><html><body style='margin:0'><div style='width:1920px;height:200px;background:#fff'></div></body></html>",
        encoding="utf-8",
    )
    design = tmp_path / "design.png"
    _image(design, width=1920, height=200, color=(0, 0, 0, 255))
    report = tmp_path / "report.json"

    result = _run_cli(
        "--html", str(html),
        "--design", str(design),
        "--emit-report", str(report),
        "--allow-visual-mismatch",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["allow_visual_mismatch"] is True
    assert payload["passed"] is True
    assert payload["diff_ratio"] > payload["thresholds"]["diff_ratio"]


@pytest.mark.browser
def test_visual_ledger_appends_optional_step_without_breaking_order(tmp_path: Path) -> None:
    pytest.importorskip("playwright.sync_api")

    ledger = tmp_path / "workflow-ledger.json"
    subprocess.run(
        [
            sys.executable,
            str(TOOLS / "workflow-ledger.py"),
            "--ledger",
            str(ledger),
            "append",
            "--step",
            "extract",
            "--provider",
            "figma-section-spec",
            "--section",
            "main",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    for step, provider in (("structure", "omx"), ("values", "omx"), ("verify", "pm-verify")):
        subprocess.run(
            [
                sys.executable,
                str(TOOLS / "workflow-ledger.py"),
                "--ledger",
                str(ledger),
                "append",
                "--step",
                step,
                "--provider",
                provider,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    html = tmp_path / "index.html"
    html.write_text(
        "<!doctype html><html><body style='margin:0'><div style='width:1920px;height:100px;background:#abc'></div></body></html>",
        encoding="utf-8",
    )
    design = tmp_path / "design.png"
    _image(design, width=1920, height=100, color=(170, 187, 204, 255))

    result = _run_cli(
        "--html", str(html),
        "--design", str(design),
        "--section", "main",
        "--ledger", str(ledger),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert payload["steps"][-1]["step"] == "visual-compare"
    assert payload["steps"][-1]["provider"] == "visual-compare"

    order = subprocess.run(
        [sys.executable, str(TOOLS / "check-workflow-order.py"), "--ledger", str(ledger)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert order.returncode == 0, order.stdout + order.stderr

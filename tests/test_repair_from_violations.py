import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPAIR_SCRIPT = ROOT / "tools" / "repair-from-violations.py"


def _run_repair(tmp_path: Path, css_text: str, html_text: str = "<html><body><div class=\"title\">x</div></body></html>"):
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    report_path = tmp_path / "repair-report.json"

    html_path.write_text(html_text + "\n", encoding="utf-8")
    css_path.write_text(textwrap.dedent(css_text).strip() + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(REPAIR_SCRIPT),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--report",
            str(report_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    return proc, css_path.read_text(encoding="utf-8"), report


def test_pill_radius_999_to_2em(tmp_path):
    proc, css, report = _run_repair(
        tmp_path,
        """
        .chip{border-radius:999px}
        .chip2{border-radius:99px}
        """,
    )
    assert proc.returncode == 0
    assert "999px" not in css
    assert "99px" not in css
    assert "border-radius:2em" in css
    assert report["by_category"]["pill_radius"] >= 2


def test_rgba_opaque_to_hex(tmp_path):
    proc, css, report = _run_repair(
        tmp_path,
        """
        .box{background:rgba(255, 0, 16, 1)}
        .box2{background:rgba(255,0,0,1.0)}
        """,
    )
    assert proc.returncode == 0
    assert "rgba(" not in css
    assert "#ff0010" in css.lower()
    assert report["by_category"]["rgba_to_hex"] >= 2


def test_rgb_to_hex(tmp_path):
    proc, css, report = _run_repair(
        tmp_path,
        """
        .txt{color:rgb(0, 15, 255)}
        """,
    )
    assert proc.returncode == 0
    assert "rgb(" not in css
    assert "#000fff" in css.lower()
    assert report["by_category"]["rgb_to_hex"] >= 1


def test_hex8_opaque_to_hex6(tmp_path):
    proc, css, report = _run_repair(
        tmp_path,
        """
        .shadow{box-shadow:0 0 0 1px #AABBCCFF}
        """,
    )
    assert proc.returncode == 0
    assert "#aabbccff" not in css.lower()
    assert "#aabbcc" in css.lower()
    assert report["by_category"]["hex8_opaque_to_hex6"] >= 1


def test_multiline_selector_to_one_line(tmp_path):
    proc, css, report = _run_repair(
        tmp_path,
        """
        .btn,
        .btn_link
        {
          color: #fff;
          padding: 10px;
        }
        """,
    )
    assert proc.returncode == 0
    assert ".btn, .btn_link{" in css
    assert ".btn,\n" not in css
    assert report["by_category"]["multiline_selector"] >= 1


def test_media_indent_removed(tmp_path):
    proc, css, report = _run_repair(
        tmp_path,
        """
        @media screen and (max-width: 768px) {
          .box {
            color: #fff;
          }
        }
        """,
    )
    assert proc.returncode == 0
    assert "@media screen and (max-width: 768px) {" in css
    assert re.search(r"\n  \.box", css) is None
    assert report["by_category"]["media_indent"] >= 1


def test_letter_spacing_px_to_em(tmp_path):
    proc, css, report = _run_repair(
        tmp_path,
        """
        .title{
          font-size:20px;
          letter-spacing:4px;
        }
        """,
    )
    assert proc.returncode == 0
    assert "letter-spacing:4px" not in css.replace(" ", "")
    assert "letter-spacing:0.2em" in css.replace(" ", "")
    assert report["by_category"]["letter_spacing_px_to_em"] >= 1


def test_duplicate_selector_merged(tmp_path):
    proc, css, report = _run_repair(
        tmp_path,
        """
        .dup{color:#111}
        .dup{background:#fff}
        """,
    )
    assert proc.returncode == 0
    assert css.count(".dup{") == 1
    assert "color:#111" in css and "background:#fff" in css
    assert report["by_category"]["duplicate_selector_merge"] >= 1


def test_idempotent(tmp_path):
    css_text = """
    .pill{
      border-radius:9999px;
      color:rgb(0,0,0);
      background:rgba(255,255,255,1);
      box-shadow:0 0 0 1px #112233FF;
      font-size:20px;
      letter-spacing:2px;
    }
    .pill,
    .pill_link
    {
      margin:0;
    }
    .dup{color:#111}
    .dup{background:#fff}
    @media screen and (max-width:768px){
      .pill{padding:0}
    }
    """

    first_proc, first_css, first_report = _run_repair(tmp_path, css_text)
    assert first_proc.returncode == 0
    assert first_report["total_fixed"] > 0

    second_proc, second_css, second_report = _run_repair(tmp_path, first_css)
    assert second_proc.returncode == 0
    assert second_report["total_fixed"] == 0
    assert second_css == first_css

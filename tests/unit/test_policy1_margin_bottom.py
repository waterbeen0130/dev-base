from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"
POLICY1_SPEC_FIXTURE = ROOT / "tests" / "fixtures" / "req029" / "policy1_vertical_spacing_spec.json"


def _run_validator_with_css(tmp_path: Path, css_text: str) -> subprocess.CompletedProcess[str]:
    spec_path = tmp_path / "spec.json"
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"

    spec_path.write_text(POLICY1_SPEC_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    html_path.write_text(
        "<html><body><div class='stack'><div class='item'>A</div><div class='item'>B</div></div></body></html>\n",
        encoding="utf-8",
    )
    css_path.write_text(css_text.strip() + "\n", encoding="utf-8")

    return subprocess.run(
        [
            sys.executable,
            str(FIGMA_VALIDATE),
            "--spec",
            str(spec_path),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_policy1_passes_when_vertical_itemspacing_uses_margin_bottom(tmp_path: Path) -> None:
    proc = _run_validator_with_css(
        tmp_path,
        """
        .stack { display: flex; flex-direction: column; }
        .stack > .item { margin-bottom: 24px; }
        """,
    )

    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0
    assert "[POLICY-1]" not in combined


def test_policy1_fails_when_vertical_itemspacing_uses_gap(tmp_path: Path) -> None:
    proc = _run_validator_with_css(
        tmp_path,
        """
        .stack { display: flex; flex-direction: column; gap: 24px; }
        """,
    )

    combined = proc.stdout + proc.stderr
    assert proc.returncode == 1
    assert "[POLICY-1] VERTICAL frame itemSpacing must map to margin-bottom" in combined

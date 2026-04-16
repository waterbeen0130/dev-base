import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SEMANTIC = ROOT / "tools" / "validate-semantic.py"


def _write_case_files(tmp_path: Path, css: str) -> tuple[Path, Path]:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    html_path.write_text("<html><body><div class='wrap'></div></body></html>\n", encoding="utf-8")
    css_path.write_text(textwrap.dedent(css).strip() + "\n", encoding="utf-8")
    return html_path, css_path


def _write_column_gap_rule(tmp_path: Path) -> Path:
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        textwrap.dedent(
            """
            rules:
              - id: no_column_flex_gap
                description: flex-direction:column 컨테이너에서 gap 사용 금지
                severity: error
                applies_to: [common, basic, landing]
                category: css.layout
                validation:
                  type: custom
                  target: css
                  custom_handler: check_no_column_gap
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return rules_path


def test_column_flex_gap_violation_fails(tmp_path):
    html_path, css_path = _write_case_files(
        tmp_path,
        """
        .wrap{display:flex;flex-direction:column;gap:20px;}
        """,
    )
    rules_path = _write_column_gap_rule(tmp_path)

    proc = subprocess.run(
        [
            sys.executable,
            str(VALIDATE_SEMANTIC),
            "--rules",
            str(rules_path),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--profile",
            "landing",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode != 0
    assert "no_column_flex_gap" in proc.stdout


def test_column_flex_gap_clean_case_passes(tmp_path):
    html_path, css_path = _write_case_files(
        tmp_path,
        """
        .wrap{display:flex;flex-direction:column;}
        .wrap + .wrap{margin-top:20px;}
        """,
    )
    rules_path = _write_column_gap_rule(tmp_path)

    proc = subprocess.run(
        [
            sys.executable,
            str(VALIDATE_SEMANTIC),
            "--rules",
            str(rules_path),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--profile",
            "landing",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0

import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "validate-semantic.py"
RULES_PATH = ROOT / "rules" / "rules.yaml"

spec = importlib.util.spec_from_file_location("validate_semantic", SCRIPT_PATH)
validate_semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_semantic)


def _write_html_css(tmp_path: Path, css_text: str, html_text: str = "<html><body></body></html>") -> tuple[Path, Path]:
    html_path = tmp_path / "index.html"
    css_path = tmp_path / "common.css"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html_text, encoding="utf-8")
    css_path.write_text(textwrap.dedent(css_text).strip() + "\n", encoding="utf-8")
    return html_path, css_path


def _results_by_rule(tmp_path: Path, css_text: str, profile: str = "landing") -> dict:
    html_path, css_path = _write_html_css(tmp_path, css_text)
    results = validate_semantic.run_validation(
        rules_path=str(RULES_PATH),
        html_path=str(html_path),
        css_path=str(css_path),
        profile=profile,
    )
    return {result.rule_id: result for result in results}


def test_no_hex8_literal_detects_only_real_literal(tmp_path):
    results = _results_by_rule(
        tmp_path,
        """
        /* #ffffff26 in comment must be ignored */
        .icon{background-image:url(data:image/svg+xml;base64,PHN2ZyBmaWxsPSIjZmZmZmZmMjYiPjwvc3ZnPg==)}
        .ok{color:#fff}
        .bad{color:#ffffff26}
        """,
    )

    assert "no_hex8_literal" in results
    rule = results["no_hex8_literal"]
    assert rule.passed is False
    assert "#ffffff26" in rule.message


def test_line_height_tidy_ratio_flags_non_tidy_and_skips_markers(tmp_path):
    results = _results_by_rule(
        tmp_path,
        """
        .ok_a{line-height:1.3}
        .ok_b{line-height:1.45}
        .ok_c{line-height:1.667}
        .ok_d{line-height:1.8}
        .skip_a{line-height:1}
        .skip_b{line-height:normal}
        .skip_c{line-height:var(--lh-title)}
        .skip_d{line-height:1.193; /* lh-exact */}
        .bad_a{line-height:1.193}
        .bad_b{line-height:1.471}
        .bad_c{line-height:1.818}
        """,
    )

    assert "line_height_tidy_ratio" in results
    rule = results["line_height_tidy_ratio"]
    assert rule.passed is False
    assert "1.193" in rule.message


def test_font_family_redundant_detects_repetition(tmp_path):
    results = _results_by_rule(
        tmp_path,
        """
        *{font-family:'Pretendard',sans-serif}
        body{font-family:'Pretendard',sans-serif}
        .hero_title{font-family:'Pretendard',sans-serif}
        .hero_desc{font-family:'Pretendard',sans-serif}
        .hero_note{font-family:'Pretendard',Arial,sans-serif}
        """,
    )

    assert "font_family_redundant" in results
    rule = results["font_family_redundant"]
    assert rule.passed is False
    assert "pretendard" in rule.message.lower()


def test_font_family_redundant_ignores_different_fallback_chain(tmp_path):
    results = _results_by_rule(
        tmp_path,
        """
        *{font-family:'Pretendard',sans-serif}
        body{font-family:'Pretendard',Arial,sans-serif}
        .hero_title{font-family:'Pretendard',sans-serif}
        .hero_desc{font-family:'Pretendard',Arial,sans-serif}
        """,
    )

    assert "font_family_redundant" in results
    rule = results["font_family_redundant"]
    assert rule.passed is True


def test_empty_media_block_detects_empty_and_ignores_print(tmp_path):
    results = _results_by_rule(
        tmp_path,
        """
        @media screen and (max-width:1200px) { }
        @media print { }
        @media screen and (max-width:900px) {
        /* only comment */
        }
        @media screen and (max-width:768px) {
        }
        """,
    )

    assert "empty_media_block" in results
    rule = results["empty_media_block"]
    assert rule.passed is False
    assert "3" in rule.message


def test_box_sizing_redundant_allows_universal_reset_only(tmp_path):
    results = _results_by_rule(
        tmp_path,
        """
        *,*::before,*::after{box-sizing:border-box}
        """,
    )

    assert "box_sizing_redundant" in results
    rule = results["box_sizing_redundant"]
    assert rule.passed is True


def test_box_sizing_redundant_detects_non_universal_repetition(tmp_path):
    results = _results_by_rule(
        tmp_path,
        """
        *,*::before,*::after{box-sizing:border-box}
        .card{box-sizing:border-box}
        .panel{box-sizing:border-box}
        """,
    )

    assert "box_sizing_redundant" in results
    rule = results["box_sizing_redundant"]
    assert rule.passed is False
    assert "2" in rule.message


def test_landing_unit_mixed_scale_skips_basic_and_fails_landing(tmp_path):
    css = """
    html{font-size:clamp(14px,1.2vw,16px)}
    body{font-size:1rem}
    """
    landing_results = _results_by_rule(tmp_path / "landing", css, profile="landing")
    basic_results = _results_by_rule(tmp_path / "basic", css, profile="basic")

    assert "landing_unit_mixed_scale" in landing_results
    landing_rule = landing_results["landing_unit_mixed_scale"]
    assert landing_rule.passed is False

    assert "landing_unit_mixed_scale" in basic_results
    basic_rule = basic_results["landing_unit_mixed_scale"]
    assert basic_rule.passed is True
    assert basic_rule.skipped is True


def test_profile_auto_detects_project_type_and_flag_overrides(tmp_path):
    project_dir = tmp_path / "sample_project"
    html_path = project_dir / "html" / "page" / "index.html"
    css_path = project_dir / "html" / "css" / "common.css"
    rules_path = tmp_path / "rules_only_landing.yaml"

    html_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.parent.mkdir(parents=True, exist_ok=True)

    html_path.write_text("<html><body></body></html>\n", encoding="utf-8")
    css_path.write_text("html{font-size:clamp(14px,1.2vw,16px)}\n", encoding="utf-8")
    (project_dir / ".project-type").write_text("landing\n", encoding="utf-8")

    rules_path.write_text(
        textwrap.dedent(
            """
            rules:
              - id: landing_unit_mixed_scale
                description: test rule
                severity: warning
                applies_to: [common, basic, landing]
                category: css.typography
                validation:
                  type: custom
                  target: css
                  custom_handler: _check_landing_unit_mixed_scale
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    auto_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--rules",
            str(rules_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert auto_proc.returncode == 1
    assert "landing_unit_mixed_scale" in auto_proc.stdout

    override_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--html",
            str(html_path),
            "--css",
            str(css_path),
            "--rules",
            str(rules_path),
            "--profile",
            "basic",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert override_proc.returncode == 0
    assert "landing_unit_mixed_scale" not in override_proc.stdout

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIGMA_VALIDATE = ROOT / "tools" / "figma-validate.py"
DRIFT_CHECKER = ROOT / "tools" / "check-rules-drift.py"
POLICY1_SPEC_FIXTURE = ROOT / "tests" / "fixtures" / "req029" / "policy1_vertical_spacing_spec.json"
POLICY3_FIXTURE = ROOT / "tests" / "fixtures" / "req029" / "policy3_rules_conflict_node.json"

REQ029_POLICY_IDS = [
    "vertical_frame_itemspacing_uses_margin_bottom",
    "no_constraints_to_position_absolute_mapping",
    "figma_rules_conflict_uses_meta_marker",
]

REQ030_032_V2_CATEGORIES = [
    "v2.fills.solid.match",
    "v2.fills.gradient.match",
    "v2.fills.image.match",
    "v2.effects.shadow.match",
    "v2.effects.blur.match",
    "v2.opacity.match",
    "v2.blendMode.match",
    "v2.strokes.match",
    "v2.cornerRadii.match",
    "v2.layoutSizing.match",
    "v2.textCase.match",
    "v2.textDecoration.match",
    "v2.componentId.match",
    "v2.assetManifest.exists",
]


def _load_figma_validate_module():
    spec = importlib.util.spec_from_file_location("figma_validate_req033_regression", FIGMA_VALIDATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_policy1_with_css(tmp_path: Path, css_text: str) -> subprocess.CompletedProcess[str]:
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
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_req029_policy_enforcements_remain_passed(capsys, tmp_path: Path) -> None:
    drift_result = subprocess.run(
        [sys.executable, str(DRIFT_CHECKER), "--policy-ids", *REQ029_POLICY_IDS],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    drift_output = "\n".join(part for part in (drift_result.stdout, drift_result.stderr) if part).strip()
    assert drift_result.returncode == 0, drift_output
    for policy_id in REQ029_POLICY_IDS:
        assert f"[OK] {policy_id}" in drift_output, drift_output

    policy1_proc = _run_policy1_with_css(
        tmp_path,
        """
        .stack { display: flex; flex-direction: column; }
        .stack > .item { margin-bottom: 24px; }
        """,
    )
    policy1_output = policy1_proc.stdout + policy1_proc.stderr
    assert policy1_proc.returncode == 0, policy1_output
    assert "[POLICY-1]" not in policy1_output

    figma_validate = _load_figma_validate_module()
    node = json.loads(POLICY3_FIXTURE.read_text(encoding="utf-8"))
    seen: set[tuple[str, str]] = set()

    bypassed = figma_validate.enforce_policy3_rules_conflict_bypass(node, "no_color_grid", seen)
    assert bypassed is True
    first_log = capsys.readouterr().out
    assert "[RULES-CONFLICT]" in first_log

    bypassed_again = figma_validate.enforce_policy3_rules_conflict_bypass(node, "no_color_grid", seen)
    assert bypassed_again is True
    assert capsys.readouterr().out == ""


def test_req030_031_032_v2_categories_exposed_in_version_info() -> None:
    result = subprocess.run(
        [sys.executable, str(FIGMA_VALIDATE), "--version-info"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    combined = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    assert result.returncode == 0, combined

    for category in REQ030_032_V2_CATEGORIES:
        assert f"- {category}" in combined, combined

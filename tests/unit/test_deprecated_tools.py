"""DOD-004: deprecated/forbidden tool usage detection.

Flags resurrection of deprecated tool files and actual invocations (or the
--converge auto-retry flag) in scripts. Prohibition *mentions* in docs (.md)
must NOT be flagged (zero false positives).
"""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECK_PATH = ROOT / "tools" / "check-deprecated-tools.py"

spec = importlib.util.spec_from_file_location("check_deprecated_tools", CHECK_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_clean_tree_passes(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "ok.py").write_text("print('hello')\n", encoding="utf-8")
    assert mod.find_violations(tmp_path) == []


def test_resurrected_deprecated_file_is_flagged(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "generate.py").write_text("# resurrected\n", encoding="utf-8")
    violations = mod.find_violations(tmp_path)
    assert any("generate.py" in v["detail"] for v in violations)


def test_invocation_in_script_is_flagged(tmp_path):
    (tmp_path / "run.sh").write_text(
        "#!/bin/bash\npython3 tools/repair-from-violations.py --converge\n", encoding="utf-8"
    )
    violations = mod.find_violations(tmp_path)
    assert violations  # both the invocation and --converge are forbidden


def test_converge_flag_is_flagged(tmp_path):
    (tmp_path / "x.py").write_text("subprocess.run(['post', '--converge'])\n", encoding="utf-8")
    violations = mod.find_violations(tmp_path)
    assert any("--converge" in v["detail"] for v in violations)


def test_prohibition_mention_in_markdown_is_not_flagged(tmp_path):
    (tmp_path / "RULES.md").write_text(
        "## 금지\n- generate.py / json-to-html.py 사용 금지\n- --converge 루프 금지\n", encoding="utf-8"
    )
    assert mod.find_violations(tmp_path) == []

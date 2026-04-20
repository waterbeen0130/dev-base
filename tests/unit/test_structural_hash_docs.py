from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_structural_diff_documents_normalization_rules_in_first_100_lines() -> None:
    first_100_lines = "\n".join((ROOT / "tools" / "structural-diff.py").read_text(encoding="utf-8").splitlines()[:100])

    assert "정규화 규칙: tag + sorted(class_list) + children_index_path, text/id/inline style 제외" in first_100_lines

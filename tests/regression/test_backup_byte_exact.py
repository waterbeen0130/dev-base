from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BACKUP_DIR = ROOT / "extracted.v1.backup"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git_show_bytes(path_in_repo: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"HEAD~1:{path_in_repo}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")
    return proc.stdout


def test_backup_is_byte_exact_to_head_parent_extracted_files() -> None:
    backup_files = sorted(path for path in BACKUP_DIR.rglob("*") if path.is_file())
    assert backup_files, "extracted.v1.backup/ 에 파일이 없습니다"

    mismatches: list[str] = []

    for backup_file in backup_files:
        relative = backup_file.relative_to(BACKUP_DIR)
        original_path = (Path("extracted") / relative).as_posix()

        expected_bytes = _git_show_bytes(original_path)
        current_bytes = backup_file.read_bytes()

        if _sha256(expected_bytes) != _sha256(current_bytes):
            mismatches.append(original_path)

    assert not mismatches, f"byte-exact 불일치 파일: {', '.join(mismatches)}"

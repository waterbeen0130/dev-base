from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKUP_DIR = ROOT / "extracted.v1.backup"
HASH_FIXTURE = ROOT / "tests" / "fixtures" / "req029_backup_hashes.json"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_backup_is_byte_exact_to_req029_hash_fixture() -> None:
    backup_files = sorted(path for path in BACKUP_DIR.rglob("*") if path.is_file())
    assert backup_files, "extracted.v1.backup/ 에 파일이 없습니다"
    expected_hashes = json.loads(HASH_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(expected_hashes, dict)

    missing_from_backup: list[str] = []
    mismatches: list[str] = []
    extras: list[str] = []

    for backup_file in backup_files:
        relative = backup_file.relative_to(BACKUP_DIR).as_posix()
        expected_hash = expected_hashes.get(relative)
        if not isinstance(expected_hash, str):
            extras.append(relative)
            continue
        current_bytes = backup_file.read_bytes()
        if expected_hash != _sha256(current_bytes):
            mismatches.append(relative)

    for rel_path in expected_hashes:
        if not (BACKUP_DIR / rel_path).exists():
            missing_from_backup.append(rel_path)

    assert not extras, f"fixture 에 없는 백업 파일: {', '.join(sorted(extras))}"
    assert not missing_from_backup, f"백업에서 누락된 fixture 기준 파일: {', '.join(sorted(missing_from_backup))}"
    assert not mismatches, f"byte-exact 불일치 파일: {', '.join(sorted(mismatches))}"

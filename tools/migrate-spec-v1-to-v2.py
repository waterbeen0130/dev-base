#!/usr/bin/env python3
"""Migrate extracted spec JSON files from schema v1 to v2 (add-only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


SCHEMA_VERSION_V2 = "2.0.0"
DEFAULT_SCAN_ROOT = Path("/mnt/d/dev-base")
WORKTREE_ROOT = Path(__file__).resolve().parents[1]
SPEC_FILE_PATTERN = re.compile(r".+_spec\.json$")
V1_SEMVER_PATTERN = re.compile(r"^1(?:\.\d+\.\d+)?$")
V2_SEMVER_PATTERN = re.compile(r"^2(?:\.\d+\.\d+)?$")

V2_TOP_LEVEL_NULL_KEYS = ("_extra",)
V2_SECTION_NULL_KEYS = ("_extra",)
V2_TEXT_NODE_NULL_KEYS = (
    "characterStyleOverrides",
    "textCase",
    "textDecoration",
    "paragraphSpacing",
    "paragraphIndent",
    "rules_conflict",
    "_extra",
)
V2_FRAME_NODE_NULL_KEYS = (
    "fills_v2",
    "effects",
    "strokes",
    "strokeWeight",
    "strokeAlign",
    "layoutSizingHorizontal",
    "layoutSizingVertical",
    "layoutGrow",
    "layoutAlign",
    "constraints",
    "rules_conflict",
    "_extra",
)
V2_VECTOR_NODE_NULL_KEYS = ("rules_conflict", "_extra")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate *_spec.json files from schema v1 to v2.")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true", help="Print planned changes without writing files.")
    mode_group.add_argument("--apply", action="store_true", help="Apply migration and create backups.")
    mode_group.add_argument("--rollback", action="store_true", help="Restore specs from extracted.v1.backup.")
    parser.add_argument("--root", default=str(DEFAULT_SCAN_ROOT), help="Scan root (default: /mnt/d/dev-base).")
    return parser.parse_args()


def stable_md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()  # noqa: S324 - integrity fingerprint only


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def is_schema_v1(value: object) -> bool:
    if isinstance(value, int):
        return value == 1
    if isinstance(value, str):
        return bool(V1_SEMVER_PATTERN.match(value.strip()))
    return False


def is_schema_v2(value: object) -> bool:
    if isinstance(value, int):
        return value == 2
    if isinstance(value, str):
        return bool(V2_SEMVER_PATTERN.match(value.strip()))
    return False


def ensure_null_keys(target: object, keys: tuple[str, ...]) -> None:
    if not isinstance(target, dict):
        return
    for key in keys:
        target.setdefault(key, None)


def apply_v2_shape(payload: dict) -> dict:
    payload["schema_version"] = SCHEMA_VERSION_V2
    ensure_null_keys(payload, V2_TOP_LEVEL_NULL_KEYS)
    ensure_null_keys(payload.get("section"), V2_SECTION_NULL_KEYS)

    text_nodes = payload.get("text_nodes")
    if isinstance(text_nodes, list):
        for node in text_nodes:
            ensure_null_keys(node, V2_TEXT_NODE_NULL_KEYS)

    frame_nodes = payload.get("frame_nodes")
    if isinstance(frame_nodes, list):
        for node in frame_nodes:
            ensure_null_keys(node, V2_FRAME_NODE_NULL_KEYS)

    vector_nodes = payload.get("vector_nodes")
    if isinstance(vector_nodes, list):
        for node in vector_nodes:
            ensure_null_keys(node, V2_VECTOR_NODE_NULL_KEYS)

    return payload


def find_spec_files(root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in root.rglob("*_spec.json"):
        if not path.is_file():
            continue
        if not SPEC_FILE_PATTERN.match(path.name):
            continue
        if "extracted" not in path.parts:
            continue
        if not path.is_relative_to(WORKTREE_ROOT):
            continue
        matches.append(path)
    return sorted(matches)


def nearest_extracted_dir(path: Path) -> Path | None:
    current = path.parent
    while True:
        if current.name == "extracted":
            return current
        if current.parent == current:
            return None
        current = current.parent


def backup_path_for_spec(spec_path: Path) -> tuple[Path, Path] | None:
    extracted_dir = nearest_extracted_dir(spec_path)
    if extracted_dir is None:
        return None
    relative = spec_path.relative_to(extracted_dir)
    backup_dir = extracted_dir.parent / "extracted.v1.backup"
    return backup_dir, backup_dir / relative


def ensure_backup(spec_path: Path, dry_run: bool) -> tuple[bool, str]:
    resolved = backup_path_for_spec(spec_path)
    if resolved is None:
        return False, "skip(no-extracted-parent)"
    backup_dir, backup_path = resolved
    source_md = spec_path.with_suffix(".md")
    backup_md = backup_path.with_suffix(".md")
    created_messages: list[str] = []
    try:
        if not backup_path.exists():
            if dry_run:
                created_messages.append(f"backup-create:{backup_path}")
            else:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(spec_path, backup_path)
                created_messages.append(f"backup-created:{backup_path}")
        else:
            created_messages.append(f"backup-exists:{backup_path}")

        if source_md.exists() and not backup_md.exists():
            if dry_run:
                created_messages.append(f"backup-create:{backup_md}")
            else:
                backup_md.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_md, backup_md)
                created_messages.append(f"backup-created:{backup_md}")
        elif source_md.exists():
            created_messages.append(f"backup-exists:{backup_md}")
    except PermissionError:
        return False, f"backup-skip-permission:{spec_path}"
    except OSError as exc:
        return False, f"backup-fail:{spec_path} ({exc})"

    created = any(message.startswith("backup-create:") or message.startswith("backup-created:") for message in created_messages)
    return created or backup_path.exists(), ", ".join(created_messages)


def migrate_one(spec_path: Path, dry_run: bool) -> tuple[bool, str]:
    raw_before = read_bytes(spec_path)
    try:
        payload = json.loads(raw_before.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return False, f"invalid-json:{spec_path} ({exc})"
    if not isinstance(payload, dict):
        return False, f"invalid-root:{spec_path}"

    before_version = payload.get("schema_version")
    if is_schema_v2(before_version):
        return True, f"already-v2:{spec_path}"

    apply_v2_shape(payload)
    raw_after = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    changed = raw_before != raw_after
    if not changed:
        return True, f"unchanged:{spec_path}"

    if dry_run:
        return True, f"migrate:{spec_path} md5 {stable_md5(raw_before)} -> {stable_md5(raw_after)}"

    try:
        write_bytes_atomic(spec_path, raw_after)
    except PermissionError:
        return False, f"write-skip-permission:{spec_path}"
    except OSError as exc:
        return False, f"write-fail:{spec_path} ({exc})"
    return True, f"migrated:{spec_path} md5 {stable_md5(raw_before)} -> {stable_md5(raw_after)}"


def run_dry_or_apply(root: Path, dry_run: bool) -> int:
    specs = find_spec_files(root)
    if not specs:
        print(f"[INFO] no *_spec.json found under {root}")
        return 0

    ok_count = 0
    fail_count = 0
    for spec_path in specs:
        backup_created, backup_message = ensure_backup(spec_path, dry_run=dry_run)
        print(f"[BACKUP] {backup_message}")
        if not backup_created and (
            backup_message.startswith("skip(")
            or backup_message.startswith("backup-skip-permission:")
        ):
            print(f"[SKIP] {spec_path}")
            continue
        success, message = migrate_one(spec_path, dry_run=dry_run)
        if success:
            ok_count += 1
            print(f"[OK] {message}")
        else:
            fail_count += 1
            print(f"[FAIL] {message}", file=sys.stderr)

    print(f"[SUMMARY] mode={'dry-run' if dry_run else 'apply'} ok={ok_count} fail={fail_count} scanned={len(specs)}")
    return 0 if fail_count == 0 else 1


def find_backup_files(root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in root.rglob("*_spec.*"):
        if not path.is_file():
            continue
        if path.suffix not in {".json", ".md"}:
            continue
        if not (path.name.endswith("_spec.json") or path.name.endswith("_spec.md")):
            continue
        if "extracted.v1.backup" not in path.parts:
            continue
        if not path.is_relative_to(WORKTREE_ROOT):
            continue
        matches.append(path)
    return sorted(matches)


def original_path_from_backup(backup_spec: Path) -> Path | None:
    current = backup_spec.parent
    while True:
        if current.name == "extracted.v1.backup":
            rel = backup_spec.relative_to(current)
            return current.parent / "extracted" / rel
        if current.parent == current:
            return None
        current = current.parent


def run_rollback(root: Path) -> int:
    backups = find_backup_files(root)
    if not backups:
        print(f"[INFO] no extracted.v1.backup/*_spec.* found under {root}")
        return 0

    ok_count = 0
    fail_count = 0
    for backup in backups:
        original = original_path_from_backup(backup)
        if original is None:
            fail_count += 1
            print(f"[FAIL] invalid backup layout: {backup}", file=sys.stderr)
            continue
        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, original)
            ok_count += 1
            print(f"[OK] restored:{original} <= {backup}")
        except Exception as exc:  # noqa: BLE001
            fail_count += 1
            print(f"[FAIL] restore-error:{original} ({exc})", file=sys.stderr)

    print(f"[SUMMARY] mode=rollback ok={ok_count} fail={fail_count} scanned={len(backups)}")
    return 0 if fail_count == 0 else 1


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if args.rollback:
        return run_rollback(root)
    if args.apply:
        return run_dry_or_apply(root, dry_run=False)
    return run_dry_or_apply(root, dry_run=True)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
CACHE_PATH="$ROOT_DIR/.gran-maestro/state/drift-cache.json"
RULES_PATH="$ROOT_DIR/rules/rules.yaml"
RULES_MTIME_ORIG="$(stat -c %Y "$RULES_PATH")"
CACHE_BACKUP_PATH="$TMP_DIR/drift-cache.backup.json"
CACHE_EXISTED=0

if [[ -f "$CACHE_PATH" ]]; then
  cp "$CACHE_PATH" "$CACHE_BACKUP_PATH"
  CACHE_EXISTED=1
fi

cleanup() {
  touch -m -d "@${RULES_MTIME_ORIG}" "$RULES_PATH" 2>/dev/null || true
  if [[ "$CACHE_EXISTED" -eq 1 ]]; then
    mkdir -p "$(dirname "$CACHE_PATH")"
    cp "$CACHE_BACKUP_PATH" "$CACHE_PATH"
  else
    rm -f "$CACHE_PATH"
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

rm -f "$CACHE_PATH"

run_verify() {
  local label="$1"
  local logfile="$TMP_DIR/${label}.log"

  set +e
  python3 tools/post-impl-verify.py \
    --no-figma \
    --no-repair \
    --html landing/index.html \
    --css landing/css/common.css >"$logfile" 2>&1
  local ec=$?
  set -e

  echo "===== ${label} ====="
  cat "$logfile"
  echo "[EXIT] ${label}=${ec}"
  echo

  if [[ "$ec" -ne 0 ]]; then
    echo "[FAIL] ${label}: expected exit 0, got ${ec}" >&2
    exit 1
  fi
}

run_verify "first_run"
if [[ ! -f "$CACHE_PATH" ]]; then
  echo "[FAIL] drift cache was not created: $CACHE_PATH" >&2
  exit 1
fi
if ! grep -F "[DRIFT] check-rules-drift executed" "$TMP_DIR/first_run.log" >/dev/null; then
  echo "[FAIL] first_run should execute drift check" >&2
  exit 1
fi

run_verify "second_run"
if ! grep -F "[DRIFT] cache up-to-date" "$TMP_DIR/second_run.log" >/dev/null; then
  echo "[FAIL] second_run should use drift cache" >&2
  exit 1
fi

touch -m "$RULES_PATH"
run_verify "third_run_after_touch"
if ! grep -F "[DRIFT] check-rules-drift executed" "$TMP_DIR/third_run_after_touch.log" >/dev/null; then
  echo "[FAIL] third_run_after_touch should re-run drift check after mtime change" >&2
  exit 1
fi

echo "[PASS] post-impl drift cache behavior verified"

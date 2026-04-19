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

run_and_capture() {
  local label="$1"
  shift
  local logfile="$TMP_DIR/${label}.log"

  set +e
  "$@" >"$logfile" 2>&1
  local ec=$?
  set -e

  echo "===== ${label} ====="
  cat "$logfile"
  echo "[EXIT] ${label}=${ec}"
  echo

  return "$ec"
}

set +e
run_and_capture "check_rules_drift_default" \
  python3 tools/check-rules-drift.py
DRIFT_EC=$?
set -e
if [[ "$DRIFT_EC" -ne 0 ]]; then
  echo "[FAIL] check-rules-drift.py expected exit 0, got ${DRIFT_EC}" >&2
  exit 1
fi
if ! grep -E "\[OK\][[:space:]]+[0-9]+/[0-9]+[[:space:]]+rules in sync" "$TMP_DIR/check_rules_drift_default.log" >/dev/null; then
  echo "[FAIL] check-rules-drift default output missing sync summary" >&2
  exit 1
fi

rm -f "$CACHE_PATH"

set +e
run_and_capture "post_impl_verify_first" \
  python3 tools/post-impl-verify.py \
    --no-figma \
    --no-repair \
    --html landing/index.html \
    --css landing/css/common.css
FIRST_EC=$?
set -e
if [[ "$FIRST_EC" -ne 0 ]]; then
  echo "[FAIL] first post-impl-verify expected exit 0, got ${FIRST_EC}" >&2
  exit 1
fi
if [[ ! -f "$CACHE_PATH" ]]; then
  echo "[FAIL] drift cache was not created: ${CACHE_PATH}" >&2
  exit 1
fi
if ! grep -F "[DRIFT] check-rules-drift executed" "$TMP_DIR/post_impl_verify_first.log" >/dev/null; then
  echo "[FAIL] first post-impl-verify should execute drift check" >&2
  exit 1
fi

set +e
run_and_capture "post_impl_verify_second" \
  python3 tools/post-impl-verify.py \
    --no-figma \
    --no-repair \
    --html landing/index.html \
    --css landing/css/common.css
SECOND_EC=$?
set -e
if [[ "$SECOND_EC" -ne 0 ]]; then
  echo "[FAIL] second post-impl-verify expected exit 0, got ${SECOND_EC}" >&2
  exit 1
fi
if ! grep -F "[DRIFT] cache up-to-date" "$TMP_DIR/post_impl_verify_second.log" >/dev/null; then
  echo "[FAIL] second post-impl-verify should use drift cache" >&2
  exit 1
fi

touch -m "$RULES_PATH"

set +e
run_and_capture "post_impl_verify_after_touch" \
  python3 tools/post-impl-verify.py \
    --no-figma \
    --no-repair \
    --html landing/index.html \
    --css landing/css/common.css
THIRD_EC=$?
set -e
if [[ "$THIRD_EC" -ne 0 ]]; then
  echo "[FAIL] third post-impl-verify expected exit 0, got ${THIRD_EC}" >&2
  exit 1
fi
if ! grep -F "[DRIFT] check-rules-drift executed" "$TMP_DIR/post_impl_verify_after_touch.log" >/dev/null; then
  echo "[FAIL] third post-impl-verify should re-run drift check after rules touch" >&2
  exit 1
fi

echo "[PASS] REQ-033 end-to-end integration checks completed"

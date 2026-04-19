#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

SPEC_PATH="$TMP_DIR/req029_endtoend_spec.json"
HTML_PATH="$TMP_DIR/index.html"
CSS_PATH="$TMP_DIR/common.css"

cat >"$SPEC_PATH" <<'JSON'
{
  "schema_version": "2.0.0",
  "section": {
    "id": "S:E2E",
    "name": "REQ-029 E2E Fixture",
    "bbox": {
      "x": 0,
      "y": 0,
      "w": 100,
      "h": 100
    },
    "_extra": null
  },
  "text_nodes": [],
  "frame_nodes": [],
  "vector_nodes": [],
  "interactions": [],
  "images": {},
  "_extra": null
}
JSON

cat >"$HTML_PATH" <<'HTML'
<!doctype html><html><head><meta charset="utf-8"><title>REQ-029</title></head><body><div class="root"></div></body></html>
HTML

cat >"$CSS_PATH" <<'CSS'
.root { display: block; }
CSS

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

assert_ok_or_ignore_only() {
  local label="$1"
  local ec="$2"
  if [[ "$ec" -ne 0 && "$ec" -ne 2 ]]; then
    echo "[FAIL] ${label} expected exit 0 or 2, got ${ec}" >&2
    exit 1
  fi
}

set +e
run_and_capture "migrate_apply" python3 tools/migrate-spec-v1-to-v2.py --apply
MIGRATE_EC=$?
set -e
if [[ "$MIGRATE_EC" -ne 0 ]]; then
  echo "[FAIL] migrate --apply expected exit 0, got ${MIGRATE_EC}" >&2
  exit 1
fi

python3 - "$SPEC_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
assert payload.get("schema_version") == "2.0.0", payload.get("schema_version")
print("[INFO] schema_version=2.0.0 fixture ready")
PY

set +e
run_and_capture "figma_validate" python3 tools/figma-validate.py --spec "$SPEC_PATH" --html "$HTML_PATH" --css "$CSS_PATH"
VALIDATE_EC=$?
set -e
assert_ok_or_ignore_only "figma-validate" "$VALIDATE_EC"

set +e
run_and_capture "post_impl_verify" python3 tools/post-impl-verify.py --spec "$SPEC_PATH" --html "$HTML_PATH" --css "$CSS_PATH"
VERIFY_EC=$?
set -e
assert_ok_or_ignore_only "post-impl-verify" "$VERIFY_EC"

echo "[PASS] TS-01 migrate -> figma-validate -> post-impl-verify integration completed"

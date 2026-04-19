#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

BASELINE_PATH="tests/fixtures/req029/landing_post_impl_baseline.json"
if [[ ! -f "$BASELINE_PATH" ]]; then
  echo "[FAIL] baseline file not found: ${BASELINE_PATH}" >&2
  exit 1
fi

BASELINE_EXIT="$(python3 - "$BASELINE_PATH" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("exit_code", ""))
PY
)"

if [[ -z "$BASELINE_EXIT" ]]; then
  echo "[FAIL] baseline exit_code is empty in ${BASELINE_PATH}" >&2
  exit 1
fi

run_and_capture() {
  local label="$1"
  shift
  local logfile="$TMP_DIR/${label}.log"

  local ec=0
  if "$@" >"$logfile" 2>&1; then
    ec=0
  else
    ec=$?
  fi

  echo "===== ${label} ====="
  cat "$logfile"
  echo "[EXIT] ${label}=${ec}"
  echo

  return "$ec"
}

assert_matches_baseline() {
  local label="$1"
  local ec="$2"

  if [[ "$ec" -ne "$BASELINE_EXIT" ]]; then
    echo "[FAIL] ${label} expected baseline exit ${BASELINE_EXIT}, got ${ec}" >&2
    exit 1
  fi
}

set +e
run_and_capture "figma_validate_section_03" \
  python3 tools/figma-validate.py \
  --spec extracted/section_03_spec.json \
  --html landing/index.html \
  --css landing/css/common.css
SECTION_03_EC=$?
set -e
assert_matches_baseline "section_03" "$SECTION_03_EC"

set +e
run_and_capture "figma_validate_section_04" \
  python3 tools/figma-validate.py \
  --spec extracted/section_04_spec.json \
  --html landing/index.html \
  --css landing/css/common.css
SECTION_04_EC=$?
set -e
assert_matches_baseline "section_04" "$SECTION_04_EC"

VERSION_LOG="$TMP_DIR/version_info.log"
python3 tools/figma-validate.py --version-info >"$VERSION_LOG"
cat "$VERSION_LOG"

for category in \
  "v2.strokes.match" \
  "v2.cornerRadii.match" \
  "v2.layoutSizing.match" \
  "v2.textCase.match" \
  "v2.textDecoration.match"; do
  if ! grep -F -- "- ${category}" "$VERSION_LOG" >/dev/null; then
    echo "[FAIL] missing category in --version-info: ${category}" >&2
    exit 1
  fi
done

echo "[PASS] REQ-031 end-to-end validation checks completed"

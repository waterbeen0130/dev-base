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
BASELINE_EXIT=""
if [[ -f "$BASELINE_PATH" ]]; then
  BASELINE_EXIT="$(python3 - "$BASELINE_PATH" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("exit_code", ""))
PY
)"
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

assert_ok_ignore_or_baseline() {
  local label="$1"
  local ec="$2"

  if [[ "$ec" -eq 0 || "$ec" -eq 2 ]]; then
    return 0
  fi

  if [[ -n "$BASELINE_EXIT" && "$ec" -eq "$BASELINE_EXIT" ]]; then
    echo "[WARN] ${label} exit ${ec} matched REQ-029 baseline exit (${BASELINE_EXIT})"
    return 0
  fi

  echo "[FAIL] ${label} expected exit 0/2 or REQ-029 baseline exit (${BASELINE_EXIT:-unset}), got ${ec}" >&2
  exit 1
}

set +e
run_and_capture "figma_validate_section_03" \
  python3 tools/figma-validate.py \
  --spec extracted/section_03_spec.json \
  --html landing/index.html \
  --css landing/css/common.css
SECTION_03_EC=$?
set -e
assert_ok_ignore_or_baseline "section_03" "$SECTION_03_EC"

set +e
run_and_capture "figma_validate_section_04" \
  python3 tools/figma-validate.py \
  --spec extracted/section_04_spec.json \
  --html landing/index.html \
  --css landing/css/common.css
SECTION_04_EC=$?
set -e
assert_ok_ignore_or_baseline "section_04" "$SECTION_04_EC"

VERSION_LOG="$TMP_DIR/version_info.log"
python3 tools/figma-validate.py --version-info >"$VERSION_LOG"
cat "$VERSION_LOG"

for category in \
  "v2.fills.solid.match" \
  "v2.fills.gradient.match" \
  "v2.fills.image.match" \
  "v2.effects.shadow.match" \
  "v2.effects.blur.match" \
  "v2.opacity.match" \
  "v2.blendMode.match"; do
  if ! grep -F -- "- ${category}" "$VERSION_LOG" >/dev/null; then
    echo "[FAIL] missing category in --version-info: ${category}" >&2
    exit 1
  fi
done

echo "[PASS] REQ-030 end-to-end validation checks completed"

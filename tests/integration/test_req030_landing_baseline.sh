#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

BASELINE_PATH="tests/fixtures/req029/landing_post_impl_baseline.json"
LOG_PATH="$(mktemp)"
cleanup() {
  rm -f "$LOG_PATH"
}
trap cleanup EXIT

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

set +e
python3 tools/post-impl-verify.py \
  --spec extracted/section_03_spec.json \
  --html landing/index.html \
  --css landing/css/common.css \
  >"$LOG_PATH" 2>&1
EXIT_CODE=$?
set -e

echo "===== post-impl-verify (REQ-030 landing baseline) ====="
cat "$LOG_PATH"
echo "[EXIT] post-impl-verify=${EXIT_CODE}"

if [[ "$EXIT_CODE" -eq 0 || "$EXIT_CODE" -eq 2 ]]; then
  echo "[OK] post-impl-verify exit is PASS/IGNORE-only (${EXIT_CODE})"
  exit 0
fi

if [[ -n "$BASELINE_EXIT" && "$EXIT_CODE" -eq "$BASELINE_EXIT" ]]; then
  echo "[OK] post-impl-verify exit matched REQ-029 baseline (${BASELINE_EXIT})"
  exit 0
fi

echo "[FAIL] expected exit 0/2 or REQ-029 baseline (${BASELINE_EXIT:-unset}), got ${EXIT_CODE}" >&2
exit 1

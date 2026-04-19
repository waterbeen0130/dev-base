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

set +e
python3 tools/post-impl-verify.py \
  --spec extracted/section_03_spec.json \
  --html landing/index.html \
  --css landing/css/common.css \
  --no-repair \
  >"$LOG_PATH" 2>&1
EXIT_CODE=$?
set -e

CRITICAL_COUNT=$(grep -c '^\[CRITICAL\]' "$LOG_PATH" || true)
MAJOR_COUNT=$(grep -c '^\[MAJOR\]' "$LOG_PATH" || true)
SEMANTIC_CRITICAL_COUNT=$(grep -c '^\[SEMANTIC-CRITICAL\]' "$LOG_PATH" || true)

if [[ ! -f "$BASELINE_PATH" ]]; then
  python3 - "$BASELINE_PATH" "$EXIT_CODE" "$CRITICAL_COUNT" "$MAJOR_COUNT" "$SEMANTIC_CRITICAL_COUNT" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "exit_code": int(sys.argv[2]),
    "critical": int(sys.argv[3]),
    "major": int(sys.argv[4]),
    "semantic_critical": int(sys.argv[5]),
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[INFO] baseline created: {path}")
PY
fi

python3 - "$BASELINE_PATH" "$EXIT_CODE" "$CRITICAL_COUNT" "$MAJOR_COUNT" "$SEMANTIC_CRITICAL_COUNT" <<'PY'
import json
import sys
from pathlib import Path

baseline = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
current = {
    "exit_code": int(sys.argv[2]),
    "critical": int(sys.argv[3]),
    "major": int(sys.argv[4]),
    "semantic_critical": int(sys.argv[5]),
}

if baseline != current:
    raise SystemExit(f"[FAIL] landing baseline mismatch: expected={baseline}, current={current}")

print(f"[OK] landing baseline matched: {current}")
PY

echo "===== post-impl-verify (landing baseline) ====="
cat "$LOG_PATH"

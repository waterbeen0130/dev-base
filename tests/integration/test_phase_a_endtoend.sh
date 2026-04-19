#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
CACHE_PATH="$ROOT_DIR/.gran-maestro/state/drift-cache.json"
CACHE_BACKUP_PATH="$TMP_DIR/drift-cache.backup.json"
CACHE_EXISTED=0
HTML_PATH="$ROOT_DIR/landing/index.html"
CSS_PATH="$ROOT_DIR/landing/css/common.css"
HTML_BACKUP_PATH="$TMP_DIR/index.html.backup"
CSS_BACKUP_PATH="$TMP_DIR/common.css.backup"

if [[ -f "$CACHE_PATH" ]]; then
  cp "$CACHE_PATH" "$CACHE_BACKUP_PATH"
  CACHE_EXISTED=1
fi
cp "$HTML_PATH" "$HTML_BACKUP_PATH"
cp "$CSS_PATH" "$CSS_BACKUP_PATH"

cleanup() {
  cp "$HTML_BACKUP_PATH" "$HTML_PATH"
  cp "$CSS_BACKUP_PATH" "$CSS_PATH"
  if [[ "$CACHE_EXISTED" -eq 1 ]]; then
    mkdir -p "$(dirname "$CACHE_PATH")"
    cp "$CACHE_BACKUP_PATH" "$CACHE_PATH"
  else
    rm -f "$CACHE_PATH"
  fi
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

assert_exit_zero() {
  local label="$1"
  local ec="$2"
  if [[ "$ec" -ne 0 ]]; then
    echo "[FAIL] ${label} expected exit 0, got ${ec}" >&2
    exit 1
  fi
}

set +e
run_and_capture "pytest_all" pytest tests/ -v --tb=short
PYTEST_EC=$?
set -e
assert_exit_zero "pytest tests/ -v --tb=short" "$PYTEST_EC"

set +e
run_and_capture "check_rules_drift_default" python3 tools/check-rules-drift.py
DRIFT_EC=$?
set -e
assert_exit_zero "python3 tools/check-rules-drift.py" "$DRIFT_EC"
if ! grep -E "\[OK\][[:space:]]+[0-9]+/[0-9]+[[:space:]]+rules in sync" "$TMP_DIR/check_rules_drift_default.log" >/dev/null; then
  echo "[FAIL] check-rules-drift default output missing sync summary" >&2
  exit 1
fi

set +e
run_and_capture "figma_validate_version_info" python3 tools/figma-validate.py --version-info
VERSION_EC=$?
set -e
assert_exit_zero "python3 tools/figma-validate.py --version-info" "$VERSION_EC"

V1_COUNT="$(awk '
  /^v1 categories:$/ {in_v1=1; next}
  /^v2 categories:$/ {in_v1=0}
  in_v1 && /^- / {count++}
  END {print count+0}
' "$TMP_DIR/figma_validate_version_info.log")"
if [[ "$V1_COUNT" -ne 9 ]]; then
  echo "[FAIL] v1 category count expected 9, got ${V1_COUNT}" >&2
  exit 1
fi

V2_DETAIL_COUNT="$(grep -c '^- v2\.' "$TMP_DIR/figma_validate_version_info.log" || true)"
if [[ "$V2_DETAIL_COUNT" -ne 14 ]]; then
  echo "[FAIL] v2 detail category count expected 14, got ${V2_DETAIL_COUNT}" >&2
  exit 1
fi

for category in \
  "텍스트 위변조" \
  "줄바꿈 보존" \
  "폰트 5필드 완결성" \
  "lineHeight 비율 일치" \
  "fills color hex 일치" \
  "frame padding/gap 반영" \
  "clamp 적용" \
  "column flex gap 금지" \
  "interaction URL 일치" \
  "v2.fills.solid.match" \
  "v2.fills.gradient.match" \
  "v2.fills.image.match" \
  "v2.effects.shadow.match" \
  "v2.effects.blur.match" \
  "v2.opacity.match" \
  "v2.blendMode.match" \
  "v2.strokes.match" \
  "v2.cornerRadii.match" \
  "v2.layoutSizing.match" \
  "v2.textCase.match" \
  "v2.textDecoration.match" \
  "v2.componentId.match" \
  "v2.assetManifest.exists"; do
  if ! grep -F -- "- ${category}" "$TMP_DIR/figma_validate_version_info.log" >/dev/null; then
    echo "[FAIL] missing category in --version-info: ${category}" >&2
    exit 1
  fi
done

set +e
run_and_capture "post_impl_verify_section_03" \
  python3 tools/post-impl-verify.py \
  --spec extracted/section_03_spec.json \
  --html "$HTML_PATH" \
  --css "$CSS_PATH"
POST_IMPL_EC=$?
set -e
if [[ "$POST_IMPL_EC" -ne "$BASELINE_EXIT" ]]; then
  echo "[FAIL] post-impl-verify expected REQ-029 baseline exit ${BASELINE_EXIT}, got ${POST_IMPL_EC}" >&2
  exit 1
fi

set +e
run_and_capture "migrate_v1_to_v2_dry_run" python3 tools/migrate-spec-v1-to-v2.py --dry-run
MIGRATE_EC=$?
set -e
assert_exit_zero "python3 tools/migrate-spec-v1-to-v2.py --dry-run" "$MIGRATE_EC"
if grep -Eiq '\[WARN\]|warning' "$TMP_DIR/migrate_v1_to_v2_dry_run.log"; then
  echo "[FAIL] migrate dry-run emitted warning output" >&2
  exit 1
fi
if ! grep -F "[OK] already-v2:${ROOT_DIR}/extracted/section_03_spec.json" "$TMP_DIR/migrate_v1_to_v2_dry_run.log" >/dev/null; then
  echo "[FAIL] migrate dry-run missing already-v2 marker for section_03_spec.json" >&2
  exit 1
fi
if ! grep -F "[OK] already-v2:${ROOT_DIR}/extracted/section_04_spec.json" "$TMP_DIR/migrate_v1_to_v2_dry_run.log" >/dev/null; then
  echo "[FAIL] migrate dry-run missing already-v2 marker for section_04_spec.json" >&2
  exit 1
fi
if ! grep -F "[SUMMARY] mode=dry-run ok=2 fail=0 scanned=2" "$TMP_DIR/migrate_v1_to_v2_dry_run.log" >/dev/null; then
  echo "[FAIL] migrate dry-run summary mismatch" >&2
  exit 1
fi

echo "[PASS] Phase A final end-to-end integration checks completed"

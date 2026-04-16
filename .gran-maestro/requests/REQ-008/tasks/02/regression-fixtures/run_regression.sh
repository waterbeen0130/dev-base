#!/usr/bin/env bash
# REQ-008-02 regression runner for tools/figma-validate.py
set +e
cd "$(dirname "$0")"
ROOT=".."

echo "=== base ==="
python3 "$ROOT/tools/figma-validate.py" --spec base/section_spec.json --html base/index.html --css base/style.css
echo "exit=$?"

for dir in scenarios/*/; do
  name=$(basename "$dir")
  echo "=== $name ==="
  python3 "$ROOT/tools/figma-validate.py" --spec "$dir/section_spec.json" --html "$dir/index.html" --css "$dir/style.css"
  echo "exit=$?"
done

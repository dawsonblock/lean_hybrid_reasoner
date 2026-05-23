#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="${1:-dist}"
OUT_NAME="${2:-lean_hybrid_reasoner-main.zip}"
OUT_PATH="$OUT_DIR/$OUT_NAME"

mkdir -p "$OUT_DIR"
rm -f "$OUT_PATH"

# Archive only tracked files at HEAD to avoid bundling runtime/cache artifacts.
git archive --format=zip --output "$OUT_PATH" HEAD

forbidden_pattern='(^|/)__pycache__/|\.pyc$|(^|/)\.runs/'
if unzip -Z -1 "$OUT_PATH" | grep -E "$forbidden_pattern" >/dev/null; then
  echo "[build-clean-zip] forbidden generated artifact found in archive: $OUT_PATH" >&2
  exit 1
fi

echo "[build-clean-zip] wrote $OUT_PATH"
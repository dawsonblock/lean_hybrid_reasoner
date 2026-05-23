#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[release-check] scripts/release_v06_check.sh is deprecated; use scripts/release_check.sh"
exec bash scripts/release_check.sh

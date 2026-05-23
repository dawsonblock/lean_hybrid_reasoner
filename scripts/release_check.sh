#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"

if ! command -v pytest >/dev/null 2>&1; then
  echo "pytest is required in the active environment" >&2
  exit 1
fi

if command -v hybrid-proof >/dev/null 2>&1; then
  HP=(hybrid-proof)
else
  HP=(python -m lean_hybrid_reasoner.cli)
fi

echo "[release-check] Running test suite"
pytest

echo "[release-check] Running mock backend smoke"
"${HP[@]}" list-theorems >/tmp/lhr_list_theorems.txt
"${HP[@]}" run --theorem and_comm_example >/tmp/lhr_run.txt
"${HP[@]}" failure-report --group-by theorem >/tmp/lhr_failure_report.txt

if [[ -f .runs/traces.jsonl ]]; then
  echo "[release-check] Validating existing traces"
  "${HP[@]}" validate-traces --input .runs/traces.jsonl >/tmp/lhr_validate.txt || true
fi

echo "[release-check] Building accepted-quality dataset pack"
"${HP[@]}" pack-dataset --include-failures --min-quality accepted --output-dir .runs/dataset_pack_release >/tmp/lhr_pack.txt

echo "[release-check] Completed"

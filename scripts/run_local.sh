#!/usr/bin/env bash
set -euo pipefail
python -m pip install -e ".[dev]"
pytest
hybrid-proof list-theorems
hybrid-proof run --theorem and_comm_example --print-trace
hybrid-proof eval

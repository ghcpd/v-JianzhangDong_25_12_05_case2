#!/usr/bin/env bash
# Usage: ./run_test.sh <file> <vulnerable|secure>
set -euo pipefail
FILE=${1:-input.py}
MODE=${2:-secure}
python -u test_runner.py "$FILE" "$MODE"

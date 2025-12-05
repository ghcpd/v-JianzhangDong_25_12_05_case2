#!/usr/bin/env bash
set -e
if [ -z "$1" ]; then
  FILE="inputs.py"
else
  FILE="$1"
fi
python -m tests.run_tests "$FILE"

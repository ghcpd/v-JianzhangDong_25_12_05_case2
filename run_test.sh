#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-module>" >&2
  exit 2
fi
TARGET=$1
export TARGET_MODULE="$TARGET"
pytest -q tests/test_inputs.py

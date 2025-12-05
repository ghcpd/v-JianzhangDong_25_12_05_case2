#!/usr/bin/env bash
set -euo pipefail
echo "Running security tests..."
python security_test_runner.py input_backup.py
python security_test_runner.py inputs.py
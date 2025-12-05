#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Environment ready. Set required env vars: INTERNAL_AUTH and ADMIN_API_KEY."

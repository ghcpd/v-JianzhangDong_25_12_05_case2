#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "Environment set up. Use 'source .venv/bin/activate' to activate." 

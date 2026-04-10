#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
pip install -r requirements.txt

# Optional Node bootstrap for mixed projects
if [[ -f package.json ]]; then
  if command -v npm >/dev/null 2>&1; then
    npm ci || true
  fi
fi

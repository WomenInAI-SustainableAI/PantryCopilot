#!/usr/bin/env bash
set -euo pipefail

# Ensure we're at repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Python deps
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

# Node/Next build
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found on PATH" >&2
  exit 1
fi
pushd frontend >/dev/null
  npm ci || npm install
  npm run build
popd >/dev/null

# Copy static export into backend/static served by FastAPI
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/out/* backend/static

echo "Build complete: frontend exported to backend/static"
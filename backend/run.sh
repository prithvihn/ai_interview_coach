#!/usr/bin/env bash
# run.sh — start the AI Interview Coach backend

set -e

echo "🚀 Starting AI Interview Coach API..."

# Export env vars from .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --log-level info

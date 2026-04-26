#!/usr/bin/env bash
# run.sh — start the AI Interview Coach backend (production)

set -e

echo "🚀 Starting AI Interview Coach API..."

# Use Render's PORT env var, default to 8000 locally
PORT=${PORT:-8000}

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --log-level info

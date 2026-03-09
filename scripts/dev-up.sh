#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[1/4] starting runtime-service on :8123"
(
  cd "$ROOT_DIR/apps/runtime-service"
  nohup uv run langgraph dev --config graph_src_v2/langgraph.json --port 8123 --no-browser > /tmp/aitestlab-runtime-service.log 2>&1 &
)

echo "[2/4] starting platform-api on :2024"
(
  cd "$ROOT_DIR/apps/platform-api"
  nohup uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload > /tmp/aitestlab-platform-api.log 2>&1 &
)

echo "[3/4] starting platform-web on :3000"
(
  cd "$ROOT_DIR/apps/platform-web"
  nohup pnpm dev > /tmp/aitestlab-platform-web.log 2>&1 &
)

echo "[4/4] starting runtime-web on :3001"
(
  cd "$ROOT_DIR/apps/runtime-web"
  nohup env PORT=3001 pnpm dev > /tmp/aitestlab-runtime-web.log 2>&1 &
)

echo "done. logs:"
echo "  /tmp/aitestlab-runtime-service.log"
echo "  /tmp/aitestlab-platform-api.log"
echo "  /tmp/aitestlab-platform-web.log"
echo "  /tmp/aitestlab-runtime-web.log"

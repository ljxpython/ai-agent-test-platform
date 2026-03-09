#!/usr/bin/env bash
set -euo pipefail

SSH_HOST="${SSH_HOST:-61.147.247.83}"
SSH_PORT="${SSH_PORT:-10526}"
SSH_USER="${SSH_USER:-root}"

LOCAL_KEYCLOAK_PORT="${LOCAL_KEYCLOAK_PORT:-28080}"
LOCAL_OPENFGA_PORT="${LOCAL_OPENFGA_PORT:-28081}"
LOCAL_PG_PORT="${LOCAL_PG_PORT:-15432}"
LOCAL_OLLAMA_PORT="${LOCAL_OLLAMA_PORT:-11143}"
LOCAL_RUNTIME_PORT="${LOCAL_RUNTIME_PORT:-8123}"

REMOTE_KEYCLOAK_PORT="${REMOTE_KEYCLOAK_PORT:-18080}"
REMOTE_OPENFGA_PORT="${REMOTE_OPENFGA_PORT:-18081}"
REMOTE_PG_PORT="${REMOTE_PG_PORT:-5432}"
REMOTE_OLLAMA_PORT="${REMOTE_OLLAMA_PORT:-11434}"
REMOTE_RUNTIME_PORT="${REMOTE_RUNTIME_PORT:-8123}"

PID_FILE="${PID_FILE:-.cache/dev_tunnel_ssh.pid}"
mkdir -p "$(dirname "$PID_FILE")"

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Tunnel already running (pid=$old_pid)."
    exit 0
  fi
fi

existing_pid="$(lsof -tiTCP:"${LOCAL_KEYCLOAK_PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [[ -n "$existing_pid" ]]; then
  if ps -p "$existing_pid" -o command= | grep -q "^ssh "; then
    echo "$existing_pid" > "$PID_FILE"
    echo "Tunnel already listening on ${LOCAL_KEYCLOAK_PORT} (pid=$existing_pid)."
    exit 0
  fi
  echo "Port ${LOCAL_KEYCLOAK_PORT} is already in use by non-ssh process (pid=$existing_pid)."
  exit 1
fi

ssh -fN \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -p "$SSH_PORT" \
  -L "${LOCAL_KEYCLOAK_PORT}:127.0.0.1:${REMOTE_KEYCLOAK_PORT}" \
  -L "${LOCAL_OPENFGA_PORT}:127.0.0.1:${REMOTE_OPENFGA_PORT}" \
  -L "${LOCAL_PG_PORT}:127.0.0.1:${REMOTE_PG_PORT}" \
  -L "${LOCAL_OLLAMA_PORT}:127.0.0.1:${REMOTE_OLLAMA_PORT}" \
  -L "${LOCAL_RUNTIME_PORT}:127.0.0.1:${REMOTE_RUNTIME_PORT}" \
  "${SSH_USER}@${SSH_HOST}"

pid="$(lsof -tiTCP:"${LOCAL_KEYCLOAK_PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [[ -z "$pid" ]]; then
  echo "Tunnel started, but pid lookup failed."
  exit 1
fi

echo "$pid" > "$PID_FILE"

echo "Tunnel started: pid=$pid"
echo "Keycloak: http://127.0.0.1:${LOCAL_KEYCLOAK_PORT}"
echo "OpenFGA:  http://127.0.0.1:${LOCAL_OPENFGA_PORT}"
echo "Postgres: 127.0.0.1:${LOCAL_PG_PORT}"
echo "Ollama:   http://127.0.0.1:${LOCAL_OLLAMA_PORT}"
echo "Runtime:  http://127.0.0.1:${LOCAL_RUNTIME_PORT}"

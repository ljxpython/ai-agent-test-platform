#!/usr/bin/env bash
set -euo pipefail

SSH_HOST="${SSH_HOST:-61.147.247.83}"
SSH_USER="${SSH_USER:-root}"
LOCAL_KEYCLOAK_PORT="${LOCAL_KEYCLOAK_PORT:-28080}"
PID_FILE="${PID_FILE:-.cache/dev_tunnel_ssh.pid}"

stopped=0

if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE" || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    stopped=1
    echo "Stopped tunnel pid=$pid"
  fi
  rm -f "$PID_FILE"
fi

if [[ "$stopped" -eq 0 ]]; then
  pid_by_port="$(lsof -tiTCP:"${LOCAL_KEYCLOAK_PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [[ -n "$pid_by_port" ]] && ps -p "$pid_by_port" -o command= | grep -q "^ssh "; then
    cmd="$(ps -p "$pid_by_port" -o command=)"
    if echo "$cmd" | grep -q "${SSH_USER}@${SSH_HOST}"; then
      kill "$pid_by_port"
      echo "Stopped tunnel by port ${LOCAL_KEYCLOAK_PORT}: pid=$pid_by_port"
      stopped=1
    fi
  fi
fi

if [[ "$stopped" -eq 0 ]]; then
  echo "No matching tunnel process found."
fi

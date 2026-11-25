#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export TF_CPP_MIN_LOG_LEVEL=2
export CUDA_VISIBLE_DEVICES=-1

ACTION_PID=""
RASA_PID=""
FLASK_PID=""

cleanup() {
  echo ""
  echo "Shutting down Mental Health Chatbot services..."
  for pid in "$FLASK_PID" "$RASA_PID" "$ACTION_PID"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [[ ! -d "$ROOT_DIR/rasa_bot/models" ]] || [[ -z "$(ls -A "$ROOT_DIR/rasa_bot/models" 2>/dev/null)" ]]; then
  echo "No trained Rasa model found. Training Rasa model first..."
  (cd "$ROOT_DIR/rasa_bot" && "$ROOT_DIR/rasa_bot/.venv/bin/rasa" train)
fi

echo "Starting Rasa Action Server on port 5055..."
(cd "$ROOT_DIR/rasa_bot" && "$ROOT_DIR/rasa_bot/.venv/bin/rasa" run actions --port 5055) &
ACTION_PID=$!

echo "Starting Rasa Server on port 5005..."
(cd "$ROOT_DIR/rasa_bot" && "$ROOT_DIR/rasa_bot/.venv/bin/rasa" run --enable-api --cors "*" --port 5005) &
RASA_PID=$!

echo "Waiting for Rasa server to finish loading..."
for _ in $(seq 1 45); do
  if curl -sf http://127.0.0.1:5005/status >/dev/null 2>&1; then
    echo "Rasa server is ready."
    break
  fi
  sleep 2
done

echo "Starting Flask web application on http://127.0.0.1:${FLASK_PORT:-5000} ..."
"$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/run.py" &
FLASK_PID=$!

wait "$FLASK_PID"

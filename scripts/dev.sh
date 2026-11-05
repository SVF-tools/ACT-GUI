#!/usr/bin/env bash
# Start the ACT-GUI development stack on loopback:
#   FastAPI service  -> http://127.0.0.1:${ACT_GUI_SERVICE_PORT:-18765}
#   Browser (Vite)   -> http://127.0.0.1:${ACT_GUI_WEB_PORT:-5173}   <- open this URL
# Requires .venv and node_modules (see README "Development").
set -euo pipefail
cd "$(dirname "$0")/.."
export ACT_ROOT="${ACT_ROOT:-/data1/guanqin/ACT}"
export ACT_GUI_SERVICE_PORT="${ACT_GUI_SERVICE_PORT:-18765}"
export ACT_GUI_WEB_PORT="${ACT_GUI_WEB_PORT:-5173}"

.venv/bin/python -m uvicorn visual_bench.server:app --host 127.0.0.1 --port "$ACT_GUI_SERVICE_PORT" &
SERVICE_PID=$!
trap 'kill $SERVICE_PID 2>/dev/null || true' EXIT INT TERM

# Do not start the browser server until *this* service answers (another program may own the port).
for _ in $(seq 60); do
  if ! kill -0 "$SERVICE_PID" 2>/dev/null; then
    echo "ACT-GUI service failed to start on port $ACT_GUI_SERVICE_PORT (port in use?). Set ACT_GUI_SERVICE_PORT." >&2
    exit 1
  fi
  if curl -sf "http://127.0.0.1:$ACT_GUI_SERVICE_PORT/api/health" | grep -q act-gui-workbench; then
    break
  fi
  sleep 1
done

echo "ACT-GUI: open http://127.0.0.1:$ACT_GUI_WEB_PORT in your browser"
npx vite

#!/usr/bin/env bash
# One-command launcher for the PhishGuard demo (backend + frontend).
# Stop everything with Ctrl-C.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "▶ Starting backend (FastAPI :8000)…"
cd "$ROOT/backend"
if [ ! -d ".venv" ]; then
  echo "  · creating virtualenv + installing dependencies (first run only)…"
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi
if [ ! -f "ml/model.joblib" ]; then
  echo "  · training classifier (first run only)…"
  ./.venv/bin/python -m ml.train >/dev/null
fi
./.venv/bin/uvicorn main:app --port 8000 &
BACK_PID=$!

cleanup() { echo; echo "■ Stopping…"; kill $BACK_PID $FRONT_PID 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo "▶ Starting frontend (Vite :5173)…"
cd "$ROOT/frontend"
if [ ! -d "node_modules" ]; then
  echo "  · installing npm packages (first run only)…"
  npm install --no-audit --no-fund
fi
npm run dev &
FRONT_PID=$!

echo
echo "──────────────────────────────────────────────"
echo "  PhishGuard is starting up."
echo "  Open:  http://localhost:5173"
echo "  API:   http://localhost:8000/docs"
echo "──────────────────────────────────────────────"
wait

#!/bin/bash
# Fast launch script for Neo-Hack: Gridlock local environment

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR"

echo "=================================================="
echo " NEO-HACK: GRIDLOCK - FAST LAUNCH TOOL"
echo "=================================================="

echo "[*] Stopping any existing backend/frontend background processes..."
pkill -f "uvicorn.*backend.main:app" >/dev/null 2>&1 || true

echo "[*] Starting the game backend (which serves the frontend)..."
cd backend
.venv/bin/python main.py > backend.log 2>&1 &
BACKEND_PID=$!

echo "[*] Waiting for the service to start..."
sleep 2

if curl -s http://localhost:8000/api/health >/dev/null; then
    echo "[+] SUCCESS! Game is running locally."
    echo "[+] Access the game in your browser at: http://localhost:8000/"
    echo "[i] Service is running in the background with PID $BACKEND_PID"
    echo "    Check backend/backend.log for detailed output if needed."
else
    echo "[-] WARNING: The service might not have started correctly."
    echo "    Please check backend/backend.log for errors."
fi

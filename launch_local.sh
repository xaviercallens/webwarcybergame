#!/bin/bash
# Fast and Smart launch script for Neo-Hack: Gridlock local environment

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR"

FORCE_BUILD=false
if [ "$1" == "--build" ] || [ "$1" == "-b" ]; then
    FORCE_BUILD=true
fi

echo "=================================================="
echo " NEO-HACK: GRIDLOCK - FAST LAUNCH TOOL"
echo "=================================================="

# 1. Start setup for Frontend
echo "[*] Checking Frontend..."
WEB_DIR="$SCRIPT_DIR/build/web"

# Auto-load NVM if node is missing
if ! command -v node >/dev/null 2>&1; then
    export NVM_DIR="$HOME/.config/nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
fi

if [ ! -d "$WEB_DIR/node_modules" ]; then
    echo "[i] node_modules not found. Installing dependencies..."
    (cd "$WEB_DIR" && npm install)
fi

if [ "$FORCE_BUILD" = true ] || [ ! -d "$WEB_DIR/dist" ]; then
    echo "[i] Building frontend for production..."
    (cd "$WEB_DIR" && npm run build)
else
    echo "[i] Frontend build (dist/) already exists. Skipping build (use --build to force rebuild)."
fi

# 2. Stop existing instances
echo "[*] Stopping any existing backend/frontend background processes..."
pkill -f "uvicorn.*backend.main:app" >/dev/null 2>&1 || true

# 3. Launch Backend
echo "[*] Starting the game backend (which serves the compiled frontend)..."
cd "$SCRIPT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "[-] WARNING: .venv not found in backend/. Ensure dependencies are installed."
fi

export WEB_BUILD_DIR="$WEB_DIR/dist"
.venv/bin/python main.py > backend.log 2>&1 &
BACKEND_PID=$!

echo "[*] Waiting for the service to become healthy..."
MAX_RETRIES=15
RETRY_COUNT=0
HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/api/health | grep -q 'healthy'; then
        HEALTHY=true
        break
    fi
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo -n "."
done
echo ""

if [ "$HEALTHY" = true ]; then
    echo "[+] SUCCESS! Game is running locally."
    echo "[i] Service is running in the background with PID $BACKEND_PID"
    echo "    Check backend/backend.log for detailed output if needed."
    
    # Run End-to-End Selenium Tests
    echo "[*] Running Automated Selenium E2E Tests..."
    if ! .venv/bin/python -c "import selenium" >/dev/null 2>&1; then
        echo "[i] Installing Selenium..."
        uv pip install selenium > /dev/null 2>&1 || .venv/bin/python -m pip install selenium > /dev/null 2>&1
    fi
    .venv/bin/python ../test_e2e_selenium.py
    TEST_EXIT_CODE=$?
    if [ $TEST_EXIT_CODE -ne 0 ]; then
        echo "[-] WARNING: Selenium E2E Tests failed! Check for selenium_failure.png."
    else
        echo "[+] Selenium E2E Verification Passed."
    fi

    # Auto-open browser
    echo "[*] Opening browser..."
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "http://localhost:8000/" >/dev/null 2>&1 &
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m webbrowser "http://localhost:8000/" >/dev/null 2>&1 &
    fi
else
    echo "[-] WARNING: The service failed to become healthy in time."
    echo "    Please check backend/backend.log for errors."
    kill $BACKEND_PID 2>/dev/null
fi

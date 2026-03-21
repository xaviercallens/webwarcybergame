#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Neo-Hack: Gridlock v3.2 — Demo Recording Script
# 
# Records a 10-minute demo playthrough with:
#   - WebM video of the browser UI
#   - Backend API call log (all requests/responses)
#   - Frontend console log (all JS events)
#
# Prerequisites:
#   - Backend running on port 8000
#   - Frontend running on port 5173
#   - Playwright browsers installed
#
# Usage:
#   chmod +x scripts/run-demo-recording.sh
#   ./scripts/run-demo-recording.sh
#
# Output:
#   specs/demo_recordings/  — video files (.webm), screenshots, console logs
#   specs/demo_logs/        — backend API call logs
# ══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/build/web"
RECORDINGS_DIR="$PROJECT_DIR/specs/demo_recordings"
LOGS_DIR="$PROJECT_DIR/specs/demo_logs"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  NEO-HACK: GRIDLOCK v3.2 — DEMO RECORDING${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""

# Create output directories
mkdir -p "$RECORDINGS_DIR" "$LOGS_DIR"

# ── Check prerequisites ──────────────────────────────────────

echo -e "${YELLOW}[1/5] Checking prerequisites...${NC}"

# Check backend
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${RED}  ✗ Backend not running on port 8000${NC}"
    echo -e "  Start it with: cd backend && DEMO_RECORDING=1 uvicorn src.backend.main:app --port 8000"
    
    echo -e "${YELLOW}  → Starting backend with DEMO_RECORDING=1...${NC}"
    cd "$BACKEND_DIR"
    DEMO_RECORDING=1 uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    echo "  Backend PID: $BACKEND_PID"
    sleep 5
    
    if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${RED}  ✗ Backend failed to start${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  ✓ Backend running on port 8000${NC}"
    # Check if DEMO_RECORDING is enabled
    echo -e "${YELLOW}  Note: Restart backend with DEMO_RECORDING=1 for API logging${NC}"
fi

# Check frontend
if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${RED}  ✗ Frontend not running on port 5173${NC}"
    echo -e "${YELLOW}  → Starting frontend...${NC}"
    cd "$FRONTEND_DIR"
    npx vite --port 5173 &
    FRONTEND_PID=$!
    echo "  Frontend PID: $FRONTEND_PID"
    sleep 3
else
    echo -e "${GREEN}  ✓ Frontend running on port 5173${NC}"
fi

# Check Playwright
cd "$FRONTEND_DIR"
if ! npx playwright --version > /dev/null 2>&1; then
    echo -e "${YELLOW}  → Installing Playwright...${NC}"
    npx playwright install chromium
fi
echo -e "${GREEN}  ✓ Playwright available${NC}"

echo ""

# ── Run demo recording ───────────────────────────────────────

echo -e "${YELLOW}[2/5] Starting demo recording...${NC}"
echo -e "  Output: $RECORDINGS_DIR"
echo -e "  Duration: ~10 minutes"
echo ""

cd "$FRONTEND_DIR"

# Run Playwright with demo config
DEMO_RECORDING=1 npx playwright test \
    --config=playwright.demo.config.js \
    e2e/demo-recording.spec.js \
    2>&1 | tee "$RECORDINGS_DIR/playwright_output.txt"

PLAYWRIGHT_EXIT=$?

echo ""

# ── Collect outputs ──────────────────────────────────────────

echo -e "${YELLOW}[3/5] Collecting recording outputs...${NC}"

# Find the video file
VIDEO_FILE=$(find "$RECORDINGS_DIR" -name "*.webm" -newer "$RECORDINGS_DIR/playwright_output.txt" 2>/dev/null | head -1)
if [ -z "$VIDEO_FILE" ]; then
    VIDEO_FILE=$(find "$RECORDINGS_DIR" -name "*.webm" 2>/dev/null | sort -r | head -1)
fi

if [ -n "$VIDEO_FILE" ]; then
    echo -e "${GREEN}  ✓ Video recorded: $VIDEO_FILE${NC}"
    
    # Try to convert to MP4 if ffmpeg is available
    if command -v ffmpeg &> /dev/null; then
        MP4_FILE="${VIDEO_FILE%.webm}.mp4"
        echo -e "${YELLOW}  → Converting to MP4...${NC}"
        ffmpeg -i "$VIDEO_FILE" -c:v libx264 -preset fast -crf 23 "$MP4_FILE" -y 2>/dev/null
        if [ -f "$MP4_FILE" ]; then
            echo -e "${GREEN}  ✓ MP4 created: $MP4_FILE${NC}"
        fi
    else
        echo -e "${YELLOW}  Note: Install ffmpeg to auto-convert to MP4${NC}"
    fi
else
    echo -e "${RED}  ✗ No video file found${NC}"
fi

# Find console log
CONSOLE_LOG=$(find "$RECORDINGS_DIR" -name "console_log*.txt" 2>/dev/null | sort -r | head -1)
if [ -n "$CONSOLE_LOG" ]; then
    echo -e "${GREEN}  ✓ Console log: $CONSOLE_LOG${NC}"
else
    echo -e "${YELLOW}  ⚠ No console log found${NC}"
fi

# Find API log
API_LOG=$(find "$LOGS_DIR" -name "demo_api_log*.txt" 2>/dev/null | sort -r | head -1)
if [ -n "$API_LOG" ]; then
    echo -e "${GREEN}  ✓ API log: $API_LOG${NC}"
else
    echo -e "${YELLOW}  ⚠ No API log found (ensure backend was started with DEMO_RECORDING=1)${NC}"
fi

echo ""

# ── Summary ──────────────────────────────────────────────────

echo -e "${YELLOW}[4/5] Recording summary:${NC}"
echo -e "  Playwright exit code: $PLAYWRIGHT_EXIT"
echo -e "  Video:       ${VIDEO_FILE:-'not found'}"
echo -e "  Console log: ${CONSOLE_LOG:-'not found'}"
echo -e "  API log:     ${API_LOG:-'not found'}"

echo ""
echo -e "${YELLOW}[5/5] Output files:${NC}"
ls -la "$RECORDINGS_DIR"/ 2>/dev/null || echo "  (empty)"
echo ""
ls -la "$LOGS_DIR"/ 2>/dev/null || echo "  (empty)"

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
if [ $PLAYWRIGHT_EXIT -eq 0 ]; then
    echo -e "${GREEN}  ✓ DEMO RECORDING COMPLETE${NC}"
else
    echo -e "${YELLOW}  ⚠ Recording finished with warnings (exit: $PLAYWRIGHT_EXIT)${NC}"
fi
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"

# Cleanup background processes if we started them
if [ -n "$BACKEND_PID" ]; then
    echo -e "  Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
fi
if [ -n "$FRONTEND_PID" ]; then
    echo -e "  Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
fi

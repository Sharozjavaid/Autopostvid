#!/bin/bash

# Philosophy Video Generator - Stop Script
# Stops both frontend and backend services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOG_DIR="$SCRIPT_DIR/logs"
PID_FILE="$LOG_DIR/pids.txt"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Philosophy Video Generator${NC}"
echo -e "${BLUE}  Stopping Services...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to kill process tree
kill_tree() {
    local pid=$1
    local signal=${2:-TERM}
    
    # Kill child processes
    for child in $(pgrep -P $pid 2>/dev/null); do
        kill_tree $child $signal
    done
    
    # Kill the process itself
    kill -$signal $pid 2>/dev/null
}

# Read PIDs from file
if [ -f "$PID_FILE" ]; then
    source "$PID_FILE"
    
    if [ -n "$BACKEND_PID" ]; then
        echo -e "${YELLOW}🛑 Stopping Backend (PID: $BACKEND_PID)...${NC}"
        kill_tree $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}   ✓ Backend stopped${NC}"
    fi
    
    if [ -n "$FRONTEND_PID" ]; then
        echo -e "${YELLOW}🛑 Stopping Frontend (PID: $FRONTEND_PID)...${NC}"
        kill_tree $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}   ✓ Frontend stopped${NC}"
    fi
    
    rm -f "$PID_FILE"
else
    echo -e "${YELLOW}⚠️  No PID file found. Trying to find processes...${NC}"
fi

# Also kill any lingering processes on the ports
echo ""
echo -e "${YELLOW}🔍 Checking for processes on ports 8001 and 3000...${NC}"

# Kill backend on port 8001
BACKEND_PORT_PID=$(lsof -ti:8001 2>/dev/null || true)
if [ -n "$BACKEND_PORT_PID" ]; then
    echo -e "   Killing process on port 8001 (PID: $BACKEND_PORT_PID)"
    kill -9 $BACKEND_PORT_PID 2>/dev/null || true
fi

# Kill frontend on port 3000 (and 3001, 3002 as fallbacks)
for port in 3000 3001 3002; do
    FRONTEND_PORT_PID=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$FRONTEND_PORT_PID" ]; then
        echo -e "   Killing process on port $port (PID: $FRONTEND_PORT_PID)"
        kill -9 $FRONTEND_PORT_PID 2>/dev/null || true
    fi
done

# Kill any uvicorn processes for this project
pkill -f "uvicorn app.main:app.*8001" 2>/dev/null || true

# Kill any npm/vite dev processes
pkill -f "vite.*philosophy_video_generator" 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All Services Stopped!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 Logs are preserved in:${NC}"
echo "   $LOG_DIR/"
echo ""

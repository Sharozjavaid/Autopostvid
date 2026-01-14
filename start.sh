#!/bin/bash

# Philosophy Video Generator - Start Script
# Starts both frontend and backend with logging

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log directories
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Log files
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
COMBINED_LOG="$LOG_DIR/combined.log"
PID_FILE="$LOG_DIR/pids.txt"

# Timestamp for logs
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Philosophy Video Generator${NC}"
echo -e "${BLUE}  Starting Services...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if already running
if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  Services may already be running.${NC}"
    echo -e "${YELLOW}   Run ./stop.sh first if you want to restart.${NC}"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Clear old logs (keep last 5)
echo -e "${YELLOW}📁 Rotating logs...${NC}"
for log in "$BACKEND_LOG" "$FRONTEND_LOG" "$COMBINED_LOG"; do
    if [ -f "$log" ]; then
        # Keep backup of last log
        mv "$log" "${log}.$(date '+%Y%m%d_%H%M%S').bak" 2>/dev/null || true
    fi
done
# Clean up old backups (keep last 5)
ls -t "$LOG_DIR"/*.bak 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true

# Initialize log files
echo "=== Started at $TIMESTAMP ===" > "$BACKEND_LOG"
echo "=== Started at $TIMESTAMP ===" > "$FRONTEND_LOG"
echo "=== Combined Log Started at $TIMESTAMP ===" > "$COMBINED_LOG"

# Function to log with prefix
log_with_prefix() {
    local prefix=$1
    local color=$2
    while IFS= read -r line; do
        timestamp=$(date '+%H:%M:%S')
        echo "[$timestamp] [$prefix] $line" >> "$COMBINED_LOG"
        echo -e "${color}[$prefix]${NC} $line"
    done
}

# Start Backend
echo -e "${GREEN}🚀 Starting Backend (port 8001)...${NC}"
cd "$SCRIPT_DIR/backend"

# Activate virtual environment if exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start backend with logging
python3 -m uvicorn app.main:app --reload --port 8001 2>&1 | tee -a "$BACKEND_LOG" | log_with_prefix "BACKEND" "$GREEN" &
BACKEND_PID=$!

cd "$SCRIPT_DIR"

# Wait a moment for backend to start
sleep 2

# Start Frontend
echo -e "${BLUE}🎨 Starting Frontend (port 3000)...${NC}"
cd "$SCRIPT_DIR/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend with logging
npm run dev 2>&1 | tee -a "$FRONTEND_LOG" | log_with_prefix "FRONTEND" "$BLUE" &
FRONTEND_PID=$!

cd "$SCRIPT_DIR"

# Save PIDs
echo "BACKEND_PID=$BACKEND_PID" > "$PID_FILE"
echo "FRONTEND_PID=$FRONTEND_PID" >> "$PID_FILE"
echo "STARTED_AT=$TIMESTAMP" >> "$PID_FILE"

# Wait for services to be ready
echo ""
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 3

# Check if services are running
BACKEND_RUNNING=false
FRONTEND_RUNNING=false

if kill -0 $BACKEND_PID 2>/dev/null; then
    BACKEND_RUNNING=true
fi

if kill -0 $FRONTEND_PID 2>/dev/null; then
    FRONTEND_RUNNING=true
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Started!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} Backend:  http://localhost:8001"
echo -e "  ${GREEN}✓${NC} Frontend: http://localhost:3000"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo "  • Backend:  $BACKEND_LOG"
echo "  • Frontend: $FRONTEND_LOG"
echo "  • Combined: $COMBINED_LOG"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "  • View combined logs: tail -f $COMBINED_LOG"
echo "  • Stop services: ./stop.sh"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop watching logs (services will continue running)${NC}"
echo ""

# Follow combined log
tail -f "$COMBINED_LOG"

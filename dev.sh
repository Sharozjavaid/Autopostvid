#!/bin/bash

# Philosophy Video Generator - Development Mode
# Runs both services in foreground with interleaved colored output
# Press Ctrl+C to stop both services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Log directory
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down...${NC}"
    
    # Kill all background jobs
    jobs -p | xargs -r kill 2>/dev/null
    
    # Kill processes on ports
    lsof -ti:8001 | xargs -r kill -9 2>/dev/null
    lsof -ti:3000 | xargs -r kill -9 2>/dev/null
    lsof -ti:3001 | xargs -r kill -9 2>/dev/null
    lsof -ti:3002 | xargs -r kill -9 2>/dev/null
    
    echo -e "${GREEN}✓ All services stopped${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

echo -e "${MAGENTA}========================================${NC}"
echo -e "${MAGENTA}  Philosophy Video Generator${NC}"
echo -e "${MAGENTA}  Development Mode${NC}"
echo -e "${MAGENTA}========================================${NC}"
echo ""

# Kill any existing processes on our ports
echo -e "${YELLOW}🧹 Cleaning up old processes...${NC}"
lsof -ti:8001 | xargs -r kill -9 2>/dev/null || true
lsof -ti:3000 | xargs -r kill -9 2>/dev/null || true
sleep 1

# Function to prefix output
prefix_output() {
    local prefix=$1
    local color=$2
    local log_file=$3
    while IFS= read -r line; do
        timestamp=$(date '+%H:%M:%S')
        # Log to file
        echo "[$timestamp] $line" >> "$log_file"
        # Output with color and prefix
        echo -e "${color}[$prefix]${NC} $line"
    done
}

# Start Backend
echo -e "${GREEN}🚀 Starting Backend on port 8001...${NC}"
(
    cd "$SCRIPT_DIR/backend"
    
    # Try to activate virtual environment
    if [ -d "../venv" ]; then
        source ../venv/bin/activate 2>/dev/null || true
    elif [ -d "venv" ]; then
        source venv/bin/activate 2>/dev/null || true
    fi
    
    python3 -m uvicorn app.main:app --reload --port 8001 2>&1
) | prefix_output "API" "$GREEN" "$LOG_DIR/backend.log" &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start Frontend
echo -e "${BLUE}🎨 Starting Frontend on port 3000...${NC}"
(
    cd "$SCRIPT_DIR/frontend"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    npm run dev 2>&1
) | prefix_output "WEB" "$BLUE" "$LOG_DIR/frontend.log" &
FRONTEND_PID=$!

# Wait for both to be ready
sleep 3

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Development Server Ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  ${CYAN}Frontend:${NC}  http://localhost:3000"
echo -e "  ${CYAN}Backend:${NC}   http://localhost:8001"
echo -e "  ${CYAN}API Docs:${NC}  http://localhost:8001/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""
echo -e "${MAGENTA}─────────────────────────────────────────${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

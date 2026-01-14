#!/bin/bash

# Philosophy Video Generator - Log Viewer
# View logs with filtering options

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

show_help() {
    echo -e "${BLUE}Philosophy Video Generator - Log Viewer${NC}"
    echo ""
    echo "Usage: ./logs.sh [option]"
    echo ""
    echo "Options:"
    echo "  -a, --all       Show combined logs (default)"
    echo "  -b, --backend   Show backend logs only"
    echo "  -f, --frontend  Show frontend logs only"
    echo "  -e, --errors    Show only errors from all logs"
    echo "  -l, --list      List available log files"
    echo "  -c, --clear     Clear all logs"
    echo "  -h, --help      Show this help"
    echo ""
    echo "Examples:"
    echo "  ./logs.sh              # Follow combined logs"
    echo "  ./logs.sh --backend    # Follow backend logs"
    echo "  ./logs.sh --errors     # Show only errors"
    echo ""
}

colorize_logs() {
    while IFS= read -r line; do
        # Color based on content
        if [[ $line == *"[BACKEND]"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line == *"[FRONTEND]"* ]]; then
            echo -e "${BLUE}$line${NC}"
        elif [[ $line == *"ERROR"* ]] || [[ $line == *"error"* ]] || [[ $line == *"Error"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ $line == *"WARNING"* ]] || [[ $line == *"warning"* ]] || [[ $line == *"Warning"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ $line == *"INFO"* ]] || [[ $line == *"info"* ]]; then
            echo -e "${CYAN}$line${NC}"
        else
            echo "$line"
        fi
    done
}

case "${1:-all}" in
    -a|--all|all)
        echo -e "${BLUE}📝 Following combined logs... (Ctrl+C to stop)${NC}"
        echo ""
        tail -f "$LOG_DIR/combined.log" 2>/dev/null | colorize_logs || echo "No combined log found. Start the services first."
        ;;
    -b|--backend|backend)
        echo -e "${GREEN}📝 Following backend logs... (Ctrl+C to stop)${NC}"
        echo ""
        tail -f "$LOG_DIR/backend.log" 2>/dev/null | colorize_logs || echo "No backend log found. Start the services first."
        ;;
    -f|--frontend|frontend)
        echo -e "${BLUE}📝 Following frontend logs... (Ctrl+C to stop)${NC}"
        echo ""
        tail -f "$LOG_DIR/frontend.log" 2>/dev/null | colorize_logs || echo "No frontend log found. Start the services first."
        ;;
    -e|--errors|errors)
        echo -e "${RED}📝 Showing errors from all logs...${NC}"
        echo ""
        grep -i -E "(error|exception|failed|traceback)" "$LOG_DIR"/*.log 2>/dev/null | colorize_logs || echo "No errors found."
        ;;
    -l|--list|list)
        echo -e "${BLUE}📁 Available log files:${NC}"
        echo ""
        ls -lah "$LOG_DIR"/*.log 2>/dev/null || echo "No log files found."
        echo ""
        ls -lah "$LOG_DIR"/*.bak 2>/dev/null && echo "" || true
        ;;
    -c|--clear|clear)
        echo -e "${YELLOW}🗑️  Clearing all logs...${NC}"
        rm -f "$LOG_DIR"/*.log "$LOG_DIR"/*.bak 2>/dev/null
        echo -e "${GREEN}✓ Logs cleared${NC}"
        ;;
    -h|--help|help)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

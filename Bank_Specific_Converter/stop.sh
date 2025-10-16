#!/bin/bash
# Stop script for Bank Statement Converter
# ========================================

GUNICORN_PID="/var/run/gunicorn/bank_converter.pid"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping Bank Statement Converter...${NC}"

if [ -f "$GUNICORN_PID" ]; then
    PID=$(cat "$GUNICORN_PID")
    if ps -p $PID > /dev/null; then
        kill $PID
        echo -e "${GREEN}✅ Stopped Gunicorn process (PID: $PID)${NC}"
        rm -f "$GUNICORN_PID"
    else
        echo -e "${YELLOW}⚠️  Process not running, removing stale PID file${NC}"
        rm -f "$GUNICORN_PID"
    fi
else
    echo -e "${RED}❌ PID file not found. Is the application running?${NC}"
fi

# Kill any remaining Gunicorn processes
REMAINING=$(pgrep -f "gunicorn.*wsgi:application")
if [ ! -z "$REMAINING" ]; then
    echo -e "${YELLOW}🧹 Cleaning up remaining processes...${NC}"
    pkill -f "gunicorn.*wsgi:application"
    echo -e "${GREEN}✅ Cleaned up remaining processes${NC}"
fi

echo -e "${GREEN}🏁 Bank Statement Converter stopped${NC}"
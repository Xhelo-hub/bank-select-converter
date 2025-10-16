#!/bin/bash
# Production startup script for Bank Statement Converter
# ===================================================

# Configuration
APP_DIR="/home/admin/web/yourdomain.com/public_html/bank_converter"
VENV_DIR="$APP_DIR/venv"
GUNICORN_PID="/var/run/gunicorn/bank_converter.pid"
GUNICORN_LOG="/var/log/gunicorn/bank_converter_error.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏦 Bank Statement Converter - Production Startup${NC}"
echo "=================================================="

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Error: Application directory not found: $APP_DIR${NC}"
    exit 1
fi

cd "$APP_DIR"

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}🐍 Activating virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"
else
    echo -e "${RED}❌ Error: Virtual environment not found: $VENV_DIR${NC}"
    exit 1
fi

# Check if Gunicorn is already running
if [ -f "$GUNICORN_PID" ] && ps -p $(cat "$GUNICORN_PID") > /dev/null; then
    echo -e "${YELLOW}⚠️  Gunicorn is already running (PID: $(cat $GUNICORN_PID))${NC}"
    echo "Use 'stop.sh' to stop it first, or 'restart.sh' to restart."
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p /var/log/gunicorn
mkdir -p /var/run/gunicorn

# Set environment variables
export FLASK_ENV=production
export PYTHONPATH="$APP_DIR:$PYTHONPATH"

# Start Gunicorn
echo -e "${YELLOW}🚀 Starting Gunicorn server...${NC}"
gunicorn --config gunicorn.conf.py wsgi:application --daemon

# Check if started successfully
sleep 2
if [ -f "$GUNICORN_PID" ] && ps -p $(cat "$GUNICORN_PID") > /dev/null; then
    echo -e "${GREEN}✅ Bank Statement Converter started successfully!${NC}"
    echo "PID: $(cat $GUNICORN_PID)"
    echo "Log: $GUNICORN_LOG"
    echo "Access: http://yourdomain.com"
else
    echo -e "${RED}❌ Failed to start Gunicorn. Check the logs:${NC}"
    echo "tail -f $GUNICORN_LOG"
fi
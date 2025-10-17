#!/bin/bash

# Bank Statement Converter - HestiaCP Deployment Script
# This script deploys the application to converter@c.konsulence.al

set -e  # Exit on any error

echo "=========================================="
echo "Bank Statement Converter - Server Setup"
echo "=========================================="

# Configuration
DEPLOY_USER="converter"
DEPLOY_HOST="c.konsulence.al"
DEPLOY_DIR="/home/converter/web/c.konsulence.al/public_html"
REPO_URL="https://github.com/Xhelo-hub/bank-select-converter.git"

echo ""
echo "Step 1: Navigating to deployment directory..."
cd "$DEPLOY_DIR" || { echo "Error: Cannot access $DEPLOY_DIR"; exit 1; }

echo ""
echo "Step 2: Checking if this is a git repository..."
if [ -d .git ]; then
    echo "✓ Git repository found"
    
    echo ""
    echo "Step 3: Pulling latest changes from GitHub..."
    git pull origin main || { echo "Error: Git pull failed"; exit 1; }
else
    echo "! Git repository not found. Cloning from GitHub..."
    cd ..
    rm -rf public_html
    git clone "$REPO_URL" public_html
    cd public_html
fi

echo ""
echo "Step 4: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Python is installed: $PYTHON_VERSION"
else
    echo "! Python3 is not installed. Installing Python3..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

echo ""
echo "Step 5: Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv .venv
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "Step 6: Activating virtual environment and installing dependencies..."
source .venv/bin/activate

# Install root requirements
if [ -f "requirements.txt" ]; then
    echo "Installing root requirements..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Install Bank_Specific_Converter requirements
if [ -f "Bank_Specific_Converter/requirements.txt" ]; then
    echo "Installing Bank_Specific_Converter requirements..."
    pip install -r Bank_Specific_Converter/requirements.txt
fi

echo ""
echo "Step 7: Creating necessary directories..."
mkdir -p import export converted
mkdir -p Bank_Specific_Converter/import Bank_Specific_Converter/export Bank_Specific_Converter/converted
chmod 755 import export converted
chmod 755 Bank_Specific_Converter/import Bank_Specific_Converter/export Bank_Specific_Converter/converted

echo ""
echo "Step 8: Setting up systemd service (requires sudo)..."
cat > /tmp/bank-converter.service << 'EOF'
[Unit]
Description=Bank Statement Converter Web Service
After=network.target

[Service]
Type=notify
User=converter
Group=converter
WorkingDirectory=/home/converter/web/c.konsulence.al/public_html/Bank_Specific_Converter
Environment="PATH=/home/converter/web/c.konsulence.al/public_html/.venv/bin"
ExecStart=/home/converter/web/c.konsulence.al/public_html/.venv/bin/gunicorn --config gunicorn.conf.py wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/bank-converter.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "Step 9: Installing Gunicorn if not present..."
pip install gunicorn

echo ""
echo "Step 10: Checking if gunicorn.conf.py exists..."
if [ ! -f "Bank_Specific_Converter/gunicorn.conf.py" ]; then
    echo "Creating gunicorn.conf.py..."
    cat > Bank_Specific_Converter/gunicorn.conf.py << 'EOF'
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 2

# Logging
accesslog = "/home/converter/web/c.konsulence.al/logs/gunicorn-access.log"
errorlog = "/home/converter/web/c.konsulence.al/logs/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "bank-converter"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None
EOF
fi

echo ""
echo "Step 11: Starting/Restarting the service..."
sudo systemctl enable bank-converter
sudo systemctl restart bank-converter

echo ""
echo "Step 12: Checking service status..."
sudo systemctl status bank-converter --no-pager

echo ""
echo "=========================================="
echo "✓ Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Service Information:"
echo "  - Status: sudo systemctl status bank-converter"
echo "  - Logs: sudo journalctl -u bank-converter -f"
echo "  - Restart: sudo systemctl restart bank-converter"
echo ""
echo "Application URLs:"
echo "  - Main: https://c.konsulence.al"
echo "  - HTTP: http://c.konsulence.al"
echo ""
echo "Next steps:"
echo "1. Configure Nginx reverse proxy in HestiaCP"
echo "2. Test the application"
echo "3. Monitor logs for any issues"
echo ""

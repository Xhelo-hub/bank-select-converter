#!/bin/bash
# Deployment script to add authentication to live server
# Run this on the server as converter user

set -e

echo "🔐 Deploying Authentication System"
echo "=========================================="

# Navigate to app directory
cd ~/web/c.konsulence.al/public_html
echo "✅ In directory: $(pwd)"

# Pull latest code
echo ""
echo "[1/7] Pulling latest code from GitHub..."
git pull origin main

# Activate virtual environment
echo ""
echo "[2/7] Activating virtual environment..."
source .venv/bin/activate

# Install new dependencies
echo ""
echo "[3/7] Installing authentication dependencies..."
pip install flask-login flask-bcrypt

# Navigate to Bank_Specific_Converter
cd Bank_Specific_Converter

# Run integration script
echo ""
echo "[4/7] Integrating authentication into app.py..."
python integrate_auth.py

# Create users database file
echo ""
echo "[5/7] Creating user database..."
if [ ! -f users.json ]; then
    echo "[]" > users.json
    chmod 600 users.json
    echo "✅ Created users.json"
else
    echo "ℹ️  users.json already exists"
fi

# Kill existing Flask process
echo ""
echo "[6/7] Stopping existing Flask app..."
pkill -f "python app.py" || echo "No existing process found"
sleep 2

# Start Flask app with authentication
echo ""
echo "[7/7] Starting Flask app with authentication..."
nohup python app.py > app.log 2>&1 &
sleep 3

# Check if app started
if ps aux | grep -v grep | grep "python app.py" > /dev/null; then
    echo ""
    echo "=========================================="
    echo "✅ Authentication deployed successfully!"
    echo "=========================================="
    echo ""
    echo "🎉 Your app is now running with authentication!"
    echo ""
    echo "Next steps:"
    echo "1. Visit: https://c.konsulence.al/auth/register"
    echo "2. Create your first user account"
    echo "3. Login at: https://c.konsulence.al/auth/login"
    echo ""
    echo "The main converter is now protected - login required!"
    echo ""
else
    echo ""
    echo "❌ Failed to start Flask app"
    echo "Check the log with: tail -f app.log"
    exit 1
fi

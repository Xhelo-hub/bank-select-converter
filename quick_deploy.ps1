# Quick Deploy Script - Run all commands on server
# This connects to the server and runs all deployment commands

$SERVER = "converter@c.konsulence.al"
$DEPLOY_DIR = "/home/converter/web/c.konsulence.al/public_html"

Write-Host "Connecting to server and deploying..." -ForegroundColor Green

ssh $SERVER @'
set -e
echo "=========================================="
echo "Bank Statement Converter - Quick Deploy"
echo "=========================================="

cd /home/converter/web/c.konsulence.al/public_html

echo ""
echo "[1/10] Pulling latest code from GitHub..."
if [ -d .git ]; then
    git pull origin main
else
    echo "Setting up git repository..."
    git init
    git remote add origin https://github.com/Xhelo-hub/bank-select-converter.git
    git fetch origin
    git checkout -b main origin/main
fi

echo ""
echo "[2/10] Checking Python installation..."
python3 --version || {
    echo "Installing Python3..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
}

echo ""
echo "[3/10] Setting up virtual environment..."
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

echo ""
echo "[4/10] Activating virtual environment..."
source .venv/bin/activate

echo ""
echo "[5/10] Upgrading pip..."
pip install --upgrade pip

echo ""
echo "[6/10] Installing root dependencies..."
pip install -r requirements.txt

echo ""
echo "[7/10] Installing Bank_Specific_Converter dependencies..."
pip install -r Bank_Specific_Converter/requirements.txt

echo ""
echo "[8/10] Installing Gunicorn..."
pip install gunicorn

echo ""
echo "[9/10] Creating necessary directories..."
mkdir -p import export converted uploads
mkdir -p Bank_Specific_Converter/import Bank_Specific_Converter/export Bank_Specific_Converter/converted Bank_Specific_Converter/uploads
chmod 755 import export converted uploads
chmod 755 Bank_Specific_Converter/import Bank_Specific_Converter/export Bank_Specific_Converter/converted Bank_Specific_Converter/uploads

echo ""
echo "[10/10] Testing application..."
cd Bank_Specific_Converter
python -c "from app import app; print('✓ App imports successfully')"

echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "To run the web interface:"
echo "  cd /home/converter/web/c.konsulence.al/public_html/Bank_Specific_Converter"
echo "  source ../.venv/bin/activate"
echo "  python app.py"
echo ""
echo "Or start with Gunicorn:"
echo "  gunicorn --bind 0.0.0.0:5002 wsgi:application"
echo ""
'@

Write-Host ""
Write-Host "Deployment finished!" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Connect to server and start the app:"
Write-Host "  ssh converter@c.konsulence.al" -ForegroundColor Yellow
Write-Host "  cd /home/converter/web/c.konsulence.al/public_html/Bank_Specific_Converter" -ForegroundColor Yellow
Write-Host "  source ../.venv/bin/activate" -ForegroundColor Yellow
Write-Host "  python app.py" -ForegroundColor Yellow

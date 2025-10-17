# PowerShell script to deploy Bank Converter to HestiaCP server
# Run this from your local machine

$SERVER = "converter@c.konsulence.al"
$DEPLOY_DIR = "/home/converter/web/c.konsulence.al/public_html"

Write-Host "=========================================="
Write-Host "Bank Statement Converter - Remote Deploy"
Write-Host "=========================================="
Write-Host ""

# Step 1: Copy deployment script to server
Write-Host "Step 1: Copying deployment script to server..."
scp deploy_to_hestia.sh "$SERVER`:~/deploy_to_hestia.sh"

# Step 2: Make script executable and run it
Write-Host ""
Write-Host "Step 2: Executing deployment on server..."
ssh $SERVER @"
chmod +x ~/deploy_to_hestia.sh
cd $DEPLOY_DIR
bash ~/deploy_to_hestia.sh
"@

Write-Host ""
Write-Host "=========================================="
Write-Host "Deployment complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "To check the status:"
Write-Host "  ssh $SERVER"
Write-Host "  sudo systemctl status bank-converter"
Write-Host ""

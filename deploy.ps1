# Bank Statement Converter - Windows Deployment Script
# ====================================================
# Usage: .\deploy.ps1 [-message "commit message"]

param(
    [string]$message = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$serverHost = "hestia"
$remotePath = "/home/converter/web/c.konsulence.al/public_html"

Write-Host "`n🏦 Bank Statement Converter - Deploy to Hestia" -ForegroundColor Cyan
Write-Host "=" * 50

# Step 1: Check git status
Write-Host "`n📋 Checking git status..." -ForegroundColor Yellow
Set-Location $projectRoot
$status = git status --porcelain

if ($status) {
    Write-Host "Changes detected:" -ForegroundColor Yellow
    git status --short
    
    if (-not $message) {
        $message = Read-Host "`nEnter commit message"
    }
    
    if (-not $message) {
        Write-Host "❌ No commit message provided. Aborting." -ForegroundColor Red
        exit 1
    }
    
    # Stage and commit
    Write-Host "`n📦 Staging and committing changes..." -ForegroundColor Yellow
    git add -A
    git commit -m $message
    
    # Push to origin
    Write-Host "`n🚀 Pushing to GitHub..." -ForegroundColor Yellow
    git push origin main
} else {
    Write-Host "✅ Working directory clean - no local changes" -ForegroundColor Green
}

# Step 2: Deploy to server
Write-Host "`n🔄 Deploying to production server..." -ForegroundColor Yellow

# Pull latest changes on server (preserving server-specific configs)
$sshCommands = @"
cd $remotePath &&
git stash --include-untracked 2>/dev/null
git fetch origin &&
git reset --hard origin/main &&
git stash pop 2>/dev/null || true
echo '✅ Code synced (server configs preserved)' &&
cd Bank_Specific_Converter &&
source ../.venv/bin/activate &&
pip install -q -r requirements.txt 2>/dev/null &&
echo '✅ Dependencies updated' &&
sudo systemctl restart bank-converter &&
echo '✅ Service restarted' &&
systemctl is-active bank-converter
"@

ssh $serverHost $sshCommands

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 Deployment successful!" -ForegroundColor Green
    Write-Host "🌐 Live at: https://converter.konsulence.al" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Deployment failed! Check server logs." -ForegroundColor Red
    Write-Host "Run: ssh hestia 'journalctl -u bank-converter -n 50'" -ForegroundColor Yellow
}

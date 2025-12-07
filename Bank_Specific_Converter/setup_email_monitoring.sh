#!/bin/bash
# Email and Health Monitor Setup Script
# Run this on the production server after pulling the latest code

echo "====================================="
echo "Email & Health Monitor Setup"
echo "====================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Navigate to project directory
PROJECT_DIR="/home/converter/web/c.konsulence.al/public_html"
cd "$PROJECT_DIR" || exit 1

echo "1. Pulling latest changes from Git..."
git pull origin main

echo ""
echo "2. Installing health monitor service..."
cp Bank_Specific_Converter/health-monitor.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "3. Checking current email configuration..."
if systemctl show bank-converter.service -p Environment | grep -q "SMTP_USERNAME"; then
    echo "✓ Email configuration found in bank-converter.service"
else
    echo "⚠ Email configuration NOT found"
    echo ""
    echo "You need to add email configuration to the bank-converter service:"
    echo "  sudo nano /etc/systemd/system/bank-converter.service"
    echo ""
    echo "Add these lines in the [Service] section:"
    echo '  Environment="SMTP_SERVER=smtp.gmail.com"'
    echo '  Environment="SMTP_PORT=587"'
    echo '  Environment="SMTP_USERNAME=your-email@gmail.com"'
    echo '  Environment="SMTP_PASSWORD=your-app-password"'
    echo '  Environment="FROM_EMAIL=your-email@gmail.com"'
    echo ""
    read -p "Press Enter after you've added the configuration..."
    systemctl daemon-reload
fi

echo ""
echo "4. Starting health monitor..."
systemctl enable health-monitor.service
systemctl start health-monitor.service

echo ""
echo "5. Restarting main application..."
systemctl restart bank-converter.service

echo ""
echo "====================================="
echo "Setup Complete!"
echo "====================================="
echo ""
echo "Service Status:"
systemctl status bank-converter.service --no-pager -l | head -10
echo ""
systemctl status health-monitor.service --no-pager -l | head -10

echo ""
echo "====================================="
echo "Next Steps:"
echo "====================================="
echo ""
echo "1. Test password reset: https://c.konsulence.al/forgot-password"
echo "2. Monitor health checks: sudo journalctl -u health-monitor.service -f"
echo "3. View all logs: sudo journalctl -u bank-converter.service -u health-monitor.service -f"
echo ""
echo "To test system alerts:"
echo "  sudo systemctl stop bank-converter.service"
echo "  (wait 5-10 minutes for alert email)"
echo "  sudo systemctl start bank-converter.service"
echo ""
echo "For full documentation, see:"
echo "  Bank_Specific_Converter/EMAIL_SETUP_GUIDE.md"
echo ""

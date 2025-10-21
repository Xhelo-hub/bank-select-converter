#!/bin/bash
# Fix Production users.json
# Run this on the production server

cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter

# Backup current file
cp users.json users.json.backup

# Create new users.json with correct admin password
cat > users.json << 'EOF'
[
  {
    "id": "5b8ea946-69fa-4595-ad82-2797490df94c",
    "email": "kontakt@konsulence.al",
    "password": "$2b$12$ynzCo79dxkWyUh/RIFrwHesPM758Zq99oLmoIvPtPZtRlGTMqCJwe",
    "created_at": "2025-10-17T20:00:29.150407",
    "is_admin": true,
    "is_approved": true,
    "is_active": true,
    "reset_token": null,
    "reset_token_expiry": null
  }
]
EOF

# Set correct permissions
chmod 600 users.json

# Restart the app
pkill -f 'python app.py'
sleep 1
source ../.venv/bin/activate
nohup python app.py > app.log 2>&1 &

# Wait and check if it's running
sleep 2
ps aux | grep 'python app.py' | grep -v grep

echo ""
echo "✅ Fix applied!"
echo "Login: kontakt@konsulence.al"
echo "Password: Admin@123"
echo ""
echo "Check log: tail -20 app.log"

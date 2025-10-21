# 🎯 SIMPLE FIX - Run This on Production Server

**Problem:** Internal Server Error (Invalid Salt)  
**Solution:** Update users.json with correct password

---

## 🚀 FASTEST FIX (Copy-Paste This)

### Step 1: SSH to server
```bash
ssh converter@c.konsulence.al
```

### Step 2: Copy-paste this entire block
```bash
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter && \
cp users.json users.json.backup && \
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

chmod 600 users.json && \
pkill -f 'python app.py' && \
source ../.venv/bin/activate && \
nohup python app.py > app.log 2>&1 & \
sleep 2 && \
ps aux | grep 'python app.py' | grep -v grep && \
echo "" && \
echo "✅ FIXED! Login with:" && \
echo "Email: kontakt@konsulence.al" && \
echo "Password: Admin@123"
```

---

## 🔑 LOGIN CREDENTIALS

**Email:** `kontakt@konsulence.al`  
**Password:** `Admin@123`

---

## ✅ What This Does

1. Backs up the corrupted `users.json`
2. Creates new `users.json` with correct password hash
3. Sets secure file permissions (600)
4. Restarts the Flask app
5. Shows confirmation

---

## 🧪 Test After Running

1. Go to: https://c.konsulence.al
2. Login with credentials above
3. Should work! ✅

---

**Time to fix:** 30 seconds ⚡

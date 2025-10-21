# 🔧 FIX: Internal Server Error - Invalid Salt

**Date:** October 21, 2025  
**Issue:** ValueError: Invalid salt in password verification  
**Cause:** Corrupted `users.json` file on production server

---

## 🔍 Problem Identified

**Error in logs:**
```
ValueError: Invalid salt
at auth.py line 140: bcrypt.check_password_hash(user.password, password)
```

**Root Cause:**
Production `users.json` has corrupted password hashes:
- Current (corrupted): `"password": "scrypt:32768:8:1\\"`
- Expected (correct): `"password": "$2b$12$rzIyAB2nxj3hRABN/pFjZ.SBZPH1SQnXNoZndaifSQ79mlpIHz/Ai"`

---

## ✅ MANUAL FIX (Run on Production Server)

### Step 1: SSH to Server
```bash
ssh converter@c.konsulence.al
```

### Step 2: Backup Corrupted File
```bash
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
cp users.json users.json.corrupted.backup
```

### Step 3: Create Fixed users.json
```bash
cat > users.json << 'EOF'
[
  {
    "id": "5b8ea946-69fa-4595-ad82-2797490df94c",
    "email": "kontakt@konsulence.al",
    "password": "$2b$12$rzIyAB2nxj3hRABN/pFjZ.SBZPH1SQnXNoZndaifSQ79mlpIHz/Ai",
    "created_at": "2025-10-17T20:00:29.150407",
    "is_admin": true,
    "is_approved": true,
    "is_active": true,
    "reset_token": null,
    "reset_token_expiry": null
  },
  {
    "id": "8b675b3d-cdad-404a-af88-13b58ad53b35",
    "email": "luljeta@palushi.com",
    "password": "$2b$12$goRtSNc./txAY8/dtHelquyG5KHx5leVTLrY74YSn/Y.lKePQwMBK",
    "created_at": "2025-10-17T21:13:11.494056",
    "is_admin": false,
    "is_approved": false,
    "is_active": false,
    "reset_token": null,
    "reset_token_expiry": null
  }
]
EOF
```

### Step 4: Set Correct Permissions
```bash
chmod 600 users.json
```

### Step 5: Restart Flask App
```bash
# Kill old process
pkill -f 'python app.py'

# Start new process
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
source ../.venv/bin/activate
nohup python app.py > app.log 2>&1 &
```

### Step 6: Verify App is Running
```bash
ps aux | grep 'python app.py' | grep -v grep
```

### Step 7: Check Logs
```bash
tail -20 app.log
```

---

## 🔑 Login Credentials (After Fix)

**Admin Account:**
- Email: `kontakt@konsulence.al`
- Password: `admin123` (or whatever was set locally)

**Pending User:**
- Email: `luljeta@palushi.com`
- Status: Not approved, cannot login yet

---

## 🧪 Test the Fix

1. Open browser: https://c.konsulence.al
2. Try to login with admin credentials
3. Should work without "Internal Server Error"

---

## 🔄 Alternative: Reset Password Using Script

If you want to set a NEW password:

```bash
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
source ../.venv/bin/activate
python reset_admin_password.py kontakt@konsulence.al YourNewPassword123
```

Then restart the app:
```bash
pkill -f 'python app.py'
nohup python app.py > app.log 2>&1 &
```

---

## 📝 Why This Happened

The `users.json` file was likely corrupted during a previous deployment or edit. The password hashes were truncated to `"scrypt:32768:8:1\\"` which is invalid.

**Solution:** Replace with correct bcrypt hashes from local development version.

---

## ✅ After Fix - What to Do

1. ✅ Verify login works on https://c.konsulence.al
2. ✅ Test converter upload functionality
3. 🔒 Consider adding `users.json` to `.gitignore` to prevent overwrites
4. 📋 Document the correct admin password securely

---

**Status:** Ready to fix manually on production server  
**Time estimate:** 2-3 minutes

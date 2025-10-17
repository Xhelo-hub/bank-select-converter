# 🚀 Deploy Authentication System - Step by Step

## Current Status
✅ All authentication files committed to GitHub  
✅ Integration scripts created  
✅ App is currently running at https://c.konsulence.al  
⏳ Ready to add authentication  

---

## 🎯 Simple Deployment Steps

### Step 1: Pull Latest Code to Server

```bash
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html
git pull origin main
```

**Expected output:**
```
Updating 0201141..c68bb10
Fast-forward
 Bank_Specific_Converter/auth.py | ...
 Bank_Specific_Converter/auth_routes.py | ...
 ... (files downloaded)
```

---

### Step 2: Install New Dependencies

```bash
cd ~/web/c.konsulence.al/public_html
source .venv/bin/activate
pip install flask-login flask-bcrypt
```

**Expected output:**
```
Collecting flask-login
Collecting flask-bcrypt
Successfully installed flask-login-... flask-bcrypt-... bcrypt-...
```

---

### Step 3: Run the Automatic Integration Script

```bash
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
python integrate_auth.py
```

**This script will:**
- Backup your current `app.py` to `app.py.backup`
- Create a new `app.py` with authentication
- Set up the users database

**Expected output:**
```
✅ Backed up app.py to app.py.backup
✅ Created new authenticated app.py
✅ Created users.json database
🎉 Authentication integration complete!
```

---

### Step 4: Restart the Flask App

```bash
# Stop the current app
pkill -f "python app.py"

# Start the new authenticated version
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
source ../.venv/bin/activate
nohup python app.py > app.log 2>&1 &

# Check if it's running
ps aux | grep "python app.py"
```

**Expected output:**
```
[1] 1234567
converter  1234567  ... python app.py
```

---

### Step 5: Test the Login System

1. **Visit the login page:**
   ```
   https://c.konsulence.al/login
   ```

2. **Register first user:**
   ```
   https://c.konsulence.al/register
   ```
   - Email: admin@konsulence.al
   - Password: (your secure password)

3. **Login and test:**
   - Should redirect to main converter page
   - Upload a test file
   - Convert and download

---

## 🔧 Alternative: Manual Deployment (If Automatic Fails)

If the automatic script has issues, use this manual method:

```bash
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter

# Backup current app
cp app.py app.py.backup

# Use the template
cp app_with_auth_template.py app.py

# Or run the deployment script
bash deploy_auth.sh
```

---

## ✅ Verification Checklist

After deployment:

- [ ] Can access https://c.konsulence.al/login (login page loads)
- [ ] Can register a new user
- [ ] Can login with registered credentials
- [ ] Redirected to login when not authenticated
- [ ] Can access converter after login
- [ ] Can upload and convert files
- [ ] Can logout successfully

---

## 🆘 Troubleshooting

### Problem: Can't access /login page (404)
**Solution:** The app didn't restart properly
```bash
pkill -f "python app.py"
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
source ../.venv/bin/activate
python app.py
```

### Problem: Import errors for flask_login
**Solution:** Dependencies not installed
```bash
source .venv/bin/activate
pip install flask-login flask-bcrypt
```

### Problem: Can't register users
**Solution:** Check users.json permissions
```bash
ls -la users.json
chmod 600 users.json
```

### Problem: App crashes on startup
**Solution:** Check the log
```bash
tail -50 app.log
```

---

## 📞 Quick Commands Reference

```bash
# Connect to server
ssh converter@c.konsulence.al

# Check if app is running
ps aux | grep "python app.py"

# View app logs
tail -f ~/web/c.konsulence.al/public_html/Bank_Specific_Converter/app.log

# Restart app
pkill -f "python app.py"
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
source ../.venv/bin/activate
nohup python app.py > app.log 2>&1 &

# Check users
cat users.json
```

---

## 🎉 Success Criteria

When everything works:
1. ✅ https://c.konsulence.al redirects to /login if not authenticated
2. ✅ Can register new users
3. ✅ Can login with credentials
4. ✅ Converter works after authentication
5. ✅ Can logout and login again

---

## 📝 What Happens Next

After successful deployment:
- All users must login to access the converter
- First registered user should be your admin account
- User data stored securely in `users.json`
- Sessions managed automatically
- HTTPS ensures secure password transmission

---

## 🚀 Ready to Deploy?

**Run these 4 commands:**

```bash
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html && git pull origin main
source .venv/bin/activate && pip install flask-login flask-bcrypt
cd Bank_Specific_Converter && python integrate_auth.py && pkill -f "python app.py" && nohup python app.py > app.log 2>&1 &
```

Then visit: **https://c.konsulence.al/login** 🎉

---

Need help with deployment? Just ask! I can guide you through each step. 🤝

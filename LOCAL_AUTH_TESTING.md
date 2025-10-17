# Local Authentication Testing Guide

## ✅ Setup Complete

The authenticated version is now running locally at: **http://127.0.0.1:5002**

## Test Checklist

### 1. Test Login Redirect
- [ ] Visit http://127.0.0.1:5002
- [ ] **Expected**: Should redirect to http://127.0.0.1:5002/auth/login
- [ ] **Status**: ___________

### 2. Test User Registration
- [ ] Click "Register" or visit http://127.0.0.1:5002/auth/register
- [ ] Fill in registration form:
  - Email: test@example.com
  - Password: Test123!@#
  - Confirm Password: Test123!@#
- [ ] Click "Register"
- [ ] **Expected**: User created, redirected to login page
- [ ] **Status**: ___________

### 3. Test User Login
- [ ] Visit http://127.0.0.1:5002/auth/login
- [ ] Enter credentials:
  - Email: test@example.com
  - Password: Test123!@#
- [ ] Click "Login"
- [ ] **Expected**: Redirected to main converter page
- [ ] **Status**: ___________

### 4. Test Main Converter Page (Authenticated)
- [ ] After login, should see:
  - User email in top-right corner
  - "Logout" button
  - Bank selection cards (BKT, OTP, Raiffeisen, etc.)
- [ ] **Status**: ___________

### 5. Test File Conversion
- [ ] Select a bank (e.g., BKT)
- [ ] Upload a test bank statement file
- [ ] Click "Convert Statement"
- [ ] **Expected**: Conversion succeeds, download button appears
- [ ] **Status**: ___________

### 6. Test Logout
- [ ] Click "Logout" button in top-right
- [ ] **Expected**: Redirected to login page
- [ ] Try to access http://127.0.0.1:5002 directly
- [ ] **Expected**: Redirected back to login
- [ ] **Status**: ___________

### 7. Test Session Persistence
- [ ] Login with "Remember Me" checked
- [ ] Close browser
- [ ] Reopen browser and visit http://127.0.0.1:5002
- [ ] **Expected**: Still logged in
- [ ] **Status**: ___________

### 8. Test Invalid Credentials
- [ ] Try to login with wrong password
- [ ] **Expected**: Error message displayed
- [ ] **Status**: ___________

### 9. Test Duplicate Registration
- [ ] Try to register with same email again
- [ ] **Expected**: Error message "Email already registered"
- [ ] **Status**: ___________

### 10. Test File Ownership
- [ ] Login as user1, convert a file, note the job_id
- [ ] Logout, register and login as user2
- [ ] Try to access user1's download URL directly
- [ ] **Expected**: "Unauthorized access to file" message
- [ ] **Status**: ___________

## Files Created During Testing

### users.json
Location: `Bank_Specific_Converter/users.json`

Structure:
```json
[
  {
    "id": "uuid-here",
    "email": "test@example.com",
    "password": "hashed_password_here",
    "created_at": "2025-10-17T..."
  }
]
```

### Test Uploads
Location: `Bank_Specific_Converter/import/`
- Files are automatically cleaned up after 1 hour

### Test Conversions
Location: `Bank_Specific_Converter/export/`
- Files are automatically cleaned up after 1 hour

## Common Issues & Solutions

### Issue: Can't access /auth/login
**Solution**: Check that templates folder exists with login.html and register.html

### Issue: Import errors
**Solution**: Verify all auth modules are using Flask-Login versions:
```bash
ls -la auth*.py
# Should show:
# auth.py (UserManager class)
# auth_routes.py (Flask-Login blueprint)
```

### Issue: Password not hashing
**Solution**: Check that Flask-Bcrypt is installed:
```bash
pip list | grep -i bcrypt
# Should show Flask-Bcrypt==1.0.1
```

### Issue: Session not persisting
**Solution**: Check that SECRET_KEY is set in app config

## Browser Testing

Test in multiple browsers:
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (if available)

## Security Testing

- [ ] Test SQL injection attempts in email field
- [ ] Test XSS attempts in email field
- [ ] Test CSRF protection (try POST without form)
- [ ] Test session hijacking (copy session cookie to another browser)

## Performance Testing

- [ ] Test with large file upload (45MB+)
- [ ] Test multiple concurrent conversions
- [ ] Test with 10+ registered users
- [ ] Check memory usage during conversion

## Deployment Readiness Checklist

Before deploying to server, ensure:

### Code Quality
- [ ] No debug mode enabled in production
- [ ] No hardcoded passwords or secrets
- [ ] Error messages don't reveal system information
- [ ] All imports working correctly

### Security
- [ ] SECRET_KEY changed from default
- [ ] Password hashing working (bcrypt)
- [ ] Session timeout configured (1 hour)
- [ ] HTTPS enforced on production

### Database
- [ ] users.json file permissions set (600)
- [ ] Backup strategy for users.json
- [ ] Consider migration to SQLite for production

### Files
- [ ] auth.py (Flask-Login version)
- [ ] auth_routes.py (Flask-Login version)
- [ ] app.py (authenticated version)
- [ ] templates/login.html
- [ ] templates/register.html
- [ ] users.json (empty [])

### Dependencies
- [ ] Flask-Login installed on server
- [ ] Flask-Bcrypt installed on server
- [ ] requirements.txt updated

## Deployment Command (When Ready)

```bash
# 1. Stop current app on server
ssh converter@c.konsulence.al "pkill -f 'python app.py'"

# 2. Backup current app
ssh converter@c.konsulence.al "cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter && cp app.py app.backup.$(date +%Y%m%d_%H%M%S).py"

# 3. Deploy new files
cd "C:\Users\XheladinPalushi\OneDrive - KONSULENCE.AL\Desktop\pdfdemo"
git add Bank_Specific_Converter/app.py Bank_Specific_Converter/auth.py Bank_Specific_Converter/auth_routes.py
git commit -m "Deploy tested authenticated app"
git push origin main

# 4. Update server
ssh converter@c.konsulence.al "cd ~/web/c.konsulence.al/public_html && git pull origin main"

# 5. Install dependencies
ssh converter@c.konsulence.al "cd ~/web/c.konsulence.al/public_html && source .venv/bin/activate && pip install flask-login flask-bcrypt"

# 6. Create users.json
ssh converter@c.konsulence.al "cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter && echo '[]' > users.json && chmod 600 users.json"

# 7. Start app
ssh converter@c.konsulence.al "cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter && source ../.venv/bin/activate && nohup python app.py > app.log 2>&1 &"

# 8. Verify
curl -I https://c.konsulence.al/auth/login
```

## Test Results

### Date: _____________
### Tester: _____________

**Overall Status**: ⬜ PASS ⬜ FAIL ⬜ NEEDS WORK

**Notes**:
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

**Ready for Production?**: ⬜ YES ⬜ NO

**Deployment Date**: _____________

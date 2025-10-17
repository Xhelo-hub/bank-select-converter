# Deploy Authenticated App to Server

## What This Does
Replaces the current `app.py` with the authenticated version (`app_authenticated.py`)

## Steps

### 1. Commit the New File to GitHub
```powershell
git add Bank_Specific_Converter/app_authenticated.py
git commit -m "Add authenticated app.py with Flask-Login integration"
git push origin main
```

### 2. Deploy to Server
```bash
# SSH to server
ssh converter@c.konsulence.al

# Navigate to app directory
cd ~/web/c.konsulence.al/public_html

# Pull latest code
git pull origin main

# Backup current app.py (if not already backed up)
cd Bank_Specific_Converter
cp app.py app.py.backup.manual

# Replace with authenticated version
cp app_authenticated.py app.py

# Create empty users database (if doesn't exist)
if [ ! -f users.json ]; then
    echo '[]' > users.json
    chmod 600 users.json
fi

# Restart the app
pkill -f "python app.py"
nohup python app.py > app.log 2>&1 &

# Check if it's running
sleep 2
ps aux | grep "python app.py" | grep -v grep

# Watch the logs
tail -f app.log
```

### 3. Register First User
Visit: https://c.konsulence.al/auth/register

Create an admin account:
- Email: your-email@example.com
- Password: (strong password)

### 4. Test Login
Visit: https://c.konsulence.al/auth/login

Log in with your credentials.

### 5. Test Converter
After logging in, you should be redirected to the main converter page.
Test a conversion to ensure everything works.

## Key Changes in Authenticated Version

### Added Dependencies
- `flask-login`: Session management
- `flask-bcrypt`: Password hashing

### New Routes
- `/auth/register` - User registration
- `/auth/login` - User login
- `/auth/logout` - User logout

### Protected Routes
All converter routes now require authentication:
- `/` (main page)
- `/convert` (file conversion)
- `/download/<job_id>` (file download)
- `/status/<job_id>` (status check)

### Security Features
- Password hashing with bcrypt
- Session-based authentication
- "Remember me" functionality
- CSRF protection (Flask built-in)
- File ownership verification (users can only download their own conversions)

### User Database
Uses JSON file (`users.json`) with structure:
```json
[
    {
        "id": "uuid",
        "email": "user@example.com",
        "password": "hashed_password",
        "created_at": "2025-01-17T15:30:00"
    }
]
```

## Rollback Plan
If something goes wrong:

```bash
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter

# Stop the app
pkill -f "python app.py"

# Restore original
cp app.py.backup.manual app.py

# Restart
nohup python app.py > app.log 2>&1 &
```

## Troubleshooting

### App won't start
```bash
# Check logs
tail -100 app.log

# Check if users.json exists and is readable
ls -la users.json
cat users.json
```

### Can't register/login
```bash
# Verify auth files are present
ls -la auth.py auth_routes.py

# Check templates exist
ls -la templates/login.html templates/register.html
```

### Import errors
```bash
# Verify dependencies installed
source ../.venv/bin/activate
pip list | grep -i flask

# Should show:
# Flask==2.3.3
# Flask-Bcrypt==1.0.1
# Flask-Login==0.6.3
```

## Next Steps After Deployment

1. **Create Admin User**: Register first user immediately
2. **Test Full Workflow**: Upload → Convert → Download
3. **Monitor Logs**: Watch `app.log` for any errors
4. **Setup Backup**: Consider backing up `users.json` regularly
5. **Add More Users**: Share registration link with team members

## File Ownership Security

The authenticated version includes file ownership tracking:
- Each conversion is associated with the user who created it
- Users can only download their own conversions
- Job IDs are still random UUIDs for security

## Session Security

- Sessions expire after 1 hour (configurable in `config.py`)
- "Remember me" extends session to 30 days
- Secret key should be changed in production (set in `config.py` or environment variable)

## Production Hardening Recommendations

1. **Change Secret Key**: Set unique `SECRET_KEY` in environment
2. **Use HTTPS**: Already configured (c.konsulence.al has SSL)
3. **Rate Limiting**: Consider adding Flask-Limiter for login attempts
4. **Email Verification**: Add email confirmation for new registrations
5. **Password Requirements**: Enforce strong passwords (currently basic validation)
6. **Audit Logging**: Log all login attempts and conversions
7. **Database Migration**: Consider moving from JSON to SQLite/PostgreSQL for better concurrency

## Quick Health Check
```bash
# From local machine
curl -I https://c.konsulence.al/server-status

# Should return:
# HTTP/1.1 200 OK
# {"status":"running",...}
```

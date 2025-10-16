# 🏦 Bank Statement Converter - HestiaCP Quick Setup
==================================================

## 📋 Files Created for Production Deployment:

### Core Application Files:
- `app.py` - Updated with production configuration
- `wsgi.py` - WSGI entry point for web server
- `config.py` - Production configuration settings
- `requirements.txt` - Updated Python dependencies

### Server Configuration:
- `gunicorn.conf.py` - Gunicorn server configuration
- `deploy.sh` - Automated deployment script
- `start.sh` - Production startup script
- `stop.sh` - Application stop script
- `restart.sh` - Application restart script

### Documentation:
- `HESTIA_DEPLOYMENT.md` - Complete deployment guide

## 🚀 Quick Start (3 Options):

### Option 1: HestiaCP Python App (Recommended)
1. Upload all files to your domain's public_html
2. In HestiaCP: Web > Add Python App
3. Set entry point to `wsgi.py`
4. Upload your converter scripts to the same directory

### Option 2: Manual Gunicorn Setup
```bash
# Upload files to server
scp -r Bank_Specific_Converter/ user@server:/home/user/web/domain.com/public_html/

# SSH to server and setup
ssh user@server
cd /home/user/web/domain.com/public_html/Bank_Specific_Converter
chmod +x *.sh
./start.sh
```

### Option 3: Automated Deployment
```bash
# Edit deploy.sh with your details first
vim deploy.sh

# Run deployment
sudo ./deploy.sh
```

## 📁 Required File Structure on Server:
```
/home/[user]/web/[domain]/public_html/
├── bank_converter/          # Main app directory
│   ├── app.py
│   ├── wsgi.py
│   ├── config.py
│   ├── requirements.txt
│   ├── uploads/             # Auto-created
│   └── converted/           # Auto-created
└── converter_scripts/       # Bank converter scripts
    ├── BKT-2-QBO.py
    ├── RAI-2-QBO.py
    ├── OTP-2-QBO.py
    ├── TIBANK-2-QBO.py
    ├── UNION-2-QBO.py
    └── Withholding.py
```

## 🔧 Configuration Notes:

### 1. Update Domain Settings:
Edit these files with your actual domain:
- `deploy.sh` (DOMAIN and USER variables)
- `gunicorn.conf.py` (user/group settings)
- `start.sh` (APP_DIR path)

### 2. Security Settings:
- Change SECRET_KEY in `config.py`
- Set proper file permissions (755 for scripts, 644 for Python files)
- Configure SSL certificate in HestiaCP

### 3. Bank Converter Scripts:
- Upload your existing converter scripts to the server
- Ensure they're in the correct location (same directory or parent directory)
- Test individual scripts work on the server

## 🔍 Testing & Monitoring:

### Test the Application:
1. Access your domain in browser
2. Select a bank and upload a test file
3. Verify conversion and download works

### Monitor Logs:
```bash
# Application logs
tail -f /var/log/gunicorn/bank_converter_error.log

# Check if running
ps aux | grep gunicorn

# Restart if needed
./restart.sh
```

## 🆘 Common Issues:

### Script Not Found Errors:
- Check converter scripts are uploaded
- Verify file permissions
- Test script paths manually

### Permission Denied:
```bash
chown -R [user]:[user] /home/[user]/web/[domain]/public_html/
chmod 755 /home/[user]/web/[domain]/public_html/bank_converter
```

### Port Issues:
- Ensure port 8000 is not used by other apps
- Check HestiaCP doesn't have conflicting configurations

---

## 📞 Need Help?

1. Check the full deployment guide: `HESTIA_DEPLOYMENT.md`
2. Test individual converter scripts first
3. Verify all dependencies are installed
4. Check server logs for specific errors

**Ready to deploy your Bank Statement Converter! 🚀**
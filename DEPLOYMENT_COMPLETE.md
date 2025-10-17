# ✅ Deployment Complete - Bank Statement Converter

## Deployment Summary

**Date:** October 17, 2025  
**Server:** converter@c.konsulence.al  
**Directory:** `/home/converter/web/c.konsulence.al/public_html`  
**Status:** ✅ Successfully Deployed

---

## What Was Installed

### 1. Repository Setup
- ✅ Cloned GitHub repository: `https://github.com/Xhelo-hub/bank-select-converter.git`
- ✅ All files copied to `/home/converter/web/c.konsulence.al/public_html`
- ✅ Git repository initialized for future updates

### 2. Python Environment
- ✅ Python 3.12.3 (already installed on server)
- ✅ Virtual environment created at `.venv/`
- ✅ Pip upgraded to version 25.2

### 3. Dependencies Installed
**Root dependencies:**
- Flask 2.3.3
- Werkzeug 2.3.7
- PyPDF2 3.0.1
- requests 2.31.0
- python-dotenv 1.0.0

**Bank_Specific_Converter dependencies:**
- Gunicorn 21.2.0 (production WSGI server)
- All Flask components (Jinja2, MarkupSafe, etc.)

### 4. Directory Structure
```
/home/converter/web/c.konsulence.al/public_html/
├── import/                  # Input files for converters
├── export/                  # Converted output files
├── converted/               # Processed files archive
├── uploads/                 # Web interface uploads
├── Bank_Specific_Converter/
│   ├── app.py              # Main Flask application
│   ├── wsgi.py             # WSGI entry point
│   ├── config.py           # Configuration
│   ├── import/             # Web app input folder
│   ├── export/             # Web app output folder
│   ├── converted/          # Web app archive
│   └── start_server.sh     # Quick start script
├── .venv/                   # Python virtual environment
├── BKT-2-QBO.py            # Individual bank converters
├── RAI-2-QBO.py
├── OTP-2-QBO.py
├── UNION-2-QBO.py
├── TIBANK-2-QBO.py
└── Withholding.py
```

---

## How to Start the Application

### Method 1: Quick Start (Development Mode)
```bash
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
./start_server.sh
```

This will start the Flask development server on port 5002.

### Method 2: Manual Start
```bash
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
source ../.venv/bin/activate
python app.py
```

### Method 3: Production with Gunicorn
```bash
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter
source ../.venv/bin/activate
gunicorn --bind 0.0.0.0:5002 wsgi:application
```

---

## Testing the Application

1. **Start the server** using one of the methods above
2. **Access the web interface:**
   - Local: `http://127.0.0.1:5002`
   - Public: `http://c.konsulence.al:5002` (if firewall allows)

3. **Upload a test file:**
   - Select a bank (BKT, Raiffeisen, OTP, Union, TiBank, or Ebill)
   - Upload a PDF or CSV statement
   - Download the converted QuickBooks CSV file

---

## Future Deployments (Updates)

When you make changes locally and want to deploy:

```bash
# On your local machine (Windows PowerShell)
cd "C:\Users\XheladinPalushi\OneDrive - KONSULENCE.AL\Desktop\pdfdemo"
git add .
git commit -m "Your commit message"
git push origin main

# On the server
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html
git pull origin main
# Restart the server (Ctrl+C and restart, or use systemd service)
```

---

## Next Steps (Optional Production Setup)

### 1. Set up Nginx Reverse Proxy
Configure HestiaCP to proxy requests from port 80/443 to port 5002

### 2. Create Systemd Service
For automatic startup and background running:
```bash
sudo nano /etc/systemd/system/bank-converter.service
```

Use the configuration from `deploy_to_hestia.sh`

### 3. Enable HTTPS
Configure SSL certificate through HestiaCP or Let's Encrypt

### 4. Set up Monitoring
- Check logs: `tail -f ~/web/c.konsulence.al/logs/gunicorn-*.log`
- Monitor service: `systemctl status bank-converter`

---

## Troubleshooting

### Application won't start
```bash
# Check Python path
which python3

# Verify virtual environment
source .venv/bin/activate
python --version

# Test import
python -c "from app import app; print('OK')"
```

### Port already in use
```bash
# Find process using port 5002
sudo lsof -i :5002
# Kill if needed
sudo kill -9 <PID>
```

### Permission errors
```bash
# Ensure correct ownership
sudo chown -R converter:www-data ~/web/c.konsulence.al/public_html
chmod -R 755 import export converted uploads
```

---

## Support & Documentation

- **GitHub:** https://github.com/Xhelo-hub/bank-select-converter
- **README:** `/home/converter/web/c.konsulence.al/public_html/README.md`
- **Individual Converter Docs:** `/home/converter/web/c.konsulence.al/public_html/Readme/`

---

## Summary

✅ All code deployed to server  
✅ Python and dependencies installed  
✅ Virtual environment configured  
✅ Directories created  
✅ Application tested and working  
✅ Start scripts created  

**The application is ready to use!**

Simply SSH into the server and run `./start_server.sh` from the `Bank_Specific_Converter` directory.

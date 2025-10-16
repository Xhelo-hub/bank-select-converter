# Bank Statement Converter - HestiaCP Deployment Guide
=====================================================

## Overview
This guide helps you deploy the Bank Statement Converter on a HestiaCP server.

## Prerequisites
- HestiaCP server with Python 3.8+
- Domain name configured in HestiaCP
- SSH access to your server
- Basic Linux command line knowledge

## Step 1: Prepare Your Files

### 1.1 Upload Files to Server
Upload these files to your server in `/home/[username]/web/[domain]/public_html/`:

```
bank_converter/
├── app.py                 # Main Flask application
├── wsgi.py               # WSGI entry point
├── config.py             # Production configuration
├── gunicorn.conf.py      # Gunicorn settings
├── requirements.txt      # Python dependencies
├── deploy.sh            # Deployment script
└── converter_scripts/   # Bank converter scripts
    ├── BKT-2-QBO.py
    ├── RAI-2-QBO.py
    ├── OTP-2-QBO.py
    ├── TIBANK-2-QBO.py
    ├── UNION-2-QBO.py
    └── Withholding.py
```

### 1.2 Set Permissions
```bash
chmod +x deploy.sh
chmod 644 *.py
chmod 644 requirements.txt
```

## Step 2: Configuration

### 2.1 Update Configuration
Edit `deploy.sh` and update these variables:
```bash
DOMAIN="yourdomain.com"     # Your actual domain
USER="your_username"        # Your HestiaCP username
```

### 2.2 Update App Paths
In `app.py`, ensure the script paths are correct for your server structure.

## Step 3: HestiaCP Setup

### 3.1 Create Web Domain
1. Log into HestiaCP
2. Go to **Web** section
3. Click **Add Web Domain**
4. Enter your domain name
5. Enable SSL if needed

### 3.2 Python Environment Setup
SSH into your server and run:

```bash
cd /home/[username]/web/[domain]/public_html/bank_converter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 4: Deployment Options

### Option A: Simple Python Server (Development)
For testing purposes only:
```bash
cd /home/[username]/web/[domain]/public_html/bank_converter
source venv/bin/activate
python app.py
```

### Option B: Gunicorn + Nginx (Production)
1. Run the deployment script:
```bash
sudo ./deploy.sh
```

2. Or manually configure:
```bash
# Install Gunicorn
pip install gunicorn

# Start with Gunicorn
gunicorn --config gunicorn.conf.py wsgi:application
```

### Option C: HestiaCP Python App (Recommended)
1. In HestiaCP, go to **Web** > **[Your Domain]**
2. Click **Add Python App**
3. Set:
   - **Name**: bank_converter
   - **Directory**: bank_converter
   - **Entry Point**: wsgi.py
   - **Python Version**: 3.8+ (latest available)

## Step 5: Nginx Configuration

### 5.1 Custom Nginx Template
Create `/usr/local/hestia/data/templates/web/nginx/php-fpm/[domain].tpl`:

```nginx
server {
    listen      %ip%:%web_port%;
    server_name %domain_idn% %alias_idn%;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_request_buffering off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
    
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 5.2 Apply Configuration
```bash
# Rebuild web configuration
v-rebuild-web-domain [username] [domain]

# Restart services
systemctl reload nginx
```

## Step 6: File Permissions & Security

### 6.1 Set Correct Permissions
```bash
# Application files
chown -R [username]:[username] /home/[username]/web/[domain]/public_html/bank_converter
chmod 755 /home/[username]/web/[domain]/public_html/bank_converter
chmod 644 /home/[username]/web/[domain]/public_html/bank_converter/*.py

# Upload directories
chmod 777 /home/[username]/web/[domain]/public_html/bank_converter/uploads
chmod 777 /home/[username]/web/[domain]/public_html/bank_converter/converted
```

### 6.2 Security Considerations
- Change the SECRET_KEY in `config.py`
- Set up SSL certificate
- Configure firewall rules
- Regular security updates

## Step 7: Monitoring & Maintenance

### 7.1 Check Application Status
```bash
# Check if app is running
ps aux | grep gunicorn

# Check logs
tail -f /var/log/gunicorn/bank_converter_error.log
```

### 7.2 Restart Application
```bash
# If using systemd service
systemctl restart bank-converter

# If running manually
pkill -f gunicorn
cd /home/[username]/web/[domain]/public_html/bank_converter
source venv/bin/activate
gunicorn --config gunicorn.conf.py wsgi:application &
```

## Troubleshooting

### Common Issues:

1. **Permission Denied**
   ```bash
   chown -R [username]:[username] /home/[username]/web/[domain]/public_html/bank_converter
   ```

2. **Module Not Found**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Port Already in Use**
   ```bash
   netstat -tulpn | grep 8000
   pkill -f gunicorn
   ```

4. **Nginx 502 Error**
   - Check if Gunicorn is running
   - Verify proxy_pass URL in Nginx config
   - Check error logs

## Testing

1. Access your domain: `https://yourdomain.com`
2. Try uploading a test CSV file
3. Verify conversion works
4. Check download functionality

## Support

If you encounter issues:
1. Check application logs
2. Verify file permissions
3. Ensure all dependencies are installed
4. Test individual converter scripts manually

---

**Note**: Replace `[username]` and `[domain]` with your actual HestiaCP username and domain name throughout this guide.
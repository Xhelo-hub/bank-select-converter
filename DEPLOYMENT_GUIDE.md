# 🚀 Hetzner + HestiaCP + Cloudflare Deployment Guide

## **Prerequisites Checklist**

- [x] Hetzner server with HestiaCP installed
- [x] Domain registered and managed on Cloudflare  
- [x] SSH access to your Hetzner server
- [x] HestiaCP admin credentials
- [x] Bank Select Converter repository on GitHub

---

## **Phase 1: Cloudflare DNS Setup**

### **Step 1: Configure DNS A Record**

1. **Login to Cloudflare Dashboard**: https://dash.cloudflare.com
2. **Select your domain**
3. **Navigate to**: DNS → Records
4. **Click**: "Add record"
4. **Configure**:
   ```
   Type: A
   Name: converter (creates converter.yourdomain.com)
   IPv4 address: 78.46.201.151
   Proxy status: 🟠 Proxied (recommended for DDoS protection)
   TTL: Auto
   ```
6. **Save the record**

### **Step 2: SSL/TLS Configuration**

1. **Go to**: SSL/TLS → Overview
2. **Set encryption mode**: `Full (strict)` 
3. **Navigate to**: SSL/TLS → Edge Certificates
4. **Enable**:
   - ✅ Always Use HTTPS
   - ✅ HTTP Strict Transport Security (HSTS)

---

## **Phase 2: Server Preparation**

### **Step 3: Connect to Your Hetzner Server**

```bash
# SSH into your server
ssh root@YOUR_SERVER_IP
```

### **Step 4: Update System & Install Dependencies**

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv git nginx curl htop
```

---

## **Phase 3: HestiaCP Domain Setup**

### **Step 5: Add Domain via HestiaCP**

**Option A: Via Web Interface**
1. Login to HestiaCP: `https://YOUR_SERVER_IP:8083`
2. Go to **Web** → **Add Web Domain**
3. **Domain**: `converter.yourdomain.com`
4. **IP**: Your server IP
5. **Template**: default
6. **Click**: Add

**Option B: Via Command Line**
```bash
# Add web domain
v-add-web-domain admin converter.yourdomain.com

# Enable SSL (Let's Encrypt)
v-add-letsencrypt-domain admin converter.yourdomain.com
```

---

## **Phase 4: Application Deployment**

### **Step 6: Clone Repository**

```bash
# Navigate to user home directory
cd /home/admin

# Clone the repository
git clone https://github.com/Xhelo-hub/bank-select-converter.git

# Set correct permissions
chown -R admin:admin bank-select-converter
```

### **Step 7: Setup Python Environment**

```bash
# Navigate to app directory
cd /home/admin/bank-select-converter/Bank_Specific_Converter

# Create virtual environment
sudo -u admin python3 -m venv venv

# Activate environment and install dependencies
sudo -u admin ./venv/bin/pip install --upgrade pip
sudo -u admin ./venv/bin/pip install flask gunicorn pandas openpyxl
```

### **Step 8: Prepare Application Structure**

```bash
# Create necessary directories
mkdir -p /home/admin/web/converter.yourdomain.com/public_html
mkdir -p /home/admin/bank-select-converter/Bank_Specific_Converter/{import,export,logs}

# Copy application files
cp -r /home/admin/bank-select-converter/* /home/admin/web/converter.yourdomain.com/public_html/

# Set permissions
chown -R admin:admin /home/admin/web/converter.yourdomain.com/public_html
chmod 755 /home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter
chmod 777 /home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter/{import,export}
```

---

## **Phase 5: Service Configuration**

### **Step 9: Create Systemd Service**

```bash
# Create service file
cat > /etc/systemd/system/bank-converter.service << 'EOF'
[Unit]
Description=Bank Select Converter Flask App
After=network.target

[Service]
User=admin
Group=admin
WorkingDirectory=/home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter
Environment=PATH=/home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter/venv/bin
Environment=FLASK_ENV=production
ExecStart=/home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 300 wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

### **Step 10: Configure Nginx (Replace HestiaCP Default)**

```bash
# Backup original config
cp /home/admin/conf/web/converter.yourdomain.com/nginx.conf /home/admin/conf/web/converter.yourdomain.com/nginx.conf.backup

# Create new Nginx configuration
cat > /home/admin/conf/web/converter.yourdomain.com/nginx.conf << 'EOF'
server {
    listen      80;
    server_name converter.yourdomain.com www.converter.yourdomain.com;
    return      301 https://$server_name$request_uri;
}

server {
    listen      443 ssl http2;
    server_name converter.yourdomain.com www.converter.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate     /home/admin/conf/web/converter.yourdomain.com/ssl/converter.yourdomain.com.pem;
    ssl_certificate_key /home/admin/conf/web/converter.yourdomain.com/ssl/converter.yourdomain.com.key;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # File Upload Limits
    client_max_body_size 20M;
    
    # Application Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_request_buffering off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:8000/server-status;
        access_log off;
    }
    
    # Error and Access logs
    access_log  /var/log/nginx/domains/converter.yourdomain.com.log combined;
    error_log   /var/log/nginx/domains/converter.yourdomain.com.error.log error;
}
EOF
```

---

## **Phase 6: Start Services**

### **Step 11: Enable and Start Services**

```bash
# Reload systemd
systemctl daemon-reload

# Enable and start the application service
systemctl enable bank-converter
systemctl start bank-converter

# Reload Nginx to apply new configuration
systemctl reload nginx

# Check service status
systemctl status bank-converter
systemctl status nginx
```

---

## **Phase 7: Verification & Testing**

### **Step 12: Verify Deployment**

```bash
# Check if services are running
systemctl is-active bank-converter
systemctl is-active nginx

# Test local connection
curl -I http://127.0.0.1:8000/server-status

# Check application logs
journalctl -u bank-converter -f --no-pager -n 20
```

### **Step 13: DNS Propagation Check**

```bash
# Check DNS resolution
nslookup converter.yourdomain.com
dig converter.yourdomain.com

# Test HTTPS connection
curl -I https://converter.yourdomain.com
```

---

## **Phase 8: Monitoring & Maintenance**

### **Step 14: Setup Log Rotation**

```bash
# Create log rotation config
cat > /etc/logrotate.d/bank-converter << 'EOF'
/home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl reload bank-converter
    endscript
}
EOF
```

### **Step 15: Create Management Scripts**

```bash
# Status check script
cat > /home/admin/check_status.sh << 'EOF'
#!/bin/bash
echo "🏦 Bank Select Converter - Status Check"
echo "======================================"
echo "Service Status: $(systemctl is-active bank-converter)"
echo "Nginx Status: $(systemctl is-active nginx)"
echo "Disk Usage: $(df -h /home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter | tail -1 | awk '{print $5}')"
echo ""
echo "Recent Logs:"
journalctl -u bank-converter -n 10 --no-pager
EOF

chmod +x /home/admin/check_status.sh

# Restart script
cat > /home/admin/restart_app.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting Bank Select Converter..."
systemctl restart bank-converter
systemctl reload nginx
echo "✅ Services restarted"
systemctl status bank-converter --no-pager -l
EOF

chmod +x /home/admin/restart_app.sh
```

---

## **🎉 Deployment Complete!**

### **Final Verification**

1. **Visit**: `https://converter.yourdomain.com`
2. **Test**: Upload a bank statement file
3. **Verify**: File conversion and auto-deletion works
4. **Monitor**: Check logs for any issues

### **Quick Management Commands**

```bash
# Check status
/home/admin/check_status.sh

# Restart application
/home/admin/restart_app.sh

# View real-time logs
journalctl -u bank-converter -f

# Check Cloudflare connection
curl -I -H "CF-Connecting-IP: test" https://converter.yourdomain.com
```

### **Troubleshooting**

If something goes wrong:

1. **Check service logs**: `journalctl -u bank-converter -n 50`
2. **Check Nginx logs**: `tail -f /var/log/nginx/domains/converter.yourdomain.com.error.log`
3. **Verify permissions**: `ls -la /home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter/`
4. **Test locally**: `curl http://127.0.0.1:8000`

---

## **🔒 Security Recommendations**

1. **Firewall**: Only allow ports 22, 80, 443, 8083
2. **Regular Updates**: `apt update && apt upgrade` monthly
3. **Backup**: Setup automated backups via HestiaCP
4. **Monitoring**: Consider adding Cloudflare Analytics
5. **Rate Limiting**: Configure Cloudflare rate limiting rules

Your Bank Select Converter is now live and secure! 🚀
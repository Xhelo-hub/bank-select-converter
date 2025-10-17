# 🚀 Deploy from GitHub to converter.konsulence.al

## **Prerequisites**
- ✅ GitHub repository: `https://github.com/Xhelo-hub/bank-select-converter`
- ✅ Server: `78.46.201.151` 
- ✅ Domain: `converter.konsulence.al`
- ✅ HestiaCP access: `http://78.46.201.151:8083`

---

## **Method 1: SSH Deployment (Recommended)**

### **Step 1: Connect to Server**
```bash
# If you have SSH key setup
ssh root@78.46.201.151

# If using password (enter when prompted)
ssh root@78.46.201.151
```

### **Step 2: Run Auto-Deploy Script**
```bash
# Download and run the deployment script
wget https://raw.githubusercontent.com/Xhelo-hub/bank-select-converter/main/deploy_to_server.sh
chmod +x deploy_to_server.sh
./deploy_to_server.sh
```

**OR Manual Commands:**

### **Step 3: Manual Deployment**
```bash
# Update system
apt update && apt install -y python3 python3-pip python3-venv git nginx

# Add domain to HestiaCP
v-add-web-domain admin converter.konsulence.al
v-add-letsencrypt-domain admin converter.konsulence.al

# Clone repository
cd /tmp
git clone https://github.com/Xhelo-hub/bank-select-converter.git

# Deploy files
WEB_DIR="/home/admin/web/converter.konsulence.al/public_html"
mkdir -p $WEB_DIR
cp -r /tmp/bank-select-converter/* $WEB_DIR/
chown -R admin:admin $WEB_DIR

# Setup Python environment
cd $WEB_DIR/Bank_Specific_Converter
sudo -u admin python3 -m venv venv
sudo -u admin ./venv/bin/pip install flask gunicorn pandas openpyxl

# Create directories
mkdir -p $WEB_DIR/Bank_Specific_Converter/{import,export,logs}
chmod 777 $WEB_DIR/Bank_Specific_Converter/{import,export}

# Create systemd service
cat > /etc/systemd/system/bank-converter.service << 'EOF'
[Unit]
Description=Bank Select Converter Flask App
After=network.target

[Service]
User=admin
Group=admin
WorkingDirectory=/home/admin/web/converter.konsulence.al/public_html/Bank_Specific_Converter
Environment=PATH=/home/admin/web/converter.konsulence.al/public_html/Bank_Specific_Converter/venv/bin
Environment=FLASK_ENV=production
ExecStart=/home/admin/web/converter.konsulence.al/public_html/Bank_Specific_Converter/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 300 wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Start services
systemctl daemon-reload
systemctl enable bank-converter
systemctl start bank-converter
systemctl reload nginx
```

---

## **Method 2: HestiaCP File Manager (Alternative)**

### **Step 1: Access HestiaCP**
1. Go to: `http://78.46.201.151:8083`
2. Login with admin credentials
3. Go to **Web** → **converter.konsulence.al** → **File Manager**

### **Step 2: Download Repository**
1. **Delete existing files** in public_html (if any)
2. **Download ZIP**: Go to GitHub → Code → Download ZIP
3. **Upload ZIP** via HestiaCP File Manager
4. **Extract** the ZIP file in public_html

### **Step 3: Setup via SSH**
```bash
ssh root@78.46.201.151
cd /home/admin/web/converter.konsulence.al/public_html/Bank_Specific_Converter
python3 -m venv venv
./venv/bin/pip install flask gunicorn pandas openpyxl
```

---

## **Method 3: Git Clone via HestiaCP Terminal**

### **Step 1: HestiaCP Web Terminal**
1. **Login to HestiaCP**: `http://78.46.201.151:8083`
2. **Go to**: Server → Terminal (if available)

### **Step 2: Run Commands**
```bash
# Navigate to web directory
cd /home/admin/web/converter.konsulence.al/public_html

# Clone repository
git clone https://github.com/Xhelo-hub/bank-select-converter.git .

# Setup Python
cd Bank_Specific_Converter
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

---

## **Cloudflare DNS Setup**

### **Configure A Record**
1. **Login to Cloudflare**: https://dash.cloudflare.com
2. **Select**: konsulence.al domain
3. **DNS → Records → Add record**:
   ```
   Type: A
   Name: converter
   IPv4: 78.46.201.151
   Proxy: 🟠 Proxied (Orange cloud)
   TTL: Auto
   ```

---

## **Verification Steps**

### **Check Deployment**
```bash
# Check service status
systemctl status bank-converter

# Test local connection
curl -I http://127.0.0.1:8000/server-status

# Check SSL
curl -I https://converter.konsulence.al
```

### **Expected Results**
- ✅ Service: `active (running)`
- ✅ Local test: `HTTP/1.1 200 OK`
- ✅ SSL test: `HTTP/2 200` with valid certificate
- ✅ Website: `https://converter.konsulence.al` loads correctly

---

## **Management Commands**

### **Update from GitHub**
```bash
# Update application
cd /tmp
git clone https://github.com/Xhelo-hub/bank-select-converter.git
cp -r bank-select-converter/* /home/admin/web/converter.konsulence.al/public_html/
systemctl restart bank-converter
```

### **Monitor Logs**
```bash
# Real-time logs
journalctl -u bank-converter -f

# Application status
systemctl status bank-converter nginx
```

### **Restart Services**
```bash
systemctl restart bank-converter
systemctl reload nginx
```

---

## **Troubleshooting**

| Issue | Solution |
|-------|----------|
| SSH connection refused | Check server firewall, try password auth |
| Permission denied | Use `chown -R admin:admin /home/admin/web/...` |
| 502 Bad Gateway | Restart service: `systemctl restart bank-converter` |
| SSL errors | Re-run: `v-add-letsencrypt-domain admin converter.konsulence.al` |
| Python errors | Check venv: `cd Bank_Specific_Converter && ./venv/bin/pip list` |

---

## **Success Indicators**

✅ **Deployment Complete When:**
- Service status shows `active (running)`
- `https://converter.konsulence.al` loads the bank converter interface
- File upload and conversion work correctly
- Files are auto-deleted after download
- SSL certificate shows green padlock

**🎉 Your bank converter will be live at: `https://converter.konsulence.al`**
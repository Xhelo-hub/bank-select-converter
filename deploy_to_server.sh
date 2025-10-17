#!/bin/bash
# Deploy Bank Select Converter from GitHub to converter.konsulence.al
# ================================================================

echo "🚀 Deploying Bank Select Converter to converter.konsulence.al"
echo "============================================================"

# Server Configuration
SERVER_IP="78.46.201.151"
DOMAIN="converter.konsulence.al"
REPO_URL="https://github.com/Xhelo-hub/bank-select-converter.git"
USER="admin"
WEB_DIR="/home/$USER/web/$DOMAIN/public_html"

# Step 1: Update system and install dependencies
echo "📦 Step 1: Installing dependencies..."
apt update
apt install -y python3 python3-pip python3-venv git nginx curl

# Step 2: Create domain in HestiaCP (if not exists)
echo "🌐 Step 2: Setting up domain in HestiaCP..."
v-add-web-domain $USER $DOMAIN 2>/dev/null || echo "Domain already exists"

# Step 3: Enable SSL
echo "🔒 Step 3: Enabling SSL certificate..."
v-add-letsencrypt-domain $USER $DOMAIN

# Step 4: Clone repository
echo "📥 Step 4: Cloning repository from GitHub..."
cd /tmp
rm -rf bank-select-converter
git clone $REPO_URL
cd bank-select-converter

# Step 5: Deploy to web directory
echo "📁 Step 5: Deploying files to web directory..."
# Backup existing files if any
if [ -d "$WEB_DIR" ]; then
    cp -r $WEB_DIR ${WEB_DIR}_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null
fi

# Create web directory
mkdir -p $WEB_DIR
rm -rf $WEB_DIR/* # Clear existing files

# Copy application files
cp -r /tmp/bank-select-converter/* $WEB_DIR/
chown -R $USER:$USER $WEB_DIR

# Step 6: Setup Python environment
echo "🐍 Step 6: Setting up Python environment..."
cd $WEB_DIR/Bank_Specific_Converter
sudo -u $USER python3 -m venv venv
sudo -u $USER ./venv/bin/pip install --upgrade pip
sudo -u $USER ./venv/bin/pip install flask gunicorn pandas openpyxl

# Step 7: Create necessary directories
echo "📂 Step 7: Creating application directories..."
mkdir -p $WEB_DIR/Bank_Specific_Converter/{import,export,logs}
chmod 755 $WEB_DIR/Bank_Specific_Converter
chmod 777 $WEB_DIR/Bank_Specific_Converter/{import,export}
chmod 755 $WEB_DIR/Bank_Specific_Converter/logs

# Step 8: Create systemd service
echo "⚙️ Step 8: Creating systemd service..."
cat > /etc/systemd/system/bank-converter.service << EOF
[Unit]
Description=Bank Select Converter Flask App
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$WEB_DIR/Bank_Specific_Converter
Environment=PATH=$WEB_DIR/Bank_Specific_Converter/venv/bin
Environment=FLASK_ENV=production
ExecStart=$WEB_DIR/Bank_Specific_Converter/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 300 wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Step 9: Configure Nginx
echo "🌐 Step 9: Configuring Nginx for $DOMAIN..."
cat > /home/$USER/conf/web/$DOMAIN/nginx.conf << EOF
server {
    listen      80;
    server_name $DOMAIN www.$DOMAIN;
    return      301 https://\$server_name\$request_uri;
}

server {
    listen      443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL Configuration
    ssl_certificate     /home/$USER/conf/web/$DOMAIN/ssl/$DOMAIN.pem;
    ssl_certificate_key /home/$USER/conf/web/$DOMAIN/ssl/$DOMAIN.key;
    
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
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
    
    # Static files
    location /static {
        alias $WEB_DIR/Bank_Specific_Converter/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Error and Access logs
    access_log  /var/log/nginx/domains/$DOMAIN.log combined;
    error_log   /var/log/nginx/domains/$DOMAIN.error.log error;
}
EOF

# Step 10: Start services
echo "🔄 Step 10: Starting services..."
systemctl daemon-reload
systemctl enable bank-converter
systemctl start bank-converter
systemctl reload nginx

# Step 11: Create management scripts
echo "🛠️ Step 11: Creating management scripts..."
cat > $WEB_DIR/status.sh << 'EOF'
#!/bin/bash
echo "🏦 Bank Select Converter Status for converter.konsulence.al"
echo "========================================================="
echo "Service Status: $(systemctl is-active bank-converter)"
echo "Nginx Status: $(systemctl is-active nginx)"
echo "Domain SSL: $(curl -s -I https://converter.konsulence.al | head -1)"
echo ""
echo "Recent Application Logs:"
journalctl -u bank-converter -n 10 --no-pager
EOF

chmod +x $WEB_DIR/status.sh

cat > $WEB_DIR/update_from_github.sh << EOF
#!/bin/bash
echo "🔄 Updating Bank Select Converter from GitHub..."
cd /tmp
rm -rf bank-select-converter
git clone $REPO_URL
cd bank-select-converter

# Backup current
cp -r $WEB_DIR ${WEB_DIR}_backup_\$(date +%Y%m%d_%H%M%S)

# Update files (preserve venv)
rsync -av --exclude='venv' --exclude='import' --exclude='export' /tmp/bank-select-converter/ $WEB_DIR/
chown -R $USER:$USER $WEB_DIR

# Restart service
systemctl restart bank-converter
echo "✅ Update completed!"
EOF

chmod +x $WEB_DIR/update_from_github.sh

# Final verification
echo ""
echo "✅ Deployment Summary:"
echo "====================="
echo "Domain: https://$DOMAIN"
echo "Repository: $REPO_URL"
echo "Web Directory: $WEB_DIR"
echo ""
echo "Service Status:"
systemctl is-active bank-converter
echo "SSL Status:"
openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | grep "Verification:"

echo ""
echo "🎉 Deployment completed!"
echo "🌐 Your app should be available at: https://$DOMAIN"
echo "📊 Check status: $WEB_DIR/status.sh"
echo "🔄 Update from GitHub: $WEB_DIR/update_from_github.sh"
echo "📋 View logs: journalctl -u bank-converter -f"

# Cleanup
rm -rf /tmp/bank-select-converter
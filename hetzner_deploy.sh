#!/bin/bash
# Hetzner + HestiaCP Deployment Script for Bank Select Converter
# =============================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Bank Select Converter - Hetzner Deployment${NC}"
echo "============================================================"

# Configuration - CHANGE THESE VALUES
DOMAIN="converter.yourdomain.com"        # Replace with your actual subdomain
USER="admin"                            # Your HestiaCP username
HESTIA_PASSWORD="your_hestia_password"  # Your HestiaCP password
APP_DIR="/home/$USER/web/$DOMAIN/public_html"
REPO_URL="https://github.com/Xhelo-hub/bank-select-converter.git"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "Domain: $DOMAIN"
echo "User: $USER"
echo "App Directory: $APP_DIR"
echo "Repository: $REPO_URL"
echo ""

# Step 1: Create web domain in HestiaCP
echo -e "${YELLOW}🌐 Step 1: Creating web domain in HestiaCP...${NC}"
v-add-web-domain $USER $DOMAIN

# Step 2: Enable SSL for the domain
echo -e "${YELLOW}🔒 Step 2: Enabling SSL...${NC}"
v-add-letsencrypt-domain $USER $DOMAIN

# Step 3: Install required packages
echo -e "${YELLOW}📦 Step 3: Installing required packages...${NC}"
apt update
apt install -y python3 python3-pip python3-venv git nginx

# Step 4: Clone the repository
echo -e "${YELLOW}📥 Step 4: Cloning repository...${NC}"
cd /home/$USER
rm -rf bank-select-converter  # Remove if exists
git clone $REPO_URL
chown -R $USER:$USER bank-select-converter

# Step 5: Setup Python environment
echo -e "${YELLOW}🐍 Step 5: Setting up Python environment...${NC}"
cd /home/$USER/bank-select-converter/Bank_Specific_Converter
sudo -u $USER python3 -m venv venv
sudo -u $USER ./venv/bin/pip install --upgrade pip
sudo -u $USER ./venv/bin/pip install -r requirements.txt

# Step 6: Copy files to web directory
echo -e "${YELLOW}📁 Step 6: Copying files to web directory...${NC}"
mkdir -p $APP_DIR
cp -r /home/$USER/bank-select-converter/* $APP_DIR/
chown -R $USER:$USER $APP_DIR

# Step 7: Create directories
echo -e "${YELLOW}📂 Step 7: Creating application directories...${NC}"
mkdir -p $APP_DIR/Bank_Specific_Converter/{import,export,logs}
chmod 755 $APP_DIR/Bank_Specific_Converter
chmod 777 $APP_DIR/Bank_Specific_Converter/{import,export}
chmod 755 $APP_DIR/Bank_Specific_Converter/logs

# Step 8: Setup Gunicorn service
echo -e "${YELLOW}⚙️ Step 8: Setting up Gunicorn service...${NC}"
cat > /etc/systemd/system/bank-converter.service << EOF
[Unit]
Description=Bank Select Converter Flask App
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR/Bank_Specific_Converter
Environment=PATH=$APP_DIR/Bank_Specific_Converter/venv/bin
Environment=FLASK_ENV=production
ExecStart=$APP_DIR/Bank_Specific_Converter/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 300 wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Step 9: Configure Nginx
echo -e "${YELLOW}🌐 Step 9: Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL Configuration (HestiaCP will handle certificates)
    ssl_certificate /home/$USER/conf/web/$DOMAIN/ssl/$DOMAIN.pem;
    ssl_certificate_key /home/$USER/conf/web/$DOMAIN/ssl/$DOMAIN.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # File upload limits
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Handle large file uploads
        proxy_request_buffering off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Static files (if any)
    location /static {
        alias $APP_DIR/Bank_Specific_Converter/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/server-status;
        access_log off;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Step 10: Start services
echo -e "${YELLOW}🔄 Step 10: Starting services...${NC}"
systemctl daemon-reload
systemctl enable bank-converter
systemctl start bank-converter
systemctl reload nginx

# Step 11: Setup log rotation
echo -e "${YELLOW}📝 Step 11: Setting up log rotation...${NC}"
cat > /etc/logrotate.d/bank-converter << EOF
$APP_DIR/Bank_Specific_Converter/logs/*.log {
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

# Step 12: Create management scripts
echo -e "${YELLOW}🛠️ Step 12: Creating management scripts...${NC}"
cat > $APP_DIR/Bank_Specific_Converter/deploy_status.sh << 'EOF'
#!/bin/bash
echo "🏦 Bank Select Converter - Deployment Status"
echo "============================================"
echo "Service Status:"
systemctl status bank-converter --no-pager -l
echo ""
echo "Nginx Status:"
systemctl status nginx --no-pager -l
echo ""
echo "Logs (last 20 lines):"
journalctl -u bank-converter -n 20 --no-pager
EOF

chmod +x $APP_DIR/Bank_Specific_Converter/deploy_status.sh

# Final status check
echo -e "${GREEN}✅ Deployment Summary:${NC}"
echo "Domain: https://$DOMAIN"
echo "Service Status:"
systemctl is-active bank-converter
echo "Nginx Status:"
systemctl is-active nginx

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}🌐 Your app should be available at: https://$DOMAIN${NC}"
echo -e "${YELLOW}📊 Check status: $APP_DIR/Bank_Specific_Converter/deploy_status.sh${NC}"
echo -e "${YELLOW}📋 View logs: journalctl -u bank-converter -f${NC}"
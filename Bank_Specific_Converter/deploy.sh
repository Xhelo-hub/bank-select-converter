#!/bin/bash
# Bank Statement Converter Deployment Script for HestiaCP
# ======================================================

echo "🏦 Bank Statement Converter - HestiaCP Deployment"
echo "=================================================="

# Set variables (modify these for your server)
DOMAIN="your-domain.com"  # Change to your actual domain
USER="admin"              # Change to your HestiaCP username
APP_DIR="/home/$USER/web/$DOMAIN/public_html/bank_converter"
SCRIPTS_DIR="/home/$USER/web/$DOMAIN/public_html"

echo "📂 Creating application directories..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/uploads
mkdir -p $APP_DIR/converted
mkdir -p $APP_DIR/logs
mkdir -p /var/log/gunicorn
mkdir -p /var/run/gunicorn

echo "📋 Setting permissions..."
chown -R $USER:$USER $APP_DIR
chmod 755 $APP_DIR
chmod 777 $APP_DIR/uploads
chmod 777 $APP_DIR/converted
chmod 755 $APP_DIR/logs

echo "🐍 Setting up Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "📄 Copying converter scripts..."
# Copy your individual bank converter scripts to the scripts directory
cp $SCRIPTS_DIR/BKT*.py $SCRIPTS_DIR/ 2>/dev/null || echo "BKT script not found"
cp $SCRIPTS_DIR/RAI*.py $SCRIPTS_DIR/ 2>/dev/null || echo "Raiffeisen script not found" 
cp $SCRIPTS_DIR/OTP*.py $SCRIPTS_DIR/ 2>/dev/null || echo "OTP script not found"
cp $SCRIPTS_DIR/TIBANK*.py $SCRIPTS_DIR/ 2>/dev/null || echo "TI Bank script not found"
cp $SCRIPTS_DIR/UNION*.py $SCRIPTS_DIR/ 2>/dev/null || echo "Union script not found"
cp $SCRIPTS_DIR/Withholding*.py $SCRIPTS_DIR/ 2>/dev/null || echo "E-Bills script not found"

echo "🔧 Setting up systemd service..."
cat > /etc/systemd/system/bank-converter.service << EOF
[Unit]
Description=Bank Statement Converter Flask App
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/gunicorn --config $APP_DIR/gunicorn.conf.py wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "🌐 Setting up Nginx configuration..."
cat > /etc/nginx/sites-available/bank-converter << EOF
server {
    listen 80;
    server_name $DOMAIN;

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
    }

    location /static {
        alias $APP_DIR/static;
        expires 1d;
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/bank-converter /etc/nginx/sites-enabled/

echo "🔄 Starting services..."
systemctl daemon-reload
systemctl enable bank-converter
systemctl start bank-converter
systemctl reload nginx

echo "✅ Deployment completed!"
echo "🌐 Your app should be available at: http://$DOMAIN"
echo "📊 Check status with: systemctl status bank-converter"
echo "📋 View logs with: journalctl -u bank-converter -f"
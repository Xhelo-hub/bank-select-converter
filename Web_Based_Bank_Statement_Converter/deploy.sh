#!/bin/bash

# Web-Based Bank Statement Converter API Deployment Script
# ========================================================

set -e

echo "🏦 Web-Based Bank Statement Converter API - Deployment Script"
echo "=============================================================="

# Configuration
APP_NAME="bank-converter-api"
APP_USER="bank-converter"
APP_DIR="/opt/bank-converter"
VENV_DIR="$APP_DIR/.venv"
LOG_DIR="/var/log/bank-converter"
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d" " -f2 | cut -d"." -f1-2)
    if (( $(echo "$python_version < 3.8" | bc -l) )); then
        error "Python 3.8+ is required (found $python_version)"
        exit 1
    fi
    
    log "Python $python_version found ✓"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        error "git is required but not installed"
        exit 1
    fi
    
    log "System requirements check passed ✓"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        python3-venv \
        python3-pip \
        python3-dev \
        build-essential \
        nginx \
        supervisor \
        curl \
        certbot \
        python3-certbot-nginx
    
    log "System dependencies installed ✓"
}

# Create application user
create_user() {
    if ! id "$APP_USER" &>/dev/null; then
        log "Creating application user: $APP_USER"
        sudo useradd --system --home "$APP_DIR" --shell /bin/bash "$APP_USER"
    else
        log "User $APP_USER already exists ✓"
    fi
}

# Setup application directory
setup_directory() {
    log "Setting up application directory: $APP_DIR"
    
    sudo mkdir -p "$APP_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    sudo chown -R "$APP_USER:$APP_USER" "$LOG_DIR"
    
    log "Application directory setup complete ✓"
}

# Clone or update application code
deploy_code() {
    log "Deploying application code..."
    
    if [[ -d "$APP_DIR/.git" ]]; then
        log "Updating existing code..."
        sudo -u "$APP_USER" git -C "$APP_DIR" pull origin main
    else
        log "Cloning application code..."
        sudo -u "$APP_USER" git clone https://github.com/Xhelo-hub/web-based-bank-statement-converter.git "$APP_DIR"
    fi
    
    log "Code deployment complete ✓"
}

# Setup Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    if [[ ! -d "$VENV_DIR" ]]; then
        sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
    fi
    
    # Install/update dependencies
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
    sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install gunicorn
    
    log "Virtual environment setup complete ✓"
}

# Create systemd service
create_service() {
    log "Creating systemd service..."
    
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Web-Based Bank Statement Converter API
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 300 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$APP_DIR $LOG_DIR /tmp
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

# Environment
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable "$APP_NAME"
    
    log "Systemd service created ✓"
}

# Configure nginx
configure_nginx() {
    log "Configuring nginx..."
    
    sudo tee "/etc/nginx/sites-available/$APP_NAME" > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /api/health {
        proxy_pass http://127.0.0.1:5000/api/health;
        access_log off;
    }
}
EOF
    
    # Enable the site
    sudo ln -sf "/etc/nginx/sites-available/$APP_NAME" "/etc/nginx/sites-enabled/"
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    sudo nginx -t
    
    log "Nginx configuration complete ✓"
}

# Setup SSL certificate
setup_ssl() {
    read -p "Enter your domain name (or press Enter to skip SSL setup): " domain
    
    if [[ -n "$domain" ]]; then
        log "Setting up SSL certificate for $domain..."
        
        # Update nginx configuration with domain
        sudo sed -i "s/server_name _;/server_name $domain;/" "/etc/nginx/sites-available/$APP_NAME"
        
        # Restart nginx
        sudo systemctl restart nginx
        
        # Get SSL certificate
        sudo certbot --nginx -d "$domain" --non-interactive --agree-tos --email "admin@$domain" || warn "SSL setup failed"
        
        log "SSL setup complete for $domain ✓"
    else
        warn "Skipping SSL setup"
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start application
    sudo systemctl restart "$APP_NAME"
    sudo systemctl restart nginx
    
    # Check status
    sleep 5
    
    if sudo systemctl is-active --quiet "$APP_NAME"; then
        log "Application service is running ✓"
    else
        error "Application service failed to start"
        sudo systemctl status "$APP_NAME"
        exit 1
    fi
    
    if sudo systemctl is-active --quiet nginx; then
        log "Nginx service is running ✓"
    else
        error "Nginx service failed to start"
        sudo systemctl status nginx
        exit 1
    fi
}

# Setup monitoring
setup_monitoring() {
    log "Setting up log rotation..."
    
    sudo tee "/etc/logrotate.d/$APP_NAME" > /dev/null << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl restart $APP_NAME
    endscript
}
EOF
    
    log "Monitoring setup complete ✓"
}

# Create environment file template
create_env_template() {
    if [[ ! -f "$APP_DIR/.env.example" ]]; then
        log "Creating environment template..."
        
        sudo -u "$APP_USER" tee "$APP_DIR/.env.example" > /dev/null << EOF
# Web-Based Bank Statement Converter API Configuration
# ===================================================

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=change-this-to-a-random-secret-key

# File Handling
MAX_FILE_SIZE_MB=50
UPLOAD_RETENTION_HOURS=1
CLEANUP_INTERVAL_MINUTES=30

# Server Configuration
HOST=127.0.0.1
PORT=5000
WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/app.log

# Security (optional)
API_KEY_REQUIRED=false
RATE_LIMIT_ENABLED=true

# Database (optional)
DATABASE_URL=postgresql://user:password@localhost/bank_converter
EOF
        
        log "Environment template created at $APP_DIR/.env.example"
        info "Please copy .env.example to .env and configure your settings"
    fi
}

# Display deployment summary
deployment_summary() {
    echo
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo
    info "Application URL: http://$(hostname -I | awk '{print $1}')"
    info "API Health Check: http://$(hostname -I | awk '{print $1}')/api/health"
    info "Application Directory: $APP_DIR"
    info "Log Directory: $LOG_DIR"
    echo
    info "Service Management:"
    echo "  Start:   sudo systemctl start $APP_NAME"
    echo "  Stop:    sudo systemctl stop $APP_NAME"
    echo "  Restart: sudo systemctl restart $APP_NAME"
    echo "  Status:  sudo systemctl status $APP_NAME"
    echo "  Logs:    sudo journalctl -u $APP_NAME -f"
    echo
    info "Configuration:"
    echo "  App Config: $APP_DIR/.env"
    echo "  Nginx Config: /etc/nginx/sites-available/$APP_NAME"
    echo "  Service File: $SERVICE_FILE"
    echo
    warn "Remember to:"
    echo "  1. Configure environment variables in $APP_DIR/.env"
    echo "  2. Set up SSL certificate for production use"
    echo "  3. Configure firewall rules"
    echo "  4. Set up monitoring and backups"
    echo
}

# Main deployment function
main() {
    log "Starting deployment of Web-Based Bank Statement Converter API..."
    
    check_root
    check_requirements
    install_dependencies
    create_user
    setup_directory
    deploy_code
    setup_venv
    create_service
    configure_nginx
    setup_ssl
    start_services
    setup_monitoring
    create_env_template
    deployment_summary
    
    log "Deployment completed successfully! 🎉"
}

# Handle script interruption
trap 'error "Deployment interrupted!"; exit 1' INT TERM

# Run main function
main "$@"
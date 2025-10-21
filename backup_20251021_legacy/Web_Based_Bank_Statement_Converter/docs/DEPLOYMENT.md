# 🚀 Deployment Guide

## 📋 Overview

This guide covers various deployment options for the Web-Based Bank Statement Converter API, from development to production environments.

## 🏠 Local Development

### Quick Start
```bash
# Clone the repository
git clone https://github.com/Xhelo-hub/web-based-bank-statement-converter.git
cd web-based-bank-statement-converter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start development server
python app.py
```

### Development Configuration
```bash
# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=True
export SECRET_KEY=dev-secret-key

# Start with custom host/port
python app.py --host 0.0.0.0 --port 8080
```

---

## 🐳 Docker Deployment

### Single Container
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p uploads converted logs

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

### Build and Run
```bash
# Build Docker image
docker build -t bank-converter-api .

# Run container
docker run -d \
  --name bank-converter \
  -p 5000:5000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/converted:/app/converted \
  -e SECRET_KEY=your-secret-key \
  bank-converter-api

# Check logs
docker logs bank-converter

# Stop container
docker stop bank-converter
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key-here
      - MAX_FILE_SIZE_MB=50
    volumes:
      - ./uploads:/app/uploads
      - ./converted:/app/converted
      - ./logs:/app/logs
    restart: unless-stopped
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  uploads:
  converted:
  logs:
```

### Run with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## ☁️ Cloud Deployment

### 🟦 Heroku Deployment

#### Prepare for Heroku
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Create runtime.txt
echo "python-3.11.2" > runtime.txt

# Initialize git repository
git init
git add .
git commit -m "Initial commit"
```

#### Deploy to Heroku
```bash
# Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create Heroku app
heroku create your-bank-converter-api

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set FLASK_ENV=production
heroku config:set MAX_FILE_SIZE_MB=50

# Deploy
git push heroku main

# Open the app
heroku open
```

#### Heroku Configuration
```bash
# Scale dynos
heroku ps:scale web=2

# View logs
heroku logs --tail

# Restart app
heroku restart

# Add custom domain
heroku domains:add api.yourdomain.com
```

### 🟧 AWS Deployment

#### AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init

# Create environment
eb create production

# Deploy
eb deploy

# Open application
eb open
```

#### AWS Lambda (Serverless)
```python
# lambda_handler.py
from app import app
import awsgi

def lambda_handler(event, context):
    return awsgi.response(app, event, context)
```

```yaml
# serverless.yml
service: bank-converter-api

provider:
  name: aws
  runtime: python3.9
  region: us-east-1
  
functions:
  api:
    handler: lambda_handler.lambda_handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
    timeout: 300
    memorySize: 1024
```

### 🟨 Google Cloud Platform

#### App Engine
```yaml
# app.yaml
runtime: python39

env_variables:
  FLASK_ENV: production
  SECRET_KEY: your-secret-key

resources:
  cpu: 2
  memory_gb: 4
  disk_size_gb: 10

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

```bash
# Deploy to App Engine
gcloud app deploy

# View logs
gcloud app logs tail -s default
```

#### Cloud Run
```bash
# Build and push to Container Registry
docker build -t gcr.io/your-project/bank-converter .
docker push gcr.io/your-project/bank-converter

# Deploy to Cloud Run
gcloud run deploy bank-converter \
  --image gcr.io/your-project/bank-converter \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

### 🟣 Microsoft Azure

#### Azure App Service
```bash
# Create resource group
az group create --name bank-converter-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name bank-converter-plan \
  --resource-group bank-converter-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group bank-converter-rg \
  --plan bank-converter-plan \
  --name your-bank-converter \
  --runtime "PYTHON|3.9"

# Deploy code
az webapp deployment source config-zip \
  --resource-group bank-converter-rg \
  --name your-bank-converter \
  --src app.zip
```

---

## 🔧 Production Configuration

### Environment Variables
```bash
# Production environment
export FLASK_ENV=production
export FLASK_DEBUG=False
export SECRET_KEY=your-super-secret-key-here

# File handling
export MAX_FILE_SIZE_MB=50
export UPLOAD_RETENTION_HOURS=1
export CLEANUP_INTERVAL_MINUTES=30

# Server configuration
export HOST=0.0.0.0
export PORT=5000
export WORKERS=4

# Logging
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/bank-converter/app.log
```

### Production Settings
```python
# config.py
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    TESTING = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE_MB', 50)) * 1024 * 1024
    UPLOAD_FOLDER = '/app/uploads'
    CONVERTED_FOLDER = '/app/converted'
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true'
```

### Gunicorn Configuration
```python
# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 2

# Restart workers
preload_app = True
max_requests = 1000
max_requests_jitter = 50

# Logging
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
accesslog = "/var/log/gunicorn/access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "bank_converter_api"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

---

## 🌐 Reverse Proxy Setup

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/bank-converter
server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # File upload size
    client_max_body_size 50M;
    
    # Timeouts
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    
    # Proxy to Flask app
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files (if any)
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:5000/api/health;
    }
}
```

### Apache Configuration
```apache
# /etc/apache2/sites-available/bank-converter.conf
<VirtualHost *:80>
    ServerName api.yourdomain.com
    Redirect permanent / https://api.yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName api.yourdomain.com
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/yourdomain.crt
    SSLCertificateKeyFile /etc/ssl/private/yourdomain.key
    
    # Security headers
    Header always set X-Frame-Options DENY
    Header always set X-Content-Type-Options nosniff
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
    
    # Proxy configuration
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
    
    # File upload size
    LimitRequestBody 52428800  # 50MB
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/bank-converter_error.log
    CustomLog ${APACHE_LOG_DIR}/bank-converter_access.log combined
</VirtualHost>
```

---

## 📊 Monitoring & Logging

### Application Monitoring
```python
# monitoring.py
import logging
import time
from functools import wraps
from flask import request, g

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler('/var/log/bank-converter/app.log'),
            logging.StreamHandler()
        ]
    )

def log_requests(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.start_time = time.time()
        response = f(*args, **kwargs)
        
        duration = time.time() - g.start_time
        logging.info(f'{request.method} {request.path} - {response.status_code} - {duration:.3f}s')
        
        return response
    return decorated_function
```

### Health Check Endpoint
```python
# health.py
import psutil
import os
from datetime import datetime

def get_system_health():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'system': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        },
        'application': {
            'active_jobs': len(conversion_jobs),
            'upload_dir_size': get_directory_size('uploads'),
            'converted_dir_size': get_directory_size('converted')
        }
    }
```

### Log Rotation
```bash
# /etc/logrotate.d/bank-converter
/var/log/bank-converter/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl restart bank-converter
    endscript
}
```

---

## ⚡ Performance Optimization

### Application Optimization
```python
# performance.py
from flask_caching import Cache
from werkzeug.middleware.profiler import ProfilerMiddleware

# Add caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Add profiling (development only)
if app.debug:
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

# Optimize file operations
def optimize_pdf_processing():
    # Use memory-mapped files for large PDFs
    # Implement streaming for file uploads
    # Add compression for output files
    pass
```

### Database Optimization (if added)
```python
# database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/bank_converter'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)
```

### Caching Strategy
```python
# caching.py
import redis
from flask_caching import Cache

# Redis configuration
cache_config = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 0,
    'CACHE_DEFAULT_TIMEOUT': 300
}

cache = Cache(app, config=cache_config)

@cache.memoize(timeout=3600)
def get_bank_info(bank_code):
    # Cached bank information
    pass
```

---

## 🔒 Security Hardening

### SSL/TLS Configuration
```bash
# Generate SSL certificate (Let's Encrypt)
sudo certbot --nginx -d api.yourdomain.com

# Manual certificate installation
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/yourdomain.key \
    -out /etc/ssl/certs/yourdomain.crt
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# iptables rules
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -j DROP
```

### Application Security
```python
# security.py
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Security headers
Talisman(app, force_https=True)

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"]
)

@app.route('/api/upload', methods=['POST'])
@limiter.limit("5 per minute")
def upload_file():
    # Upload logic with rate limiting
    pass
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Set production environment variables
- [ ] Configure SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure firewall rules
- [ ] Test file upload limits
- [ ] Verify converter scripts work
- [ ] Test API endpoints
- [ ] Set up backup strategy

### Post-Deployment
- [ ] Verify all endpoints work
- [ ] Test file upload and conversion
- [ ] Check SSL certificate installation
- [ ] Monitor system resources
- [ ] Set up log rotation
- [ ] Configure automated backups
- [ ] Test disaster recovery
- [ ] Update DNS records

### Maintenance
- [ ] Monitor disk space usage
- [ ] Check application logs
- [ ] Update dependencies regularly
- [ ] Backup configuration files
- [ ] Monitor SSL certificate expiry
- [ ] Review security logs
- [ ] Update converter scripts as needed

---

## 🆘 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python --version

# Check dependencies
pip check

# Check port availability
netstat -tulpn | grep :5000

# Check logs
tail -f /var/log/bank-converter/app.log
```

#### File Upload Issues
```bash
# Check disk space
df -h

# Check file permissions
ls -la uploads/ converted/

# Check nginx/apache configuration
nginx -t
apache2ctl configtest
```

#### SSL Certificate Issues
```bash
# Test SSL certificate
openssl s_client -connect api.yourdomain.com:443

# Check certificate expiry
openssl x509 -in /etc/ssl/certs/yourdomain.crt -text -noout
```

### Performance Issues
```bash
# Monitor system resources
htop
iotop
netstat -i

# Check application performance
curl -w "@curl-format.txt" -s -o /dev/null http://api.yourdomain.com/api/health
```

This comprehensive deployment guide covers all major deployment scenarios and provides the necessary configuration for production use.
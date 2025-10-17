# Nginx Reverse Proxy Setup for c.konsulence.al

## Current Status
✅ Flask app is running on port 5002  
❌ App is NOT accessible from https://c.konsulence.al  
🔧 **Need:** Configure Nginx to proxy web traffic to Flask app

---

## Problem
The Flask app runs on `127.0.0.1:5002` (internal only). To access it at `https://c.konsulence.al`, we need Nginx to act as a reverse proxy.

---

## Solution: Configure Nginx in HestiaCP

### Option 1: Via HestiaCP Web Panel (Recommended)

1. **Login to HestiaCP:**
   - URL: `https://apps.konsulence.al:8083` (or your HestiaCP URL)
   - User: `admin` or the main admin account

2. **Navigate to Web Domains:**
   - Go to **WEB** → Find `c.konsulence.al`
   - Click **Edit** (pencil icon)

3. **Add Proxy Configuration:**
   - Scroll down to **Proxy Template**
   - Change from `default` to `custom` or add custom config
   
4. **Add this to Nginx configuration:**
   ```nginx
   location / {
       proxy_pass http://127.0.0.1:5002;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_connect_timeout 300;
       proxy_send_timeout 300;
       proxy_read_timeout 300;
       client_max_body_size 50M;
   }
   ```

5. **Save** and restart Nginx

---

### Option 2: Via SSH with Admin Access

```bash
# Login as admin (not converter user)
ssh admin@c.konsulence.al

# Or if you have sudo access as converter
ssh converter@c.konsulence.al

# Become root or use sudo for the following commands
sudo su

# Edit the Nginx configuration for c.konsulence.al
nano /home/converter/conf/web/c.konsulence.al/nginx.conf_custom

# Add this content (or create the file if it doesn't exist):
```

```nginx
location / {
    proxy_pass http://127.0.0.1:5002;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    client_max_body_size 50M;
}
```

```bash
# Test Nginx configuration
nginx -t

# If test passes, restart Nginx
systemctl restart nginx

# Or via HestiaCP command
v-restart-web
```

---

### Option 3: Quick Test - Direct Port Access

If you want to test immediately without Nginx setup:

1. **Open firewall port 5002:**
   ```bash
   sudo ufw allow 5002/tcp
   ```

2. **Access directly:**
   - Visit: `http://c.konsulence.al:5002`
   - Note: This is HTTP only, not HTTPS

3. **⚠️ Warning:** This is NOT recommended for production. Use Nginx proxy instead.

---

## Verify the Flask App is Running

```bash
ssh converter@c.konsulence.al

# Check if app is running
ps aux | grep "python app.py"

# Test locally
curl http://127.0.0.1:5002

# If you see HTML output, the app is working!
```

---

## Alternative: Use Gunicorn with Systemd (Production Setup)

Instead of running Flask directly, use Gunicorn with systemd:

### 1. Create systemd service file

```bash
ssh converter@c.konsulence.al
sudo nano /etc/systemd/system/bank-converter.service
```

Add this content:

```ini
[Unit]
Description=Bank Statement Converter Web Service
After=network.target

[Service]
Type=notify
User=converter
Group=converter
WorkingDirectory=/home/converter/web/c.konsulence.al/public_html/Bank_Specific_Converter
Environment="PATH=/home/converter/web/c.konsulence.al/public_html/.venv/bin"
ExecStart=/home/converter/web/c.konsulence.al/public_html/.venv/bin/gunicorn \
    --bind 127.0.0.1:5002 \
    --workers 4 \
    --timeout 300 \
    --access-logfile /home/converter/web/c.konsulence.al/logs/gunicorn-access.log \
    --error-logfile /home/converter/web/c.konsulence.al/logs/gunicorn-error.log \
    wsgi:application

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable bank-converter
sudo systemctl start bank-converter
sudo systemctl status bank-converter
```

### 3. Stop the manual Flask process first

```bash
# Find the process
ps aux | grep "python app.py"

# Kill it (use the PID from above)
kill -9 <PID>

# Or kill all python app.py processes
pkill -f "python app.py"
```

---

## Complete Deployment Checklist

- [x] Code deployed to `/home/converter/web/c.konsulence.al/public_html`
- [x] Python virtual environment created
- [x] Dependencies installed
- [x] Flask app running on port 5002
- [ ] **Nginx reverse proxy configured** ⬅️ YOU ARE HERE
- [ ] SSL certificate configured (HestiaCP auto-configures this)
- [ ] Systemd service setup (optional but recommended)
- [ ] Auto-start on boot configured

---

## Troubleshooting

### App not responding
```bash
# Restart the app
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html/Bank_Specific_Converter

# Kill existing process
pkill -f "python app.py"

# Restart
source ../.venv/bin/activate
python app.py &
```

### Check logs
```bash
# Flask app logs (if running in background)
tail -f ~/web/c.konsulence.al/public_html/Bank_Specific_Converter/nohup.out

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /home/converter/web/c.konsulence.al/logs/error.log
```

### Nginx not forwarding requests
```bash
# Check Nginx configuration
sudo nginx -t

# Check if Nginx is running
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx
```

---

## Summary

**Current State:**
- ✅ App is running on internal port 5002
- ❌ Not accessible from https://c.konsulence.al

**What You Need to Do:**
1. Login to HestiaCP web panel
2. Edit the Nginx configuration for `c.konsulence.al`
3. Add the proxy configuration from Option 1 above
4. Save and restart Nginx
5. Visit https://c.konsulence.al - it should work!

**Or:**
Ask your system administrator to add the Nginx reverse proxy configuration using the commands in Option 2.

---

## Quick Command to Check Status

```bash
ssh converter@c.konsulence.al "ps aux | grep 'python app.py' && curl -s -o /dev/null -w 'HTTP Status: %{http_code}\n' http://127.0.0.1:5002"
```

This will show if the app is running and responding on port 5002.

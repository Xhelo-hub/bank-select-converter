# Email Configuration and System Monitoring Setup Guide

## Overview
This system includes:
1. **Password Reset Emails** - Already functional
2. **System Health Monitoring** - New feature that monitors system health and sends alerts
3. **Admin Notifications** - Alerts for new user registrations and system issues

## Email Configuration

### Step 1: Set Environment Variables

You need to configure SMTP settings. Add these to your server environment:

```bash
# Edit the systemd service file to include email configuration
sudo nano /etc/systemd/system/bank-converter.service
```

Add these environment variables in the `[Service]` section:

```ini
Environment="SMTP_SERVER=smtp.gmail.com"
Environment="SMTP_PORT=587"
Environment="SMTP_USERNAME=your-email@gmail.com"
Environment="SMTP_PASSWORD=your-app-password"
Environment="FROM_EMAIL=your-email@gmail.com"
```

### Step 2: Gmail App Password (if using Gmail)

If using Gmail, you need to create an App Password:

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Scroll down to "App passwords"
4. Create a new app password for "Mail"
5. Copy the 16-character password
6. Use this password in `SMTP_PASSWORD`

### Step 3: Alternative Email Providers

#### For Office 365/Outlook:
```ini
Environment="SMTP_SERVER=smtp.office365.com"
Environment="SMTP_PORT=587"
Environment="SMTP_USERNAME=your-email@outlook.com"
Environment="SMTP_PASSWORD=your-password"
```

#### For Custom SMTP Server:
```ini
Environment="SMTP_SERVER=mail.yourdomain.com"
Environment="SMTP_PORT=587"
Environment="SMTP_USERNAME=noreply@yourdomain.com"
Environment="SMTP_PASSWORD=your-password"
```

## System Health Monitor Setup

### Step 1: Install Health Monitor Service

```bash
# Navigate to project directory
cd /home/converter/web/c.konsulence.al/public_html

# Pull latest changes
git pull origin main

# Copy service file
sudo cp Bank_Specific_Converter/health-monitor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the health monitor
sudo systemctl enable health-monitor.service

# Start the health monitor
sudo systemctl start health-monitor.service

# Check status
sudo systemctl status health-monitor.service
```

### Step 2: Verify Health Monitor is Running

```bash
# Check if it's active
sudo systemctl is-active health-monitor.service

# View logs
sudo journalctl -u health-monitor.service -f
```

## What the Health Monitor Does

The health monitor checks every 5 minutes:

1. **Service Status** - Is bank-converter.service running?
2. **Process Count** - Are gunicorn workers alive?
3. **Disk Space** - Is disk usage below 90%?
4. **Memory Usage** - Is memory usage below 90%?

### Alert Behavior

- **First Alert**: Sent immediately when issue detected
- **Cooldown**: 1 hour between identical alerts (prevents spam)
- **Recovery**: Automatic notification when system recovers
- **Recipients**: All users with admin privileges in `users.json`

## Email Notifications Available

### 1. System Alerts (health_monitor.py)
- Service down alerts
- High disk space warnings
- High memory usage warnings
- Includes full system diagnostics

### 2. Password Reset (email_utils.py)
- Already functional
- Sent when user requests password reset
- Contains 6-digit code valid for 30 minutes

### 3. Admin Management (email_utils.py)
- Admin promotion notifications
- Admin removal verification
- New user registration alerts (optional - needs integration)

## Testing Email Configuration

### Test Password Reset Email

1. Go to https://c.konsulence.al/forgot-password
2. Enter your email
3. Check your inbox for reset code

### Test System Alert Email

Manually trigger an alert by temporarily stopping the service:

```bash
# Stop service (will trigger alert)
sudo systemctl stop bank-converter.service

# Wait 5-10 minutes for health check to run
# Check health monitor logs
sudo journalctl -u health-monitor.service -n 50

# Restart service (will trigger recovery notification)
sudo systemctl start bank-converter.service
```

## Troubleshooting

### No Emails Being Sent

1. **Check SMTP credentials**:
   ```bash
   sudo systemctl status bank-converter.service | grep SMTP
   ```

2. **Test SMTP connection manually**:
   ```bash
   python3 -c "
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   print('SMTP connection successful!')
   server.quit()
   "
   ```

3. **Check logs**:
   ```bash
   sudo journalctl -u bank-converter.service | grep -i email
   sudo journalctl -u health-monitor.service | grep -i email
   ```

### Health Monitor Not Running

```bash
# Check status
sudo systemctl status health-monitor.service

# Restart
sudo systemctl restart health-monitor.service

# View detailed logs
sudo journalctl -u health-monitor.service -n 100 --no-pager
```

### Gmail Blocking Login

- Ensure 2-Step Verification is enabled
- Use App Password, not regular password
- Check Google Security alerts
- Enable "Less secure app access" (if not using App Password)

## Reload Services After Configuration Changes

```bash
# Reload systemd
sudo systemctl daemon-reload

# Restart main service
sudo systemctl restart bank-converter.service

# Restart health monitor
sudo systemctl restart health-monitor.service

# Verify both are running
sudo systemctl status bank-converter.service
sudo systemctl status health-monitor.service
```

## Monitoring Logs in Real-Time

```bash
# Main application logs
sudo journalctl -u bank-converter.service -f

# Health monitor logs
sudo journalctl -u health-monitor.service -f

# Both together
sudo journalctl -u bank-converter.service -u health-monitor.service -f
```

## Quick Reference Commands

```bash
# Check all services
systemctl status bank-converter.service health-monitor.service

# Restart everything
sudo systemctl restart bank-converter.service health-monitor.service

# View recent logs
sudo journalctl -u bank-converter.service -u health-monitor.service -n 50

# Test email sending
python3 -m Bank_Specific_Converter.email_utils
```

## Security Recommendations

1. **Never commit SMTP credentials to Git**
2. **Use environment variables for all secrets**
3. **Create a dedicated email account for system notifications**
4. **Use App Passwords instead of regular passwords**
5. **Consider using a transactional email service** (SendGrid, Mailgun, AWS SES) for production
6. **Monitor email bounce rates and delivery issues**

## Future Enhancements

Consider adding:
- Email rate limiting
- Email queue for failed sends
- HTML/text email templates system
- Email delivery status tracking
- Integration with external monitoring services (UptimeRobot, Pingdom)
- SMS alerts for critical issues
- Slack/Discord webhook integration

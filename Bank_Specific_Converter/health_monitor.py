"""
System Health Monitor
=====================
Monitors system health and sends email alerts to admins when issues are detected
"""

import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from email_utils import send_email

# Get admin emails from database
def get_admin_emails():
    """Get list of admin email addresses from database"""
    try:
        from app import app
        from models import User

        with app.app_context():
            admin_users = User.query.filter_by(is_admin=True, is_approved=True, _is_active=True).all()
            return [user.email for user in admin_users]
    except Exception as e:
        print(f"Error getting admin emails: {e}")
        return []

def check_service_status():
    """Check if bank-converter service is running"""
    try:
        result = subprocess.run(
            ['/bin/systemctl', 'is-active', 'bank-converter.service'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == 'active'
    except Exception as e:
        print(f"Error checking service status: {e}")
        return False

def check_gunicorn_processes():
    """Check if gunicorn processes are running"""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        gunicorn_count = len([line for line in result.stdout.split('\n') 
                              if 'gunicorn' in line and 'wsgi:application' in line])
        return gunicorn_count >= 2  # At least master + 1 worker
    except Exception as e:
        print(f"Error checking gunicorn processes: {e}")
        return False

def check_disk_space():
    """Check available disk space"""
    try:
        result = subprocess.run(
            ['df', '-h', '/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            usage = parts[4].replace('%', '')
            return int(usage) < 90  # Alert if > 90% used
    except Exception as e:
        print(f"Error checking disk space: {e}")
        return True  # Don't alert on check failure

def check_memory_usage():
    """Check memory usage"""
    try:
        result = subprocess.run(
            ['free', '-m'],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            total = int(parts[1])
            used = int(parts[2])
            usage_percent = (used / total) * 100
            return usage_percent < 90  # Alert if > 90% used
    except Exception as e:
        print(f"Error checking memory usage: {e}")
        return True

def get_system_info():
    """Get detailed system information"""
    info = {}
    
    # Service status
    try:
        result = subprocess.run(
            ['/bin/systemctl', 'status', 'bank-converter.service', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=5
        )
        info['service_status'] = result.stdout
    except:
        info['service_status'] = 'Unable to retrieve'
    
    # Disk usage
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
        info['disk_usage'] = result.stdout
    except:
        info['disk_usage'] = 'Unable to retrieve'
    
    # Memory usage
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        info['memory_usage'] = result.stdout
    except:
        info['memory_usage'] = 'Unable to retrieve'
    
    # Recent journal logs
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'bank-converter.service', '-n', '20', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=5
        )
        info['recent_logs'] = result.stdout
    except:
        info['recent_logs'] = 'Unable to retrieve'
    
    return info

def send_alert(issue_type, details):
    """Send alert email to all admins"""
    admin_emails = get_admin_emails()
    
    if not admin_emails:
        print("Warning: No admin emails found to send alerts")
        return
    
    system_info = get_system_info()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = f"🚨 ALERT: {issue_type} - Albanian Bank Converter"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; }}
            .alert {{ 
                background-color: #fff3cd; 
                border-left: 4px solid #ff0000; 
                padding: 15px; 
                margin: 20px 0;
            }}
            .content {{ background-color: #f9f9f9; padding: 30px; }}
            .info-box {{ 
                background-color: #fff; 
                border: 1px solid #ddd; 
                padding: 15px; 
                margin: 10px 0;
                border-radius: 5px;
            }}
            .code {{ 
                background-color: #f4f4f4; 
                border: 1px solid #ddd; 
                padding: 10px; 
                font-family: 'Courier New', monospace; 
                font-size: 12px; 
                white-space: pre-wrap;
                overflow-x: auto;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            h3 {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 System Alert</h1>
                <p>Albanian Bank Statement Converter</p>
            </div>
            <div class="content">
                <div class="alert">
                    <h2>{issue_type}</h2>
                    <p><strong>Time:</strong> {timestamp}</p>
                    <p><strong>Details:</strong> {details}</p>
                </div>
                
                <div class="info-box">
                    <h3>Service Status</h3>
                    <div class="code">{system_info.get('service_status', 'N/A')}</div>
                </div>
                
                <div class="info-box">
                    <h3>Disk Usage</h3>
                    <div class="code">{system_info.get('disk_usage', 'N/A')}</div>
                </div>
                
                <div class="info-box">
                    <h3>Memory Usage</h3>
                    <div class="code">{system_info.get('memory_usage', 'N/A')}</div>
                </div>
                
                <div class="info-box">
                    <h3>Recent Logs (Last 20 lines)</h3>
                    <div class="code">{system_info.get('recent_logs', 'N/A')}</div>
                </div>
                
                <p style="margin-top: 20px;"><strong>Recommended Actions:</strong></p>
                <ul>
                    <li>Check the service status: <code>sudo systemctl status bank-converter.service</code></li>
                    <li>View logs: <code>sudo journalctl -u bank-converter.service -f</code></li>
                    <li>Restart service: <code>sudo systemctl restart bank-converter.service</code></li>
                    <li>Or use the admin panel: <a href="https://c.konsulence.al/admin">https://c.konsulence.al/admin</a></li>
                </ul>
            </div>
            <div class="footer">
                <p>This is an automated alert from the System Health Monitor</p>
                <p>Albanian Bank Statement Converter</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    SYSTEM ALERT: {issue_type}
    
    Time: {timestamp}
    Details: {details}
    
    Service Status:
    {system_info.get('service_status', 'N/A')}
    
    Disk Usage:
    {system_info.get('disk_usage', 'N/A')}
    
    Memory Usage:
    {system_info.get('memory_usage', 'N/A')}
    
    Recent Logs:
    {system_info.get('recent_logs', 'N/A')}
    
    Recommended Actions:
    - Check the service status: sudo systemctl status bank-converter.service
    - View logs: sudo journalctl -u bank-converter.service -f
    - Restart service: sudo systemctl restart bank-converter.service
    - Or use the admin panel: https://c.konsulence.al/admin
    """
    
    # Send to all admins
    for admin_email in admin_emails:
        try:
            success, message = send_email(admin_email, subject, html_body, text_body)
            if success:
                print(f"Alert sent to {admin_email}")
            else:
                print(f"Failed to send alert to {admin_email}: {message}")
        except Exception as e:
            print(f"Error sending alert to {admin_email}: {e}")

def check_system_health():
    """Perform comprehensive health check"""
    issues = []
    
    # Check service
    if not check_service_status():
        issues.append("Service is not active")
    
    # Check processes
    if not check_gunicorn_processes():
        issues.append("Insufficient gunicorn processes running")
    
    # Check disk space
    if not check_disk_space():
        issues.append("Disk space usage is above 90%")
    
    # Check memory
    if not check_memory_usage():
        issues.append("Memory usage is above 90%")
    
    return issues

def run_health_monitor():
    """Main monitoring loop"""
    print("System Health Monitor started")
    print(f"Monitoring service: bank-converter.service")
    
    last_alert_time = {}
    alert_cooldown = 3600  # 1 hour cooldown between same alerts
    
    while True:
        try:
            issues = check_system_health()
            
            if issues:
                current_time = time.time()
                
                for issue in issues:
                    # Check cooldown
                    if issue not in last_alert_time or \
                       (current_time - last_alert_time[issue]) > alert_cooldown:
                        
                        print(f"Issue detected: {issue}")
                        send_alert(issue, f"System health check failed: {issue}")
                        last_alert_time[issue] = current_time
                    else:
                        print(f"Issue detected but in cooldown: {issue}")
            else:
                print(f"Health check passed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"Error in health monitor: {e}")
        
        # Check every 5 minutes
        time.sleep(300)

if __name__ == '__main__':
    run_health_monitor()

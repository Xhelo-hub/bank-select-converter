"""
Email Utility Module
====================
Provides email sending functionality for password reset and admin notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

def load_email_config():
    """Load email configuration from database or environment variables"""
    try:
        from models import db, EmailConfig
        config = db.session.get(EmailConfig, 1)
        if config and config.enabled:
            return {
                'smtp_server': config.smtp_server,
                'smtp_port': config.smtp_port,
                'smtp_username': config.smtp_username,
                'smtp_password': config.smtp_password,
                'from_email': config.from_email,
                'enabled': True
            }
    except Exception as e:
        print(f"Error loading email config from database: {e}")

    # Fallback to environment variables
    return {
        'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
        'smtp_username': os.environ.get('SMTP_USERNAME', ''),
        'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
        'from_email': os.environ.get('FROM_EMAIL', os.environ.get('SMTP_USERNAME', '')),
        'enabled': True
    }

def _get_config():
    """Get current email configuration (loads fresh each time)"""
    config = load_email_config()
    return (
        config['smtp_server'],
        config['smtp_port'],
        config['smtp_username'],
        config['smtp_password'],
        config['from_email']
    )

def send_email(to_email, subject, html_body, text_body=None):
    """
    Send an email

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML content of the email
        text_body: Plain text fallback (optional)

    Returns:
        tuple: (success, message)
    """
    # Get current config
    SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL = _get_config()

    # Check if email is configured
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("Warning: Email not configured. Email would have been sent to:", to_email)
        print("Subject:", subject)
        print("Body:", html_body)
        return True, "Email configuration not set (simulated send)"

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email

        # Add text and HTML parts
        if text_body:
            text_part = MIMEText(text_body, 'plain')
            msg.attach(text_part)

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return True, "Email sent successfully"

    except Exception as e:
        print(f"Error sending email: {e}")
        return False, f"Failed to send email: {str(e)}"

def send_password_reset_email(to_email, reset_code):
    """Send password reset email with code"""
    subject = "Password Reset Code - Albanian Bank Converter"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; }}
            .code {{ 
                font-size: 32px; 
                font-weight: bold; 
                color: #3498db; 
                text-align: center; 
                padding: 20px; 
                background-color: #fff; 
                border: 2px dashed #3498db; 
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You have requested to reset your password for Albanian Bank Statement Converter.</p>
                <p>Your password reset code is:</p>
                <div class="code">{reset_code}</div>
                <p>This code will expire in <strong>30 minutes</strong>.</p>
                <p>If you did not request this password reset, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>Albanian Bank Statement Converter</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Password Reset Request
    
    You have requested to reset your password for Albanian Bank Statement Converter.
    
    Your password reset code is: {reset_code}
    
    This code will expire in 30 minutes.
    
    If you did not request this password reset, please ignore this email.
    """
    
    return send_email(to_email, subject, html_body, text_body)

def send_admin_removal_verification(to_email, verification_code, remover_email):
    """Send verification code for admin privilege removal"""
    subject = "Admin Privilege Removal Verification - Albanian Bank Converter"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; }}
            .code {{ 
                font-size: 32px; 
                font-weight: bold; 
                color: #e74c3c; 
                text-align: center; 
                padding: 20px; 
                background-color: #fff; 
                border: 2px dashed #e74c3c; 
                margin: 20px 0;
            }}
            .warning {{ 
                background-color: #fff3cd; 
                border-left: 4px solid #ffc107; 
                padding: 15px; 
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Admin Privilege Removal</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <div class="warning">
                    <strong>Important:</strong> Admin <strong>{remover_email}</strong> has requested to remove your admin privileges.
                </div>
                <p>To confirm this action, please provide the following verification code:</p>
                <div class="code">{verification_code}</div>
                <p>This code will expire in <strong>15 minutes</strong>.</p>
                <p><strong>Note:</strong> After your admin privileges are removed, you will still have access to the converter as a regular user.</p>
                <p>If you did not authorize this action, please contact the system administrator immediately.</p>
            </div>
            <div class="footer">
                <p>Albanian Bank Statement Converter</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Admin Privilege Removal Verification
    
    Admin {remover_email} has requested to remove your admin privileges.
    
    To confirm this action, please provide the following verification code:
    
    {verification_code}
    
    This code will expire in 15 minutes.
    
    Note: After your admin privileges are removed, you will still have access to the converter as a regular user.
    
    If you did not authorize this action, please contact the system administrator immediately.
    """
    
    return send_email(to_email, subject, html_body, text_body)

def send_admin_promotion_notification(to_email, promoter_email):
    """Send notification when user is promoted to admin"""
    subject = "You've Been Promoted to Admin - Albanian Bank Converter"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Admin Privileges Granted</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>Congratulations! Admin <strong>{promoter_email}</strong> has granted you administrator privileges.</p>
                <p><strong>As an admin, you can now:</strong></p>
                <ul>
                    <li>Approve or reject new user registrations</li>
                    <li>Promote other users to admin</li>
                    <li>Remove admin privileges from other admins</li>
                    <li>Manage all system users</li>
                </ul>
                <p>Please log in to access the admin dashboard.</p>
            </div>
            <div class="footer">
                <p>Albanian Bank Statement Converter</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Admin Privileges Granted
    
    Congratulations! Admin {promoter_email} has granted you administrator privileges.
    
    As an admin, you can now:
    - Approve or reject new user registrations
    - Promote other users to admin
    - Remove admin privileges from other admins
    - Manage all system users
    
    Please log in to access the admin dashboard.
    """
    
    return send_email(to_email, subject, html_body, text_body)

def send_system_recovery_notification(admin_emails, recovery_type):
    """Send notification when system recovers from an issue"""
    from datetime import datetime
    
    subject = "✅ System Recovered - Albanian Bank Converter"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; }}
            .success-box {{ 
                background-color: #d4edda; 
                border-left: 4px solid #27ae60; 
                padding: 15px; 
                margin: 20px 0;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ System Recovered</h1>
            </div>
            <div class="content">
                <div class="success-box">
                    <h2>Good News!</h2>
                    <p><strong>Recovery Type:</strong> {recovery_type}</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                    <p>The system has automatically recovered and is now operating normally.</p>
                </div>
                <p>The Albanian Bank Statement Converter is back online and processing conversions.</p>
                <p>No action is required at this time.</p>
            </div>
            <div class="footer">
                <p>Albanian Bank Statement Converter - System Health Monitor</p>
                <p>This is an automated notification, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    System Recovered
    
    Recovery Type: {recovery_type}
    Time: {timestamp}
    
    The system has automatically recovered and is now operating normally.
    The Albanian Bank Statement Converter is back online and processing conversions.
    
    No action is required at this time.
    """
    
    # Send to all admins
    for admin_email in admin_emails:
        try:
            send_email(admin_email, subject, html_body, text_body)
        except Exception as e:
            print(f"Error sending recovery notification to {admin_email}: {e}")

def send_new_user_registration_notification(admin_emails, user_email, user_name):
    """Send notification to admins when a new user registers"""
    from datetime import datetime
    
    subject = "🔔 New User Registration - Albanian Bank Converter"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; }}
            .info-box {{ 
                background-color: #fff; 
                border: 1px solid #ddd; 
                padding: 15px; 
                margin: 20px 0;
                border-radius: 5px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 5px;
            }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>New User Registration</h1>
            </div>
            <div class="content">
                <p>A new user has registered and is awaiting approval:</p>
                <div class="info-box">
                    <p><strong>Name:</strong> {user_name}</p>
                    <p><strong>Email:</strong> {user_email}</p>
                    <p><strong>Registration Time:</strong> {timestamp}</p>
                </div>
                <p style="text-align: center;">
                    <a href="https://c.konsulence.al/admin" class="button">Review in Admin Panel</a>
                </p>
                <p>Please review and approve or reject this registration from the admin dashboard.</p>
            </div>
            <div class="footer">
                <p>Albanian Bank Statement Converter</p>
                <p>This is an automated notification, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    New User Registration
    
    A new user has registered and is awaiting approval:
    
    Name: {user_name}
    Email: {user_email}
    Registration Time: {timestamp}
    
    Please review and approve or reject this registration from the admin dashboard:
    https://c.konsulence.al/admin
    """
    
    # Send to all admins
    for admin_email in admin_emails:
        try:
            send_email(admin_email, subject, html_body, text_body)
        except Exception as e:
            print(f"Error sending registration notification to {admin_email}: {e}")


def send_notification_email(to_email, title, message, notification_type):
    """
    Send notification email with styled HTML
    
    Args:
        to_email: Recipient email address
        title: Notification title
        message: Notification message
        notification_type: Type (info, warning, important, success)
    
    Returns:
        tuple: (success, message)
    """
    # Color scheme based on notification type
    type_colors = {
        'info': {'primary': '#3b82f6', 'light': '#eff6ff', 'icon': 'fa-info-circle'},
        'warning': {'primary': '#f59e0b', 'light': '#fffbeb', 'icon': 'fa-exclamation-triangle'},
        'important': {'primary': '#ef4444', 'light': '#fef2f2', 'icon': 'fa-exclamation-circle'},
        'success': {'primary': '#10b981', 'light': '#ecfdf5', 'icon': 'fa-check-circle'}
    }
    
    colors = type_colors.get(notification_type, type_colors['info'])
    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    subject = f"Notification: {title}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ 
                background: {colors['primary']}; 
                color: white; 
                padding: 30px 20px; 
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
            .content {{ 
                background: white; 
                padding: 30px; 
                border: 1px solid #e5e7eb;
                border-top: none;
            }}
            .notification-box {{
                background: {colors['light']};
                border-left: 4px solid {colors['primary']};
                padding: 20px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .notification-title {{
                font-size: 20px;
                font-weight: 700;
                color: {colors['primary']};
                margin-bottom: 12px;
            }}
            .notification-message {{
                font-size: 15px;
                color: #374151;
                line-height: 1.6;
                white-space: pre-wrap;
            }}
            .timestamp {{
                color: #6b7280;
                font-size: 13px;
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid #e5e7eb;
            }}
            .button {{
                display: inline-block;
                background: {colors['primary']};
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #6b7280;
                font-size: 12px;
                border-top: 1px solid #e5e7eb;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📬 System Notification</h1>
            </div>
            <div class="content">
                <div class="notification-box">
                    <div class="notification-title">{title}</div>
                    <div class="notification-message">{message}</div>
                    <div class="timestamp">
                        <strong>Sent:</strong> {timestamp}
                    </div>
                </div>
                <p style="text-align: center;">
                    <a href="https://c.konsulence.al" class="button">Open Converter</a>
                </p>
            </div>
            <div class="footer">
                <p>Albanian Bank Statement Converter</p>
                <p>This is an automated notification, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    System Notification
    
    {title}
    
    {message}
    
    Sent: {timestamp}
    
    ---
    Albanian Bank Statement Converter
    https://c.konsulence.al
    """
    
    return send_email(to_email, subject, html_body, text_body)


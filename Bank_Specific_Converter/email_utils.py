"""
Email Utility Module
====================
Provides email sending functionality for password reset and admin notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Email configuration (load from environment variables)
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', SMTP_USERNAME)

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

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
from functools import wraps
from auth import UserManager
from models import db, User, Conversion, Download, EmailConfig, ContactMessage, MarketingMessage
from email_utils import send_admin_promotion_notification, send_admin_removal_verification, send_notification_email
from notification_utils import (
    create_notification, get_all_notifications, delete_notification,
    get_user_notifications, get_unread_count
)
from werkzeug.utils import secure_filename
from PIL import Image
import subprocess
import os
import signal
import json
import smtplib
import re
from email.mime.text import MIMEText
from collections import defaultdict
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
user_manager = UserManager()


def _read_marketing_file(content_file):
    """Read marketing content from file for migration fallback."""
    if not os.path.exists(content_file):
        return None, None
    try:
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            return None, None
        if '<!-- SIMPLE_MODE -->' in content:
            title_match = re.search(r'<h2>(.*?)</h2>', content, re.DOTALL)
            body_match = re.search(r'<p>(.*?)</p>', content, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ''
            body = body_match.group(1).strip() if body_match else ''
            if title or body:
                return title, body
            return None, None
        return '', content
    except Exception:
        return None, None


def _get_latest_marketing_message():
    """Get latest active marketing message, migrating from file if needed."""
    latest = (MarketingMessage.query
              .filter_by(is_active=True)
              .order_by(MarketingMessage.created_at.desc())
              .first())
    if latest:
        return latest

    app_dir = os.path.dirname(os.path.abspath(__file__))
    content_file = os.path.join(app_dir, 'templates', 'marketing_content.html')
    title, body = _read_marketing_file(content_file)
    if title is None and body is None:
        return None

    migrated = MarketingMessage(
        title=title or '',
        content=body or '',
        image_url=None,
        link_url=None,
        link_text=None,
        is_active=True,
        display_order=0,
        created_at=datetime.now().isoformat(),
        created_by='file-migration'
    )
    db.session.add(migrated)
    db.session.commit()
    return migrated

def load_stats():
    """Load conversion and download stats from database"""
    try:
        total_conversions = db.session.query(db.func.count(Conversion.id)).scalar() or 0
        total_downloads = db.session.query(db.func.count(Download.id)).scalar() or 0

        # Get all conversions and downloads for detailed stats
        conversions = Conversion.query.all()
        downloads = Download.query.all()

        return {
            "total_conversions": total_conversions,
            "total_downloads": total_downloads,
            "conversions": [{"user_email": c.user_email, "bank": c.bank or "Unknown"} for c in conversions],
            "downloads": [{"user_email": d.user_email} for d in downloads]
        }
    except Exception as e:
        print(f"Error loading stats: {e}")
        return {"total_conversions": 0, "total_downloads": 0, "conversions": [], "downloads": []}

def load_email_config():
    """Load email configuration from database"""
    try:
        config = db.session.get(EmailConfig, 1)
        if config:
            return {
                'smtp_server': config.smtp_server,
                'smtp_port': config.smtp_port,
                'smtp_username': config.smtp_username,
                'smtp_password': config.smtp_password,
                'from_email': config.from_email,
                'enabled': config.enabled,
                'test_email': config.test_email or ''
            }
    except Exception as e:
        print(f"Error loading email config: {e}")

    # Return defaults
    return {
        'smtp_server': 'smtp.office365.com',
        'smtp_port': 587,
        'smtp_username': '',
        'smtp_password': '',
        'from_email': '',
        'enabled': False,
        'test_email': ''
    }

def save_email_config(config):
    """Save email configuration to database"""
    try:
        email_config = db.session.get(EmailConfig, 1)
        if not email_config:
            email_config = EmailConfig(id=1)
            db.session.add(email_config)

        email_config.smtp_server = config['smtp_server']
        email_config.smtp_port = config['smtp_port']
        email_config.smtp_username = config['smtp_username']
        email_config.smtp_password = config['smtp_password']
        email_config.from_email = config['from_email']
        email_config.enabled = config['enabled']
        email_config.test_email = config.get('test_email', '')

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard for managing users"""
    pending_users = user_manager.get_pending_users()
    all_users = user_manager.get_all_users()

    # Load conversion/download stats
    stats = load_stats()
    total_conversions = stats.get("total_conversions", 0)
    total_downloads = stats.get("total_downloads", 0)

    # Per-user aggregates
    user_stats = defaultdict(lambda: {"conversions": 0, "downloads": 0})
    for c in stats.get("conversions", []):
        user_stats[c["user_email"]]["conversions"] += 1
    for d in stats.get("downloads", []):
        user_stats[d["user_email"]]["downloads"] += 1
    user_stats = dict(user_stats)

    # Per-bank counts
    bank_stats = defaultdict(int)
    for c in stats.get("conversions", []):
        bank_stats[c.get("bank", "Unknown")] += 1
    bank_stats = dict(sorted(bank_stats.items(), key=lambda x: x[1], reverse=True))

    return render_template('admin_dashboard.html',
                         pending_users=pending_users,
                         all_users=all_users,
                         pending_count=len(pending_users),
                         total_users=len(all_users),
                         total_conversions=total_conversions,
                         total_downloads=total_downloads,
                         user_stats=user_stats,
                         bank_stats=bank_stats)

@admin_bp.route('/approve/<user_id>')
@login_required
@admin_required
def approve_user(user_id):
    """Approve a pending user"""
    success, message = user_manager.approve_user(user_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject/<user_id>')
@login_required
@admin_required
def reject_user(user_id):
    """Reject a pending user (deletes them)"""
    success = user_manager.reject_user(user_id)
    
    if success:
        flash('User rejected and removed', 'success')
    else:
        flash('Failed to reject user', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/promote/<user_id>')
@login_required
@admin_required
def promote_user(user_id):
    """Promote a user to admin"""
    # Get user to promote
    users = user_manager.get_all_users()
    user_to_promote = None
    for user in users:
        if user.id == user_id:
            user_to_promote = user
            break
    
    if not user_to_promote:
        flash('User not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Check if already admin
    if user_to_promote.is_admin:
        flash('User is already an admin', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Promote user
    success, message = user_manager.promote_to_admin(user_id)
    
    if success:
        # Send notification email
        send_admin_promotion_notification(user_to_promote.email, current_user.email)
        flash(f'{user_to_promote.email} has been promoted to admin', 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/demote/<user_id>')
@login_required
@admin_required
def demote_user(user_id):
    """Demote an admin to regular user (direct demotion without verification)"""
    # Get user to demote
    users = user_manager.get_all_users()
    user_to_demote = None
    for user in users:
        if user.id == user_id:
            user_to_demote = user
            break
    
    if not user_to_demote:
        flash('User not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Prevent self-demotion
    if user_to_demote.id == current_user.id:
        flash('You cannot demote yourself. Another admin must demote you.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Check if user is actually an admin
    if not user_to_demote.is_admin:
        flash('User is not an admin', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Demote user directly
    success, message = user_manager.demote_from_admin(user_id)
    if success:
        flash(f'{user_to_demote.email} has been demoted to regular user', 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/activate/<user_id>')
@login_required
@admin_required
def activate_user(user_id):
    """Activate a user account"""
    success, message = user_manager.activate_user(user_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/deactivate/<user_id>')
@login_required
@admin_required
def deactivate_user(user_id):
    """Deactivate a user account"""
    # Prevent self-deactivation
    if user_id == current_user.id:
        flash('You cannot deactivate yourself', 'error')
        return redirect(url_for('admin.dashboard'))
    
    success, message = user_manager.deactivate_user(user_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete/<user_id>')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user permanently"""
    # Prevent self-deletion
    if user_id == current_user.id:
        flash('You cannot delete yourself', 'error')
        return redirect(url_for('admin.dashboard'))
    
    success, message = user_manager.delete_user(user_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reset-password/<user_id>', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """Admin reset user password"""
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not new_password:
        flash('Password is required', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if new_password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('admin.dashboard'))
    
    success, message = user_manager.admin_reset_password(user_id, new_password)
    
    if success:
        flash(f'Password reset successfully for user', 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/upload-logo', methods=['POST'])
@login_required
@admin_required
def upload_logo():
    """Upload custom logo for the application"""
    try:
        if 'logo' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin.dashboard'))
        
        file = request.files['logo']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'svg'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            flash('Invalid file type. Please upload PNG, JPG, or SVG', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Get the static directory path
        app_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(app_dir, 'static')
        os.makedirs(static_dir, exist_ok=True)
        
        logo_path = os.path.join(static_dir, 'logo.png')
        
        # For SVG files, save directly
        if file_ext == 'svg':
            svg_path = os.path.join(static_dir, 'logo.svg')
            file.save(svg_path)
            # Also create a note that SVG is being used
            with open(os.path.join(static_dir, 'logo_type.txt'), 'w') as f:
                f.write('svg')
            flash('SVG logo uploaded successfully!', 'success')
        else:
            # For raster images, resize to 80x80
            img = Image.open(file.stream)
            
            # Convert RGBA to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize maintaining aspect ratio
            img.thumbnail((80, 80), Image.Resampling.LANCZOS)
            
            # Create a new 80x80 image with white background
            final_img = Image.new('RGB', (80, 80), (255, 255, 255))
            
            # Center the resized image
            offset = ((80 - img.size[0]) // 2, (80 - img.size[1]) // 2)
            final_img.paste(img, offset)
            
            # Save as PNG
            final_img.save(logo_path, 'PNG', optimize=True)
            
            with open(os.path.join(static_dir, 'logo_type.txt'), 'w') as f:
                f.write('png')
            
            flash('Logo uploaded and resized to 80x80 pixels successfully!', 'success')
        
    except Exception as e:
        flash(f'Failed to upload logo: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete-logo', methods=['POST'])
@login_required
@admin_required
def delete_logo():
    """Delete custom logo and revert to placeholder"""
    try:
        app_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(app_dir, 'static')
        
        # Remove logo files
        for filename in ['logo.png', 'logo.svg', 'logo_type.txt']:
            file_path = os.path.join(static_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        flash('Logo deleted successfully! Reverted to default placeholder.', 'success')
        
    except Exception as e:
        flash(f'Failed to delete logo: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/restart-server', methods=['POST'])
@login_required
@admin_required
def restart_server():
    """Restart the Flask application using systemd service"""
    try:
        import time
        
        # Try to restart using systemd service (production)
        # Use full path to systemctl (running as root, no sudo needed)
        result = subprocess.run(
            ['/bin/systemctl', 'restart', 'bank-converter.service'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            time.sleep(2)  # Give service time to restart
            flash('Server restarted successfully via systemd! Please refresh the page in a few seconds.', 'success')
        else:
            # If systemd fails, try the old manual method (fallback for non-systemd environments)
            app_dir = os.path.dirname(os.path.abspath(__file__))
            pid_file = os.path.join(app_dir, 'gunicorn.pid')
            
            # Check if gunicorn is running and kill it
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Kill the gunicorn master process (will kill workers too)
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(2)  # Wait for processes to terminate
                except (ProcessLookupError, ValueError):
                    pass
            
            # Also try to kill any remaining gunicorn processes
            try:
                subprocess.run(['pkill', '-f', 'gunicorn.*wsgi:application'], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
                time.sleep(1)
            except:
                pass
            
            # Start gunicorn with the simple config
            venv_path = os.path.join(os.path.dirname(app_dir), '.venv', 'bin', 'activate')
            gunicorn_cmd = f"cd {app_dir} && source {venv_path} && gunicorn --config gunicorn_simple.conf.py wsgi:application"
            
            # Execute the command in background
            process = subprocess.Popen(
                gunicorn_cmd,
                shell=True,
                executable='/bin/bash',
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new session to detach from parent
            )
            
            time.sleep(1)  # Give it time to start
            flash('Server restart initiated successfully (manual mode)! Please refresh the page in a few seconds.', 'success')
        
    except Exception as e:
        flash(f'Failed to restart server: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/email-settings')
@login_required
@admin_required
def email_settings():
    """Email configuration page"""
    config = load_email_config()
    return render_template('email_settings.html', config=config)

@admin_bp.route('/email-settings/save', methods=['POST'])
@login_required
@admin_required
def save_email_settings():
    """Save email configuration"""
    try:
        config = {
            'smtp_server': request.form.get('smtp_server', '').strip(),
            'smtp_port': int(request.form.get('smtp_port', 587)),
            'smtp_username': request.form.get('smtp_username', '').strip(),
            'smtp_password': request.form.get('smtp_password', '').strip(),
            'from_email': request.form.get('from_email', '').strip(),
            'enabled': request.form.get('enabled') == 'on',
            'test_email': request.form.get('test_email', '').strip()
        }
        
        # Don't overwrite password if it's the placeholder
        if config['smtp_password'] == '••••••••':
            old_config = load_email_config()
            config['smtp_password'] = old_config.get('smtp_password', '')
        
        save_email_config(config)
        
        # Update environment variables for the current process
        os.environ['SMTP_SERVER'] = config['smtp_server']
        os.environ['SMTP_PORT'] = str(config['smtp_port'])
        os.environ['SMTP_USERNAME'] = config['smtp_username']
        os.environ['SMTP_PASSWORD'] = config['smtp_password']
        os.environ['FROM_EMAIL'] = config['from_email']
        
        flash('Email settings saved successfully! Note: Restart the server for changes to take full effect.', 'success')
        return redirect(url_for('admin.email_settings'))
    except Exception as e:
        flash(f'Failed to save email settings: {str(e)}', 'error')
        return redirect(url_for('admin.email_settings'))

@admin_bp.route('/email-settings/test', methods=['POST'])
@login_required
@admin_required
def test_email_settings():
    """Test email configuration by sending a test email"""
    try:
        config = load_email_config()
        test_email = request.form.get('test_email', '').strip()
        
        if not test_email:
            return jsonify({'success': False, 'message': 'Please enter a test email address'})
        
        if not config.get('smtp_username') or not config.get('smtp_password'):
            return jsonify({'success': False, 'message': 'SMTP credentials are not configured'})
        
        # Test SMTP connection
        try:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['smtp_username'], config['smtp_password'])
            
            # Send test email
            msg = MIMEText('This is a test email from the Bank Statement Converter admin panel. If you received this, your email configuration is working correctly!')
            msg['Subject'] = 'Test Email - Bank Statement Converter'
            msg['From'] = config['from_email']
            msg['To'] = test_email
            
            server.send_message(msg)
            server.quit()
            
            return jsonify({'success': True, 'message': f'Test email sent successfully to {test_email}'})
        except smtplib.SMTPAuthenticationError as e:
            return jsonify({'success': False, 'message': f'Authentication failed: {str(e)}. Please check your credentials and ensure SMTP AUTH is enabled.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Failed to send email: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# ============ Notification Management Routes ============

@admin_bp.route('/notifications/send', methods=['POST'])
@login_required
@admin_required
def send_notification():
    """Send a notification to users"""
    try:
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        notification_type = request.form.get('type', 'info')
        recipient_type = request.form.get('recipient_type', 'all')
        send_email_notification = request.form.get('send_email') == 'true'
        
        # Validation
        if not title or not message:
            flash('Title and message are required', 'error')
            return redirect(url_for('admin.dashboard'))
        
        if len(title) > 100:
            flash('Title must be 100 characters or less', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Determine recipients
        if recipient_type == 'all':
            recipients = ['all']
            recipient_count = len(user_manager.get_all_users())
        else:
            recipients = request.form.getlist('recipients[]')
            if not recipients:
                flash('Please select at least one recipient', 'error')
                return redirect(url_for('admin.dashboard'))
            recipient_count = len(recipients)
        
        # Create notification
        notification_id = create_notification(
            title=title,
            message=message,
            notification_type=notification_type,
            recipients=recipients,
            send_email=send_email_notification,
            created_by=current_user.email
        )
        
        # Send email notifications if requested
        email_sent_count = 0
        if send_email_notification:
            if recipient_type == 'all':
                all_users = user_manager.get_all_users()
                recipient_emails = [user.email for user in all_users if user.is_approved and user.is_active]
            else:
                recipient_emails = recipients
            
            for email in recipient_emails:
                try:
                    success, msg = send_notification_email(email, title, message, notification_type)
                    if success:
                        email_sent_count += 1
                except Exception as e:
                    print(f"Error sending notification email to {email}: {e}")
        
        # Success message
        if send_email_notification:
            flash(f'Notification sent to {recipient_count} user(s). Email sent to {email_sent_count} recipient(s).', 'success')
        else:
            flash(f'Notification sent to {recipient_count} user(s).', 'success')
        
        return redirect(url_for('admin.dashboard'))
        
    except Exception as e:
        flash(f'Error sending notification: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/notifications/list')
@login_required
@admin_required
def list_all_notifications():
    """Get all notifications for admin view (JSON)"""
    try:
        notifications = get_all_notifications()
        return jsonify({'success': True, 'notifications': notifications})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route('/notifications/delete/<notification_id>', methods=['POST'])
@login_required
@admin_required
def delete_notification_route(notification_id):
    """Delete a notification"""
    try:
        success = delete_notification(notification_id)
        if success:
            flash('Notification deleted successfully', 'success')
        else:
            flash('Notification not found', 'error')
    except Exception as e:
        flash(f'Error deleting notification: {str(e)}', 'error')

    return redirect(url_for('admin.dashboard'))


# ============ Marketing Content Management (Simple HTML Editor) ============

@admin_bp.route('/marketing-content')
@login_required
@admin_required
def marketing_content():
    """Marketing content editor page"""
    import sys
    sys.stdout.flush()  # Force flush before any output

    # Get the current content from database (with file migration fallback)
    print("\n" + "="*60, flush=True)
    print("[DEBUG] Loading marketing content...", flush=True)
    print("="*60 + "\n", flush=True)

    # Default values
    mode = 'simple'
    title = ''
    simple_content = ''
    html_content = ''

    try:
        latest = _get_latest_marketing_message()
        if latest:
            title = latest.title or ''
            stored_content = latest.content or ''
            if title or (stored_content and '<div' not in stored_content):
                mode = 'simple'
                simple_content = stored_content
            else:
                mode = 'html'
                html_content = stored_content
    except Exception as e:
        print(f"[ERROR] Error reading database: {str(e)}", flush=True)
        flash(f'Gabim në leximin e përmbajtjes: {str(e)}', 'error')

    print(f"[DEBUG] Returning mode={mode}, title={title}, content_len={len(simple_content)}", flush=True)

    return render_template('marketing_content_editor.html',
                         mode=mode,
                         title=title,
                         simple_content=simple_content,
                         html_content=html_content)


@admin_bp.route('/marketing-content/save', methods=['POST'])
@login_required
@admin_required
def save_marketing_content():
    """Save marketing content to file"""
    import sys
    sys.stdout.flush()  # Force flush before any output

    try:
        mode = request.form.get('mode', 'simple')

        # Debug logging
        print("\n" + "="*60, flush=True)
        print("[DEBUG] Saving marketing content...", flush=True)
        print(f"[DEBUG] Mode: {mode}", flush=True)
        print(f"[DEBUG] Mode: {mode}", flush=True)

        if mode == 'simple':
            # Simple mode - build HTML from title and content
            title = request.form.get('title', '').strip()
            simple_content = request.form.get('simple_content', '').strip()

            print(f"[DEBUG] Title: {title}", flush=True)
            print(f"[DEBUG] Content: {simple_content[:100] if simple_content else 'empty'}", flush=True)

            if not title and not simple_content:
                MarketingMessage.query.update({'is_active': False})
                db.session.commit()
                flash('Përmbajtja u fshi - do të shfaqet default content.', 'success')
                return redirect(url_for('admin.marketing_content'))

            MarketingMessage.query.update({'is_active': False})
            msg = MarketingMessage(
                title=title,
                content=simple_content,
                image_url=None,
                link_url=None,
                link_text=None,
                is_active=True,
                display_order=0,
                created_at=datetime.now().isoformat(),
                created_by=current_user.email
            )
            db.session.add(msg)
            db.session.commit()

        else:
            # HTML mode - save as-is
            html_content = request.form.get('html_content', '').strip()

            print(f"[DEBUG] HTML content length: {len(html_content)}", flush=True)

            if not html_content:
                MarketingMessage.query.update({'is_active': False})
                db.session.commit()
                flash('Përmbajtja u fshi - do të shfaqet default content.', 'success')
                return redirect(url_for('admin.marketing_content'))

            MarketingMessage.query.update({'is_active': False})
            msg = MarketingMessage(
                title='',
                content=html_content,
                image_url=None,
                link_url=None,
                link_text=None,
                is_active=True,
                display_order=0,
                created_at=datetime.now().isoformat(),
                created_by=current_user.email
            )
            db.session.add(msg)
            db.session.commit()

        print("="*60 + "\n", flush=True)
        flash('Përmbajtja u ruajt me sukses në database.', 'success')
        return redirect(url_for('admin.marketing_content'))

    except Exception as e:
        print(f"[ERROR] Exception during save: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        flash(f'Gabim në ruajtjen e përmbajtjes: {str(e)}', 'error')
        return redirect(url_for('admin.marketing_content'))


# ============ User Contact Messages ============

@admin_bp.route('/user-messages')
@login_required
@admin_required
def user_messages():
    """Get all user contact messages (JSON)"""
    try:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return jsonify({
            'success': True,
            'messages': [m.to_dict() for m in messages],
            'unread_count': ContactMessage.query.filter_by(is_read=False).count()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/user-messages/mark-read/<message_id>', methods=['POST'])
@login_required
@admin_required
def mark_message_read(message_id):
    """Mark a user message as read"""
    try:
        msg = db.session.get(ContactMessage, message_id)
        if msg:
            msg.is_read = True
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Mesazhi nuk u gjet'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/user-messages/reply/<message_id>', methods=['POST'])
@login_required
@admin_required
def reply_to_message(message_id):
    """Reply to a user message by sending them a notification"""
    try:
        msg = db.session.get(ContactMessage, message_id)
        if not msg:
            return jsonify({'success': False, 'message': 'Mesazhi nuk u gjet'})

        reply_text = request.json.get('reply', '').strip() if request.is_json else request.form.get('reply', '').strip()
        if not reply_text:
            return jsonify({'success': False, 'message': 'Përgjigjja nuk mund të jetë bosh'})

        # Mark the original message as read
        msg.is_read = True
        db.session.commit()

        # Send a notification to the user
        from notification_utils import create_notification
        create_notification(
            title=f'Përgjigje: {msg.subject}',
            message=reply_text,
            notification_type='info',
            recipients=[msg.user_email],
            send_email=False,
            created_by=current_user.email
        )

        return jsonify({'success': True, 'message': 'Përgjigja u dërgua si njoftim'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


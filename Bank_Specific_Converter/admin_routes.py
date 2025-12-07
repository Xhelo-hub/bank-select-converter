from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
from functools import wraps
from auth import UserManager
from email_utils import send_admin_promotion_notification, send_admin_removal_verification
from werkzeug.utils import secure_filename
from PIL import Image
import subprocess
import os
import signal
import json
import smtplib
from email.mime.text import MIMEText

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
user_manager = UserManager()

def get_email_config_path():
    """Get the path to email configuration file"""
    return os.path.join(os.path.dirname(__file__), 'email_config.json')

def load_email_config():
    """Load email configuration from JSON file"""
    config_path = get_email_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            pass
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
    """Save email configuration to JSON file"""
    config_path = get_email_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

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
    
    return render_template('admin_dashboard.html',
                         pending_users=pending_users,
                         all_users=all_users,
                         pending_count=len(pending_users),
                         total_users=len(all_users))

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

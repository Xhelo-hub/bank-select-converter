from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from functools import wraps
from auth import UserManager
from email_utils import send_admin_promotion_notification, send_admin_removal_verification
from werkzeug.utils import secure_filename
from PIL import Image
import subprocess
import os
import signal

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
user_manager = UserManager()

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
    """Restart the Flask application using gunicorn"""
    try:
        # Get the path to the PID file
        app_dir = os.path.dirname(os.path.abspath(__file__))
        pid_file = os.path.join(app_dir, 'gunicorn.pid')
        
        # Check if gunicorn is running
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Kill the gunicorn master process (will kill workers too)
                os.kill(pid, signal.SIGTERM)
                flash('Server stopped. Starting new instance...', 'info')
            except (ProcessLookupError, ValueError):
                flash('Old process not found. Starting new instance...', 'info')
        
        # Start gunicorn with the simple config
        venv_path = os.path.join(os.path.dirname(app_dir), '.venv', 'bin', 'activate')
        gunicorn_cmd = f"cd {app_dir} && source {venv_path} && gunicorn --config gunicorn_simple.conf.py wsgi:application"
        
        # Execute the command
        subprocess.Popen(
            gunicorn_cmd,
            shell=True,
            executable='/bin/bash',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        flash('Server restart initiated successfully! Please refresh the page in a few seconds.', 'success')
        
    except Exception as e:
        flash(f'Failed to restart server: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

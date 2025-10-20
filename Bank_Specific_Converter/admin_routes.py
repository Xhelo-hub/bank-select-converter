from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from functools import wraps
from auth import UserManager
from email_utils import send_admin_promotion_notification, send_admin_removal_verification

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

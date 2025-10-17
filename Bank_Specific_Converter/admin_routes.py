from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from auth import UserManager

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

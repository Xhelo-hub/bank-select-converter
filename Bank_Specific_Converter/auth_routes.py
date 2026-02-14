"""
Authentication Routes with Flask-Login Support
==============================================
Routes for login, logout, and registration
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from auth import UserManager
from models import User
from email_utils import send_password_reset_email, send_new_user_registration_notification
import os
import re

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize UserManager
user_manager = UserManager()

def get_marketing_content():
    """Read custom marketing content from file, returns (has_content, title, body) tuple"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    content_file = os.path.join(app_dir, 'templates', 'marketing_content.html')
    if os.path.exists(content_file):
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if not content:
                return False, '', ''
            # Parse simple mode content
            if '<!-- SIMPLE_MODE -->' in content:
                title_match = re.search(r'<h2>(.*?)</h2>', content, re.DOTALL)
                body_match = re.search(r'<p>(.*?)</p>', content, re.DOTALL)
                title = title_match.group(1).strip() if title_match else ''
                body = body_match.group(1).strip() if body_match else ''
                if title or body:
                    return True, title, body
                return False, '', ''
            # HTML mode - return raw content
            return True, '', content
        except Exception:
            return False, '', ''
    return False, '', ''

def _login_template_vars():
    """Build template variables for login page"""
    has_content, title, body = get_marketing_content()
    return {
        'has_marketing_content': has_content,
        'marketing_title': title,
        'marketing_body': body,
    }

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not email or not password:
            flash('Please provide both email and password', 'error')
            return render_template('login.html', **_login_template_vars())

        # Get user
        user = user_manager.get_user_by_email(email)
        if not user:
            flash('Invalid email or password', 'error')
            return render_template('login.html', **_login_template_vars())

        # Verify password
        if not user_manager.verify_password(user, password):
            flash('Invalid email or password', 'error')
            return render_template('login.html', **_login_template_vars())

        # Check if user is approved
        if not user.is_approved:
            flash('Your account is pending admin approval. Please wait for approval before logging in.', 'error')
            return render_template('login.html', **_login_template_vars())

        # Check if user is active
        if not user.is_active:
            flash('Your user is inactive. Contact customer service at kontakt@konsulence.al or +355692064518.', 'error')
            return render_template('login.html', **_login_template_vars())

        # Login user
        login_user(user, remember=remember)
        flash('Logged in successfully!', 'success')

        # Redirect to next page or home
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))

    return render_template('login.html', **_login_template_vars())

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not email or not password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return render_template('register.html')
        
        if len(password) < 12:
            flash('Password must be at least 12 characters long', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Create user
        user, message = user_manager.create_user(email, password)
        if not user:
            flash(message, 'error')
            return render_template('register.html')
        
        # Send notification to admins about new registration
        try:
            admin_emails = [u.email for u in User.query.filter_by(is_admin=True).all()]
            if admin_emails:
                send_new_user_registration_notification(admin_emails, email, email.split('@')[0])
        except Exception:
            pass
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset code"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Please provide your email address', 'error')
            return render_template('forgot_password.html')
        
        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return render_template('forgot_password.html')
        
        # Generate reset token
        token, message = user_manager.generate_reset_token(email)
        if token:
            # Send email
            success, email_message = send_password_reset_email(email, token)
            if success:
                # Store email in session for reset page
                session['reset_email'] = email
                flash('Password reset code has been sent to your email. Please check your inbox.', 'success')
                return redirect(url_for('auth.reset_password'))
            else:
                flash(f'Failed to send email: {email_message}', 'error')
                return render_template('forgot_password.html')
        else:
            # Don't reveal if user exists or not for security
            flash('If an account exists with this email, a reset code has been sent.', 'info')
            return render_template('forgot_password.html')
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password with code"""
    # Get email from session or query parameter
    email = session.get('reset_email') or request.args.get('email')
    
    if not email:
        flash('Please request a password reset first', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not code or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('reset_password.html', email=email)
        
        if len(code) != 6 or not code.isdigit():
            flash('Invalid reset code format. Code must be 6 digits.', 'error')
            return render_template('reset_password.html', email=email)
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('reset_password.html', email=email)
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', email=email)
        
        # Reset password
        success, message = user_manager.reset_password(email, code, new_password)
        if success:
            # Clear session
            session.pop('reset_email', None)
            flash('Password reset successfully! Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'error')
            return render_template('reset_password.html', email=email)
    
    return render_template('reset_password.html', email=email)

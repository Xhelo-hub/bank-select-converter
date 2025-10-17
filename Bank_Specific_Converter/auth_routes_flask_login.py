"""
Authentication Routes with Flask-Login Support
==============================================
Routes for login, logout, and registration
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from auth import UserManager
import re

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize UserManager
user_manager = UserManager()

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
            return render_template('login.html')
        
        # Get user
        user = user_manager.get_user_by_email(email)
        if not user:
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        # Verify password
        if not user_manager.verify_password(user, password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        # Login user
        login_user(user, remember=remember)
        flash('Logged in successfully!', 'success')
        
        # Redirect to next page or home
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))
    
    return render_template('login.html')

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
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Create user
        user, message = user_manager.create_user(email, password)
        if not user:
            flash(message, 'error')
            return render_template('register.html')
        
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

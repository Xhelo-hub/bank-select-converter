"""
Authentication Module for Bank Statement Converter
==================================================
Provides user authentication, registration, and session management
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash

# User database file
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

def hash_password(password):
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"

def verify_password(password, hashed):
    """Verify a password against its hash"""
    try:
        salt, pwd_hash = hashed.split('$')
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return test_hash == pwd_hash
    except:
        return False

def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def create_user(username, password, email='', is_admin=False):
    """Create a new user"""
    users = load_users()
    
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        'password': hash_password(password),
        'email': email,
        'is_admin': is_admin,
        'created_at': datetime.now().isoformat(),
        'last_login': None,
        'conversions_count': 0
    }
    
    save_users(users)
    return True, "User created successfully"

def authenticate_user(username, password):
    """Authenticate a user"""
    users = load_users()
    
    if username not in users:
        return False, "Invalid username or password"
    
    user = users[username]
    
    if not verify_password(password, user['password']):
        return False, "Invalid username or password"
    
    # Update last login
    user['last_login'] = datetime.now().isoformat()
    save_users(users)
    
    return True, user

def get_user(username):
    """Get user information"""
    users = load_users()
    return users.get(username)

def update_user_stats(username):
    """Increment user's conversion count"""
    users = load_users()
    if username in users:
        users[username]['conversions_count'] = users[username].get('conversions_count', 0) + 1
        save_users(users)

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = get_user(session['username'])
        if not user or not user.get('is_admin', False):
            flash('Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def initialize_default_admin():
    """Create default admin user if no users exist"""
    users = load_users()
    if not users:
        # Create default admin with password 'admin123' - CHANGE THIS!
        create_user('admin', 'admin123', 'admin@konsulence.al', is_admin=True)
        print("✅ Default admin user created: admin / admin123")
        print("⚠️  IMPORTANT: Change the default password immediately!")
        return True
    return False

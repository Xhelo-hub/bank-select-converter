#!/usr/bin/env python3
"""
Bank-Specific Converter Web Interface WITH AUTHENTICATION
=====================================
Uses individual bank converter scripts for accurate conversion
Includes user login/registration system
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file, jsonify, render_template, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import subprocess
import tempfile
import shutil
from datetime import datetime
import uuid

# Import authentication modules
from auth import User, UserManager, init_auth
from auth_routes import create_auth_routes

app = Flask(__name__)

# Load configuration
try:
    from config import config
    config_name = os.environ.get('FLASK_ENV', 'production')
    app.config.from_object(config[config_name])
except ImportError:
    # Fallback configuration if config.py is not available
    app.secret_key = os.environ.get('SECRET_KEY', 'bank-specific-converter-key-change-this-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Initialize authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access the converter.'
login_manager.login_message_category = 'info'

user_manager = UserManager()

@login_manager.user_loader
def load_user(user_id):
    return user_manager.get_user_by_id(user_id)

# Register authentication routes
auth_blueprint = create_auth_routes(user_manager)
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# Configuration - Use simple import/export folders
UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'import')
CONVERTED_FOLDER = app.config.get('CONVERTED_FOLDER', 'export')
MAX_FILE_SIZE = app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Bank configurations with their corresponding scripts
# Scripts directory - flexible for both development and production
SCRIPTS_DIR = app.config.get('SCRIPTS_DIR', os.path.join(os.path.dirname(__file__), '..'))

def get_script_path(script_name):
    """Get script path, checking multiple possible locations"""
    possible_paths = [
        os.path.join(SCRIPTS_DIR, script_name),  # Parent directory
        os.path.join(os.path.dirname(__file__), script_name),  # Same directory
        os.path.join(os.path.dirname(__file__), 'converter_scripts', script_name),  # Subdirectory
        script_name  # Current directory
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return script_name  # Fallback to script name

BANK_CONFIGS = {
    'BKT': {
        'name': 'BKT Bank',
        'script': 'BKT-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'BKT Bank statements (PDF and CSV formats)'
    },
    'OTP': {
        'name': 'OTP Bank',
        'script': 'OTP-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'OTP Bank statements (PDF and CSV formats)'
    },
    'RAIFFEISEN': {
        'name': 'Raiffeisen Bank',
        'script': 'RAI-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'Raiffeisen Bank statements (PDF and CSV formats)'
    },
    'TIBANK': {
        'name': 'TI Bank',
        'script': 'TIBANK-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'TI Bank statements (PDF and CSV formats)'
    },
    'UNION': {
        'name': 'Union Bank',
        'script': 'UNION-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'Union Bank statements (PDF and CSV formats)'
    },
    'EBILL': {
        'name': 'E-Bills',
        'script': 'Withholding.py',
        'formats': ['PDF'],
        'description': 'E-Bills (PDF format only)'
    }
}

# Store conversion jobs
conversion_jobs = {}

def cleanup_old_files():
    """Clean up old files and directories periodically"""
    # [Keep existing cleanup logic from original app.py - lines 100-150 approximately]
    # This function remains the same
    pass

# Import the rest of the routes from original app.py
# I'll indicate where to paste them below

# ==========================================
# PROTECTED ROUTES (require login)
# ==========================================

@app.route('/')
@login_required  # <-- ADD THIS to protect the main page
def index():
    """Main upload page - NOW PROTECTED"""
    # [Paste the original index() function code here]
    # Just add @login_required decorator above it
    pass

@app.route('/upload', methods=['POST'])
@login_required  # <-- ADD THIS to protect upload
def upload_file():
    """Handle file upload and conversion - NOW PROTECTED"""
    # [Paste the original upload_file() function code here]
    pass

@app.route('/status/<job_id>')
@login_required  # <-- ADD THIS to protect status checks
def check_status(job_id):
    """Check conversion status - NOW PROTECTED"""
    # [Paste the original check_status() function code here]
    pass

@app.route('/download/<job_id>')
@login_required  # <-- ADD THIS to protect downloads
def download_file(job_id):
    """Download converted file - NOW PROTECTED"""
    # [Paste the original download_file() function code here]
    pass

# ==========================================
# PUBLIC ROUTES (accessible without login)
# ==========================================

# Login/Register routes are handled by auth_blueprint (already registered)

@app.route('/api/health')
def health_check():
    """Health check endpoint - PUBLIC"""
    # [Keep original health_check code]
    pass

@app.route('/api/info')
def api_info():
    """API information - PUBLIC"""
    # [Keep original api_info code]
    pass

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(401)
def unauthorized(e):
    """Handle unauthorized access"""
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('auth.login'))

@app.errorhandler(403)
def forbidden(e):
    """Handle forbidden access"""
    flash('You do not have permission to access this page.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🏦 Bank-Specific Albanian Statement Converter")
    print("🔐 WITH USER AUTHENTICATION")
    print("=" * 60)
    print("🌐 Starting web server...")
    print(f"📁 Import folder: {UPLOAD_FOLDER}")
    print(f"📂 Export folder: {CONVERTED_FOLDER}")
    print("🗂️  Flat file structure (no job directories)")
    print("🏛️ Supported banks:")
    for bank_id, config in BANK_CONFIGS.items():
        print(f"   - {config['name']} ({', '.join(config['formats'])})")
    print("=" * 60)
    print("🔐 Authentication enabled:")
    print("   - Login: /auth/login")
    print("   - Register: /auth/register")
    print("   - Logout: /auth/logout")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5002, debug=True)

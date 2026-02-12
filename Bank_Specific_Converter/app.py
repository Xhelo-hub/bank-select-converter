#!/usr/bin/env python3
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file, jsonify, make_response
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_required, current_user
import os
import subprocess
import tempfile
import shutil
import datetime
import uuid
import time
import threading
from pathlib import Path

# Import authentication components
from auth import UserManager
from auth_routes import auth_bp
from admin_routes import admin_bp

# App initialization
app = Flask(__name__)

# Load configuration
try:
    from config import Config
    app.config.from_object(Config)
except ImportError:
    # Fallback configuration - SECRET_KEY required
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is required")
    app.config.update(
        SECRET_KEY=secret_key,
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max
        PERMANENT_SESSION_LIFETIME=3600,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize UserManager
user_manager = UserManager()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return user_manager.get_user_by_id(user_id)

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# Register admin blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')

# Directory setup
BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_FOLDER = BASE_DIR / 'import'
CONVERTED_FOLDER = BASE_DIR / 'export'
SCRIPTS_DIR = BASE_DIR.parent

# Create directories if they don't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
CONVERTED_FOLDER.mkdir(exist_ok=True)

# Allowed extensions
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'txt'}

# Bank configurations
BANK_CONFIGS = {
    'BKT': {
        'name': 'BKT Bank',
        'script': 'BKT-2-QBO.py',
        'formats': ['PDF'],
        'description': 'BKT Bank of Albania statements'
    },
    'OTP': {
        'name': 'OTP Bank',
        'script': 'OTP-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'OTP Bank Albania statements'
    },
    'RAIFFEISEN': {
        'name': 'Raiffeisen Bank',
        'script': 'RAI-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'Raiffeisen Bank Albania statements'
    },
    'TIBANK': {
        'name': 'Tirana Bank',
        'script': 'TIBANK-2-QBO.py',
        'formats': ['PDF'],
        'description': 'Tirana Bank statements'
    },
    'UNION': {
        'name': 'Union Bank',
        'script': 'UNION-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'Union Bank Albania statements'
    },
    'CREDINS': {
        'name': 'Credins Bank',
        'script': 'CREDINS-2-QBO.py',
        'formats': ['PDF', 'CSV'],
        'description': 'Credins Bank Albania statements'
    },
    'INTESA': {
        'name': 'Intesa Sanpaolo Bank',
        'script': 'INTESA-2-QBO.py',
        'formats': ['CSV'],
        'description': 'Intesa Sanpaolo Bank Albania statements (CSV only)'
    },
    'PROCREDIT': {
        'name': 'ProCredit Bank',
        'script': 'PROCREDIT-2-QBO.py',
        'formats': ['CSV', 'PDF'],
        'description': 'ProCredit Bank Albania statements (CSV and PDF formats)'
    },
    'PAYSERA': {
        'name': 'Paysera',
        'script': 'PAYSERA-2-QBO.py',
        'formats': ['CSV', 'PDF'],
        'description': 'Paysera statements (CSV and PDF formats)'
    },
    'EBILL': {
        'name': 'E-Bill',
        'script': 'Withholding.py',
        'formats': ['PDF'],
        'description': 'E-Bill withholding tax statements (PDF only)'
    }
}

# Job status tracking
jobs = {}
jobs_lock = threading.Lock()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_script_path(script_name):
    """Get the absolute path to a converter script"""
    # Try multiple locations
    locations = [
        SCRIPTS_DIR / script_name,  # Parent directory
        BASE_DIR / script_name,     # Current directory
        Path.cwd() / script_name,   # Working directory
    ]
    
    for path in locations:
        if path.exists():
            return str(path)
    
    return None

def cleanup_old_files():
    """Background task to cleanup old files"""
    while True:
        try:
            time.sleep(1800)  # Run every 30 minutes
            current_time = time.time()
            cutoff_time = current_time - 7200  # 2 hours (same as job retention)
            
            # Clean upload folder (now contains job subdirectories)
            for item in UPLOAD_FOLDER.glob('*'):
                if item.is_dir():
                    # Check if directory is old
                    try:
                        dir_mtime = max(f.stat().st_mtime for f in item.rglob('*') if f.is_file())
                        if dir_mtime < cutoff_time:
                            import shutil
                            shutil.rmtree(item)
                            print(f"Cleaned up old upload directory: {item.name}")
                    except Exception as e:
                        print(f"Error deleting directory {item}: {e}")
                elif item.is_file() and item.stat().st_mtime < cutoff_time:
                    try:
                        item.unlink()
                        print(f"Cleaned up old upload file: {item.name}")
                    except Exception as e:
                        print(f"Error deleting file {item}: {e}")
            
            # Clean converted folder (now contains job subdirectories)
            for item in CONVERTED_FOLDER.glob('*'):
                if item.is_dir():
                    # Check if directory is old
                    try:
                        dir_mtime = max(f.stat().st_mtime for f in item.rglob('*') if f.is_file())
                        if dir_mtime < cutoff_time:
                            import shutil
                            shutil.rmtree(item)
                            print(f"Cleaned up old converted directory: {item.name}")
                    except Exception as e:
                        print(f"Error deleting directory {item}: {e}")
                elif item.is_file() and item.stat().st_mtime < cutoff_time:
                    try:
                        item.unlink()
                        print(f"Cleaned up old converted file: {item.name}")
                    except Exception as e:
                        print(f"Error deleting file {item}: {e}")
            
            # Clean old jobs from memory
            with jobs_lock:
                old_jobs = [job_id for job_id, job in jobs.items() 
                           if current_time - job.get('timestamp', current_time) > 7200]  # 2 hours
                for job_id in old_jobs:
                    del jobs[job_id]
                    print(f"Cleaned up old job: {job_id}")
                    
        except Exception as e:
            print(f"Error in cleanup task: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
@login_required
def index():
    """Main converter page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Albanian Bank Statement Converter</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #4f46e5;
                --primary-light: #6366f1;
                --primary-dark: #4338ca;
                --surface: #ffffff;
                --surface-dim: #f8fafc;
                --text: #0f172a;
                --text-secondary: #64748b;
                --text-muted: #94a3b8;
                --border: #e2e8f0;
                --border-light: #f1f5f9;
                --success: #10b981;
                --success-light: #ecfdf5;
                --error: #ef4444;
                --error-light: #fef2f2;
                --radius: 16px;
                --radius-sm: 10px;
                --radius-xs: 8px;
                --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
                --shadow-md: 0 4px 12px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
                --shadow-lg: 0 4px 12px rgba(0,0,0,0.05), 0 20px 48px rgba(0,0,0,0.1);
            }

            [data-theme="dark"] {
                --primary: #818cf8;
                --primary-light: #a5b4fc;
                --primary-dark: #6366f1;
                --surface: #1e1e2e;
                --surface-dim: #181825;
                --text: #e2e8f0;
                --text-secondary: #94a3b8;
                --text-muted: #64748b;
                --border: #334155;
                --border-light: #1e293b;
                --success: #34d399;
                --success-light: rgba(16, 185, 129, 0.1);
                --error: #f87171;
                --error-light: rgba(239, 68, 68, 0.1);
                --shadow-sm: 0 1px 3px rgba(0,0,0,0.2);
                --shadow-md: 0 4px 12px rgba(0,0,0,0.3);
                --shadow-lg: 0 4px 12px rgba(0,0,0,0.3), 0 20px 48px rgba(0,0,0,0.4);
            }

            [data-theme="dark"] .page-bg {
                background:
                    radial-gradient(ellipse at 20% 50%, rgba(129, 140, 248, 0.06) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 20%, rgba(165, 180, 252, 0.04) 0%, transparent 50%);
            }

            [data-theme="dark"] .bank-select option { background: #1e1e2e; color: #e2e8f0; }

            * { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: var(--surface-dim);
                min-height: 100vh;
                padding: 24px;
                color: var(--text);
            }

            .page-bg {
                position: fixed;
                inset: 0;
                background:
                    radial-gradient(ellipse at 20% 50%, rgba(79, 70, 229, 0.04) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 20%, rgba(99, 102, 241, 0.03) 0%, transparent 50%);
                z-index: 0;
            }

            .container {
                position: relative;
                z-index: 1;
                max-width: 880px;
                margin: 0 auto;
                background: var(--surface);
                border-radius: var(--radius);
                box-shadow: var(--shadow-lg);
                overflow: hidden;
                border: 1px solid var(--border-light);
            }

            /* Header */
            .header {
                padding: 24px 32px;
                border-bottom: 1px solid var(--border-light);
                background: var(--surface);
            }

            .header-top {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
            }

            .header-left {
                display: flex;
                align-items: center;
                gap: 14px;
                flex: 1;
                min-width: 0;
            }

            .logo-placeholder {
                width: 44px;
                height: 44px;
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                color: white;
                font-weight: 700;
                flex-shrink: 0;
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
            }

            .app-logo {
                width: 44px;
                height: 44px;
                object-fit: contain;
                background: white;
                border-radius: 12px;
                padding: 4px;
                box-shadow: var(--shadow-sm);
            }

            .header-title {
                font-size: 18px;
                font-weight: 700;
                color: var(--text);
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .header-right {
                display: flex;
                align-items: center;
                gap: 12px;
                flex-shrink: 0;
            }

            .user-badge {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 12px;
                background: var(--surface-dim);
                border-radius: var(--radius-xs);
                border: 1px solid var(--border);
                font-size: 13px;
                color: var(--text-secondary);
                font-weight: 500;
            }

            .user-badge i { color: var(--primary); font-size: 14px; }

            .header-btn {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 8px 14px;
                border-radius: var(--radius-xs);
                font-size: 13px;
                font-weight: 500;
                text-decoration: none;
                transition: all 0.2s ease;
                border: 1px solid var(--border);
                color: var(--text-secondary);
                background: var(--surface);
            }

            .header-btn i { font-size: 13px; }

            .header-btn:hover {
                background: var(--surface-dim);
                color: var(--text);
                border-color: var(--text-muted);
            }

            .header-btn.admin-btn:hover {
                color: var(--primary);
                border-color: var(--primary);
                background: rgba(79, 70, 229, 0.04);
            }

            .header-btn.logout-btn:hover {
                color: var(--error);
                border-color: var(--error);
                background: rgba(239, 68, 68, 0.04);
            }

            .theme-toggle { cursor: pointer; font-family: inherit; }
            .theme-toggle:hover {
                color: var(--primary) !important;
                border-color: var(--primary) !important;
                background: rgba(79, 70, 229, 0.04) !important;
            }

            /* Converter Section */
            .converter-section {
                padding: 32px;
            }

            .step {
                margin-bottom: 24px;
                padding: 24px;
                border: 1.5px solid var(--border);
                border-radius: var(--radius-sm);
                transition: all 0.3s ease;
                background: var(--surface);
            }

            .step.active {
                border-color: var(--primary);
                background: rgba(79, 70, 229, 0.02);
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.06);
            }

            .step-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 16px;
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .step-number {
                background: var(--primary);
                color: white;
                width: 36px;
                height: 36px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 15px;
                flex-shrink: 0;
                box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
            }

            /* Bank Select */
            .bank-select-wrapper {
                position: relative;
            }

            .bank-select {
                width: 100%;
                padding: 14px 44px 14px 16px;
                font-size: 14px;
                font-weight: 500;
                border: 1.5px solid var(--border);
                border-radius: var(--radius-sm);
                background: var(--surface);
                color: var(--text);
                cursor: pointer;
                transition: all 0.2s ease;
                appearance: none;
                -webkit-appearance: none;
                -moz-appearance: none;
                font-family: 'Inter', sans-serif;
            }

            .bank-select:hover { border-color: var(--text-muted); }

            .bank-select:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
            }

            .bank-select-wrapper::after {
                content: '\\f107';
                font-family: 'Font Awesome 6 Free';
                font-weight: 900;
                position: absolute;
                right: 16px;
                top: 50%;
                transform: translateY(-50%);
                color: var(--text-muted);
                font-size: 14px;
                pointer-events: none;
            }

            .bank-select option:disabled { color: var(--text-muted); }

            .selected-bank-info {
                margin-top: 14px;
                padding: 14px 16px;
                background: rgba(79, 70, 229, 0.04);
                border: 1px solid rgba(79, 70, 229, 0.15);
                border-radius: var(--radius-xs);
                display: none;
                font-size: 13px;
            }

            .selected-bank-info.show {
                display: flex;
                align-items: center;
                gap: 10px;
                animation: slideIn 0.3s ease;
            }

            @keyframes slideIn {
                from { opacity: 0; transform: translateY(-6px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .selected-bank-info .bank-icon {
                color: var(--primary);
                font-size: 15px;
                flex-shrink: 0;
            }

            .selected-bank-info strong {
                color: var(--text);
                font-weight: 600;
            }

            .selected-bank-info .formats {
                color: var(--text-secondary);
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .selected-bank-info .formats i { color: var(--primary); font-size: 13px; }

            /* Upload Area */
            .upload-area {
                border: 2px dashed var(--border);
                border-radius: var(--radius-sm);
                padding: 40px 24px;
                text-align: center;
                transition: all 0.3s ease;
                background: var(--surface-dim);
                cursor: pointer;
            }

            .upload-area.dragover {
                border-color: var(--primary);
                background: rgba(79, 70, 229, 0.04);
            }

            .upload-area:not(.disabled):hover {
                border-color: var(--primary);
                background: rgba(79, 70, 229, 0.02);
            }

            .upload-area .upload-icon {
                color: var(--primary);
                font-size: 40px;
                margin-bottom: 16px;
                display: block;
                opacity: 0.8;
            }

            .upload-area.disabled {
                opacity: 0.4;
                pointer-events: none;
            }

            .upload-area .upload-text {
                font-size: 15px;
                color: var(--text-secondary);
                font-weight: 500;
                margin-bottom: 8px;
            }

            .upload-area .upload-hint {
                font-size: 12px;
                color: var(--text-muted);
            }

            .upload-area .upload-hint i { margin-right: 4px; }

            .file-input { display: none; }

            .selected-file {
                background: var(--success-light);
                padding: 14px 16px;
                border-radius: var(--radius-xs);
                margin-top: 12px;
                border-left: 3px solid var(--success);
                font-size: 13px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .selected-file i { color: var(--success); }

            /* Convert Button */
            .convert-btn {
                background: var(--primary);
                color: white;
                padding: 14px 28px;
                border: none;
                border-radius: var(--radius-sm);
                cursor: pointer;
                font-size: 15px;
                font-weight: 600;
                width: 100%;
                margin-top: 8px;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                font-family: 'Inter', sans-serif;
            }

            .convert-btn:hover {
                background: var(--primary-dark);
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
                transform: translateY(-1px);
            }

            .convert-btn:disabled {
                background: var(--text-muted);
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }

            .convert-btn i { color: white !important; }

            /* Result Section */
            .result-section {
                margin-top: 24px;
                padding: 24px;
                border-radius: var(--radius-sm);
                display: none;
            }

            .result-section.success {
                background: var(--success-light);
                border: 1px solid #a7f3d0;
            }

            .result-section.error {
                background: var(--error-light);
                border: 1px solid #fecaca;
            }

            .result-section.processing {
                background: rgba(79, 70, 229, 0.04);
                border: 1px solid rgba(79, 70, 229, 0.15);
            }

            /* Download Button */
            .download-btn {
                background: var(--primary);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: var(--radius-xs);
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                transition: all 0.2s ease;
                font-family: 'Inter', sans-serif;
                min-width: 200px;
            }

            .download-btn i { color: white !important; }

            .download-btn:hover {
                background: var(--primary-dark);
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
                transform: translateY(-1px);
            }

            .download-btn.secondary {
                background: var(--text-secondary);
            }

            .download-btn.secondary:hover {
                background: #475569;
                box-shadow: 0 4px 12px rgba(100, 116, 139, 0.3);
            }

            /* Animations */
            .spinner {
                border: 3px solid rgba(79, 70, 229, 0.1);
                border-top: 3px solid var(--primary);
                border-radius: 50%;
                width: 44px;
                height: 44px;
                animation: spin 0.8s linear infinite;
                margin: 16px auto;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .hourglass-container {
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 20px auto 16px;
            }

            .hourglass-spin {
                animation: hourglass-rotate 2s ease-in-out infinite;
            }

            @keyframes hourglass-rotate {
                0% { transform: rotate(0deg); }
                50% { transform: rotate(180deg); }
                100% { transform: rotate(180deg); }
            }

            .success-animation {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 32px 20px;
            }

            .success-icon {
                animation: success-pop 0.6s ease-out;
            }

            @keyframes success-pop {
                0% { transform: scale(0); opacity: 0; }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); opacity: 1; }
            }

            /* Footer */
            .footer {
                padding: 20px 32px;
                text-align: center;
                border-top: 1px solid var(--border-light);
                background: var(--surface-dim);
                font-size: 12px;
                color: var(--text-muted);
            }

            .footer i { color: var(--primary); }

            .footer .banks-list {
                margin-top: 4px;
                font-size: 11px;
                color: var(--text-muted);
            }

            /* Hidden bank grid/card styles (kept for JS compatibility) */
            .bank-grid { display: none; }

            /* Mobile Responsiveness */
            @media (max-width: 768px) {
                body { padding: 12px; }
                .container { border-radius: 12px; }
                .header { padding: 16px 20px; }

                .header-top {
                    flex-direction: column;
                    gap: 12px;
                }

                .header-left { justify-content: center; }

                .header-right {
                    width: 100%;
                    justify-content: center;
                    flex-wrap: wrap;
                }

                .user-badge { font-size: 12px; }

                .converter-section { padding: 20px 16px; }
                .step { padding: 20px 16px; }
                .step-title { font-size: 15px; }

                .upload-area { padding: 28px 16px; }

                .download-btn {
                    width: 100%;
                    min-width: unset;
                }
            }

            @media (max-width: 480px) {
                body { padding: 8px; }
                .header-title { font-size: 16px; }

                .header-btn {
                    padding: 6px 10px;
                    font-size: 12px;
                }

                .step-title { font-size: 14px; }

                .step-number {
                    width: 32px;
                    height: 32px;
                    font-size: 13px;
                    border-radius: 8px;
                }

                .convert-btn {
                    padding: 12px 20px;
                    font-size: 14px;
                }

                .converter-section { padding: 16px 12px; }
                .step { padding: 16px 12px; margin-bottom: 16px; }
            }
        </style>
        <script>(function(){var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t);})();</script>
    </head>
    <body>
        <div class="page-bg"></div>
        <div class="container">
            <div class="header">
                <div class="header-top">
                    <div class="header-left">
                        <div class="logo-placeholder" id="appLogo">BS</div>
                        <span class="header-title">Bank Statement Converter</span>
                    </div>
                    <div class="header-right">
                        <div class="user-badge">
                            <i class="fas fa-user-circle"></i>
                            <span>{{ current_user.email }}</span>
                        </div>
                        <button class="header-btn theme-toggle" id="themeToggle" onclick="toggleTheme()" title="Toggle dark mode">
                            <i class="fas fa-moon"></i>
                        </button>
                        {% if current_user.is_admin %}
                        <a href="{{ url_for('admin.dashboard') }}" class="header-btn admin-btn">
                            <i class="fas fa-shield-halved"></i> Admin
                        </a>
                        {% endif %}
                        <a href="{{ url_for('auth.logout') }}" class="header-btn logout-btn">
                            <i class="fas fa-arrow-right-from-bracket"></i> Logout
                        </a>
                    </div>
                </div>
            </div>

            <div class="converter-section">
                <form id="converterForm" enctype="multipart/form-data">
                    <!-- Step 1: Select Bank -->
                    <div class="step active" id="step1">
                        <div class="step-title">
                            <div class="step-number"><i class="fas fa-building-columns"></i></div>
                            Select Your Bank
                        </div>

                        <div class="bank-select-wrapper">
                            <select class="bank-select" id="bankSelect" onchange="selectBankFromDropdown()">
                                <option value="" disabled selected>Choose your bank...</option>
                                {% for bank_id, config in banks.items() %}
                                <option value="{{ bank_id }}" data-formats="{{ config.formats|join(', ') }}" data-description="{{ config.description }}">
                                    {{ config.name }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>

                        <div class="selected-bank-info" id="selectedBankInfo">
                            <i class="fas fa-file-lines bank-icon"></i>
                            <div class="formats">
                                <strong>Supported Formats:</strong>&nbsp; <span id="selectedBankFormats"></span>
                            </div>
                        </div>
                    </div>

                    <!-- Step 2: Upload File -->
                    <div class="step" id="step2">
                        <div class="step-title">
                            <div class="step-number"><i class="fas fa-cloud-arrow-up"></i></div>
                            Upload Bank Statement
                        </div>
                        <div class="upload-area disabled" id="uploadArea">
                            <i class="fas fa-cloud-arrow-up upload-icon"></i>
                            <input type="file" id="fileInput" name="file" class="file-input" onchange="handleFileSelect(event)" accept=".pdf,.csv,.txt">
                            <p class="upload-text">Drag & drop or click to upload</p>
                            <p class="upload-hint"><i class="fas fa-info-circle"></i> Supported: PDF, CSV, TXT (Max 50MB)</p>
                        </div>
                        <div id="selectedFile" class="selected-file" style="display: none;">
                            <i class="fas fa-check-circle"></i> <strong>Selected:</strong> <span id="fileName"></span>
                        </div>
                    </div>

                    <!-- Step 3: Convert -->
                    <div class="step" id="step3">
                        <div class="step-title">
                            <div class="step-number"><i class="fas fa-arrow-right-arrow-left"></i></div>
                            Convert to QuickBooks Format
                        </div>
                        <button type="submit" class="convert-btn" disabled id="convertBtn">
                            <i class="fas fa-arrow-right-arrow-left"></i> Convert Statement
                        </button>
                    </div>
                </form>

                <!-- Results Section -->
                <div class="result-section" id="resultSection">
                    <div id="resultContent"></div>
                </div>
            </div>

            <div class="footer">
                <p><i class="fas fa-shield-halved"></i> Albanian Bank Statement Converter &middot; QuickBooks Compatible</p>
                <p class="banks-list">BKT &middot; OTP &middot; Raiffeisen &middot; Tirana Bank &middot; Union Bank &middot; Credins &middot; Intesa &middot; ProCredit &middot; Paysera &middot; E-Bill</p>
            </div>
        </div>

        <script>
            // Theme toggle
            function toggleTheme() {
                const html = document.documentElement;
                const isDark = html.getAttribute('data-theme') === 'dark';
                const newTheme = isDark ? 'light' : 'dark';
                html.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateThemeIcon(newTheme);
            }

            function updateThemeIcon(theme) {
                const icon = document.querySelector('#themeToggle i');
                if (icon) {
                    icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                }
            }

            // Apply saved theme icon on load
            (function() {
                const saved = localStorage.getItem('theme') || 'light';
                updateThemeIcon(saved);
            })();

            // Load custom logo if exists
            (function() {
                const logoContainer = document.getElementById('appLogo');
                const logoPath = '/static/logo.png';

                fetch(logoPath)
                    .then(response => {
                        if (response.ok) {
                            const img = document.createElement('img');
                            img.src = logoPath;
                            img.className = 'app-logo';
                            img.alt = 'Bank Statement Converter Logo';
                            logoContainer.replaceWith(img);
                        }
                    })
                    .catch(() => {});
            })();

            let selectedBank = null;
            let selectedFile = null;

            async function downloadFile(jobId) {
                try {
                    const response = await fetch('/download/' + jobId);

                    if (!response.ok) {
                        const errorText = await response.text();
                        alert('Download error: ' + errorText);
                        return;
                    }

                    const blob = await response.blob();

                    let filename = 'converted_statement.csv';
                    const contentDisposition = response.headers.get('Content-Disposition');
                    if (contentDisposition) {
                        const filenameMatch = contentDisposition.match(/filename[^;=\\n]*=((['"]).*?\\2|[^;\\n]*)/);
                        if (filenameMatch && filenameMatch[1]) {
                            filename = filenameMatch[1].replace(/['"]/g, '');
                        }
                    }

                    filename = filename.trim();
                    if (!filename.endsWith('.csv')) {
                        const csvIndex = filename.indexOf('.csv');
                        if (csvIndex > -1) {
                            filename = filename.substring(0, csvIndex + 4);
                        } else {
                            filename = filename + '.csv';
                        }
                    }

                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);

                } catch (error) {
                    console.error('Download error:', error);
                    alert('Download failed: ' + error.message);
                }
            }

            function selectBankFromDropdown() {
                const selectElement = document.getElementById('bankSelect');
                const selectedOption = selectElement.options[selectElement.selectedIndex];

                selectedBank = selectElement.value;

                if (selectedBank) {
                    const bankFormats = selectedOption.getAttribute('data-formats');

                    document.getElementById('selectedBankFormats').textContent = bankFormats;
                    document.getElementById('selectedBankInfo').classList.add('show');

                    document.getElementById('step2').classList.add('active');
                    const uploadArea = document.getElementById('uploadArea');
                    uploadArea.classList.remove('disabled');
                    uploadArea.style.pointerEvents = '';

                    document.getElementById('fileInput').value = '';
                    selectedFile = null;
                    document.getElementById('selectedFile').style.display = 'none';
                    document.getElementById('step3').classList.remove('active');
                    document.getElementById('convertBtn').disabled = true;
                }
            }

            function selectBank(bankId) {
                selectedBank = bankId;

                document.querySelectorAll('.bank-card').forEach(card => {
                    card.classList.remove('selected');
                });
                const selectedCard = document.querySelector('[data-bank="' + bankId + '"]');
                if (selectedCard) {
                    selectedCard.classList.add('selected');
                }

                document.getElementById('step2').classList.add('active');
                const uploadArea = document.getElementById('uploadArea');
                uploadArea.classList.remove('disabled');
                uploadArea.style.pointerEvents = '';

                document.getElementById('fileInput').value = '';
                selectedFile = null;
                document.getElementById('selectedFile').style.display = 'none';
                document.getElementById('step3').classList.remove('active');
                document.getElementById('convertBtn').disabled = true;
            }

            function resetForm() {
                document.getElementById('fileInput').value = '';
                selectedFile = null;
                document.getElementById('selectedFile').style.display = 'none';

                const uploadArea = document.getElementById('uploadArea');
                uploadArea.style.pointerEvents = '';

                document.getElementById('step3').classList.remove('active');
                document.getElementById('convertBtn').disabled = true;

                document.getElementById('resultSection').style.display = 'none';
            }

            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (file) {
                    selectedFile = file;
                    document.getElementById('fileName').textContent = file.name;
                    document.getElementById('selectedFile').style.display = 'flex';
                    document.getElementById('step3').classList.add('active');
                    document.getElementById('convertBtn').disabled = false;

                    document.getElementById('uploadArea').style.pointerEvents = 'none';
                }
            }

            // Drag and drop
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');

            const bankSelectElement = document.getElementById('bankSelect');
            if (bankSelectElement) {
                bankSelectElement.addEventListener('change', function() {
                    selectBankFromDropdown();
                });
            }

            uploadArea.addEventListener('click', (e) => {
                if (!uploadArea.classList.contains('disabled') && e.target !== fileInput && !selectedFile) {
                    fileInput.click();
                }
            });

            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!uploadArea.classList.contains('disabled')) {
                    uploadArea.classList.add('dragover');
                }
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                uploadArea.classList.remove('dragover');

                if (!uploadArea.classList.contains('disabled')) {
                    const file = e.dataTransfer.files[0];
                    if (file) {
                        fileInput.files = e.dataTransfer.files;
                        handleFileSelect({ target: { files: [file] } });
                    }
                }
            });

            // Form submission
            document.getElementById('converterForm').addEventListener('submit', async (e) => {
                e.preventDefault();

                if (!selectedBank || !selectedFile) {
                    alert('Please select a bank and upload a file');
                    return;
                }

                const resultSection = document.getElementById('resultSection');
                const resultContent = document.getElementById('resultContent');
                resultSection.className = 'result-section processing';
                resultSection.style.display = 'block';
                resultContent.innerHTML = '<div class="hourglass-container"><i class="fas fa-hourglass-half fa-3x hourglass-spin" style="color: var(--primary);"></i></div><p style="text-align: center; margin-top: 16px; color: var(--primary); font-weight: 600; font-size: 15px;">Converting your statement...<br><span style="font-size: 13px; color: var(--text-muted); font-weight: 400;">Please wait, this may take a few moments</span></p>';

                document.getElementById('convertBtn').disabled = true;

                const formData = new FormData();
                formData.append('bank', selectedBank);
                formData.append('file', selectedFile);

                try {
                    const response = await fetch('/convert', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        resultSection.className = 'result-section success';
                        resultContent.innerHTML = '<div class="success-animation"><i class="fas fa-check-circle fa-4x success-icon" style="color: #10b981;"></i><h3 style="color: #065f46; margin-top: 16px; font-size: 18px;">Conversion Successful!</h3></div>';

                        setTimeout(() => {
                            resultContent.innerHTML = '<div style="text-align: center;"><i class="fas fa-circle-check fa-2x" style="color: #10b981; margin-bottom: 12px;"></i><h3 style="color: #065f46; margin-bottom: 16px; font-size: 16px;">Ready to Download</h3></div><p style="margin-bottom: 8px; font-size: 13px; color: var(--text-secondary);"><strong style="color: var(--text);">Original:</strong> ' + result.original_filename + '</p><p style="margin-bottom: 8px; font-size: 13px; color: var(--text-secondary);"><strong style="color: var(--text);">Converted:</strong> ' + result.output_filename + '</p><div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 20px;"><button onclick="downloadFile(\\''+result.job_id+'\\')\" class="download-btn"><i class="fas fa-download"></i> Download CSV</button><button onclick="resetForm()" class="download-btn secondary"><i class="fas fa-arrow-rotate-right"></i> Convert Another</button></div>';
                        }, 1500);
                    } else {
                        resultSection.className = 'result-section error';
                        resultContent.innerHTML = '<div style="text-align: center;"><i class="fas fa-circle-xmark fa-2x" style="color: var(--error); margin-bottom: 12px;"></i><h3 style="color: #991b1b; margin-bottom: 12px; font-size: 16px;">Conversion Failed</h3><p style="font-size: 13px; color: #991b1b;"><strong>Error:</strong> ' + (result.error || 'Unknown error occurred') + '</p></div>';
                    }
                } catch (error) {
                    resultSection.className = 'result-section error';
                    resultContent.innerHTML = '<div style="text-align: center;"><i class="fas fa-circle-xmark fa-2x" style="color: var(--error); margin-bottom: 12px;"></i><h3 style="color: #991b1b; margin-bottom: 12px; font-size: 16px;">Error</h3><p style="font-size: 13px; color: #991b1b;"><strong>Error:</strong> ' + error.message + '</p></div>';
                } finally {
                    document.getElementById('convertBtn').disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """
    response = make_response(render_template_string(html_content, banks=BANK_CONFIGS, current_user=current_user))
    # Prevent caching to ensure users always get the latest version
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/convert', methods=['POST'])
@login_required
def convert_file():
    """Handle file conversion"""
    try:
        # Get selected bank
        bank_id = request.form.get('bank')
        if not bank_id or bank_id not in BANK_CONFIGS:
            return jsonify({'success': False, 'error': 'Invalid bank selection'}), 400
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Use PDF, CSV, or TXT'}), 400
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Store original filename for display
        original_filename = file.filename
        
        # Save uploaded file directly to import folder
        # Use versioned filename if file already exists to avoid conflicts
        filename = secure_filename(file.filename)
        input_path = UPLOAD_FOLDER / filename
        
        # If file exists, add version number (v.1), (v.2), etc.
        if input_path.exists():
            base_name = input_path.stem
            extension = input_path.suffix
            counter = 1
            while input_path.exists():
                input_path = UPLOAD_FOLDER / f"{base_name} (v.{counter}){extension}"
                counter += 1
            filename = input_path.name  # Update filename to versioned name
        
        file.save(str(input_path))
        
        # Get converter script
        bank_config = BANK_CONFIGS[bank_id]
        script_name = bank_config['script']
        script_path = get_script_path(script_name)
        
        if not script_path:
            # Clean up uploaded file
            if input_path.exists():
                input_path.unlink()
            return jsonify({
                'success': False,
                'error': f'Converter script not found: {script_name}'
            }), 500
        
        # Run converter script - output will go directly to export folder
        try:
            import sys
            print(f"[DEBUG] Running converter...")
            print(f"[DEBUG] Script: {script_path}")
            print(f"[DEBUG] Input: {input_path}")
            print(f"[DEBUG] Output: {CONVERTED_FOLDER}")
            
            result = subprocess.run(
                [sys.executable, script_path, '--input', str(input_path), '--output', str(CONVERTED_FOLDER)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            print(f"[DEBUG] Converter return code: {result.returncode}")
            print(f"[DEBUG] Converter stdout: {result.stdout[:500] if result.stdout else 'None'}")
            print(f"[DEBUG] Converter stderr: {result.stderr[:500] if result.stderr else 'None'}")
            
            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                return jsonify({
                    'success': False,
                    'error': f'Conversion failed: {error_msg}'
                }), 500
            
            # Find output file in export folder
            # Converter creates files with " - 4qbo.csv" suffix based on input filename
            # Output will be like "filename - 4qbo.csv" or "filename (v.1) - 4qbo.csv"
            
            # Get the base name without extension
            base_stem = Path(filename).stem
            
            # Try multiple search patterns
            print(f"[DEBUG] Looking for output file...")
            print(f"[DEBUG] Input filename: {filename}")
            print(f"[DEBUG] Base stem: {base_stem}")
            print(f"[DEBUG] Search folder: {CONVERTED_FOLDER}")
            
            # Pattern 1: Exact stem match
            output_files = list(CONVERTED_FOLDER.glob(f'*{base_stem}*4qbo.csv'))
            print(f"[DEBUG] Pattern 1 found {len(output_files)} files")
            
            if not output_files:
                # Pattern 2: Remove version number and try again
                base_name = base_stem.split(' (v.')[0]
                output_files = list(CONVERTED_FOLDER.glob(f'{base_name}*4qbo.csv'))
                print(f"[DEBUG] Pattern 2 found {len(output_files)} files")
            
            if not output_files:
                # Pattern 3: List all 4qbo.csv files and find by timestamp
                all_output_files = list(CONVERTED_FOLDER.glob('*4qbo.csv'))
                print(f"[DEBUG] Pattern 3: All 4qbo files in folder: {len(all_output_files)}")
                if all_output_files:
                    # Get the most recent one created in the last 60 seconds
                    current_time = time.time()
                    recent_files = [f for f in all_output_files if (current_time - f.stat().st_mtime) < 60]
                    if recent_files:
                        output_files = recent_files
                        print(f"[DEBUG] Found {len(recent_files)} recent files")
            
            if not output_files:
                # List what's actually in the folder for debugging
                all_files = list(CONVERTED_FOLDER.glob('*'))
                print(f"[DEBUG] All files in export folder: {[f.name for f in all_files]}")
                return jsonify({
                    'success': False,
                    'error': f'Conversion completed but output file not found. Searched for: {base_stem}'
                }), 500
            
            # Get the most recently created file if multiple matches
            output_file = max(output_files, key=lambda p: p.stat().st_mtime)
            print(f"[DEBUG] Selected output file: {output_file}")
            print(f"[DEBUG] File exists: {output_file.exists()}")
            print(f"[DEBUG] File size: {output_file.stat().st_size if output_file.exists() else 'N/A'}")
            
            # Verify the output file is fully written (not still being written)
            # Wait up to 10 seconds for file to be stable (increased for slower conversions)
            max_wait = 10
            last_size = 0
            stable_count = 0
            for i in range(max_wait):
                if not output_file.exists():
                    print(f"[DEBUG] Waiting for output file to be created... ({i+1}/{max_wait})")
                    time.sleep(1)
                    continue
                current_size = output_file.stat().st_size
                if current_size > 0:
                    if current_size == last_size:
                        stable_count += 1
                        if stable_count >= 2:  # File size stable for 2 consecutive checks
                            print(f"[DEBUG] Output file is stable at {current_size} bytes")
                            break
                    else:
                        stable_count = 0
                last_size = current_size
                if i < max_wait - 1:
                    print(f"[DEBUG] Waiting for output file to stabilize... ({i+1}/{max_wait}, size: {current_size})")
                    time.sleep(1)
            
            # Final verification
            if not output_file.exists():
                return jsonify({
                    'success': False,
                    'error': 'Output file was not created by converter script'
                }), 500
            
            if output_file.stat().st_size == 0:
                return jsonify({
                    'success': False,
                    'error': 'Output file is empty - conversion may have failed'
                }), 500
            
            # Delete original uploaded file immediately after successful conversion
            try:
                if input_path.exists():
                    input_path.unlink()
            except Exception as cleanup_error:
                # Log but don't fail the conversion
                print(f"Warning: Failed to delete uploaded file: {cleanup_error}")
            
            # Store job info
            with jobs_lock:
                jobs[job_id] = {
                    'bank': bank_id,
                    'original_filename': original_filename,  # Use original filename
                    'output_filename': output_file.name,
                    'output_path': str(output_file),
                    'timestamp': time.time(),
                    'user_id': current_user.id
                }
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'original_filename': original_filename,  # Show original filename to user
                'output_filename': output_file.name
            })
            
        except subprocess.TimeoutExpired:
            input_path.unlink()  # Clean up
            return jsonify({
                'success': False,
                'error': 'Conversion timed out. File may be too large or complex.'
            }), 500
        except Exception as e:
            input_path.unlink()  # Clean up
            return jsonify({
                'success': False,
                'error': f'Conversion error: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/download/<job_id>')
@login_required
def download_file(job_id):
    """Download converted file"""
    try:
        print(f"[DEBUG] Download request for job_id: {job_id}")
        with jobs_lock:
            if job_id not in jobs:
                print(f"[DEBUG] Job {job_id} not found in jobs dictionary")
                print(f"[DEBUG] Available jobs: {list(jobs.keys())}")
                return "File not found or has expired", 404
            
            job = jobs[job_id]
            print(f"[DEBUG] Job found: {job}")
            
            # Verify user owns this job
            if job['user_id'] != current_user.id:
                print(f"[DEBUG] Unauthorized access - job user_id: {job['user_id']}, current user: {current_user.id}")
                return "Unauthorized access to file", 403
            
            output_path = job['output_path']
            output_filename = job['output_filename']
        
        print(f"[DEBUG] Checking file exists: {output_path}")
        if not Path(output_path).exists():
            print(f"[DEBUG] File does not exist at path: {output_path}")
            return "File not found or has been deleted", 404
        
        # Create response with file - specify mimetype explicitly for CSV
        # NOTE: File is NOT deleted after download to allow multiple downloads
        # Background cleanup thread will remove files older than 1 hour
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='text/csv'
        )
        
        print(f"File downloaded for job {job_id}. File will be auto-cleaned after 1 hour.")
        
        return response
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        return f"Download error: {str(e)}", 500

@app.route('/status/<job_id>')
@login_required
def check_status(job_id):
    """Check conversion status"""
    with jobs_lock:
        if job_id not in jobs:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        job = jobs[job_id]
        
        # Verify user owns this job
        if job['user_id'] != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        return jsonify({'success': True, 'job': job})

@app.route('/cleanup')
@login_required
def manual_cleanup():
    """Manually trigger cleanup (admin only - you can add role check here)"""
    try:
        cleanup_old_files()
        flash('Cleanup completed successfully', 'success')
    except Exception as e:
        flash(f'Cleanup error: {str(e)}', 'error')
    return redirect(url_for('index'))

@app.route('/server-status')
@login_required
def server_status():
    """Health check endpoint - requires authentication"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.datetime.now().isoformat(),
        'banks_configured': len(BANK_CONFIGS)
    })

@app.route('/api/info')
@login_required
def api_info():
    """API information endpoint - requires authentication"""
    return jsonify({
        'name': 'Albanian Bank Statement Converter',
        'version': '2.0.0',
        'banks': list(BANK_CONFIGS.keys()),
        'supported_formats': list(ALLOWED_EXTENSIONS)
    })

# Security headers for all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

if __name__ == '__main__':
    print("=" * 60)
    print("Albanian Bank Statement Converter - Authenticated")
    print("=" * 60)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Export folder: {CONVERTED_FOLDER}")
    print(f"Scripts directory: {SCRIPTS_DIR}")
    print(f"Configured banks: {', '.join(BANK_CONFIGS.keys())}")
    print("=" * 60)
    print("Starting server...")
    print("Access at: http://127.0.0.1:5002")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5002, debug=False)

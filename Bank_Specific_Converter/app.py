#!/usr/bin/env python3
from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash, send_file, jsonify, make_response
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from sqlalchemy import event
import os
import subprocess
import tempfile
import shutil
import datetime
import uuid
import time
import threading
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import db, User, Job, Conversion, Download, ContactMessage

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

# Enable template auto-reload for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Create tables on first run and set up WAL mode
with app.app_context():
    # Enable WAL mode for SQLite (critical for multi-worker gunicorn)
    @event.listens_for(db.engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    db.create_all()

# Import authentication components (after db init)
from auth import UserManager
from auth_routes import auth_bp
from admin_routes import admin_bp
from notification_utils import get_user_notifications, mark_as_read, mark_all_as_read, get_unread_count

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
    return db.session.get(User, user_id)

@app.context_processor
def inject_globals():
    """Inject global variables into all templates"""
    logo_path = Path(__file__).parent / 'static' / 'logo.png'
    return {
        'logo_exists': logo_path.exists()
    }

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

def log_conversion(user_email, user_id, bank, original_filename, output_filename, success):
    """Log a conversion event to database"""
    try:
        conv = Conversion(
            user_email=user_email, user_id=user_id, bank=bank,
            original_filename=original_filename, output_filename=output_filename,
            timestamp=datetime.datetime.now().isoformat(), success=success
        )
        db.session.add(conv)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging conversion: {e}")

def log_download(user_email, user_id, job_id, filename):
    """Log a download event to database"""
    try:
        dl = Download(
            user_email=user_email, user_id=user_id, job_id=job_id,
            filename=filename, timestamp=datetime.datetime.now().isoformat()
        )
        db.session.add(dl)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging download: {e}")

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
            
            # Clean old jobs from database
            with app.app_context():
                old_jobs = Job.query.filter(Job.timestamp < cutoff_time).all()
                for job in old_jobs:
                    db.session.delete(job)
                    print(f"Cleaned up old job: {job.id}")
                if old_jobs:
                    db.session.commit()
                    
        except Exception as e:
            print(f"Error in cleanup task: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
@login_required
def index():
    """Main converter page"""
    # Check if logo exists
    logo_exists = (Path(__file__).parent / 'static' / 'logo.png').exists()

    return render_template('converter.html',
                         user=current_user,
                         banks=BANK_CONFIGS,
                         logo_exists=logo_exists)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    """User settings page - profile and password"""
    if request.method == 'POST':
        form_type = request.form.get('form_type', '')

        if form_type == 'profile':
            # Update personal data
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            current_user.display_name = request.form.get('display_name', '').strip()
            db.session.commit()
            flash('Të dhënat personale u ruajtën me sukses!', 'success')
            return redirect(url_for('user_settings'))

        elif form_type == 'password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_password or not new_password or not confirm_password:
                flash('Të gjitha fushat janë të detyrueshme', 'error')
                return render_template('user_settings.html')

            if not user_manager.verify_password(current_user, current_password):
                flash('Fjalëkalimi aktual është i gabuar', 'error')
                return render_template('user_settings.html')

            if len(new_password) < 6:
                flash('Fjalëkalimi i ri duhet të ketë të paktën 6 karaktere', 'error')
                return render_template('user_settings.html')

            if new_password != confirm_password:
                flash('Fjalëkalimet nuk përputhen', 'error')
                return render_template('user_settings.html')

            success, message = user_manager.admin_reset_password(current_user.id, new_password)
            if success:
                flash('Fjalëkalimi u ndryshua me sukses!', 'success')
            else:
                flash(f'Gabim: {message}', 'error')

            return redirect(url_for('user_settings'))

    return render_template('user_settings.html')

@app.route('/notifications')
@login_required
def notifications_page():
    """Full notifications page"""
    return render_template('notifications.html')

@app.route('/contact-admin', methods=['GET', 'POST'])
@login_required
def contact_admin():
    """Contact admin - send a message"""
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message_text = request.form.get('message', '').strip()

        if not subject or not message_text:
            flash('Subjekti dhe mesazhi janë të detyrueshme', 'error')
        elif len(message_text) > 120:
            flash('Mesazhi nuk mund të jetë më i gjatë se 120 karaktere', 'error')
        else:
            msg = ContactMessage(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                user_email=current_user.email,
                subject=subject[:200],
                message=message_text[:120],
                created_at=datetime.datetime.now().isoformat(),
                is_read=False
            )
            db.session.add(msg)
            db.session.commit()
            flash('Mesazhi u dërgua me sukses!', 'success')
            return redirect(url_for('contact_admin'))

    # Get user's sent messages
    messages = ContactMessage.query.filter_by(user_id=current_user.id)\
        .order_by(ContactMessage.created_at.desc()).all()
    return render_template('contact_admin.html', messages=messages)

@app.route('/_old_converter')
@login_required
def old_converter_backup():
    """Backup of old inline HTML converter (for reference)"""
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

            /* Notification Bell */
            .notification-wrapper {
                position: relative;
            }

            .notification-btn {
                position: relative;
            }

            .notification-badge {
                position: absolute;
                top: 4px;
                right: 4px;
                background: #ef4444;
                color: white;
                border-radius: 10px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: 700;
                min-width: 18px;
                text-align: center;
            }

            .notification-dropdown {
                position: absolute;
                top: calc(100% + 8px);
                right: 0;
                width: 380px;
                max-height: 480px;
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                box-shadow: var(--shadow-lg);
                z-index: 1000;
                overflow: hidden;
                display: none;
            }

            .notif-header {
                padding: 14px 18px;
                border-bottom: 1px solid var(--border);
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: var(--surface-dim);
            }

            .notif-header h4 {
                font-size: 15px;
                font-weight: 600;
                margin: 0;
            }

            .notif-header button {
                background: none;
                border: none;
                color: var(--primary);
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                padding: 4px 8px;
                border-radius: 4px;
            }

            .notif-header button:hover {
                background: rgba(79, 70, 229, 0.1);
            }

            .notif-list {
                max-height: 400px;
                overflow-y: auto;
            }

            .notif-item {
                padding: 14px 18px;
                border-bottom: 1px solid var(--border-light);
                cursor: pointer;
                transition: background 0.2s;
            }

            .notif-item.unread {
                background: rgba(79, 70, 229, 0.04);
                border-left: 3px solid var(--primary);
            }

            .notif-item:hover {
                background: var(--surface-dim);
            }

            .notif-item.type-warning { border-left-color: #f59e0b; }
            .notif-item.type-important { border-left-color: #ef4444; }
            .notif-item.type-success { border-left-color: #10b981; }

            .notif-title {
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 4px;
            }

            .notif-message {
                font-size: 13px;
                color: var(--text-secondary);
                margin-bottom: 6px;
                line-height: 1.4;
            }

            .notif-time {
                font-size: 11px;
                color: var(--text-muted);
            }

            .notif-empty {
                padding: 40px;
                text-align: center;
                color: var(--text-muted);
                font-size: 13px;
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
                        <!-- Notification Bell -->
                        <div class="notification-wrapper">
                            <button class="header-btn notification-btn" onclick="toggleNotifications()" title="Notifications">
                                <i class="fas fa-bell"></i>
                                <span class="notification-badge" id="notifBadge" style="display:none;"></span>
                            </button>
                            
                            <!-- Notification Dropdown -->
                            <div class="notification-dropdown" id="notificationDropdown">
                                <div class="notif-header">
                                    <h4>Notifications</h4>
                                    <button onclick="markAllRead()">Mark all read</button>
                                </div>
                                <div class="notif-list" id="notifList">
                                    <div class="notif-empty">Loading...</div>
                                </div>
                            </div>
                        </div>

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

            // ============ Notification System ============
            let notificationsVisible = false;

            // Poll for unread count
            function updateNotificationBadge() {
                fetch('/notifications/unread-count')
                    .then(r => r.json())
                    .then(data => {
                        const badge = document.getElementById('notifBadge');
                        if (data.count > 0) {
                            badge.textContent = data.count;
                            badge.style.display = 'block';
                        } else {
                            badge.style.display = 'none';
                        }
                    })
                    .catch(err => console.error('Error fetching unread count:', err));
            }

            // Load notifications
            function loadNotifications() {
                fetch('/notifications/my')
                    .then(r => r.json())
                    .then(data => {
                        const list = document.getElementById('notifList');
                        if (data.success && data.notifications.length > 0) {
                            list.innerHTML = data.notifications.map(n => {
                                const typeIcons = {
                                    info: '📘',
                                    warning: '⚠️',
                                    important: '🚨',
                                    success: '✅'
                                };
                                return `
                                    <div class="notif-item ${!n.is_read ? 'unread' : ''} type-${n.type}" 
                                         onclick="markNotificationRead('${n.id}')">
                                        <div class="notif-title">${typeIcons[n.type]} ${n.title}</div>
                                        <div class="notif-message">${n.message}</div>
                                        <div class="notif-time">${formatTime(n.created_at)}</div>
                                    </div>
                                `;
                            }).join('');
                        } else {
                            list.innerHTML = '<div class="notif-empty">No notifications</div>';
                        }
                    })
                    .catch(err => {
                        console.error('Error loading notifications:', err);
                        document.getElementById('notifList').innerHTML = '<div class="notif-empty">Failed to load notifications</div>';
                    });
            }

            function toggleNotifications() {
                notificationsVisible = !notificationsVisible;
                const dropdown = document.getElementById('notificationDropdown');
                dropdown.style.display = notificationsVisible ? 'block' : 'none';
                if (notificationsVisible) {
                    loadNotifications();
                }
            }

            function markNotificationRead(id) {
                fetch(`/notifications/mark-read/${id}`, {method: 'POST'})
                    .then(r => r.json())
                    .then(() => {
                        updateNotificationBadge();
                        loadNotifications();
                    })
                    .catch(err => console.error('Error marking notification as read:', err));
            }

            function markAllRead() {
                fetch('/notifications/mark-all-read', {method: 'POST'})
                    .then(r => r.json())
                    .then(() => {
                        updateNotificationBadge();
                        loadNotifications();
                    })
                    .catch(err => console.error('Error marking all as read:', err));
            }

            function formatTime(isoString) {
                const date = new Date(isoString);
                const now = new Date();
                const diff = now - date;
                const minutes = Math.floor(diff / 60000);
                if (minutes < 1) return 'Just now';
                if (minutes < 60) return `${minutes}m ago`;
                const hours = Math.floor(minutes / 60);
                if (hours < 24) return `${hours}h ago`;
                const days = Math.floor(hours / 24);
                if (days < 7) return `${days}d ago`;
                return date.toLocaleDateString();
            }

            // Poll every 30 seconds
            setInterval(updateNotificationBadge, 30000);
            updateNotificationBadge(); // Initial load

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.notification-wrapper')) {
                    document.getElementById('notificationDropdown').style.display = 'none';
                    notificationsVisible = false;
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

        # Run converter script synchronously - output goes directly to export folder
        try:
            import sys
            print(f"[DEBUG] Running converter...", flush=True)
            print(f"[DEBUG] Script: {script_path}", flush=True)
            print(f"[DEBUG] Input: {input_path}", flush=True)
            print(f"[DEBUG] Output: {CONVERTED_FOLDER}", flush=True)

            result = subprocess.run(
                [sys.executable, script_path, '--input', str(input_path), '--output', str(CONVERTED_FOLDER)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            print(f"[DEBUG] Converter return code: {result.returncode}", flush=True)
            print(f"[DEBUG] Converter stdout: {result.stdout[:500] if result.stdout else 'None'}", flush=True)
            print(f"[DEBUG] Converter stderr: {result.stderr[:500] if result.stderr else 'None'}", flush=True)

            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                if input_path.exists():
                    input_path.unlink()
                return jsonify({
                    'success': False,
                    'error': f'Conversion failed: {error_msg}'
                }), 500

            # Find output file - search by timestamp (most recent in last 60 seconds)
            base_stem = Path(filename).stem
            output_files = list(CONVERTED_FOLDER.glob(f'*{base_stem}*4qbo.csv'))

            if not output_files:
                # Fallback: find any recent 4qbo file
                all_output_files = list(CONVERTED_FOLDER.glob('*4qbo.csv'))
                current_time = time.time()
                output_files = [f for f in all_output_files if (current_time - f.stat().st_mtime) < 60]

            if not output_files:
                if input_path.exists():
                    input_path.unlink()
                return jsonify({
                    'success': False,
                    'error': f'Conversion completed but output file not found'
                }), 500

            # Get most recent file
            output_file = max(output_files, key=lambda p: p.stat().st_mtime)
            print(f"[DEBUG] Output file: {output_file.name}", flush=True)

            # Delete uploaded file
            if input_path.exists():
                input_path.unlink()

            # Save job to database
            job = Job(
                id=job_id,
                bank=bank_id,
                original_filename=original_filename,
                output_filename=output_file.name,
                output_path=str(output_file),
                status='completed',
                timestamp=time.time(),
                user_id=current_user.id
            )
            db.session.add(job)
            db.session.commit()

            # Log conversion
            log_conversion(current_user.email, current_user.id, bank_id,
                          original_filename, output_file.name, True)

            return jsonify({
                'success': True,
                'job_id': job_id,
                'original_filename': original_filename,
                'output_filename': output_file.name
            })

        except subprocess.TimeoutExpired:
            if input_path.exists():
                input_path.unlink()
            return jsonify({
                'success': False,
                'error': 'Conversion timed out. File may be too large or complex.'
            }), 500
        except Exception as e:
            if input_path.exists():
                input_path.unlink()
            print(f"[ERROR] Conversion error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Conversion error: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

def _update_job_status_with_retry(job_id, status, output_filename=None, output_path=None, error_message=None, max_retries=3):
    """Update job status with retry logic for database locks"""
    for attempt in range(max_retries):
        try:
            job = db.session.get(Job, job_id)
            if job:
                job.status = status
                if output_filename:
                    job.output_filename = output_filename
                if output_path:
                    job.output_path = output_path
                if error_message:
                    job.error_message = error_message
                db.session.commit()
                print(f"[DEBUG] Successfully updated job status to {status}")
                return True
        except Exception as db_error:
            print(f"[WARNING] Database commit failed (attempt {attempt + 1}/{max_retries}): {db_error}")
            db.session.rollback()
            if attempt < max_retries - 1:
                time.sleep(0.5)  # Wait before retry
    print(f"[ERROR] Failed to update job status after {max_retries} attempts")
    return False

def _perform_conversion(job_id, input_path, script_path, filename, bank_id, original_filename, user_id, user_email):
    """Perform the actual conversion in background"""
    # Run converter script - output will go directly to export folder
    try:
        import sys
        print(f"[DEBUG] Running converter...", flush=True)
        print(f"[DEBUG] Script: {script_path}", flush=True)
        print(f"[DEBUG] Input: {input_path}", flush=True)
        print(f"[DEBUG] Output: {CONVERTED_FOLDER}", flush=True)
        
        result = subprocess.run(
            [sys.executable, script_path, '--input', str(input_path), '--output', str(CONVERTED_FOLDER)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(f"[DEBUG] Converter return code: {result.returncode}", flush=True)
        print(f"[DEBUG] Converter stdout: {result.stdout[:500] if result.stdout else 'None'}", flush=True)
        print(f"[DEBUG] Converter stderr: {result.stderr[:500] if result.stderr else 'None'}", flush=True)
        
        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            # Update job status to failed
            _update_job_status_with_retry(job_id, 'failed', error_message=f'Conversion failed: {error_msg}')
            return
        
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
            # Update job status to failed
            _update_job_status_with_retry(job_id, 'failed', error_message=f'Conversion completed but output file not found. Searched for: {base_stem}')
            return
        
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
            _update_job_status_with_retry(job_id, 'failed', error_message='Output file was not created by converter script')
            return

        if output_file.stat().st_size == 0:
            _update_job_status_with_retry(job_id, 'failed', error_message='Output file is empty - conversion may have failed')
            return
        
        # Delete original uploaded file immediately after successful conversion
        try:
            if input_path.exists():
                input_path.unlink()
        except Exception as cleanup_error:
            # Log but don't fail the conversion
            print(f"Warning: Failed to delete uploaded file: {cleanup_error}")
        
        # Update job info with completed status (with retry for database locks)
        _update_job_status_with_retry(job_id, 'completed',
                                      output_filename=output_file.name,
                                      output_path=str(output_file))

        # Log successful conversion
        try:
            log_conversion(user_email, user_id, bank_id,
                          original_filename, output_file.name, True)
        except Exception as log_error:
            print(f"[WARNING] Failed to log conversion: {log_error}")
        
    except subprocess.TimeoutExpired:
        if input_path.exists():
            input_path.unlink()  # Clean up
        # Update job status to failed
        _update_job_status_with_retry(job_id, 'failed',
                                      error_message='Conversion timed out. File may be too large or complex.')
    except Exception as e:
        if input_path.exists():
            input_path.unlink()  # Clean up
        # Update job status to failed
        print(f"[ERROR] Conversion exception: {e}")
        import traceback
        traceback.print_exc()
        _update_job_status_with_retry(job_id, 'failed',
                                      error_message=f'Conversion error: {str(e)}')


# ============ Notification Routes (User-facing) ============

@app.route('/notifications/my')
@login_required
def my_notifications():
    """Get current user's notifications (JSON)"""
    try:
        notifications = get_user_notifications(current_user.email)
        return jsonify({'success': True, 'notifications': notifications})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/notifications/mark-read/<notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read for current user"""
    try:
        success = mark_as_read(notification_id, current_user.email)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    try:
        count = mark_all_as_read(current_user.email)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/notifications/unread-count')
@login_required
def unread_count():
    """Get unread notification count for current user"""
    try:
        count = get_unread_count(current_user.email)
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0, 'error': str(e)})


@app.route('/download/<job_id>')
@app.route('/download/<job_id>/<path:filename>')
@login_required
def download_file(job_id, filename=None):
    """Download converted file"""
    try:
        print(f"[DEBUG] Download request for job_id: {job_id}")
        job = db.session.get(Job, job_id)
        if not job:
            print(f"[DEBUG] Job {job_id} not found in database")
            return "File not found or has expired", 404

        print(f"[DEBUG] Job found: {job.id}")

        # Verify user owns this job
        if job.user_id != current_user.id:
            print(f"[DEBUG] Unauthorized access - job user_id: {job.user_id}, current user: {current_user.id}")
            return "Unauthorized access to file", 403

        output_path = job.output_path
        output_filename = job.output_filename
        
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

        # Log download
        log_download(current_user.email, current_user.id, job_id, output_filename)

        return response
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        return f"Download error: {str(e)}", 500

@app.route('/status/<job_id>')
@login_required
def check_status(job_id):
    """Check conversion status"""
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'}), 404

    # Verify user owns this job
    if job.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    response = {
        'status': job.status,
        'bank': job.bank,
        'original_filename': job.original_filename,
    }

    if job.status == 'completed':
        response['files'] = [job.output_filename] if job.output_filename and job.output_filename.strip() else []
        response['output_path'] = job.output_path
    elif job.status == 'failed':
        response['error'] = job.error_message or 'Conversion failed'

    return jsonify(response)

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

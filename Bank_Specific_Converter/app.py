#!/usr/bin/env python3
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file, jsonify
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
    # Fallback configuration
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max
        PERMANENT_SESSION_LIFETIME=3600,
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
            cutoff_time = current_time - 3600  # 1 hour
            
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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --fa-style-family-classic: "Font Awesome 6 Free";
                --fa-font-solid: normal 900 1em / 1 "Font Awesome 6 Free";
                --primary-color: #33cc66;
                --primary-hover: #2eb85c;
                --header-bg: #2b2b38;
                --text-dark: #1a1a1a;
                --text-secondary: #666666;
                --bg-light: #f8f9fb;
                --bg-gradient: linear-gradient(135deg, #f8fff8 0%, #e8f5ee 100%);
                --border-color: #e0e0e0;
                --shadow-sm: 0 2px 8px rgba(0,0,0,0.05);
                --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
                --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
                --danger-color: #ff4d4d;
                --radius-sm: 8px;
                --radius-md: 12px;
                --radius-lg: 16px;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: var(--bg-gradient);
                min-height: 100vh;
                padding: 20px;
                color: var(--text-dark);
            }
            
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: var(--radius-lg);
                box-shadow: var(--shadow-lg);
                overflow: hidden;
            }
            
            .header {
                background: var(--header-bg);
                border-radius: var(--radius-md);
                padding: 24px;
                margin-bottom: 20px;
                box-shadow: var(--shadow-md);
                color: white;
            }
            
            .header-top {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 15px;
            }
            
            .header-left {
                display: flex;
                align-items: center;
                gap: 15px;
                flex: 1;
            }
            
            .logo-container {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .app-logo {
                width: 80px;
                height: 80px;
                object-fit: contain;
                background: white;
                border-radius: var(--radius-sm);
                padding: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            
            .logo-placeholder {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                border-radius: var(--radius-sm);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2em;
                color: white;
                font-weight: 700;
                box-shadow: 0 4px 12px rgba(51, 204, 102, 0.4);
            }
            
            .header h1 {
                font-size: 1.8em;
                font-weight: 600;
                margin: 0;
            }
            
            .header h1 i {
                color: var(--primary-color);
                font-size: 1.1em;
            }
            
            .header-right {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .user-info i {
                color: white;
                font-size: 1.1em;
            }
            
            .user-email {
                font-size: 0.9em;
                font-weight: 500;
            }
            
            .button-row {
                display: flex;
                justify-content: flex-end;
                gap: 8px;
            }
            
            .button-group {
                display: flex;
                gap: 8px;
            }
            
            .admin-btn,
            .logout-btn {
                background: rgba(255,255,255,0.1);
                color: white;
                padding: 10px 20px;
                border: 2px solid rgba(255,255,255,0.2);
                border-radius: var(--radius-sm);
                cursor: pointer;
                font-size: 0.9em;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s ease;
                font-weight: 500;
            }
            
            .admin-btn i,
            .logout-btn i {
                color: var(--primary-color);
                font-size: 1.1em;
            }
            
            .admin-btn:hover,
            .logout-btn:hover {
                background: rgba(255,255,255,0.2);
                border-color: var(--primary-color);
                transform: translateY(-2px) scale(1.02);
                box-shadow: 0 4px 12px rgba(51, 204, 102, 0.3);
            }
            
            .converter-section {
                padding: 40px;
            }
            
            .step {
                margin-bottom: 35px;
                padding: 24px;
                border: 2px solid var(--border-color);
                border-radius: var(--radius-md);
                transition: all 0.3s ease;
                background: white;
            }
            
            .step.active {
                border-color: var(--primary-color);
                background: rgba(51, 204, 102, 0.02);
                box-shadow: var(--shadow-sm);
            }
            
            .step-title {
                font-size: 1.4em;
                font-weight: 600;
                color: var(--text-dark);
                margin-bottom: 15px;
                display: flex;
                align-items: center;
            }
            
            .step-number {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                color: white;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 15px;
                font-weight: 600;
                font-size: 1.1em;
                box-shadow: 0 4px 12px rgba(51, 204, 102, 0.25);
            }
            
            .step-number i {
                font-size: 1em;
            }
            
            .bank-select-wrapper {
                margin-top: 20px;
                position: relative;
            }
            
            .bank-select {
                width: 100%;
                padding: 18px 50px 18px 20px;
                font-size: 1.1em;
                font-weight: 500;
                border: 2px solid var(--border-color);
                border-radius: var(--radius-md);
                background: white;
                color: var(--text-dark);
                cursor: pointer;
                transition: all 0.3s ease;
                appearance: none;
                -webkit-appearance: none;
                -moz-appearance: none;
                font-family: 'Inter', sans-serif;
                box-shadow: var(--shadow-sm);
            }
            
            .bank-select:hover {
                border-color: var(--primary-color);
                box-shadow: var(--shadow-md), 0 0 0 3px rgba(51, 204, 102, 0.1);
            }
            
            .bank-select:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: var(--shadow-md), 0 0 0 4px rgba(51, 204, 102, 0.15);
            }
            
            .bank-select-wrapper::after {
                content: '\f107';
                font-family: 'Font Awesome 6 Free';
                font-weight: 900;
                position: absolute;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                color: var(--primary-color);
                font-size: 1.3em;
                pointer-events: none;
            }
            
            .bank-select option {
                padding: 15px;
                font-size: 1em;
            }
            
            .bank-select option:disabled {
                color: var(--text-secondary);
            }
            
            .selected-bank-info {
                margin-top: 20px;
                padding: 20px 24px;
                background: linear-gradient(135deg, rgba(52, 152, 219, 0.08) 0%, rgba(41, 128, 185, 0.04) 100%);
                border: 2px solid rgba(52, 152, 219, 0.3);
                border-radius: var(--radius-md);
                display: none;
                box-shadow: var(--shadow-sm);
            }
            
            .selected-bank-info.show {
                display: block;
                animation: slideIn 0.3s ease;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .selected-bank-info .bank-icon {
                color: #3498db;
                font-size: 1.4em;
                margin-right: 10px;
            }
            
            .selected-bank-info strong {
                color: var(--text-dark);
                font-weight: 600;
                font-size: 1.05em;
            }
            
            .selected-bank-info .formats {
                color: var(--text-dark);
                font-size: 1em;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .selected-bank-info .formats i {
                color: var(--primary-color);
            }
            
            .selected-bank-info .formats {
                color: var(--text-secondary);
                font-size: 0.9em;
                margin-top: 8px;
            }
            
            .bank-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 20px;
                display: none;
            }
            
            .bank-card {
                border: 2px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: 24px;
                cursor: pointer;
                transition: all 0.2s ease;
                background: white;
                box-shadow: var(--shadow-sm);
            }
            
            .bank-card:hover {
                border-color: var(--primary-color);
                transform: translateY(-3px) scale(1.02);
                box-shadow: var(--shadow-md), 0 0 0 3px rgba(51, 204, 102, 0.1);
            }
            
            .bank-card.selected {
                border-color: var(--primary-color);
                background: linear-gradient(135deg, rgba(51, 204, 102, 0.08) 0%, rgba(51, 204, 102, 0.04) 100%);
                box-shadow: var(--shadow-md), 0 0 0 3px rgba(51, 204, 102, 0.15);
            }
            
            .bank-card i {
                color: var(--primary-color);
                font-size: 2em;
                margin-bottom: 12px;
                display: block;
            }
            
            .bank-name {
                font-size: 1.3em;
                font-weight: 600;
                color: var(--text-dark);
                margin-bottom: 8px;
            }
            }
            
            .bank-formats {
                color: #7f8c8d;
                font-size: 0.9em;
                margin-bottom: 5px;
            }
            
            .bank-description {
                color: var(--text-secondary);
                font-size: 0.85em;
                line-height: 1.4;
            }
            
            .upload-area {
                border: 3px dashed var(--border-color);
                border-radius: var(--radius-md);
                padding: 50px 40px;
                text-align: center;
                margin-top: 20px;
                transition: all 0.3s ease;
                background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
                cursor: pointer;
            }
            
            .upload-area.dragover {
                border-color: var(--primary-color);
                background: linear-gradient(135deg, rgba(51, 204, 102, 0.08) 0%, rgba(51, 204, 102, 0.04) 100%);
                transform: scale(1.01);
                border-width: 4px;
            }
            
            .upload-area:not(.disabled):hover {
                border-color: var(--primary-color);
                background: linear-gradient(135deg, rgba(51, 204, 102, 0.05) 0%, rgba(51, 204, 102, 0.02) 100%);
            }
            
            .upload-area i {
                color: var(--primary-color);
                font-size: 3.5em;
                margin-bottom: 20px;
                display: block;
                filter: drop-shadow(0 4px 8px rgba(51, 204, 102, 0.2));
            }
            
            .upload-area.disabled {
                opacity: 0.5;
                pointer-events: none;
            }
            
            .file-input {
                display: none;
            }
            
            .upload-btn {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                color: white;
                padding: 16px 32px;
                border: none;
                border-radius: var(--radius-sm);
                cursor: pointer;
                font-size: 1.1em;
                font-weight: 600;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(51, 204, 102, 0.3);
                width: 100%;
                max-width: 400px;
                margin: 0 auto;
            }
            
            .upload-btn:hover {
                background: linear-gradient(135deg, var(--primary-hover) 0%, #27a04d 100%);
                transform: translateY(-2px) scale(1.02);
                box-shadow: 0 6px 16px rgba(51, 204, 102, 0.4);
            }
            
            .upload-btn:disabled {
                background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .convert-btn {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                color: white;
                padding: 18px 40px;
                border: none;
                border-radius: var(--radius-md);
                cursor: pointer;
                font-size: 1.2em;
                font-weight: 600;
                width: 100%;
                margin-top: 25px;
                transition: all 0.2s ease;
                box-shadow: var(--shadow-md), 0 0 0 0 rgba(51, 204, 102, 0.4);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
            }
            
            .convert-btn:hover {
                background: linear-gradient(135deg, var(--primary-hover) 0%, #27a04d 100%);
                transform: translateY(-2px) scale(1.01);
                box-shadow: var(--shadow-lg), 0 0 0 4px rgba(51, 204, 102, 0.15);
            }
            
            .convert-btn:disabled {
                background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .result-section {
                margin-top: 30px;
                padding: 24px;
                border-radius: var(--radius-md);
                display: none;
                box-shadow: var(--shadow-sm);
            }
            
            .result-section.success {
                background: linear-gradient(135deg, #d5f4e6 0%, #e8f9f0 100%);
                border: 2px solid var(--primary-color);
            }
            
            .result-section.error {
                background: linear-gradient(135deg, #fadbd8 0%, #ffe6e6 100%);
                border: 2px solid var(--danger-color);
            }
            
            .result-section.processing {
                background: linear-gradient(135deg, #fef9e7 0%, #fff8e1 100%);
                border: 2px solid #f39c12;
            }
            
            .download-btn {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                color: white;
                padding: 14px 32px;
                border: none;
                border-radius: var(--radius-sm);
                cursor: pointer;
                font-size: 1.05em;
                font-weight: 600;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 10px;
                margin-top: 15px;
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(51, 204, 102, 0.3);
            }
            
            .download-btn:hover {
                background: linear-gradient(135deg, var(--primary-hover) 0%, #27a04d 100%);
                transform: translateY(-2px) scale(1.03);
                box-shadow: 0 6px 16px rgba(51, 204, 102, 0.4);
            }
            
            .selected-file {
                background: linear-gradient(135deg, #e8f5e8 0%, #f0f9f0 100%);
                padding: 18px;
                border-radius: var(--radius-sm);
                margin-top: 15px;
                border-left: 4px solid var(--primary-color);
                box-shadow: var(--shadow-sm);
            }
            
            .spinner {
                border: 4px solid rgba(51, 204, 102, 0.1);
                border-top: 4px solid var(--primary-color);
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 0.8s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .footer {
                background: linear-gradient(135deg, #2b2b38 0%, #1f1f29 100%);
                padding: 25px;
                text-align: center;
                color: rgba(255, 255, 255, 0.7);
                border-radius: 0 0 var(--radius-lg) var(--radius-lg);
            }
            
            .footer strong {
                color: var(--primary-color);
                font-weight: 600;
            }
            
            /* Mobile Responsiveness */
            @media (max-width: 768px) {
                body {
                    padding: 10px;
                }

                .container {
                    border-radius: 10px;
                }

                .header {
                    padding: 20px 15px;
                }
                
                .header-top {
                    flex-direction: column;
                    text-align: center;
                }
                
                .header-left {
                    flex-direction: column;
                    width: 100%;
                    text-align: center;
                }
                
                .logo-container {
                    flex-direction: column;
                    gap: 12px;
                }

                .header h1 {
                    font-size: 1.5em;
                    text-align: center;
                }

                .header p {
                    font-size: 1em;
                }
                
                .header-right {
                    width: 100%;
                    justify-content: center;
                }

                .user-info {
                    flex-direction: column;
                    gap: 12px;
                    align-items: stretch;
                }

                .user-email {
                    text-align: center;
                }

                .button-group {
                    justify-content: center;
                    flex-wrap: wrap;
                }

                .converter-section {
                    padding: 25px 15px;
                }

                .step-title {
                    font-size: 1.3em;
                }

                .bank-grid {
                    grid-template-columns: 1fr;
                    gap: 12px;
                }

                .bank-card {
                    padding: 18px;
                }

                .bank-name {
                    font-size: 1.2em;
                }

                .upload-area {
                    padding: 25px 15px;
                }

                .upload-area p {
                    font-size: 1em !important;
                }

                .upload-btn,
                .download-btn {
                    padding: 10px 20px;
                    font-size: 1em;
                }

                .convert-btn {
                    padding: 14px 25px;
                    font-size: 1.1em;
                }

                .result-section {
                    padding: 15px;
                    font-size: 0.95em;
                }

                .footer {
                    padding: 15px;
                    font-size: 0.9em;
                }
            }

            @media (max-width: 480px) {
                .header h1 {
                    font-size: 1.5em;
                }

                .header p {
                    font-size: 0.9em;
                }

                .admin-btn,
                .logout-btn {
                    padding: 8px 12px;
                    font-size: 0.8em;
                }

                .step-title {
                    font-size: 1.1em;
                }

                .step-number {
                    width: 35px;
                    height: 35px;
                    font-size: 1.1em;
                }

                .bank-card {
                    padding: 15px;
                }

                .bank-name {
                    font-size: 1.1em;
                }

                .bank-formats,
                .bank-description {
                    font-size: 0.85em;
                }

                .upload-area {
                    padding: 20px 10px;
                }

                .convert-btn {
                    padding: 12px 20px;
                    font-size: 1em;
                }

                .converter-section {
                    padding: 20px 10px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-top">
                    <div class="header-left">
                        <div class="logo-container">
                            <div class="logo-placeholder" id="appLogo">
                                BS
                            </div>
                            <h1>Bank Statement Converter</h1>
                        </div>
                    </div>
                    <div class="header-right">
                        <div class="user-info">
                            <i class="fas fa-user-circle"></i>
                            <span class="user-email">{{ current_user.email }}</span>
                        </div>
                    </div>
                </div>
                <div class="button-row">
                    <div class="button-group">
                        {% if current_user.is_admin %}
                        <a href="{{ url_for('admin.dashboard') }}" class="admin-btn">
                            <i class="fas fa-users-cog"></i> Admin Panel
                        </a>
                        {% endif %}
                        <a href="{{ url_for('auth.logout') }}" class="logout-btn">
                            <i class="fas fa-sign-out-alt"></i> Logout
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="converter-section">
                <form id="converterForm" enctype="multipart/form-data">
                    <!-- Step 1: Select Bank -->
                    <div class="step active" id="step1">
                        <div class="step-title">
                            <div class="step-number"><i class="fas fa-university"></i></div>
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
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <i class="fas fa-info-circle bank-icon"></i>
                                <strong>Supported Formats:</strong>
                            </div>
                            <div class="formats">
                                <i class="fas fa-file-alt"></i> <span id="selectedBankFormats"></span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Step 2: Upload File -->
                    <div class="step" id="step2">
                        <div class="step-title">
                            <div class="step-number"><i class="fas fa-upload"></i></div>
                            Upload Bank Statement
                        </div>
                        <div class="upload-area disabled" id="uploadArea">
                            <i class="fas fa-cloud-upload-alt"></i>
                            <input type="file" id="fileInput" name="file" class="file-input" onchange="handleFileSelect(event)" accept=".pdf,.csv,.txt">
                            <p style="font-size: 1.2em; color: #7f8c8d; margin-bottom: 15px;">Drag & Drop or Click to Upload</p>
                            <p style="margin-top: 15px; color: #95a5a6; font-size: 0.9em;"><i class="fas fa-info-circle"></i> Supported: PDF, CSV, TXT (Max 50MB)</p>
                        </div>
                        <div id="selectedFile" class="selected-file" style="display: none;">
                            <i class="fas fa-check-circle" style="color: var(--primary-color);"></i> <strong>Selected:</strong> <span id="fileName"></span>
                        </div>
                    </div>
                    
                    <!-- Step 3: Convert -->
                    <div class="step" id="step3">
                        <div class="step-title">
                            <div class="step-number"><i class="fas fa-sync-alt"></i></div>
                            Convert to QuickBooks Format
                        </div>
                        <button type="submit" class="convert-btn" disabled id="convertBtn">
                            <i class="fas fa-magic"></i> Convert Statement
                        </button>
                    </div>
                </form>
                
                <!-- Results Section -->
                <div class="result-section" id="resultSection">
                    <div id="resultContent"></div>
                </div>
            </div>
            
            <div class="footer">
                <p><i class="fas fa-shield-alt" style="color: var(--primary-color);"></i> Albanian Bank Statement Converter | QuickBooks Compatible</p>
                <p style="margin-top: 5px; font-size: 0.9em;">Supports: BKT, OTP, Raiffeisen, Tirana Bank, Union Bank, Credins, Intesa, ProCredit, Paysera, E-Bill</p>
            </div>
        </div>
        
        <script>
            // Load custom logo if exists
            (function() {
                const logoContainer = document.getElementById('appLogo');
                const logoPath = '/static/logo.png';
                
                // Try to load custom logo
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
                    .catch(() => {
                        // Use placeholder if logo doesn't exist
                    });
            })();
            
            let selectedBank = null;
            let selectedFile = null;
            
            function downloadFile(jobId) {
                // Create a temporary link and click it to trigger download
                const link = document.createElement('a');
                link.href = '/download/' + jobId;
                link.download = '';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
            
            function selectBankFromDropdown() {
                const selectElement = document.getElementById('bankSelect');
                const selectedOption = selectElement.options[selectElement.selectedIndex];
                
                selectedBank = selectElement.value;
                
                if (selectedBank) {
                    // Show selected bank formats
                    const bankFormats = selectedOption.getAttribute('data-formats');
                    
                    document.getElementById('selectedBankFormats').textContent = bankFormats;
                    document.getElementById('selectedBankInfo').classList.add('show');
                    
                    // Enable upload
                    document.getElementById('step2').classList.add('active');
                    document.getElementById('uploadArea').classList.remove('disabled');
                    
                    // Reset file selection
                    document.getElementById('fileInput').value = '';
                    selectedFile = null;
                    document.getElementById('selectedFile').style.display = 'none';
                    document.getElementById('convertBtn').disabled = true;
                }
            }
            
            function selectBank(bankId) {
                selectedBank = bankId;
                
                // Update UI
                document.querySelectorAll('.bank-card').forEach(card => {
                    card.classList.remove('selected');
                });
                const selectedCard = document.querySelector(`[data-bank="${bankId}"]`);
                if (selectedCard) {
                    selectedCard.classList.add('selected');
                }
                
                // Enable upload
                document.getElementById('step2').classList.add('active');
                document.getElementById('uploadArea').classList.remove('disabled');
                
                // Reset file selection
                document.getElementById('fileInput').value = '';
                selectedFile = null;
                document.getElementById('selectedFile').style.display = 'none';
                document.getElementById('convertBtn').disabled = true;
            }
            
            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (file) {
                    selectedFile = file;
                    document.getElementById('fileName').textContent = file.name;
                    document.getElementById('selectedFile').style.display = 'block';
                    document.getElementById('step3').classList.add('active');
                    document.getElementById('convertBtn').disabled = false;
                    
                    // Disable upload area clicks to prevent reopening file dialog
                    document.getElementById('uploadArea').style.pointerEvents = 'none';
                }
            }
            
            // Drag and drop
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            
            // Make entire upload area clickable (only when no file is selected)
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
                
                // Show processing
                const resultSection = document.getElementById('resultSection');
                const resultContent = document.getElementById('resultContent');
                resultSection.className = 'result-section processing';
                resultSection.style.display = 'block';
                resultContent.innerHTML = '<div class="spinner"></div><p style="text-align: center; margin-top: 10px;">Converting your statement...</p>';
                
                // Disable form
                document.getElementById('convertBtn').disabled = true;
                
                // Prepare form data
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
                        resultContent.innerHTML = `
                            <h3 style="color: #27ae60; margin-bottom: 15px;">✅ Conversion Successful!</h3>
                            <p style="margin-bottom: 10px;"><strong>Original File:</strong> ${result.original_filename}</p>
                            <p style="margin-bottom: 10px;"><strong>Converted File:</strong> ${result.output_filename}</p>
                            <button onclick="downloadFile('${result.job_id}')" class="download-btn" style="border: none; cursor: pointer;">⬇️ Download QuickBooks CSV</button>
                        `;
                    } else {
                        resultSection.className = 'result-section error';
                        resultContent.innerHTML = `
                            <h3 style="color: #e74c3c; margin-bottom: 15px;">❌ Conversion Failed</h3>
                            <p><strong>Error:</strong> ${result.error || 'Unknown error occurred'}</p>
                        `;
                    }
                } catch (error) {
                    resultSection.className = 'result-section error';
                    resultContent.innerHTML = `
                        <h3 style="color: #e74c3c; margin-bottom: 15px;">❌ Error</h3>
                        <p><strong>Error:</strong> ${error.message}</p>
                    `;
                } finally {
                    document.getElementById('convertBtn').disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content, banks=BANK_CONFIGS, current_user=current_user)

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
                    'original_filename': filename,
                    'output_filename': output_file.name,
                    'output_path': str(output_file),
                    'timestamp': time.time(),
                    'user_id': current_user.id
                }
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'original_filename': filename,
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
        with jobs_lock:
            if job_id not in jobs:
                flash('File not found or has expired', 'error')
                return redirect(url_for('index'))
            
            job = jobs[job_id]
            
            # Verify user owns this job
            if job['user_id'] != current_user.id:
                flash('Unauthorized access to file', 'error')
                return redirect(url_for('index'))
            
            output_path = job['output_path']
        
        if not Path(output_path).exists():
            flash('File not found or has been deleted', 'error')
            return redirect(url_for('index'))
        
        # Create response with file
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=job['output_filename']
        )
        
        # Delete file immediately after sending (cleanup on response close)
        @response.call_on_close
        def cleanup_after_download():
            try:
                output_file_path = Path(output_path)
                if output_file_path.exists():
                    output_file_path.unlink()
                
                # Remove job from memory
                with jobs_lock:
                    jobs.pop(job_id, None)
                    
                print(f"Cleaned up job {job_id}: deleted file and removed from memory")
            except Exception as cleanup_error:
                print(f"Warning: Failed to cleanup after download for job {job_id}: {cleanup_error}")
        
        return response
        
    except Exception as e:
        flash(f'Download error: {str(e)}', 'error')
        return redirect(url_for('index'))

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
def server_status():
    """Health check endpoint (no auth required for monitoring)"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.datetime.now().isoformat(),
        'upload_folder': str(UPLOAD_FOLDER),
        'converted_folder': str(CONVERTED_FOLDER),
        'banks_configured': len(BANK_CONFIGS)
    })

@app.route('/api/info')
def api_info():
    """API information endpoint (no auth required)"""
    return jsonify({
        'name': 'Albanian Bank Statement Converter',
        'version': '2.0.0',
        'banks': list(BANK_CONFIGS.keys()),
        'max_file_size': '50MB',
        'supported_formats': list(ALLOWED_EXTENSIONS)
    })

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

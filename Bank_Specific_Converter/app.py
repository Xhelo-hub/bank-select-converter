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
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white;
                padding: 30px;
                text-align: center;
                position: relative;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
                margin-bottom: 20px;
            }
            
            .header-divider {
                border: none;
                border-top: 1px solid rgba(255,255,255,0.2);
                margin: 20px 0;
            }
            
            .user-info {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 15px;
            }
            
            .user-email {
                font-size: 0.9em;
                opacity: 0.9;
                font-weight: 500;
            }
            
            .button-group {
                display: flex;
                gap: 8px;
            }
            
            .admin-btn,
            .logout-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 6px 14px;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.85em;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                transition: all 0.3s;
            }
            
            .admin-btn:hover,
            .logout-btn:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-1px);
            }
            
            .converter-section {
                padding: 40px;
            }
            
            .step {
                margin-bottom: 30px;
                padding: 20px;
                border: 2px solid #ecf0f1;
                border-radius: 10px;
                transition: border-color 0.3s;
            }
            
            .step.active {
                border-color: #3498db;
                background: #f8f9fa;
            }
            
            .step-title {
                font-size: 1.4em;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
            }
            
            .step-number {
                background: #3498db;
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 15px;
                font-weight: bold;
            }
            
            .bank-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .bank-card {
                border: 2px solid #ecf0f1;
                border-radius: 10px;
                padding: 20px;
                cursor: pointer;
                transition: all 0.3s;
                background: white;
            }
            
            .bank-card:hover {
                border-color: #3498db;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            
            .bank-card.selected {
                border-color: #27ae60;
                background: #d5f4e6;
            }
            
            .bank-name {
                font-size: 1.3em;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 8px;
            }
            
            .bank-formats {
                color: #7f8c8d;
                font-size: 0.9em;
                margin-bottom: 5px;
            }
            
            .bank-description {
                color: #95a5a6;
                font-size: 0.85em;
            }
            
            .upload-area {
                border: 3px dashed #bdc3c7;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin-top: 15px;
                transition: all 0.3s;
                background: #fafafa;
            }
            
            .upload-area.dragover {
                border-color: #3498db;
                background: #e3f2fd;
            }
            
            .upload-area.disabled {
                opacity: 0.5;
                pointer-events: none;
            }
            
            .file-input {
                display: none;
            }
            
            .upload-btn {
                background: #33cc66;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1.1em;
                transition: background 0.3s;
            }
            
            .upload-btn:hover {
                background: #29a355;
            }
            
            .upload-btn:disabled {
                background: #95a5a6;
                cursor: not-allowed;
            }
            
            .convert-btn {
                background: #33cc66;
                color: white;
                padding: 15px 40px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1.2em;
                font-weight: bold;
                width: 100%;
                margin-top: 20px;
                transition: background 0.3s;
            }
            
            .convert-btn:hover {
                background: #29a355;
            }
            
            .convert-btn:disabled {
                background: #95a5a6;
                cursor: not-allowed;
            }
            
            .result-section {
                margin-top: 30px;
                padding: 20px;
                border-radius: 10px;
                display: none;
            }
            
            .result-section.success {
                background: #d5f4e6;
                border: 2px solid #27ae60;
            }
            
            .result-section.error {
                background: #fadbd8;
                border: 2px solid #e74c3c;
            }
            
            .result-section.processing {
                background: #fef9e7;
                border: 2px solid #f39c12;
            }
            
            .download-btn {
                background: #33cc66;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1.1em;
                text-decoration: none;
                display: inline-block;
                margin-top: 15px;
                transition: background 0.3s;
            }
            
            .download-btn:hover {
                background: #29a355;
            }
            
            .selected-file {
                background: #e8f5e8;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                border-left: 4px solid #27ae60;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .footer {
                background: #ecf0f1;
                padding: 20px;
                text-align: center;
                color: #7f8c8d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Bank Statement Converter</h1>
                <p>Convert Albanian bank statements to QuickBooks .csv format</p>
                
                <hr class="header-divider">
                
                <div class="user-info">
                    <div class="user-email">{{ current_user.email }}</div>
                    <div class="button-group">
                        {% if current_user.is_admin %}
                        <a href="{{ url_for('admin.dashboard') }}" class="admin-btn">👤 User Management</a>
                        {% endif %}
                        <a href="{{ url_for('auth.logout') }}" class="logout-btn">🚪 Logout</a>
                    </div>
                </div>
            </div>
            
            <div class="converter-section">
                <form id="converterForm" enctype="multipart/form-data">
                    <!-- Step 1: Select Bank -->
                    <div class="step active" id="step1">
                        <div class="step-title">
                            <div class="step-number">1</div>
                            Select Your Bank
                        </div>
                        <div class="bank-grid" id="bankGrid">
                            {% for bank_id, config in banks.items() %}
                            <div class="bank-card" data-bank="{{ bank_id }}" onclick="selectBank('{{ bank_id }}')">
                                <div class="bank-name">{{ config.name }}</div>
                                <div class="bank-formats">Supported Formats: {{ config.formats|join(', ') }}</div>
                                <div class="bank-description">{{ config.description }}</div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <!-- Step 2: Upload File -->
                    <div class="step" id="step2">
                        <div class="step-title">
                            <div class="step-number">2</div>
                            Upload Bank Statement
                        </div>
                        <div class="upload-area disabled" id="uploadArea">
                            <input type="file" id="fileInput" name="file" class="file-input" onchange="handleFileSelect(event)" accept=".pdf,.csv,.txt">
                            <p style="font-size: 1.2em; color: #7f8c8d; margin-bottom: 15px;">📄 Drag & Drop or Click to Upload</p>
                            <button type="button" class="upload-btn" onclick="document.getElementById('fileInput').click()" disabled id="uploadBtn">
                                Choose File
                            </button>
                            <p style="margin-top: 15px; color: #95a5a6; font-size: 0.9em;">Supported: PDF, CSV, TXT (Max 50MB)</p>
                        </div>
                        <div id="selectedFile" class="selected-file" style="display: none;">
                            <strong>📎 Selected:</strong> <span id="fileName"></span>
                        </div>
                    </div>
                    
                    <!-- Step 3: Convert -->
                    <div class="step" id="step3">
                        <div class="step-title">
                            <div class="step-number">3</div>
                            Convert to QuickBooks Format
                        </div>
                        <button type="submit" class="convert-btn" disabled id="convertBtn">
                            🔄 Convert Statement
                        </button>
                    </div>
                </form>
                
                <!-- Results Section -->
                <div class="result-section" id="resultSection">
                    <div id="resultContent"></div>
                </div>
            </div>
            
            <div class="footer">
                <p>Albanian Bank Statement Converter | QuickBooks Compatible</p>
                <p style="margin-top: 5px; font-size: 0.9em;">Supports: BKT, OTP, Raiffeisen, Tirana Bank, Union Bank, E-Bill</p>
            </div>
        </div>
        
        <script>
            let selectedBank = null;
            let selectedFile = null;
            
            function selectBank(bankId) {
                selectedBank = bankId;
                
                // Update UI
                document.querySelectorAll('.bank-card').forEach(card => {
                    card.classList.remove('selected');
                });
                document.querySelector(`[data-bank="${bankId}"]`).classList.add('selected');
                
                // Enable upload
                document.getElementById('step2').classList.add('active');
                document.getElementById('uploadArea').classList.remove('disabled');
                document.getElementById('uploadBtn').disabled = false;
                
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
                }
            }
            
            // Drag and drop
            const uploadArea = document.getElementById('uploadArea');
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                if (!uploadArea.classList.contains('disabled')) {
                    const file = e.dataTransfer.files[0];
                    if (file) {
                        document.getElementById('fileInput').files = e.dataTransfer.files;
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
                            <a href="/download/${result.job_id}" class="download-btn">⬇️ Download QuickBooks CSV</a>
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

#!/usr/bin/env python3
"""
Bank-Specific Converter Web Interface
=====================================
Uses individual bank converter scripts for accurate conversion
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import subprocess
import tempfile
import shutil
from datetime import datetime
import uuid

app = Flask(__name__)

# Load configuration
try:
    from config import config
    config_name = os.environ.get('FLASK_ENV', 'production')
    app.config.from_object(config[config_name])
except ImportError:
    # Fallback configuration if config.py is not available
    app.secret_key = os.environ.get('SECRET_KEY', 'bank-specific-converter-key-change-this')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

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
    try:
        current_time = datetime.now().timestamp()
        
        # Clean up import folder - remove files older than 1 hour
        for file_path in os.listdir(UPLOAD_FOLDER):
            full_path = os.path.join(UPLOAD_FOLDER, file_path)
            if os.path.isfile(full_path):
                file_age = current_time - os.path.getctime(full_path)
                if file_age > 3600:  # 1 hour
                    os.remove(full_path)
                    print(f"🧹 Cleaned up old import file: {file_path}")
        
        # Clean up export folder - remove files older than 1 hour
        for file_path in os.listdir(CONVERTED_FOLDER):
            full_path = os.path.join(CONVERTED_FOLDER, file_path)
            if os.path.isfile(full_path):
                file_age = current_time - os.path.getctime(full_path)
                if file_age > 3600:  # 1 hour
                    os.remove(full_path)
                    print(f"🧹 Cleaned up old export file: {file_path}")
        
        # Clean up expired jobs from memory (older than 2 hours)
        expired_jobs = []
        for job_id, job in conversion_jobs.items():
            job_time = datetime.fromisoformat(job['created_at']).timestamp()
            if current_time - job_time > 7200:  # 2 hours
                expired_jobs.append(job_id)
        
        for job_id in expired_jobs:
            conversion_jobs.pop(job_id, None)
            print(f"🧹 Cleaned up expired job: {job_id}")
            
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

# Initialize cleanup on startup
import atexit
import threading
import time

def periodic_cleanup():
    """Run cleanup every 30 minutes"""
    while True:
        time.sleep(1800)  # 30 minutes
        cleanup_old_files()

# Start background cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

# Clean up on app exit
atexit.register(cleanup_old_files)

@app.route('/')
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
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
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
            
            .progress-bar {
                width: 100%;
                height: 10px;
                background: #ecf0f1;
                border-radius: 5px;
                overflow: hidden;
                margin: 15px 0;
            }
            
            .progress-fill {
                height: 100%;
                background: #27ae60;
                width: 0%;
                transition: width 0.3s;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .alert {
                padding: 15px;
                margin: 15px 0;
                border-radius: 5px;
                font-weight: bold;
            }
            
            .alert.warning {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏦 Albanian Bank Statement Converter</h1>
                <p>Convert your bank statements to QuickBooks format using bank-specific converters</p>
                <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 14px; color: #2d5a2d;">
                    🔒 <strong>Privacy:</strong> All files are automatically deleted after download. No data is permanently stored on our servers.
                </div>
            </div>
            
            <div class="converter-section">
                <form id="converterForm" method="POST" action="/convert" enctype="multipart/form-data">
                    
                    <!-- Step 1: Select Bank -->
                    <div class="step active" id="step1">
                        <div class="step-title">
                            <span class="step-number">1</span>
                            Select Your Bank
                        </div>
                        <div class="bank-grid">
                            {% for bank_id, bank_info in banks.items() %}
                            <div class="bank-card" onclick="selectBank('{{ bank_id }}')">
                                <div class="bank-name">{{ bank_info.name }}</div>
                                <div class="bank-formats">Formats: {{ ', '.join(bank_info.formats) }}</div>
                                <div class="bank-description">{{ bank_info.description }}</div>
                            </div>
                            {% endfor %}
                        </div>
                        <input type="hidden" id="selectedBank" name="bank" value="">
                    </div>
                    
                    <!-- Step 2: Upload File -->
                    <div class="step" id="step2">
                        <div class="step-title">
                            <span class="step-number">2</span>
                            Upload Bank Statement
                        </div>
                        
                        <div class="alert warning" id="bankAlert" style="display: none;">
                            Please select a bank first before uploading your statement.
                        </div>
                        
                        <div class="upload-area disabled" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                            <div id="uploadContent">
                                <h3>📄 Drag & Drop or Click to Upload</h3>
                                <p>Supported formats: <span id="supportedFormats">Select a bank first</span></p>
                                <p>Maximum file size: 50MB</p>
                                <button type="button" class="upload-btn" id="uploadBtn" disabled>Choose File</button>
                            </div>
                        </div>
                        
                        <input type="file" id="fileInput" name="file" class="file-input" accept=".pdf,.csv" onchange="handleFileSelect(this)">
                        
                        <div id="selectedFileInfo" class="selected-file" style="display: none;">
                            <strong>Selected File:</strong> <span id="fileName"></span><br>
                            <strong>Size:</strong> <span id="fileSize"></span><br>
                            <strong>Bank:</strong> <span id="selectedBankName"></span>
                        </div>
                    </div>
                    
                    <!-- Step 3: Convert -->
                    <div class="step" id="step3">
                        <div class="step-title">
                            <span class="step-number">3</span>
                            Convert Statement
                        </div>
                        
                        <button type="submit" class="convert-btn" id="convertBtn" disabled>
                            🔄 Convert to QuickBooks Format
                        </button>
                    </div>
                </form>
                
                <!-- Results Section -->
                <div id="resultSection" class="result-section">
                    <div id="resultContent"></div>
                </div>
            </div>
        </div>
        
        <script>
            let selectedBankId = null;
            let selectedFile = null;
            
            function selectBank(bankId) {
                // Remove previous selection
                document.querySelectorAll('.bank-card').forEach(card => {
                    card.classList.remove('selected');
                });
                
                // Select new bank
                document.querySelector(`[onclick="selectBank('${bankId}')"]`).classList.add('selected');
                selectedBankId = bankId;
                document.getElementById('selectedBank').value = bankId;
                
                // Get bank info
                const banks = {{ banks|tojson }};
                const bankInfo = banks[bankId];
                
                // Update upload area
                document.getElementById('uploadArea').classList.remove('disabled');
                document.getElementById('uploadBtn').disabled = false;
                document.getElementById('supportedFormats').textContent = bankInfo.formats.join(', ');
                document.getElementById('bankAlert').style.display = 'none';
                
                // Activate step 2
                document.getElementById('step2').classList.add('active');
                
                updateConvertButton();
            }
            
            function handleFileSelect(input) {
                if (!selectedBankId) {
                    document.getElementById('bankAlert').style.display = 'block';
                    return;
                }
                
                const file = input.files[0];
                if (file) {
                    selectedFile = file;
                    
                    // Show file info
                    document.getElementById('fileName').textContent = file.name;
                    document.getElementById('fileSize').textContent = formatFileSize(file.size);
                    
                    const banks = {{ banks|tojson }};
                    document.getElementById('selectedBankName').textContent = banks[selectedBankId].name;
                    
                    document.getElementById('selectedFileInfo').style.display = 'block';
                    document.getElementById('step3').classList.add('active');
                    
                    updateConvertButton();
                }
            }
            
            function updateConvertButton() {
                const convertBtn = document.getElementById('convertBtn');
                if (selectedBankId && selectedFile) {
                    convertBtn.disabled = false;
                } else {
                    convertBtn.disabled = true;
                }
            }
            
            function formatFileSize(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
            
            // Handle form submission
            document.getElementById('converterForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                if (!selectedBankId || !selectedFile) {
                    alert('Please select a bank and upload a file first.');
                    return;
                }
                
                // Show processing
                const resultSection = document.getElementById('resultSection');
                resultSection.className = 'result-section processing';
                resultSection.style.display = 'block';
                resultSection.innerHTML = `
                    <div class="spinner"></div>
                    <h3>Processing your ${document.getElementById('selectedBankName').textContent} statement...</h3>
                    <p>This may take a few moments depending on the file size.</p>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                `;
                
                // Simulate progress
                let progress = 0;
                const progressInterval = setInterval(() => {
                    progress += Math.random() * 30;
                    if (progress > 90) progress = 90;
                    document.getElementById('progressFill').style.width = progress + '%';
                }, 500);
                
                // Submit form
                const formData = new FormData(this);
                
                fetch('/convert', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    clearInterval(progressInterval);
                    document.getElementById('progressFill').style.width = '100%';
                    
                    setTimeout(() => {
                        if (data.success) {
                            resultSection.className = 'result-section success';
                            resultSection.innerHTML = `
                                <h3>✅ Conversion Successful!</h3>
                                <p>Your ${data.bank_name} statement has been successfully converted to QuickBooks format.</p>
                                <p><strong>Output File:</strong> ${data.output_file}</p>
                                <a href="${data.download_url}" class="download-btn">📥 Download QBO File</a>
                                <button onclick="resetForm()" class="upload-btn" style="margin-left: 15px;">🔄 Convert Another File</button>
                            `;
                        } else {
                            resultSection.className = 'result-section error';
                            resultSection.innerHTML = `
                                <h3>❌ Conversion Failed</h3>
                                <p><strong>Error:</strong> ${data.error}</p>
                                <p>Please check your file format and try again.</p>
                                <button onclick="resetForm()" class="upload-btn">🔄 Try Again</button>
                            `;
                        }
                    }, 1000);
                })
                .catch(error => {
                    clearInterval(progressInterval);
                    resultSection.className = 'result-section error';
                    resultSection.innerHTML = `
                        <h3>❌ Upload Error</h3>
                        <p><strong>Error:</strong> ${error.message}</p>
                        <button onclick="resetForm()" class="upload-btn">🔄 Try Again</button>
                    `;
                });
            });
            
            function resetForm() {
                // Reset form
                document.getElementById('converterForm').reset();
                selectedBankId = null;
                selectedFile = null;
                
                // Reset UI
                document.querySelectorAll('.bank-card').forEach(card => {
                    card.classList.remove('selected');
                });
                
                document.getElementById('selectedFileInfo').style.display = 'none';
                document.getElementById('resultSection').style.display = 'none';
                document.getElementById('uploadArea').classList.add('disabled');
                document.getElementById('uploadBtn').disabled = true;
                document.getElementById('convertBtn').disabled = true;
                
                document.getElementById('step2').classList.remove('active');
                document.getElementById('step3').classList.remove('active');
                
                document.getElementById('supportedFormats').textContent = 'Select a bank first';
            }
            
            // Drag and drop functionality
            const uploadArea = document.getElementById('uploadArea');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight(e) {
                if (!selectedBankId) return;
                uploadArea.classList.add('dragover');
            }
            
            function unhighlight(e) {
                uploadArea.classList.remove('dragover');
            }
            
            uploadArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                if (!selectedBankId) return;
                
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length > 0) {
                    document.getElementById('fileInput').files = files;
                    handleFileSelect(document.getElementById('fileInput'));
                }
            }
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html_content, banks=BANK_CONFIGS)

@app.route('/convert', methods=['POST'])
def convert_statement():
    """Convert bank statement using specific bank script"""
    try:
        # Get form data
        bank_id = request.form.get('bank')
        file = request.files.get('file')
        
        if not bank_id or bank_id not in BANK_CONFIGS:
            return jsonify({'success': False, 'error': 'Invalid bank selection'})
        
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        bank_config = BANK_CONFIGS[bank_id]
        
        # Create job ID
        job_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Check file format is supported by the bank
        supported_formats = [fmt.lower() for fmt in bank_config['formats']]
        if file_ext.replace('.', '') not in supported_formats:
            return jsonify({
                'success': False, 
                'error': f'File format {file_ext} not supported by {bank_config["name"]}. Supported formats: {", ".join(bank_config["formats"])}'
            })
        
        # Create input file path
        input_filename = f"{bank_id}_{timestamp}_{filename}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)
        
        # Use export folder directly (no individual job directories)
        output_dir = CONVERTED_FOLDER
        
        # Get absolute paths
        script_path = get_script_path(bank_config['script'])
        script_path = os.path.abspath(script_path)
        input_abs_path = os.path.abspath(input_path)
        
        # Check if script exists
        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'error': f'Converter script not found: {script_path}. Checked locations: {[get_script_path(bank_config["script"])]}'
            })
        
        # Run the specific bank converter script
        try:
            # Change to the script's directory to ensure relative paths work
            script_dir = os.path.dirname(script_path)
            original_cwd = os.getcwd()
            
            os.chdir(script_dir)
            
            # Run the script with the input file
            # Set environment to handle Unicode properly on Windows
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                ['python', os.path.basename(script_path), input_abs_path],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            # Change back to original directory
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                # Find generated QBO/CSV files
                output_files = []
                
                # Look in common output locations
                search_dirs = [
                    os.path.dirname(input_abs_path),  # Same dir as input
                    os.path.join(os.path.dirname(script_path), 'export'),  # export folder
                    os.path.join(os.path.dirname(script_path), 'converted'),  # converted folder
                    script_dir  # script directory
                ]
                
                for search_dir in search_dirs:
                    if os.path.exists(search_dir):
                        for file in os.listdir(search_dir):
                            # Look for both .qbo and .csv files (especially 4qbo.csv files)
                            if (file.endswith('.qbo') or file.endswith('.csv')) and (timestamp in file or job_id in file or 'converted' in file.lower() or '4qbo' in file.lower()):
                                source_path = os.path.join(search_dir, file)
                                if os.path.getctime(source_path) > (datetime.now().timestamp() - 300):  # Created in last 5 minutes
                                    output_files.append(source_path)
                
                # If no timestamped files found, look for any recent QBO/CSV files
                if not output_files:
                    for search_dir in search_dirs:
                        if os.path.exists(search_dir):
                            for file in os.listdir(search_dir):
                                if file.endswith('.qbo') or (file.endswith('.csv') and '4qbo' in file.lower()):
                                    source_path = os.path.join(search_dir, file)
                                    if os.path.getctime(source_path) > (datetime.now().timestamp() - 300):
                                        output_files.append(source_path)
                
                if output_files:
                    # Use the most recent output file
                    latest_output = max(output_files, key=os.path.getctime)
                    
                    # Determine output extension based on input file
                    file_ext = '.csv' if latest_output.endswith('.csv') else '.qbo'
                    
                    # Create output filename based on original filename + " - 4qbo"
                    original_name = os.path.splitext(filename)[0]  # Remove extension from original filename (without prefix)
                    output_filename = f"{original_name} - 4qbo{file_ext}"
                    output_path = os.path.join(output_dir, output_filename)
                    shutil.copy2(latest_output, output_path)
                    
                    # Store job info (including input path for later cleanup)
                    conversion_jobs[job_id] = {
                        'bank': bank_id,
                        'bank_name': bank_config['name'],
                        'input_file': input_filename,
                        'input_path': input_path,  # Store for cleanup after download
                        'output_file': output_filename,
                        'output_path': output_path,
                        'created_at': datetime.now().isoformat(),
                        'status': 'completed'
                    }
                    
                    # Don't clean up input file yet - wait until after download
                    
                    return jsonify({
                        'success': True,
                        'job_id': job_id,
                        'bank_name': bank_config['name'],
                        'output_file': output_filename,
                        'download_url': f'/download/{job_id}',
                        'message': f'Successfully converted {bank_config["name"]} statement'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'No output file generated. Script output: {result.stdout}\\n{result.stderr}'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Conversion failed: {result.stderr or result.stdout}'
                })
                
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'error': 'Conversion timed out. File may be too large or corrupted.'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Script execution error: {str(e)}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/download/<job_id>')
def download_file(job_id):
    """Download converted file and clean up afterward"""
    if job_id not in conversion_jobs:
        return "Job not found", 404
    
    job = conversion_jobs[job_id]
    
    if not os.path.exists(job['output_path']):
        return "File not found", 404
    
    # Determine mimetype based on file extension
    mimetype = 'text/csv' if job['output_file'].endswith('.csv') else 'application/vnd.quickbooks'
    
    # Create a response with the file
    response = send_file(
        job['output_path'],
        as_attachment=True,
        download_name=job['output_file'],
        mimetype=mimetype
    )
    
    # Schedule cleanup after response is sent
    @response.call_on_close
    def cleanup_files():
        try:
            # Delete the converted file
            if os.path.exists(job['output_path']):
                os.remove(job['output_path'])
                print(f"🗑️ Deleted converted file: {job['output_file']}")
            
            # Delete the input file
            if 'input_path' in job and os.path.exists(job['input_path']):
                os.remove(job['input_path'])
                print(f"🗑️ Deleted input file: {job['input_file']}")
            
            # Remove job from memory (no directories to clean since we use flat structure)
            conversion_jobs.pop(job_id, None)
            
            print(f"✅ Complete cleanup for job {job_id}")
        except Exception as e:
            print(f"⚠️ Cleanup warning for job {job_id}: {e}")
    
    return response

@app.route('/status/<job_id>')
def job_status(job_id):
    """Get job status"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(conversion_jobs[job_id])

@app.route('/cleanup')
def manual_cleanup():
    """Manual cleanup endpoint for testing"""
    cleanup_old_files()
    
    # Count remaining files
    upload_count = len([f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))])
    converted_count = len([f for f in os.listdir(CONVERTED_FOLDER) if os.path.isfile(os.path.join(CONVERTED_FOLDER, f))])
    jobs_count = len(conversion_jobs)
    
    return jsonify({
        'message': 'Cleanup completed',
        'remaining_import_files': upload_count,
        'remaining_export_files': converted_count,
        'active_jobs': jobs_count
    })

@app.route('/server-status')
def server_status():
    """Server status and storage info"""
    import_files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
    export_files = [f for f in os.listdir(CONVERTED_FOLDER) if os.path.isfile(os.path.join(CONVERTED_FOLDER, f))]
    
    return jsonify({
        'server': 'Bank Statement Converter',
        'status': 'running',
        'active_jobs': len(conversion_jobs),
        'import_files_count': len(import_files),
        'export_files_count': len(export_files),
        'cleanup_enabled': True,
        'auto_delete_after_download': True,
        'folder_structure': 'Flat (import/export only)',
        'storage': {
            'import_folder': str(UPLOAD_FOLDER),
            'export_folder': str(CONVERTED_FOLDER),
            'files_in_import': import_files[:10],  # Show first 10
            'files_in_export': export_files[:10]  # Show first 10
        }
    })

@app.route('/api/info')
def api_info():
    """API information"""
    return jsonify({
        'name': 'Bank-Specific Albanian Statement Converter',
        'version': '1.0.0',
        'description': 'Convert Albanian bank statements using individual bank-specific scripts',
        'features': [
            'Auto-delete files after download',
            'Periodic cleanup of old files',
            'No permanent file storage',
            'Memory-only job tracking'
        ],
        'supported_banks': {bank_id: config['name'] for bank_id, config in BANK_CONFIGS.items()},
        'bank_details': BANK_CONFIGS
    })

if __name__ == '__main__':
    print("🏦 Bank-Specific Albanian Statement Converter")
    print("=" * 60)
    print("🌐 Starting web server...")
    print(f"� Import folder: {UPLOAD_FOLDER}")
    print(f"� Export folder: {CONVERTED_FOLDER}")
    print("🗂️  Flat file structure (no job directories)")
    print("🏛️ Supported banks:")
    for bank_id, config in BANK_CONFIGS.items():
        print(f"   - {config['name']} ({', '.join(config['formats'])})")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5002, debug=True)
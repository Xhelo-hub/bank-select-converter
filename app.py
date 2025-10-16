#!/usr/bin/env python3
"""
Albanian Bank Statement Converter - Web Interface
=================================================
A Flask web application for converting Albanian bank statements to QuickBooks format.

Features:
- Upload PDF/CSV bank statements
- Automatic bank detection and conversion
- Download converted QuickBooks CSV files
- Multi-currency support (ALL, USD, EUR)
- Supports all major Albanian banks
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import subprocess
import sys
import json
import time
from pathlib import Path

# Import the converter modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = 'bank-statement-converter-2025-secure-key'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuration
UPLOAD_FOLDER = 'web_uploads'
CONVERTED_FOLDER = 'web_converted'
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'txt'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)
os.makedirs('export', exist_ok=True)

# Session storage for conversion jobs
conversion_jobs = {}

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_bank_type(filepath):
    """Detect bank type from file content."""
    try:
        filename = os.path.basename(filepath).lower()
        
        # Read file content for detection
        if filepath.endswith('.pdf'):
            # For PDF files, use filename patterns
            if 'otp' in filename or 'otp' in filepath.lower():
                return 'OTP'
            elif 'bkt' in filename:
                return 'BKT'
            elif 'raiffeisen' in filename or 'rai' in filename:
                return 'RAIFFEISEN'
            elif 'tibank' in filename or 'tabank' in filename:
                return 'TIBANK'
            elif 'union' in filename:
                return 'UNION'
            elif 'ebill' in filename or 'e-bill' in filename:
                return 'EBILL'
        
        elif filepath.endswith('.csv'):
            # For CSV files, check content
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000).lower()  # Read first 1000 chars
                
                if 'raiffeisen' in content or 'rai bank' in content:
                    return 'RAIFFEISEN'
                elif 'otp' in content:
                    return 'OTP'
                elif 'bkt' in content:
                    return 'BKT'
                elif 'tibank' in content or 'tabank' in content:
                    return 'TIBANK'
                elif 'union' in content:
                    return 'UNION'
        
        # Default to universal converter
        return 'UNIVERSAL'
        
    except Exception as e:
        print(f"Error detecting bank type: {e}")
        return 'UNIVERSAL'

def get_converter_script(bank_type):
    """Get the appropriate converter script for bank type."""
    converters = {
        'OTP': 'OTP-2-QBO.py',
        'BKT': 'BKT-2-QBO.py',
        'RAIFFEISEN': 'RAI-2-QBO.py',
        'TIBANK': 'TIBANK-2-QBO.py',
        'UNION': 'UNION-2-QBO.py',
        'EBILL': 'Ebill-2-QBO (pdf-converter).py',
        'UNIVERSAL': 'ALL-BANKS-2-QBO.py'
    }
    return converters.get(bank_type, 'ALL-BANKS-2-QBO.py')

def convert_file(filepath, job_id):
    """Convert a bank statement file to QuickBooks format."""
    try:
        # Update job status
        conversion_jobs[job_id]['status'] = 'processing'
        conversion_jobs[job_id]['message'] = 'Detecting bank type...'
        
        # Detect bank type
        bank_type = detect_bank_type(filepath)
        converter_script = get_converter_script(bank_type)
        
        conversion_jobs[job_id]['bank_type'] = bank_type
        conversion_jobs[job_id]['message'] = f'Converting {bank_type} statement...'
        
        # Copy file to main directory for processing
        filename = os.path.basename(filepath)
        temp_file = os.path.join('.', f'temp_{job_id}_{filename}')
        shutil.copy2(filepath, temp_file)
        
        # Run the converter
        result = subprocess.run([
            sys.executable, converter_script
        ], capture_output=True, text=True, cwd='.')
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        if result.returncode == 0:
            # Find the converted file in export directory
            export_files = []
            for file in os.listdir('export'):
                if file.endswith('.csv') and os.path.getmtime(os.path.join('export', file)) > time.time() - 300:  # Files created in last 5 minutes
                    export_files.append(file)
            
            if export_files:
                # Move converted file to web converted folder
                latest_file = max(export_files, key=lambda x: os.path.getmtime(os.path.join('export', x)))
                source_path = os.path.join('export', latest_file)
                dest_path = os.path.join(CONVERTED_FOLDER, f'{job_id}_{latest_file}')
                shutil.move(source_path, dest_path)
                
                conversion_jobs[job_id]['status'] = 'completed'
                conversion_jobs[job_id]['message'] = 'Conversion completed successfully!'
                conversion_jobs[job_id]['output_file'] = f'{job_id}_{latest_file}'
                conversion_jobs[job_id]['original_filename'] = latest_file
            else:
                conversion_jobs[job_id]['status'] = 'error'
                conversion_jobs[job_id]['message'] = 'No output file generated'
        else:
            conversion_jobs[job_id]['status'] = 'error'
            conversion_jobs[job_id]['message'] = f'Conversion failed: {result.stderr}'
            
    except Exception as e:
        conversion_jobs[job_id]['status'] = 'error'
        conversion_jobs[job_id]['message'] = f'Error: {str(e)}'

@app.route('/')
def index():
    """Main upload page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start conversion."""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f'{job_id}_{filename}')
        file.save(filepath)
        
        # Initialize conversion job
        conversion_jobs[job_id] = {
            'status': 'uploaded',
            'message': 'File uploaded successfully',
            'filename': filename,
            'upload_time': datetime.now(),
            'bank_type': None,
            'output_file': None,
            'original_filename': None
        }
        
        # Start conversion in background
        try:
            convert_file(filepath, job_id)
        except Exception as e:
            conversion_jobs[job_id]['status'] = 'error'
            conversion_jobs[job_id]['message'] = f'Conversion error: {str(e)}'
        
        return redirect(url_for('conversion_status', job_id=job_id))
    else:
        flash('Invalid file type. Please upload PDF or CSV files only.')
        return redirect(request.url)

@app.route('/status/<job_id>')
def conversion_status(job_id):
    """Show conversion status page."""
    if job_id not in conversion_jobs:
        flash('Invalid job ID')
        return redirect(url_for('index'))
    
    job = conversion_jobs[job_id]
    return render_template('status.html', job=job, job_id=job_id)

@app.route('/api/status/<job_id>')
def api_status(job_id):
    """API endpoint for checking conversion status."""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Invalid job ID'}), 404
    
    job = conversion_jobs[job_id]
    return jsonify({
        'status': job['status'],
        'message': job['message'],
        'bank_type': job.get('bank_type'),
        'filename': job['filename'],
        'can_download': job['status'] == 'completed' and job.get('output_file')
    })

@app.route('/download/<job_id>')
def download_file(job_id):
    """Download converted file."""
    if job_id not in conversion_jobs:
        flash('Invalid job ID')
        return redirect(url_for('index'))
    
    job = conversion_jobs[job_id]
    if job['status'] != 'completed' or not job.get('output_file'):
        flash('File not ready for download')
        return redirect(url_for('conversion_status', job_id=job_id))
    
    file_path = os.path.join(CONVERTED_FOLDER, job['output_file'])
    if not os.path.exists(file_path):
        flash('File not found')
        return redirect(url_for('conversion_status', job_id=job_id))
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=job['original_filename']
    )

@app.route('/cleanup')
def cleanup_old_files():
    """Clean up old files (older than 1 hour)."""
    cutoff_time = datetime.now() - timedelta(hours=1)
    cleaned = 0
    
    # Clean conversion jobs
    jobs_to_remove = []
    for job_id, job in conversion_jobs.items():
        if job['upload_time'] < cutoff_time:
            jobs_to_remove.append(job_id)
    
    for job_id in jobs_to_remove:
        # Remove files
        upload_file = os.path.join(UPLOAD_FOLDER, f"{job_id}_*")
        converted_file = os.path.join(CONVERTED_FOLDER, f"{job_id}_*")
        
        for pattern in [upload_file, converted_file]:
            import glob
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    cleaned += 1
                except:
                    pass
        
        # Remove job record
        del conversion_jobs[job_id]
    
    return jsonify({'cleaned_files': cleaned, 'active_jobs': len(conversion_jobs)})

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('File is too large. Maximum size is 50MB.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🏦 Albanian Bank Statement Converter - Web Interface")
    print("=" * 55)
    print("🌐 Starting web server...")
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("📁 Export folder:", CONVERTED_FOLDER)
    print("🔧 Max file size: 50MB")
    print("📄 Supported formats: PDF, CSV")
    print("🏛️  Supported banks: OTP, BKT, Raiffeisen, TI Bank, Union Bank, E-Bills")
    print("=" * 55)
    
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
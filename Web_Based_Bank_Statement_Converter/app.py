#!/usr/bin/env python3
"""
Web-Based Bank Statement Converter API
=====================================
A professional Flask API for converting Albanian bank statements to QuickBooks format.

Version: 1.0.0
Author: Xhelo-hub
License: MIT
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_cors import CORS
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
import logging
from logging.handlers import RotatingFileHandler

# Add the converters directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'converters'))

# Import converter modules
from src.converters.bank_detector import BankDetector
from src.converters.universal_converter import UniversalConverter
from src.converters.file_manager import FileManager

# Initialize Flask app
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# Enable CORS for API endpoints
CORS(app)

# Configuration
app.config.update(
    SECRET_KEY='web-bank-converter-2025-secure-key-v1',
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max file size
    UPLOAD_FOLDER='uploads',
    CONVERTED_FOLDER='converted',
    DEBUG=True,
    API_VERSION='1.0.0',
    API_TITLE='Web-Based Bank Statement Converter API',
    API_DESCRIPTION='Convert Albanian bank statements to QuickBooks format via web interface and REST API'
)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CONVERTED_FOLDER'], exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Setup logging
if not app.debug:
    file_handler = RotatingFileHandler('logs/api.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Web-Based Bank Statement Converter API startup')

# Session storage for conversion jobs
conversion_jobs = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'txt'}

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API Routes
@app.route('/api/info')
def api_info():
    """Get API information and version."""
    return jsonify({
        'name': app.config['API_TITLE'],
        'version': app.config['API_VERSION'],
        'description': app.config['API_DESCRIPTION'],
        'endpoints': {
            'upload': '/api/upload',
            'status': '/api/status/<job_id>',
            'download': '/api/download/<job_id>',
            'supported_banks': '/api/banks',
            'health': '/api/health'
        },
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': '50MB',
        'supported_banks': [
            'OTP Bank', 'BKT Bank', 'Raiffeisen Bank', 
            'TI Bank', 'Union Bank', 'E-Bills'
        ]
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': app.config['API_VERSION'],
        'active_jobs': len(conversion_jobs)
    })

@app.route('/api/banks')
def supported_banks():
    """Get list of supported banks."""
    return jsonify({
        'banks': [
            {
                'code': 'OTP',
                'name': 'OTP Bank',
                'formats': ['PDF', 'CSV'],
                'features': ['Auto-detection', 'Multi-currency']
            },
            {
                'code': 'BKT',
                'name': 'BKT Bank', 
                'formats': ['PDF', 'CSV'],
                'features': ['Balance verification', 'Multi-currency']
            },
            {
                'code': 'RAIFFEISEN',
                'name': 'Raiffeisen Bank',
                'formats': ['PDF', 'CSV'],
                'features': ['Multi-currency', 'EUR/USD support']
            },
            {
                'code': 'TIBANK',
                'name': 'TI Bank (formerly TABANK)',
                'formats': ['PDF', 'CSV'],
                'features': ['Albanian date formats', 'Multi-currency']
            },
            {
                'code': 'UNION',
                'name': 'Union Bank',
                'formats': ['PDF', 'CSV'],
                'features': ['Multi-line descriptions', 'Multi-currency']
            },
            {
                'code': 'EBILL',
                'name': 'E-Bills',
                'formats': ['PDF', 'CSV', 'TXT'],
                'features': ['Electronic bill processing', 'Tax calculation']
            }
        ]
    })

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint for file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not (file and allowed_file(file.filename)):
        return jsonify({'error': 'Invalid file type. Allowed: PDF, CSV, TXT'}), 400
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{job_id}_{filename}')
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
        
        # Start conversion process
        file_manager = FileManager()
        universal_converter = UniversalConverter()
        
        try:
            # Detect bank type
            bank_detector = BankDetector()
            bank_type = bank_detector.detect_bank(filepath)
            
            conversion_jobs[job_id]['status'] = 'processing'
            conversion_jobs[job_id]['bank_type'] = bank_type
            conversion_jobs[job_id]['message'] = f'Converting {bank_type} statement...'
            
            # Convert file
            output_file = universal_converter.convert_file(filepath, bank_type)
            
            if output_file and os.path.exists(output_file):
                # Move to converted folder
                dest_path = os.path.join(app.config['CONVERTED_FOLDER'], f'{job_id}_{os.path.basename(output_file)}')
                shutil.move(output_file, dest_path)
                
                conversion_jobs[job_id]['status'] = 'completed'
                conversion_jobs[job_id]['message'] = 'Conversion completed successfully!'
                conversion_jobs[job_id]['output_file'] = f'{job_id}_{os.path.basename(output_file)}'
                conversion_jobs[job_id]['original_filename'] = os.path.basename(output_file)
            else:
                conversion_jobs[job_id]['status'] = 'error'
                conversion_jobs[job_id]['message'] = 'Conversion failed - no output generated'
                
        except Exception as e:
            conversion_jobs[job_id]['status'] = 'error'
            conversion_jobs[job_id]['message'] = f'Conversion error: {str(e)}'
        
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            'job_id': job_id,
            'status': conversion_jobs[job_id]['status'],
            'message': conversion_jobs[job_id]['message'],
            'bank_type': conversion_jobs[job_id].get('bank_type'),
            'status_url': f'/api/status/{job_id}',
            'download_url': f'/api/download/{job_id}' if conversion_jobs[job_id]['status'] == 'completed' else None
        })
        
    except Exception as e:
        app.logger.error(f'Upload error: {str(e)}')
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/status/<job_id>')
def api_status(job_id):
    """API endpoint for checking conversion status."""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Invalid job ID'}), 404
    
    job = conversion_jobs[job_id]
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'message': job['message'],
        'bank_type': job.get('bank_type'),
        'filename': job['filename'],
        'upload_time': job['upload_time'].isoformat(),
        'can_download': job['status'] == 'completed' and job.get('output_file'),
        'download_url': f'/api/download/{job_id}' if job['status'] == 'completed' and job.get('output_file') else None
    })

@app.route('/api/download/<job_id>')
def api_download(job_id):
    """API endpoint for downloading converted files."""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Invalid job ID'}), 404
    
    job = conversion_jobs[job_id]
    if job['status'] != 'completed' or not job.get('output_file'):
        return jsonify({'error': 'File not ready for download'}), 400
    
    file_path = os.path.join(app.config['CONVERTED_FOLDER'], job['output_file'])
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=job['original_filename']
    )

# Web Interface Routes
@app.route('/')
def index():
    """Main web interface page."""
    return render_template('index.html', api_info={
        'version': app.config['API_VERSION'],
        'title': app.config['API_TITLE']
    })

@app.route('/upload', methods=['POST'])
def web_upload():
    """Web interface file upload."""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Use API upload logic
        response = api_upload()
        if isinstance(response, tuple) and response[1] != 200:
            flash('Upload failed')
            return redirect(url_for('index'))
        
        # Extract job_id from API response
        data = response.get_json() if hasattr(response, 'get_json') else json.loads(response.data)
        job_id = data.get('job_id')
        
        return redirect(url_for('web_status', job_id=job_id))
    else:
        flash('Invalid file type. Please upload PDF or CSV files only.')
        return redirect(url_for('index'))

@app.route('/status/<job_id>')
def web_status(job_id):
    """Web interface status page."""
    if job_id not in conversion_jobs:
        flash('Invalid job ID')
        return redirect(url_for('index'))
    
    job = conversion_jobs[job_id]
    return render_template('status.html', job=job, job_id=job_id)

@app.route('/download/<job_id>')
def web_download(job_id):
    """Web interface download."""
    return api_download(job_id)

@app.route('/api/cleanup')
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
        upload_pattern = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_*")
        converted_pattern = os.path.join(app.config['CONVERTED_FOLDER'], f"{job_id}_*")
        
        import glob
        for pattern in [upload_pattern, converted_pattern]:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    cleaned += 1
                except:
                    pass
        
        # Remove job record
        del conversion_jobs[job_id]
    
    return jsonify({
        'cleaned_files': cleaned, 
        'active_jobs': len(conversion_jobs),
        'cleanup_time': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413
    else:
        flash('File is too large. Maximum size is 50MB.')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    else:
        return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    else:
        return render_template('500.html'), 500

if __name__ == '__main__':
    print("🏦 Web-Based Bank Statement Converter API v1.0.0")
    print("=" * 60)
    print("🌐 Starting web server...")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📁 Converted folder: {app.config['CONVERTED_FOLDER']}")
    print("🔧 Max file size: 50MB")
    print("📄 Supported formats: PDF, CSV, TXT")
    print("🏛️  Supported banks: OTP, BKT, Raiffeisen, TI Bank, Union Bank, E-Bills")
    print("🔗 API endpoints: /api/info, /api/upload, /api/status, /api/download")
    print("=" * 60)
    
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
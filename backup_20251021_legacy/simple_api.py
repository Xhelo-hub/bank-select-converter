#!/usr/bin/env python3
"""
Simple API Test Server - Web-Based Bank Statement Converter
"""

from flask import Flask, jsonify, request, render_template_string, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
CORS(app)

# Configuration
MAX_FILE_SIZE_MB = 50
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Job storage
conversion_jobs = {}

@app.route('/')
def index():
    """Main page with simple HTML interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bank Statement Converter API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
            .section { background: white; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; margin: 20px 0; }
            .endpoint { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .method { color: #28a745; font-weight: bold; }
            .path { color: #007bff; font-weight: bold; }
            .upload-form { margin: 20px 0; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; border-radius: 8px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏦 Albanian Bank Statement Converter API</h1>
                <p>Professional API for converting Albanian bank statements to QuickBooks format</p>
                <p><strong>Status:</strong> ✅ Online | <strong>Version:</strong> 1.0.0</p>
            </div>

            <div class="section">
                <h2>📋 API Endpoints</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/info</span><br>
                    <small>Get API information and supported banks</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/upload</span><br>
                    <small>Upload bank statement for conversion (PDF or CSV)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/status/{job_id}</span><br>
                    <small>Check conversion job status</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/download/{job_id}</span><br>
                    <small>Download converted QBO file</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/health</span><br>
                    <small>Health check endpoint</small>
                </div>
            </div>

            <div class="section">
                <h2>🏛️ Supported Banks</h2>
                <ul>
                    <li><strong>OTP Bank</strong> - PDF and CSV formats</li>
                    <li><strong>BKT Bank</strong> - PDF and CSV formats</li>
                    <li><strong>Raiffeisen Bank</strong> - PDF and CSV formats</li>
                    <li><strong>TI Bank</strong> - PDF and CSV formats</li>
                    <li><strong>Union Bank</strong> - PDF and CSV formats</li>
                    <li><strong>E-Bills</strong> - CSV format</li>
                </ul>
            </div>

            <div class="section">
                <h2>📤 Quick Upload Test</h2>
                <form method="post" action="/api/upload" enctype="multipart/form-data">
                    <div class="upload-area">
                        <input type="file" name="file" accept=".pdf,.csv" required>
                        <br><br>
                        <button type="submit">Upload & Convert</button>
                    </div>
                </form>
            </div>

            <div class="section">
                <h2>🔗 API Testing</h2>
                <p>Test the API endpoints:</p>
                <button onclick="testApiInfo()">Test /api/info</button>
                <button onclick="testHealth()">Test /health</button>
                
                <div id="api-result" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; display: none;"></div>
            </div>
        </div>

        <script>
            async function testApiInfo() {
                try {
                    const response = await fetch('/api/info');
                    const data = await response.json();
                    document.getElementById('api-result').style.display = 'block';
                    document.getElementById('api-result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('api-result').style.display = 'block';
                    document.getElementById('api-result').innerHTML = '<span style="color: red;">Error: ' + error.message + '</span>';
                }
            }

            async function testHealth() {
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    document.getElementById('api-result').style.display = 'block';
                    document.getElementById('api-result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    document.getElementById('api-result').style.display = 'block';
                    document.getElementById('api-result').innerHTML = '<span style="color: red;">Error: ' + error.message + '</span>';
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/api/info')
def api_info():
    """Get API information"""
    return jsonify({
        'version': '1.0.0',
        'name': 'Albanian Bank Statement Converter API',
        'description': 'Convert Albanian bank statements to QuickBooks format',
        'supported_banks': [
            'OTP Bank',
            'BKT Bank', 
            'Raiffeisen Bank',
            'TI Bank',
            'Union Bank',
            'E-Bills'
        ],
        'supported_formats': ['PDF', 'CSV'],
        'max_file_size_mb': MAX_FILE_SIZE_MB,
        'endpoints': {
            'info': 'GET /api/info',
            'upload': 'POST /api/upload',
            'status': 'GET /api/status/{job_id}',
            'download': 'GET /api/download/{job_id}',
            'health': 'GET /health'
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': 'running',
        'version': '1.0.0'
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and conversion"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job entry
    conversion_jobs[job_id] = {
        'status': 'processing',
        'filename': file.filename,
        'created_at': datetime.now().isoformat(),
        'message': 'File uploaded successfully, processing...'
    }
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
        file.save(filepath)
        
        # Simulate conversion (replace with actual conversion logic)
        conversion_jobs[job_id]['status'] = 'completed'
        conversion_jobs[job_id]['message'] = 'Conversion completed successfully'
        conversion_jobs[job_id]['download_url'] = f'/api/download/{job_id}'
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'message': 'File uploaded and converted successfully',
            'download_url': f'/api/download/{job_id}'
        })
        
    except Exception as e:
        conversion_jobs[job_id]['status'] = 'error'
        conversion_jobs[job_id]['message'] = f'Error: {str(e)}'
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>')
def check_status(job_id):
    """Check conversion job status"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(conversion_jobs[job_id])

@app.route('/api/download/<job_id>')
def download_file(job_id):
    """Download converted file"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = conversion_jobs[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': 'Conversion not completed'}), 400
    
    # For now, return a simple QBO file
    qbo_content = """!Type:Bank
D01/01/2024
T-100.00
PTest Transaction
^
"""
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.qbo', delete=False)
    temp_file.write(qbo_content)
    temp_file.close()
    
    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name=f"converted_{job_id}.qbo",
        mimetype='application/vnd.quickbooks'
    )

if __name__ == '__main__':
    print("🏦 Albanian Bank Statement Converter - Simple API Server")
    print("="*60)
    print("🌐 Starting server...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Export folder: {CONVERTED_FOLDER}")
    print(f"🔧 Max file size: {MAX_FILE_SIZE_MB}MB")
    print("📄 Supported formats: PDF, CSV")
    print("🏛️ Supported banks: OTP, BKT, Raiffeisen, TI Bank, Union Bank, E-Bills")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
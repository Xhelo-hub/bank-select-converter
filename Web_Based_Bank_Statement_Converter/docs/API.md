# 📡 API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
Currently no authentication required. Ready for API key implementation.

## Headers
```http
Content-Type: application/json
Accept: application/json
```

## Rate Limiting
- No current limits
- Ready for implementation (recommended: 100 requests/minute)

---

## 📊 Endpoints

### 1. API Information
**Get API metadata and available endpoints**

```http
GET /api/info
```

**Response 200:**
```json
{
  "name": "Web-Based Bank Statement Converter API",
  "version": "1.0.0",
  "description": "Convert Albanian bank statements to QuickBooks format",
  "endpoints": {
    "upload": "/api/upload",
    "status": "/api/status/<job_id>",
    "download": "/api/download/<job_id>",
    "supported_banks": "/api/banks",
    "health": "/api/health"
  },
  "supported_formats": ["pdf", "csv", "txt"],
  "max_file_size": "50MB",
  "supported_banks": ["OTP Bank", "BKT Bank", "Raiffeisen Bank", "TI Bank", "Union Bank", "E-Bills"]
}
```

### 2. Health Check
**Check API service health and status**

```http
GET /api/health
```

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T10:30:00Z",
  "version": "1.0.0",
  "active_jobs": 3
}
```

### 3. Supported Banks
**Get list of supported Albanian banks**

```http
GET /api/banks
```

**Response 200:**
```json
{
  "banks": [
    {
      "code": "OTP",
      "name": "OTP Bank",
      "formats": ["PDF", "CSV"],
      "features": ["Auto-detection", "Multi-currency"]
    },
    {
      "code": "BKT",
      "name": "BKT Bank",
      "formats": ["PDF", "CSV"],
      "features": ["Balance verification", "Multi-currency"]
    },
    {
      "code": "RAIFFEISEN",
      "name": "Raiffeisen Bank",
      "formats": ["PDF", "CSV"],
      "features": ["Multi-currency", "EUR/USD support"]
    },
    {
      "code": "TIBANK",
      "name": "TI Bank (formerly TABANK)",
      "formats": ["PDF", "CSV"],
      "features": ["Albanian date formats", "Multi-currency"]
    },
    {
      "code": "UNION",
      "name": "Union Bank",
      "formats": ["PDF", "CSV"],
      "features": ["Multi-line descriptions", "Multi-currency"]
    },
    {
      "code": "EBILL",
      "name": "E-Bills",
      "formats": ["PDF", "CSV", "TXT"],
      "features": ["Electronic bill processing", "Tax calculation"]
    }
  ]
}
```

### 4. File Upload
**Upload and convert a bank statement file**

```http
POST /api/upload
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (file, required): Bank statement file
  - **Formats**: PDF, CSV, TXT
  - **Max size**: 50MB
  - **Encoding**: UTF-8 recommended for CSV/TXT

**Response 200 (Success):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Conversion completed successfully!",
  "bank_type": "RAIFFEISEN",
  "status_url": "/api/status/550e8400-e29b-41d4-a716-446655440000",
  "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000"
}
```

**Response 400 (Bad Request):**
```json
{
  "error": "No file provided"
}
```

**Response 400 (Invalid File):**
```json
{
  "error": "Invalid file type. Allowed: PDF, CSV, TXT"
}
```

**Response 413 (File Too Large):**
```json
{
  "error": "File too large. Maximum size is 50MB."
}
```

**Response 500 (Server Error):**
```json
{
  "error": "Upload failed: [error details]"
}
```

### 5. Conversion Status
**Check the status of a conversion job**

```http
GET /api/status/{job_id}
```

**Path Parameters:**
- `job_id` (string, required): Unique job identifier from upload response

**Response 200:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Conversion completed successfully!",
  "bank_type": "RAIFFEISEN",
  "filename": "statement_june_2025.csv",
  "upload_time": "2025-10-15T10:30:00Z",
  "can_download": true,
  "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Values:**
- `uploaded`: File received and queued
- `processing`: Conversion in progress
- `completed`: Conversion successful, file ready
- `error`: Conversion failed

**Response 404:**
```json
{
  "error": "Invalid job ID"
}
```

### 6. Download Converted File
**Download the converted QuickBooks CSV file**

```http
GET /api/download/{job_id}
```

**Path Parameters:**
- `job_id` (string, required): Job identifier from upload response

**Response 200:**
- Content-Type: `application/octet-stream`
- Content-Disposition: `attachment; filename="converted_file.csv"`
- Body: CSV file content

**Response 400:**
```json
{
  "error": "File not ready for download"
}
```

**Response 404 (Invalid Job):**
```json
{
  "error": "Invalid job ID"
}
```

**Response 404 (File Not Found):**
```json
{
  "error": "File not found"
}
```

### 7. Cleanup Files
**Manually trigger cleanup of old files**

```http
GET /api/cleanup
```

**Response 200:**
```json
{
  "cleaned_files": 5,
  "active_jobs": 2,
  "cleanup_time": "2025-10-15T10:30:00Z"
}
```

---

## 🔄 Workflow

### Standard Conversion Flow

1. **Upload File**
   ```http
   POST /api/upload
   ```

2. **Check Status** (if needed)
   ```http
   GET /api/status/{job_id}
   ```

3. **Download Result**
   ```http
   GET /api/download/{job_id}
   ```

### Polling for Status

```javascript
function pollStatus(jobId) {
    const interval = setInterval(async () => {
        const response = await fetch(`/api/status/${jobId}`);
        const status = await response.json();
        
        if (status.status === 'completed') {
            clearInterval(interval);
            window.location.href = `/api/download/${jobId}`;
        } else if (status.status === 'error') {
            clearInterval(interval);
            console.error('Conversion failed:', status.message);
        }
    }, 2000); // Check every 2 seconds
}
```

---

## 📄 File Formats

### Input Formats

#### PDF Files
- **Text-based PDFs** (not scanned images)
- **Bank statement format** with transaction details
- **Albanian/English** content supported
- **Multi-page** documents supported

#### CSV Files
- **UTF-8 encoding** recommended
- **Common delimiters**: comma, semicolon, tab
- **Headers** optional but helpful for detection
- **Date formats**: DD/MM/YYYY, DD.MM.YYYY, ISO 8601

#### TXT Files
- **Structured text** from bank exports
- **Tab-delimited** or **space-separated** formats
- **UTF-8 encoding** for Albanian characters

### Output Format

#### QuickBooks CSV
```csv
Date,Description,Amount,Type
2025-06-15,"Wire Transfer - ACME Corp Invoice #1234",1500.00,Debit
2025-06-16,"Deposit - Client Payment",2500.00,Credit
2025-06-17,"Fee - Monthly Service Charge",15.00,Debit
```

**Column Specifications:**
- **Date**: ISO 8601 format (YYYY-MM-DD)
- **Description**: UTF-8 encoded, quotes escaped
- **Amount**: Decimal format, no currency symbols
- **Type**: "Debit" or "Credit"

---

## 🏦 Bank-Specific Features

### OTP Bank
- **PDF parsing** with OCR fallback
- **Multi-currency** statements (ALL, USD, EUR)
- **Branch detection** from statement headers

### BKT Bank
- **Balance verification** against closing balance
- **Multi-account** statement support
- **Transaction categorization** improvements

### Raiffeisen Bank
- **CSV format specialization** for online banking exports
- **Foreign currency** handling (USD, EUR, GBP)
- **Investment account** transaction support

### TI Bank (TABANK)
- **Albanian date format** parsing (DD.MM.YYYY)
- **Local month names** (Jan, Shk, Mar, etc.)
- **Legacy format** support for TABANK files

### Union Bank
- **Multi-line description** handling
- **Reference number** extraction
- **Fee calculation** and separation

### E-Bills
- **Electronic invoice** processing
- **Tax calculation** (15% withholding)
- **Vendor identification** from bill data

---

## 🚨 Error Handling

### Error Response Format
```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-15T10:30:00Z",
  "job_id": "550e8400-e29b-41d4-a716-446655440000" // if applicable
}
```

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `FILE_TOO_LARGE` | File exceeds 50MB limit | Compress or split the file |
| `INVALID_FORMAT` | Unsupported file type | Use PDF, CSV, or TXT format |
| `CONVERSION_FAILED` | Bank conversion error | Check file format and content |
| `FILE_NOT_FOUND` | Uploaded file missing | Re-upload the file |
| `JOB_EXPIRED` | Job older than 1 hour | Upload a new file |
| `INVALID_JOB_ID` | Job ID not found | Check the job ID format |

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **413 Payload Too Large**: File size exceeds limit
- **500 Internal Server Error**: Server processing error

---

## 🔒 Security Considerations

### File Security
- Files are automatically deleted after 1 hour
- Upload paths are sanitized to prevent directory traversal
- File content is validated before processing
- No executable files are accepted

### API Security
- Input validation on all endpoints
- Error messages don't expose system information
- File processing is sandboxed
- Ready for authentication implementation

### Privacy Protection
- No file content is logged or stored permanently
- Processing is done locally without external API calls
- Converted files are only accessible via job ID
- Session management prevents unauthorized access

---

## 📊 Usage Examples

### Python SDK Example
```python
import requests
import time

class BankConverterAPI:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
    
    def convert_file(self, file_path):
        # Upload file
        with open(file_path, 'rb') as f:
            response = requests.post(f"{self.base_url}/upload", 
                                   files={'file': f})
        
        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.json()}")
        
        job_data = response.json()
        job_id = job_data['job_id']
        
        # Wait for completion
        while True:
            status = requests.get(f"{self.base_url}/status/{job_id}").json()
            
            if status['status'] == 'completed':
                # Download result
                download_response = requests.get(f"{self.base_url}/download/{job_id}")
                return download_response.content
            elif status['status'] == 'error':
                raise Exception(f"Conversion failed: {status['message']}")
            
            time.sleep(2)

# Usage
api = BankConverterAPI()
csv_content = api.convert_file('statement.pdf')
with open('converted.csv', 'wb') as f:
    f.write(csv_content)
```

### Node.js Example
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

class BankConverterAPI {
    constructor(baseUrl = 'http://localhost:5000/api') {
        this.baseUrl = baseUrl;
    }
    
    async convertFile(filePath) {
        // Upload file
        const form = new FormData();
        form.append('file', fs.createReadStream(filePath));
        
        const uploadResponse = await axios.post(`${this.baseUrl}/upload`, form, {
            headers: form.getHeaders()
        });
        
        const jobId = uploadResponse.data.job_id;
        
        // Wait for completion
        while (true) {
            const statusResponse = await axios.get(`${this.baseUrl}/status/${jobId}`);
            const status = statusResponse.data;
            
            if (status.status === 'completed') {
                const downloadResponse = await axios.get(`${this.baseUrl}/download/${jobId}`, {
                    responseType: 'stream'
                });
                return downloadResponse.data;
            } else if (status.status === 'error') {
                throw new Error(`Conversion failed: ${status.message}`);
            }
            
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
}

// Usage
const api = new BankConverterAPI();
api.convertFile('statement.pdf').then(stream => {
    stream.pipe(fs.createWriteStream('converted.csv'));
});
```

---

## 📈 Performance Guidelines

### Optimal File Sizes
- **PDF**: 1-10MB (optimal), up to 50MB (supported)
- **CSV**: 100KB-5MB (optimal), up to 50MB (supported)
- **TXT**: 50KB-1MB (optimal), up to 50MB (supported)

### Processing Times
- **Small files** (< 1MB): 2-5 seconds
- **Medium files** (1-10MB): 5-30 seconds
- **Large files** (10-50MB): 30-300 seconds

### Best Practices
- **Compress large PDFs** before upload when possible
- **Use CSV format** for fastest processing
- **Poll status every 2-5 seconds** (not more frequently)
- **Implement timeout handling** for large files
- **Cache API responses** when appropriate

---

## 🔧 Integration Examples

### WordPress Plugin Integration
```php
<?php
function convert_bank_statement($file_path) {
    $api_url = 'http://localhost:5000/api';
    
    // Upload file
    $curl = curl_init();
    curl_setopt_array($curl, [
        CURLOPT_URL => $api_url . '/upload',
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => [
            'file' => new CURLFile($file_path)
        ],
        CURLOPT_RETURNTRANSFER => true,
    ]);
    
    $response = curl_exec($curl);
    $data = json_decode($response, true);
    $job_id = $data['job_id'];
    
    // Wait for completion
    while (true) {
        $status_response = file_get_contents($api_url . '/status/' . $job_id);
        $status = json_decode($status_response, true);
        
        if ($status['status'] === 'completed') {
            return file_get_contents($api_url . '/download/' . $job_id);
        } elseif ($status['status'] === 'error') {
            throw new Exception('Conversion failed: ' . $status['message']);
        }
        
        sleep(2);
    }
}
?>
```

### React Component
```jsx
import React, { useState } from 'react';

function BankStatementConverter() {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('idle');
    const [downloadUrl, setDownloadUrl] = useState(null);
    
    const handleUpload = async () => {
        const formData = new FormData();
        formData.append('file', file);
        
        setStatus('uploading');
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            const jobId = data.job_id;
            
            // Poll for status
            const pollStatus = setInterval(async () => {
                const statusResponse = await fetch(`/api/status/${jobId}`);
                const statusData = await statusResponse.json();
                
                setStatus(statusData.status);
                
                if (statusData.status === 'completed') {
                    clearInterval(pollStatus);
                    setDownloadUrl(`/api/download/${jobId}`);
                } else if (statusData.status === 'error') {
                    clearInterval(pollStatus);
                    alert('Conversion failed: ' + statusData.message);
                }
            }, 2000);
            
        } catch (error) {
            setStatus('error');
            console.error('Upload failed:', error);
        }
    };
    
    return (
        <div>
            <input 
                type="file" 
                accept=".pdf,.csv,.txt"
                onChange={(e) => setFile(e.target.files[0])} 
            />
            <button onClick={handleUpload} disabled={!file || status === 'uploading'}>
                Convert Statement
            </button>
            
            {status === 'processing' && <p>Converting file...</p>}
            {status === 'completed' && (
                <a href={downloadUrl} download>Download Converted File</a>
            )}
        </div>
    );
}
```

This comprehensive API documentation provides everything developers need to integrate the Albanian Bank Statement Converter into their applications.
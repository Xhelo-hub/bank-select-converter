# 🌐 Albanian Bank Statement Converter - Web Interface

## 🚀 Quick Start

### Option 1: Double-Click to Start
1. Double-click `start_web_interface.bat` 
2. Web interface opens automatically at http://127.0.0.1:5000
3. Upload your bank statement file
4. Download the converted QuickBooks CSV file

### Option 2: Manual Start
```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start web server
python app.py
```

## 📱 How to Use

### 1. Upload Bank Statement
- **Drag & Drop** or **Click to Browse** your bank statement file
- **Supported formats**: PDF, CSV, TXT
- **Maximum file size**: 50 MB
- **Supported banks**: OTP, BKT, Raiffeisen, TI Bank, Union Bank, E-Bills

### 2. Automatic Conversion
- Bank type is **automatically detected**
- File is processed using the appropriate converter
- **Real-time status updates** show progress
- **Multi-currency support** (ALL, USD, EUR)

### 3. Download Results
- **Download** your QuickBooks-ready CSV file
- Files are **automatically deleted** after 1 hour for security
- **Direct import** to QuickBooks supported

## 🏛️ Supported Albanian Banks

| Bank | PDF Support | CSV Support | Features |
|------|-------------|-------------|----------|
| **OTP Bank** | ✅ | ✅ | Auto-detection from content |
| **BKT Bank** | ✅ | ✅ | Balance verification |
| **Raiffeisen** | ✅ | ✅ | Multi-currency (ALL, USD, EUR) |
| **TI Bank** | ✅ | ✅ | Albanian date formats |
| **Union Bank** | ✅ | ✅ | Multi-line descriptions |
| **E-Bills** | ✅ | ✅ | Electronic bill processing |

## 🔧 Features

### ✨ Web Interface Features
- **Modern responsive design** - Works on desktop, tablet, and mobile
- **Drag & drop upload** - Easy file handling
- **Real-time progress** - Live status updates during conversion
- **Automatic bank detection** - No manual selection needed
- **Secure file handling** - Files deleted after 1 hour
- **Download management** - Direct download links for converted files

### 🏦 Bank Conversion Features
- **Multi-format support** - PDF and CSV input files
- **Multi-currency processing** - ALL, USD, EUR transactions
- **QuickBooks compatibility** - Ready-to-import CSV output
- **Withholding tax calculation** - 15% Albanian tax rate
- **Date standardization** - ISO 8601 format (YYYY-MM-DD)
- **Balance verification** - Ensures conversion accuracy

## 🔒 Security & Privacy

- **Local processing** - All conversion happens on your server
- **No cloud uploads** - Files never leave your network
- **Automatic cleanup** - Files deleted after 1 hour
- **Secure file handling** - Protected upload/download paths
- **No data retention** - Zero logging of financial data

## 📊 Output Format

### QuickBooks CSV Structure
```csv
Date,Description,Amount,Type
2025-06-15,"Transfer Payment for services",1500.00,Debit
2025-06-20,"Deposit Client Payment",2500.00,Credit
```

### Import to QuickBooks
1. Open QuickBooks
2. Go to **Banking** > **Bank Deposit** 
3. Select **Import from CSV**
4. Choose your downloaded file
5. Map columns: **Date**, **Description**, **Amount**, **Type**
6. Review and import transactions

## 🌐 Network Access

The web interface runs on:
- **Local access**: http://127.0.0.1:5000
- **Network access**: http://[your-ip]:5000

To access from other devices on your network:
1. Find your computer's IP address
2. Use http://[your-ip]:5000 from other devices
3. Ensure Windows Firewall allows port 5000

## 🛠️ Technical Requirements

### System Requirements
- **Operating System**: Windows 10/11, macOS, Linux
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 1GB free space

### Dependencies
- **Flask 2.3.3** - Web framework
- **PyPDF2 3.0.1** - PDF processing
- **Werkzeug 2.3.7** - WSGI utilities
- **requests 2.31.0** - HTTP library

## 🚨 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Error: Address already in use
# Solution: Use different port
python app.py --port 5001
```

#### File Upload Fails
- **Check file size** - Maximum 50MB
- **Check file format** - Only PDF, CSV, TXT allowed
- **Check file permissions** - Ensure file is not locked

#### Conversion Fails
- **Check bank type** - Ensure file is from supported bank
- **Check file content** - File must contain transaction data
- **Check file format** - PDF must be text-readable, not scanned image

#### Browser Issues
- **Clear cache** - Refresh browser (Ctrl+F5)
- **Try different browser** - Chrome, Firefox, Edge supported
- **Check JavaScript** - Must be enabled for status updates

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "File too large" | File > 50MB | Compress or split file |
| "Invalid file type" | Wrong format | Use PDF, CSV, or TXT only |
| "No file selected" | Empty upload | Select a file first |
| "Conversion failed" | Unsupported format | Check bank type and file content |

## 📞 Support

### File Issues
1. Check if your bank is supported
2. Verify file format (PDF/CSV)
3. Ensure file contains transaction data
4. Try the command-line version for troubleshooting

### Web Interface Issues
1. Restart the web server
2. Clear browser cache
3. Try different browser
4. Check firewall settings

### Getting Help
- Check individual converter documentation in `Readme/` folder
- Review command-line converter logs
- Test with sample files first

## 🔄 Development Mode

For development and testing:

```bash
# Enable debug mode
export FLASK_ENV=development
python app.py

# Custom port
python app.py --port 8080

# External access
python app.py --host 0.0.0.0
```

## 📈 Performance Tips

### For Large Files
- **Batch processing** - Process multiple files separately
- **File compression** - Compress PDFs before upload
- **Regular cleanup** - Clear old files regularly

### For Multiple Users
- **Increase timeout** - Modify cleanup interval
- **Add file limits** - Set per-user quotas
- **Monitor storage** - Watch disk space usage

---

## 🎯 Perfect For

- **📊 Accounting Firms** - Client statement processing
- **🏢 Albanian Businesses** - Multi-bank account management  
- **💼 Bookkeepers** - Efficient workflow automation
- **👤 Individual Users** - Personal banking organization
- **🔄 Regular Processing** - Daily/weekly statement conversion

---

**🇦🇱 Built specifically for Albanian banking standards and QuickBooks integration**

*Supports all major Albanian banks with proper currency handling and tax calculations*
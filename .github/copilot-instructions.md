# Albanian Bank Statement Converter - AI Agent Instructions

## Project Overview
This is a Python-based bank statement conversion system that transforms Albanian bank statements (PDF/CSV) into QuickBooks-compatible CSV format. The system supports 6 Albanian banks with both individual converter scripts and a Flask web interface.

**GitHub Repository**: [Xhelo-hub/bank-select-converter](https://github.com/Xhelo-hub/bank-select-converter)

## Architecture

### Three-Layer Structure
1. **Individual Converters** (Root directory): Standalone Python scripts (`BKT-2-QBO.py`, `RAI-2-QBO.py`, etc.)
   - Each script is self-contained and can run independently
   - Uses `import/` and `export/` folders for file I/O
   - Pattern: `extract_text_from_pdf()` → `parse_{bank}_statement()` → write CSV
   
2. **Web Interface** (`Bank_Specific_Converter/`): Flask app that invokes the individual scripts
   - Uses `subprocess.run()` to execute converter scripts
   - Bank selection → File upload → Script execution → Download
   - Automatic file cleanup (1 hour retention)
   
3. **Legacy System** (`Web_Based_Bank_Statement_Converter/`): Previous implementation, not actively used

### Critical Design Pattern: Script Invocation
The web app (`Bank_Specific_Converter/app.py`) does NOT reimplement conversion logic. It:
- Accepts file uploads
- Copies files to `import/` folder
- Invokes the appropriate `*-2-QBO.py` script via subprocess
- Returns the converted file from `export/` folder

**Example from `app.py` line ~700+:**
```python
result = subprocess.run(
    [sys.executable, script_path, '--input', input_path, '--output', output_dir],
    capture_output=True, text=True, timeout=300
)
```

## Bank-Specific Processing

### Supported Banks (BANK_CONFIGS in `Bank_Specific_Converter/app.py`)
- **BKT**: PDF/CSV via `BKT-2-QBO.py`
- **OTP**: PDF/CSV via `OTP-2-QBO.py`
- **RAIFFEISEN**: PDF/CSV via `RAI-2-QBO.py`
- **TIBANK**: PDF/CSV via `TIBANK-2-QBO.py`
- **UNION**: PDF/CSV via `UNION-2-QBO.py`
- **EBILL**: PDF only via `Withholding.py`

### Converter Script Structure Pattern
All bank converters follow this structure:
```python
def extract_text_from_pdf(pdf_path):
    # PyPDF2 extraction
    
def parse_{bank}_statement(text_content):
    # Regex patterns to extract transactions
    # Returns transactions list
    
def get_versioned_filename(file_path):
    # Prevents overwrites with (v.1), (v.2) suffix
    
if __name__ == "__main__":
    # CLI with import/ and export/ folder handling
```

### Date Handling Convention
- **Input formats**: Varies by bank (DD-MMM-YY, DD.MM.YYYY, etc.)
- **Output format**: YYYY-MM-DD (ISO 8601) - **Always use this for QuickBooks compatibility**
- Albanian month names (Janar, Shkurt, Mars...) handled in some converters

## Development Workflow

### Repository Setup
```bash
# Clone repository
git clone https://github.com/Xhelo-hub/bank-select-converter.git
cd bank-select-converter
```

### Local Development
```powershell
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run web interface
cd Bank_Specific_Converter
python app.py  # Runs on http://127.0.0.1:5002

# Test individual converter
python BKT-2-QBO.py  # Processes all files in current dir or import/
```

### Dependencies (requirements.txt)
```
Flask==2.3.3
PyPDF2==3.0.1
requests==2.31.0
```

## Production Deployment (HestiaCP/Hetzner)

### Deployment Stack
- **Server**: Hetzner with HestiaCP
- **WSGI**: Gunicorn (via `wsgi.py`)
- **Web Server**: Nginx (configured via HestiaCP)
- **DNS**: Cloudflare with proxied SSL

### Key Deployment Files
- `Bank_Specific_Converter/config.py`: Environment-based config (development vs production)
- `Bank_Specific_Converter/wsgi.py`: Production entry point
- `Bank_Specific_Converter/deploy.sh`: Systemd service setup script
- `DEPLOYMENT_GUIDE.md`: Complete HestiaCP deployment instructions

### File Paths in Production
```python
# From config.py
BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_FOLDER = BASE_DIR / 'import'  # NOT 'uploads'
CONVERTED_FOLDER = BASE_DIR / 'export'  # NOT 'converted'
SCRIPTS_DIR = BASE_DIR.parent  # Converter scripts are in parent directory
```

### Auto-Cleanup System
Background thread in `Bank_Specific_Converter/app.py`:
- Runs every 30 minutes
- Deletes files older than 1 hour from `import/` and `export/`
- Removes expired jobs from memory (2 hours)

## Code Conventions

### File Organization
- **Input**: `import/` folder (or current directory for standalone scripts)
- **Output**: `export/` folder with `" - 4qbo.csv"` suffix
- **Versioning**: Append `(v.1)`, `(v.2)` if file exists (never overwrite)

### CSV Output Format (QuickBooks Standard)
Headers: `Date,Description,Debit,Credit,Balance`
- Date: ISO 8601 (YYYY-MM-DD)
- Amounts: Float strings (e.g., "1500.50")
- Description: Merged from multiple fields with `|` separator

### Error Handling Pattern
```python
try:
    # Conversion logic
except Exception as e:
    print(f"Error: {e}")
    return {'success': False, 'error': str(e)}
```

## Testing & Debugging

### No Automated Tests
Currently no test suite. Manual testing approach:
1. Place sample bank statement in `import/` or current directory
2. Run converter script: `python BKT-2-QBO.py`
3. Check `export/` for output file
4. Verify CSV format in Excel/QuickBooks

### Debug Mode
```python
# In Bank_Specific_Converter/app.py
FLASK_ENV=development python app.py  # Enables debug mode
```

## Common Tasks

### Adding a New Bank
1. Create `{BANK}-2-QBO.py` in root directory following existing pattern
2. Add entry to `BANK_CONFIGS` dict in `Bank_Specific_Converter/app.py`
3. Update README.md with supported formats

### Modifying Conversion Logic
**Always edit the individual converter script**, not the web app. The web interface only invokes scripts.

### Deployment Updates
```bash
cd /home/admin/bank-select-converter
git pull origin main
systemctl restart bank-converter
```

## Anti-Patterns to Avoid

❌ Don't duplicate conversion logic in `Bank_Specific_Converter/app.py`  
✅ Invoke the standalone converter scripts via subprocess

❌ Don't use relative paths for scripts in production  
✅ Use `get_script_path()` helper to check multiple locations

❌ Don't keep uploaded files indefinitely  
✅ Rely on automatic cleanup (1 hour retention)

❌ Don't mix Albanian and English in user-facing messages  
✅ Web interface is English, converter output can have Albanian metadata

## Security Considerations

- Max file size: 50MB (Flask config: `MAX_CONTENT_LENGTH`)
- Allowed extensions: `.pdf`, `.csv`, `.txt` only
- Automatic file cleanup prevents data accumulation
- No authentication system (single-tenant deployment model)
- Files stored with random UUIDs as job IDs

## Related Documentation

- `README.md`: User-facing quick start guide
- `README-COMPLETE.md`: Comprehensive feature documentation  
- `DEPLOYMENT_GUIDE.md`: HestiaCP production deployment
- `Bank_Specific_Converter/README.md`: Web interface specifics
- `Readme/*.txt`: Individual bank converter guides

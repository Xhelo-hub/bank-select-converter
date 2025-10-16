# Bank-Specific Albanian Statement Converter

A web interface that uses your existing individual bank converter scripts directly, ensuring the same accurate conversion as when running the scripts individually.

## Features

- **Bank Selection Interface**: Choose your specific bank before uploading
- **Individual Script Execution**: Uses your existing converter scripts (BKT-2-QBO.py, RAI-2-QBO.py, etc.)
- **Drag & Drop Upload**: Easy file upload with progress indication
- **Real-time Conversion**: Live progress tracking and status updates
- **Direct Download**: Download converted QBO files immediately

## Supported Banks

- **BKT Bank** (PDF, CSV) → Uses `BKT-2-QBO.py`
- **OTP Bank** (PDF, CSV) → Uses `OTP-2-QBO.py`  
- **Raiffeisen Bank** (PDF, CSV) → Uses `RAI-2-QBO.py`
- **TI Bank** (PDF, CSV) → Uses `TIBANK-2-QBO.py`
- **Union Bank** (PDF, CSV) → Uses `UNION-2-QBO.py`
- **E-Bills** (PDF) → Uses `Ebill-2-QBO (pdf-converter).py`

## Installation

1. Navigate to the project directory:
   ```bash
   cd Bank_Specific_Converter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and go to: `http://localhost:5002`

## How It Works

1. **Select Bank**: Choose your bank from the available options
2. **Upload File**: Drag & drop or select your bank statement (PDF or CSV)
3. **Convert**: Click convert to process using the specific bank script
4. **Download**: Download your converted QBO file for QuickBooks

## File Structure

```
Bank_Specific_Converter/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── uploads/              # Temporary file uploads
├── converted/            # Converted QBO files
└── README.md            # This file
```

## API Endpoints

- `GET /` - Main web interface
- `POST /convert` - Convert bank statement
- `GET /download/<job_id>` - Download converted file
- `GET /status/<job_id>` - Check conversion status
- `GET /api/info` - API information

## Advantages Over Generic Converter

- **Exact Same Logic**: Uses your original, tested converter scripts
- **Bank-Specific Processing**: Each bank's unique format handled correctly
- **No Format Mixing**: Prevents confusion between different bank formats
- **Proven Results**: Same output as running scripts individually
- **Easy Selection**: Clear bank selection prevents format errors

## Usage Notes

- Maximum file size: 50MB
- Supported formats vary by bank (check the interface for details)
- Converted files are automatically cleaned up after download
- Each conversion gets a unique job ID for tracking

## Troubleshooting

If conversion fails:
1. Ensure the correct bank is selected
2. Verify file format is supported by that bank
3. Check that the original converter script exists in the parent directory
4. Make sure file is not corrupted or password-protected
# INTESA BANK TO QUICKBOOKS CONVERTER
## INTESA-2-QBO.py

### Overview
This converter transforms Intesa Sanpaolo Bank (Albania) CSV statements into QuickBooks-compatible CSV format.

### Supported Format
- **Input**: CSV files exported from Intesa Sanpaolo Bank online banking
- **Output**: QuickBooks CSV format (Date, Description, Debit, Credit, Balance)

### CSV Structure
Intesa Bank CSV files have a specific structure:
- **Line 1**: Account number and account name
- **Line 2**: Opening balance (Bilanci duke u hapur)
- **Line 3**: Closing balance (Bilanci duke u mbyllur)
- **Line 4**: Column headers
- **Line 5+**: Transaction data

### Input Columns
- Data: Transaction date (D.M.YY format)
- Data e vlerës: Value date
- Përshkrimi: Description (complex format with || separators)
- Numri i referencës: Reference number
- Transaction Type: DEBIT or KREDIT
- Valuta: Currency (ALL)
- Shuma: Amount
- Balance Currency: Balance currency
- Balance Amount: Account balance after transaction

### Output Format
QuickBooks-compatible CSV with columns:
- **Date**: ISO format (YYYY-MM-DD)
- **Description**: Cleaned description with beneficiary/debtor and transaction details
- **Debit**: Debit amount (empty if credit transaction)
- **Credit**: Credit amount (empty if debit transaction)
- **Balance**: Account balance

### Features
✅ Albanian date format conversion (D.M.YY → YYYY-MM-DD)
✅ Complex description parsing (extracts main party and Rem Info)
✅ Automatic debit/credit classification based on Transaction Type
✅ Reference number integration in description
✅ Data quality validation and warnings
✅ Automatic file versioning (prevents overwrites)
✅ Skips header rows automatically
✅ Handles Albanian characters (UTF-8 encoding)

### Usage

#### Command Line
```bash
# Process single file
python INTESA-2-QBO.py input_file.csv

# Specify output directory
python INTESA-2-QBO.py input_file.csv --output-dir /path/to/output

# Auto-process all Intesa CSV files in current directory or import/
python INTESA-2-QBO.py
```

#### Web Interface
1. Go to http://127.0.0.1:5002
2. Login with credentials
3. Select **Intesa Sanpaolo Bank**
4. Upload CSV file
5. Download converted QuickBooks CSV

### File Naming
- Output files are named: `[original_filename] - 4qbo.csv`
- If file exists, auto-versions: `[original_filename] - 4qbo (v.1).csv`

### Data Quality Checks
The converter includes automatic validation:
- **Description length check**: Warns if description >1000 chars
- **Transaction type validation**: Detects unknown transaction types
- **Empty row detection**: Skips rows without date or amount
- **Dual transaction warning**: Flags transactions with both debit and credit
- **Error handling**: Continues processing even if individual rows fail

### Example Conversion

**Input (Intesa CSV):**
```
30.9.25,30.9.25,PGROUP INC||Debt::QENDRA IGNIS||Debt Acc::10786731801||Source Reference::30090766F43D||Rem Info::TRN Qendra IGNIS te PGROUP INC lik fat 71/2025 dt 30/09/2025 per Sherbime Shtator 2025,2527302034246000,DEBIT,ALL,50000.00,ALL,590501.15,
```

**Output (QuickBooks CSV):**
```
2025-09-30,Ref: 2527302034246000 | PGROUP INC | TRN Qendra IGNIS te PGROUP INC lik fat 71/2025 dt 30/09/2025 per Sherbime Shtator 2025,50000.00,,590501.15
```

### Common Issues & Solutions

#### Issue: "CSV file too short"
- **Cause**: File has less than 4 lines
- **Solution**: Ensure you're using the complete CSV export from Intesa Bank

#### Issue: "No transactions found"
- **Cause**: All rows are empty or header not recognized
- **Solution**: Check that CSV uses standard Intesa Bank format with "Data," header

#### Issue: "Unknown transaction type"
- **Cause**: Transaction Type column contains unexpected value
- **Solution**: Converter will default to DEBIT and show warning

### Albanian Language Support
The converter handles Albanian-specific elements:
- Date format: D.M.YY (e.g., 30.9.25)
- Headers: "Data", "Përshkrimi", "Shuma"
- Balance text: "Bilanci duke u hapur", "Bilanci duke u mbyllur"
- Transaction types: "DEBIT", "KREDIT"

### Dependencies
- Python 3.7+
- csv (built-in)
- datetime (built-in)
- pathlib (built-in)
- re (built-in)

No external packages required!

### Notes
- Always verify the output against the original statement
- QuickBooks CSV format is compatible with most accounting software
- The converter preserves all transaction details in the description field
- Original balance values are maintained as-is (no recalculation)
- Supports unlimited number of transactions per file

### Author
Created: October 2025
Last Updated: October 21, 2025

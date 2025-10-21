CREDINS BANK TO QUICKBOOKS CONVERTER
=====================================

OVERVIEW
--------
This script converts Credins Bank Albania bank statements (both PDF and CSV formats) 
into QuickBooks-compatible CSV format.

SUPPORTED FORMATS
-----------------
- CSV files exported from Credins Bank e-banking
- PDF bank statements from Credins Bank

INPUT FORMAT
------------
The Credins Bank CSV format includes:
- Date format: DD.MM.YYYY (e.g., 03.01.2025)
- Amount columns: 
  * "Amount" - Debit transactions
  * "Amount1" - Credit transactions
  * Numbers use comma as thousand separator (e.g., "2,889.85")
- BalanceAfter: Account balance after each transaction
- TransactionType: Type of transaction (in Albanian)
- Description1: Detailed transaction description

CSV Structure:
RecordNumber,City1,ValueDate,Amount,Amount1,BalanceAfter,TransactionType,Description1,...

Common Transaction Types:
- Blerje ne terminal POS (POS purchase)
- Transferte kombetare dalese (Domestic transfer outgoing)
- Transferte kombetare hyrese (Domestic transfer incoming)
- Transferte brenda bankes (Internal bank transfer)
- Komision mirembajtje per llogarine (Account maintenance fee)
- Komision i tregtarit (Merchant commission)
- Depozitime cash (Cash deposit)
- Terheqje cash (Cash withdrawal)

OUTPUT FORMAT
-------------
QuickBooks-compatible CSV with columns:
- Date (YYYY-MM-DD format, ISO 8601)
- Description (TransactionType | Description combined)
- Debit (expense/payment amounts)
- Credit (income/deposit amounts)
- Balance (running balance)

USAGE
-----
1. Standalone mode (processes all PDF/CSV files in current directory and import/ folder):
   python CREDINS-2-QBO.py

2. Process specific file:
   python CREDINS-2-QBO.py <filename.csv>
   python CREDINS-2-QBO.py <filename.pdf>

3. With command-line arguments:
   python CREDINS-2-QBO.py --input <input_file> --output <output_directory>

EXAMPLE
-------
Input file: AL75209111220000119234240001_20250101-20250930.csv
Output file: AL75209111220000119234240001_20250101-20250930 - 4qbo.csv

FEATURES
--------
- Automatically detects CSV or PDF format
- Converts Albanian date format (DD.MM.YYYY) to ISO 8601 (YYYY-MM-DD)
- Handles comma thousand separators in amounts
- Combines transaction type and description for better clarity
- Preserves running balance
- Auto-versioning: Creates (v.1), (v.2) if output file exists
- Processes multiple files in batch mode

FOLDER STRUCTURE
----------------
import/     - Place input files here (automatically scanned)
export/     - Converted files appear here with " - 4qbo.csv" suffix

DEPENDENCIES
------------
- Python 3.7+
- PyPDF2 (for PDF processing)
- csv (built-in)
- datetime (built-in)

WEB INTERFACE
-------------
Credins Bank is integrated into the web-based converter interface:
1. Select "Credins Bank" from the bank dropdown
2. Upload PDF or CSV file
3. Download converted QuickBooks CSV

NOTES
-----
- CSV conversion is preferred over PDF as it's more accurate
- The script automatically skips header rows in CSV files
- Albanian text in descriptions is preserved
- All amounts are formatted to 2 decimal places
- Empty debit/credit fields are left blank (not shown as 0.00)

TROUBLESHOOTING
---------------
If conversion fails:
1. Verify the file is a genuine Credins Bank statement
2. Check that CSV contains the expected columns (ValueDate, Amount, Amount1, etc.)
3. Ensure PDF is not password-protected or image-only
4. Check for encoding issues (script uses UTF-8)

For CSV files, the script looks for the header row containing "RecordNumber" 
and "ValueDate" to identify where transaction data begins.

AUTHOR
------
Albanian Bank Statement Converter Project
GitHub: Xhelo-hub/bank-select-converter

DATE
----
October 2025

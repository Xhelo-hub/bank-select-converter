#!/usr/bin/env python3
"""
ProCredit Bank Albania to QuickBooks CSV Converter
==================================================
Converts ProCredit Bank Albania statements (CSV and PDF format) to QuickBooks-compatible CSV.

Bank: ProCredit Bank Albania
Input: CSV or PDF export from ProCredit online banking
Output: QuickBooks CSV (Date, Description, Debit, Credit, Balance)

Features:
- Handles both CSV and PDF formats
- Handles Albanian date format (DD.MM.YYYY)
- Processes amounts with comma as decimal separator
- Supports debit/credit columns (Amount, Amount1 for CSV; Debit, Kredit for PDF)
- Extracts transaction descriptions
- Versioned output files to prevent overwrites

Author: Bank Statement Converter
Date: October 28, 2025
"""

import csv
import sys
import os
from datetime import datetime
from pathlib import Path
import re
import argparse
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: PyPDF2 not installed. PDF support disabled.")

def parse_procredit_amount(amount_str):
    """
    Parse ProCredit amount format to float.
    Format: "14,485.28" or "14.485,28" (European format with comma as decimal)
    
    Args:
        amount_str: String representation of amount
        
    Returns:
        float: Parsed amount
    """
    if not amount_str or amount_str.strip() == '0.00' or amount_str.strip() == '0,00':
        return 0.0
    
    # Remove any spaces
    amount_str = amount_str.strip()
    
    # Check if using comma as decimal separator (European format)
    # Format could be: "14,485.28" or "14.485,28"
    if ',' in amount_str and '.' in amount_str:
        # If both exist, determine which is decimal separator
        comma_pos = amount_str.rfind(',')
        dot_pos = amount_str.rfind('.')
        
        if comma_pos > dot_pos:
            # Comma is decimal: "14.485,28" -> remove dots, replace comma with dot
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            # Dot is decimal: "14,485.28" -> just remove commas
            amount_str = amount_str.replace(',', '')
    elif ',' in amount_str:
        # Only comma exists, assume it's thousands separator if there are more than 2 digits after
        parts = amount_str.split(',')
        if len(parts[-1]) == 2:
            # It's decimal separator: "14,28" -> "14.28"
            amount_str = amount_str.replace(',', '.')
        else:
            # It's thousands separator: "14,485" -> "14485"
            amount_str = amount_str.replace(',', '')
    
    try:
        return float(amount_str)
    except ValueError:
        print(f"Warning: Could not parse amount '{amount_str}', using 0.0")
        return 0.0

def parse_procredit_date(date_str):
    """
    Parse ProCredit date format to ISO format.
    
    Input format: DD.MM.YYYY (e.g., "14.10.2025")
    Output format: YYYY-MM-DD (e.g., "2025-10-14")
    
    Args:
        date_str: Date string in DD.MM.YYYY format
        
    Returns:
        str: Date in YYYY-MM-DD format
    """
    try:
        date_obj = datetime.strptime(date_str.strip(), '%d.%m.%Y')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        print(f"Warning: Could not parse date '{date_str}'")
        return date_str

def extract_description(row):
    """
    Extract and clean transaction description from ProCredit row.
    
    Combines TransactionType and Description1 fields.
    
    Args:
        row: Dictionary containing transaction data
        
    Returns:
        str: Clean description
    """
    transaction_type = row.get('TransactionType', '').strip()
    description = row.get('Description1', '').strip()
    
    # Combine both fields
    if transaction_type and description:
        full_desc = f"{transaction_type} | {description}"
    elif transaction_type:
        full_desc = transaction_type
    elif description:
        full_desc = description
    else:
        full_desc = "Transaction"
    
    # Clean up multiple spaces and newlines
    full_desc = ' '.join(full_desc.split())
    
    return full_desc

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from ProCredit PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    if not PDF_SUPPORT:
        print("Error: PyPDF2 not installed. Cannot process PDF files.")
        return ""
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def parse_procredit_pdf(pdf_path):
    """
    Parse ProCredit Bank PDF file and extract transactions.
    
    PDF format pattern:
    Nr  Nr.Trans  Data  Debit  Kredit  Bilanci  Tipi i Veprimit  Komente mbi Veprimin
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        list: List of transaction dictionaries
    """
    transactions = []
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return transactions
    
    try:
        # Split into tokens (text is separated by newlines)
        tokens = [t.strip() for t in text.split('\n') if t.strip()]
        
        # Find the start of data (after header row)
        start_index = -1
        for i, token in enumerate(tokens):
            if token == "Komente mbi  Veprimin" or token == "Komente mbi Veprimin":
                start_index = i + 1
                break
        
        if start_index == -1:
            print("Error: Could not find data start in PDF")
            return transactions
        
        # Process tokens in groups
        i = start_index
        while i < len(tokens):
            token = tokens[i]
            
            # Check if this is a row number (start of new transaction)
            if token.isdigit() and len(token) <= 3:  # Row numbers are 1-3 digits
                try:
                    # Extract transaction fields
                    row_num = token
                    trans_num = tokens[i + 1] if i + 1 < len(tokens) else ""
                    date_str = tokens[i + 2] if i + 2 < len(tokens) else ""
                    debit_str = tokens[i + 3] if i + 3 < len(tokens) else "0.00"
                    credit_str = tokens[i + 4] if i + 4 < len(tokens) else "0.00"
                    balance_str = tokens[i + 5] if i + 5 < len(tokens) else "0.00"
                    
                    # Validate date format
                    if not re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
                        i += 1
                        continue
                    
                    # Parse amounts
                    debit = parse_procredit_amount(debit_str)
                    credit = parse_procredit_amount(credit_str)
                    balance = parse_procredit_amount(balance_str)
                    
                    # Parse date
                    date = parse_procredit_date(date_str)
                    
                    # Collect description (transaction type + comments)
                    description_parts = []
                    j = i + 6
                    
                    # Look ahead for description text until we hit another row number
                    while j < len(tokens):
                        next_token = tokens[j]
                        
                        # Stop if we hit another row number with valid date pattern ahead
                        if next_token.isdigit() and len(next_token) <= 3:
                            # Check if next tokens look like a new transaction
                            if j + 2 < len(tokens) and re.match(r'\d{2}\.\d{2}\.\d{4}', tokens[j + 2]):
                                break
                        
                        description_parts.append(next_token)
                        j += 1
                        
                        # Limit description length
                        if len(description_parts) > 20:
                            break
                    
                    description = ' '.join(description_parts).strip()
                    if not description:
                        description = "Transaction"
                    
                    # Clean up description
                    description = ' '.join(description.split())  # Remove extra spaces
                    
                    transaction = {
                        'Date': date,
                        'Description': description,
                        'Debit': debit if debit > 0 else 0,
                        'Credit': credit if credit > 0 else 0,
                        'Balance': balance
                    }
                    
                    transactions.append(transaction)
                    i = j  # Move to next transaction
                    
                except (IndexError, ValueError) as e:
                    i += 1
            else:
                i += 1
        
        print(f"Successfully parsed {len(transactions)} transactions from PDF")
        return transactions
        
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
        return []

def parse_procredit_csv(csv_path):
    """
    Parse ProCredit Bank CSV file and extract transactions.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        list: List of transaction dictionaries
    """
    transactions = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as file:
            # Read all lines to find the actual data start
            lines = file.readlines()
            
            # Find the header row (contains RecordNumber, City1, ValueDate, etc.)
            header_row_index = -1
            for i, line in enumerate(lines):
                if 'RecordNumber' in line and 'ValueDate' in line:
                    header_row_index = i
                    break
            
            if header_row_index == -1:
                print("Error: Could not find transaction data header")
                return transactions
            
            # Read from the header row onwards
            reader = csv.DictReader(lines[header_row_index:])
            
            for row in reader:
                # Skip empty rows
                if not row.get('ValueDate'):
                    continue
                
                # Parse amounts
                debit_amount = parse_procredit_amount(row.get('Amount', '0'))
                credit_amount = parse_procredit_amount(row.get('Amount1', '0'))
                balance = parse_procredit_amount(row.get('BalanceAfter', '0'))
                
                # Parse date
                date = parse_procredit_date(row.get('ValueDate', ''))
                
                # Extract description
                description = extract_description(row)
                
                transaction = {
                    'Date': date,
                    'Description': description,
                    'Debit': debit_amount if debit_amount > 0 else 0,
                    'Credit': credit_amount if credit_amount > 0 else 0,
                    'Balance': balance
                }
                
                transactions.append(transaction)
        
        print(f"Successfully parsed {len(transactions)} transactions")
        return transactions
        
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return []

def get_versioned_filename(file_path):
    """
    Generate a versioned filename to avoid overwriting existing files.
    
    Args:
        file_path: Original file path
        
    Returns:
        Path: New file path with version suffix if needed
    """
    path = Path(file_path)
    if not path.exists():
        return path
    
    counter = 1
    while True:
        new_name = f"{path.stem} (v.{counter}){path.suffix}"
        new_path = path.parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def write_quickbooks_csv(transactions, output_path):
    """
    Write transactions to QuickBooks-compatible CSV format.
    
    Args:
        transactions: List of transaction dictionaries
        output_path: Path for output CSV file
        
    Returns:
        str: Path to the created file
    """
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get versioned filename
    output_path = get_versioned_filename(output_path)
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header
            writer.writerow(['Date', 'Description', 'Debit', 'Credit', 'Balance'])
            
            # Write transactions
            for trans in transactions:
                writer.writerow([
                    trans['Date'],
                    trans['Description'],
                    f"{trans['Debit']:.2f}" if trans['Debit'] > 0 else '',
                    f"{trans['Credit']:.2f}" if trans['Credit'] > 0 else '',
                    f"{trans['Balance']:.2f}"
                ])
        
        print(f"✓ QuickBooks CSV created: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"Error writing CSV: {e}")
        return None

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Convert ProCredit Bank Albania CSV or PDF to QuickBooks format'
    )
    parser.add_argument(
        '--input',
        help='Input CSV or PDF file path',
        default=None
    )
    parser.add_argument(
        '--output',
        help='Output directory path',
        default='export'
    )
    
    args = parser.parse_args()
    
    # Determine input file
    if args.input:
        input_files = [args.input]
    else:
        # Look for CSV and PDF files in current directory and import folder
        search_paths = [Path('.'), Path('import')]
        input_files = []
        for search_path in search_paths:
            if search_path.exists():
                input_files.extend(search_path.glob('*.csv'))
                if PDF_SUPPORT:
                    input_files.extend(search_path.glob('*.pdf'))
        
        if not input_files:
            file_types = "CSV/PDF" if PDF_SUPPORT else "CSV"
            print(f"Error: No {file_types} files found. Please provide --input parameter or place files in current/import folder.")
            return 1
    
    # Process each file
    success_count = 0
    for input_file in input_files:
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"Error: File not found: {input_path}")
            continue
        
        print(f"\nProcessing: {input_path.name}")
        print("=" * 60)
        
        # Determine file type and parse accordingly
        file_extension = input_path.suffix.lower()
        
        if file_extension == '.pdf':
            if not PDF_SUPPORT:
                print(f"Error: PDF support not available. Install PyPDF2 to process PDF files.")
                continue
            print("File type: PDF")
            transactions = parse_procredit_pdf(input_path)
        elif file_extension == '.csv':
            print("File type: CSV")
            transactions = parse_procredit_csv(input_path)
        else:
            print(f"Error: Unsupported file type: {file_extension}")
            continue
        
        if not transactions:
            print(f"No transactions found in {input_path.name}")
            continue
        
        # Generate output filename
        output_dir = Path(args.output)
        output_filename = f"{input_path.stem} - 4qbo.csv"
        output_path = output_dir / output_filename
        
        # Write QuickBooks CSV
        result = write_quickbooks_csv(transactions, output_path)
        
        if result:
            success_count += 1
            print(f"✓ Converted: {input_path.name} -> {Path(result).name}")
        else:
            print(f"✗ Failed to convert: {input_path.name}")
    
    print(f"\n{'=' * 60}")
    print(f"Conversion complete: {success_count} file(s) processed")
    
    return 0 if success_count > 0 else 1

if __name__ == '__main__':
    sys.exit(main())

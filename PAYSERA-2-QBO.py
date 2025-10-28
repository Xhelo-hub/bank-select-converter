#!/usr/bin/env python3
"""
Paysera to QuickBooks CSV Converter
====================================
Converts Paysera statements (CSV and PDF format) to QuickBooks-compatible CSV.

Bank: Paysera
Input: CSV or PDF export from Paysera
Output: QuickBooks CSV (Date, Description, Debit, Credit, Balance)

Features:
- Handles both CSV and PDF formats
- Processes amounts with negative values for debits
- Extracts transaction descriptions and payment purposes
- Versioned output files to prevent overwrites
- Supports multiple currencies

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

def parse_paysera_amount(amount_str):
    """
    Parse Paysera amount format to float.
    Format: "360.00" or "-150.00" (negative for debit)
    
    Args:
        amount_str: String representation of amount
        
    Returns:
        float: Parsed amount
    """
    if not amount_str or amount_str.strip() == '0.00':
        return 0.0
    
    # Remove any spaces and currency codes
    amount_str = amount_str.strip()
    amount_str = re.sub(r'[A-Z]{3}$', '', amount_str).strip()  # Remove currency code
    
    try:
        return float(amount_str)
    except ValueError:
        print(f"Warning: Could not parse amount '{amount_str}', using 0.0")
        return 0.0

def parse_paysera_date(date_str):
    """
    Parse Paysera date format to ISO format.
    
    Input format: "2025-10-02 14:13:29 +0200" or "2025-10-02"
    Output format: YYYY-MM-DD (e.g., "2025-10-02")
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        str: Date in YYYY-MM-DD format
    """
    try:
        # Try parsing full datetime format first
        if ' ' in date_str:
            date_obj = datetime.strptime(date_str.split('+')[0].strip(), '%Y-%m-%d %H:%M:%S')
        else:
            date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        print(f"Warning: Could not parse date '{date_str}'")
        return date_str.split()[0] if ' ' in date_str else date_str

def extract_description(row):
    """
    Extract and clean transaction description from Paysera row.
    
    Combines Type, Recipient/Payer, and Purpose of payment fields.
    
    Args:
        row: Dictionary containing transaction data
        
    Returns:
        str: Clean description
    """
    trans_type = row.get('Type', '').strip()
    recipient = row.get('Recipient / Payer', '').strip()
    purpose = row.get('Purpose of payment', '').strip()
    
    # Combine fields
    parts = []
    if trans_type:
        parts.append(trans_type)
    if recipient:
        parts.append(recipient)
    if purpose:
        parts.append(purpose)
    
    full_desc = ' - '.join(parts) if parts else "Transaction"
    
    # Clean up multiple spaces and newlines
    full_desc = ' '.join(full_desc.split())
    
    return full_desc

def parse_paysera_csv(csv_path):
    """
    Parse Paysera CSV file and extract transactions.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        list: List of transaction dictionaries
    """
    transactions = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Skip empty rows
                if not row.get('Date and time'):
                    continue
                
                # Parse amount
                amount_str = row.get('Amount and currency', '0')
                # Remove currency code if present
                amount_str = re.sub(r'\s*[A-Z]{3}$', '', amount_str)
                amount = parse_paysera_amount(amount_str)
                
                # Determine debit or credit based on amount sign
                debit = abs(amount) if amount < 0 else 0
                credit = amount if amount > 0 else 0
                
                # Parse balance
                balance_str = row.get('Balance', '0')
                balance_str = re.sub(r'\s*[A-Z]{3}$', '', balance_str)
                balance = parse_paysera_amount(balance_str)
                
                # Parse date
                date = parse_paysera_date(row.get('Date and time', ''))
                
                # Extract description
                description = extract_description(row)
                
                transaction = {
                    'Date': date,
                    'Description': description,
                    'Debit': debit,
                    'Credit': credit,
                    'Balance': abs(balance)  # Ensure positive balance
                }
                
                transactions.append(transaction)
        
        print(f"Successfully parsed {len(transactions)} transactions from CSV")
        return transactions
        
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from Paysera PDF file.
    
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

def parse_paysera_pdf(pdf_path):
    """
    Parse Paysera PDF file and extract transactions.
    
    PDF format pattern:
    Type, Date and time, Statement No., Payment ID, Recipient/Payer, EVP/IBAN, Amount, Balance
    
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
        lines = text.split('\n')
        
        # Transaction pattern: Type, Date, Statement No, Payment ID, Recipient, Account, Amount, Balance
        # Look for transaction blocks
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if line starts with transaction type
            if line in ['Transfer', 'Commission fee', 'Payment', 'Withdrawal']:
                try:
                    trans_type = line
                    
                    # Next line should have date and time
                    i += 1
                    if i >= len(lines):
                        break
                    date_line = lines[i].strip()
                    
                    # Parse date
                    date = parse_paysera_date(date_line)
                    
                    # Look ahead for amount (contains EUR or other currency)
                    amount_str = ""
                    balance_str = ""
                    recipient = ""
                    purpose = ""
                    
                    # Scan next several lines for amount and balance
                    j = i + 1
                    found_amount = False
                    found_balance = False
                    
                    while j < len(lines) and j < i + 15:
                        next_line = lines[j].strip()
                        
                        # Check if this is a new transaction type
                        if next_line in ['Transfer', 'Commission fee', 'Payment', 'Withdrawal']:
                            break
                        
                        # Look for amount pattern (number with EUR)
                        if re.search(r'-?\d+\.\d{2}\s*EUR', next_line):
                            if not found_amount:
                                amount_match = re.search(r'(-?\d+\.\d{2})\s*EUR', next_line)
                                if amount_match:
                                    amount_str = amount_match.group(1)
                                    found_amount = True
                            elif not found_balance:
                                balance_match = re.search(r'(-?\d+\.\d{2})\s*EUR', next_line)
                                if balance_match:
                                    balance_str = balance_match.group(1)
                                    found_balance = True
                        
                        # Look for recipient/payer
                        if not recipient and next_line and not re.search(r'\d{10,}', next_line) and 'Purpose of payment' not in next_line:
                            # Skip statement numbers and payment IDs
                            if not next_line.isdigit() and len(next_line) > 3 and next_line not in ['EUR', date_line]:
                                if not re.search(r'EVP\d+|[A-Z]{2}\d{2}', next_line):
                                    recipient = next_line
                        
                        # Look for purpose
                        if 'Purpose of payment' in next_line:
                            purpose_line = next_line.replace('Purpose of payment', '').strip()
                            if purpose_line.startswith(':'):
                                purpose_line = purpose_line[1:].strip()
                            if purpose_line:
                                purpose = purpose_line
                        
                        j += 1
                    
                    # Parse amount and balance
                    if amount_str:
                        amount = parse_paysera_amount(amount_str)
                        balance = parse_paysera_amount(balance_str) if balance_str else 0
                        
                        # Determine debit or credit
                        debit = abs(amount) if amount < 0 else 0
                        credit = amount if amount > 0 else 0
                        
                        # Build description
                        desc_parts = [trans_type]
                        if recipient:
                            desc_parts.append(recipient)
                        if purpose:
                            desc_parts.append(purpose)
                        description = ' - '.join(desc_parts)
                        
                        transaction = {
                            'Date': date,
                            'Description': description,
                            'Debit': debit,
                            'Credit': credit,
                            'Balance': abs(balance)
                        }
                        
                        transactions.append(transaction)
                    
                    i = j
                except Exception as e:
                    print(f"Error parsing transaction at line {i}: {e}")
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
        description='Convert Paysera CSV or PDF to QuickBooks format'
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
                input_files.extend(search_path.glob('*paysera*.csv'))
                input_files.extend(search_path.glob('*Paysera*.csv'))
                if PDF_SUPPORT:
                    input_files.extend(search_path.glob('*paysera*.pdf'))
                    input_files.extend(search_path.glob('*Paysera*.pdf'))
        
        if not input_files:
            file_types = "CSV/PDF" if PDF_SUPPORT else "CSV"
            print(f"Error: No Paysera {file_types} files found. Please provide --input parameter or place files in current/import folder.")
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
            transactions = parse_paysera_pdf(input_path)
        elif file_extension == '.csv':
            print("File type: CSV")
            transactions = parse_paysera_csv(input_path)
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

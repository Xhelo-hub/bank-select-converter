#!/usr/bin/env python3
"""
OTP-2-QBO.py
============

OTP Bank statement to QuickBooks CSV converter.
This script processes OTP Bank CSV files to generate QuickBooks-compatible CSV format.

Author: Generated for QuickBooks CSV processing
Date: October 5, 2025
"""

import csv
import os
import sys
import shutil
from pathlib import Path
import re
from datetime import datetime
import PyPDF2

def read_csv_file(csv_path):
    """Read CSV file and return headers and rows."""
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as csvfile:
            # Try to detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
            
            reader = csv.reader(csvfile, delimiter=delimiter)
            headers = next(reader)  # First row as headers
            rows = list(reader)
            
        return headers, rows
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return [], []

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return ""

def convert_date_format(date_str):
    """Convert date from DD/MM/YYYY to DD/MM/YYYY (QuickBooks format)."""
    try:
        # Already in correct format DD/MM/YYYY
        if '/' in date_str and len(date_str.split('/')[2]) == 4:
            return date_str
        
        # Try DD/MM/YY format
        if '/' in date_str and len(date_str.split('/')[2]) == 2:
            parts = date_str.split('/')
            year = '20' + parts[2]  # Assume 20XX
            return f"{parts[0]}/{parts[1]}/{year}"
            
        return date_str
    except:
        return date_str

def clean_amount(amount_str):
    """Clean and normalize amount string."""
    if not amount_str:
        return ""
    
    # Remove currency codes like "ALL", "EUR", "USD"
    amount = re.sub(r'\s*(ALL|EUR|USD)\s*', '', amount_str)
    
    # Remove any leading/trailing whitespace
    amount = amount.strip()
    
    # Handle negative signs
    is_negative = amount.startswith('-')
    if is_negative:
        amount = amount[1:].strip()
    
    # Handle European format (space as thousands separator, comma as decimal)
    # Examples: "31.719,00", "9 900,00", "177.51", "550,00"
    
    # Remove spaces (thousands separators)
    amount = amount.replace(' ', '')
    
    # If there's both dot and comma, determine which is decimal
    if '.' in amount and ',' in amount:
        # Find last occurrence of each
        last_dot = amount.rfind('.')
        last_comma = amount.rfind(',')
        
        if last_comma > last_dot:
            # Comma is decimal: 31.719,00 -> 31719.00
            amount = amount.replace('.', '').replace(',', '.')
        else:
            # Dot is decimal: keep as is, remove comma (thousands)
            amount = amount.replace(',', '')
    elif ',' in amount:
        # Only comma - check if it's likely a decimal separator
        comma_pos = amount.rfind(',')
        # If comma is followed by exactly 2 digits, it's likely decimal
        if comma_pos != -1 and comma_pos == len(amount) - 3:
            amount = amount.replace(',', '.')
        else:
            # Otherwise, treat as thousands separator and remove
            amount = amount.replace(',', '')
    
    # Remove any remaining non-numeric characters except decimal point
    amount = re.sub(r'[^\d.]', '', amount)
    
    try:
        # Validate it's a proper number
        num = float(amount)
        # Format to 2 decimal places
        result = f"{num:.2f}"
        return f"-{result}" if is_negative else result
    except:
        return ""

def extract_transactions_from_pdf_text(text):
    """Extract transactions from OTP Bank PDF text."""
    transactions = []
    
    # Split text into lines and process
    lines = text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for date pattern (DD/MM/YY format in OTP PDFs)
        date_pattern = r'^(\d{1,2}/\d{1,2}/\d{2})\s+'
        date_match = re.match(date_pattern, line)
        
        if date_match:
            try:
                date_str = date_match.group(1)
                
                # Remove date from line to get description start
                line_after_date = line[len(date_match.group(0)):].strip()
                
                # Description might span multiple lines, collect until we find amount
                description_parts = [line_after_date]
                amount_str = ""
                transaction_date = ""
                
                # Look for amount in current and subsequent lines
                amount_pattern = r'(\d{1,3}(?:\s\d{3})*,\d{2})'
                j = i
                found_amount = False
                
                while j < len(lines) and j < i + 10 and not found_amount:  # Check up to 10 lines ahead
                    check_line = lines[j].strip()
                    amount_match = re.search(amount_pattern, check_line)
                    
                    if amount_match:
                        amount_str = amount_match.group(1)
                        
                        # Also look for transaction date in the same line (format: DD/MM/YY at end)
                        trans_date_pattern = r'(\d{1,2}/\d{1,2}/\d{2})\s*$'
                        trans_date_match = re.search(trans_date_pattern, check_line)
                        if trans_date_match:
                            transaction_date = trans_date_match.group(1)
                        
                        # If this is not the original line, add description parts
                        if j != i:
                            # Add all lines between start and amount line to description
                            for k in range(i + 1, j):
                                desc_line = lines[k].strip()
                                if desc_line and not re.match(r'^\d{1,2}/\d{1,2}/\d{2}', desc_line):
                                    description_parts.append(desc_line)
                            
                            # Add part of amount line before the amount
                            amount_pos = check_line.rfind(amount_str)
                            desc_part = check_line[:amount_pos].strip()
                            if desc_part:
                                description_parts.append(desc_part)
                        else:
                            # Amount is in same line as date
                            amount_pos = check_line.rfind(amount_str)
                            desc_part = check_line[len(date_match.group(0)):amount_pos].strip()
                            description_parts = [desc_part] if desc_part else description_parts
                        
                        found_amount = True
                        i = j  # Skip processed lines
                        break
                    else:
                        # Add this line to description if it's not empty and not a new date line
                        if j != i and check_line and not re.match(r'^\d{1,2}/\d{1,2}/\d{2}', check_line):
                            description_parts.append(check_line)
                    j += 1
                
                if amount_str and any(part.strip() for part in description_parts):
                    # Clean up description
                    description = ' '.join(filter(lambda x: x.strip(), description_parts)).strip()
                    
                    # Use transaction date if found, otherwise use line date
                    final_date = transaction_date if transaction_date else date_str
                    qb_date = convert_date_format(final_date)
                    
                    # Clean amount and make it negative (debit)
                    clean_amount_val = '-' + clean_amount(amount_str)
                    
                    if description and clean_amount_val:
                        transaction = {
                            'Date': qb_date,
                            'Description': description,
                            'Amount': clean_amount_val,
                            'Type': 'Debit'
                        }
                        transactions.append(transaction)
                        
            except Exception as e:
                continue
        
        i += 1
    
    return transactions

def find_otp_bank_files():
    """Find OTP Bank PDF and CSV files in current directory and import folder."""
    found_files = {'pdf': [], 'csv': []}
    
    # Search in current directory and import folder
    search_paths = [Path("."), Path("import")]
    
    for search_path in search_paths:
        if search_path.exists():
            # Look for PDF files that might be OTP Bank statements
            for pdf_file in search_path.glob("*.pdf"):
                pdf_text = ""
                try:
                    # Quick check if it's an OTP Bank PDF
                    with open(pdf_file, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        # Read first page to check
                        if len(pdf_reader.pages) > 0:
                            pdf_text = pdf_reader.pages[0].extract_text()
                    
                    # Check for OTP Bank indicators
                    if any(indicator in pdf_text.upper() for indicator in ["OTP BANK", "ACCOUNT E - STATEMENT", "AL64902117734531230220932969"]):
                        found_files['pdf'].append(pdf_file)
                        
                except Exception:
                    continue
            
            # Look for CSV files that might be OTP Bank transaction exports
            for csv_file in search_path.glob("*.csv"):
                try:
                    with open(csv_file, 'r', encoding='utf-8') as file:
                        content = file.read(1000)  # Read first 1000 chars
                    
                    # Check for OTP Bank CSV indicators
                    if any(indicator in content for indicator in ["Transaction date", "Beneficiary/Sender name", "Inflow", "Outflow", "Booked_transactions"]):
                        found_files['csv'].append(csv_file)
                        
                except Exception:
                    continue
    
    return found_files

def convert_to_quickbooks(output_directory=None):
    """Convert OTP Bank PDF and CSV files to QuickBooks CSV format."""
    print("=" * 80)
    print("OTP BANK TO QUICKBOOKS CONVERTER")
    print("=" * 80)
    print()
    
    # Search for OTP Bank files
    print("🔍 Searching for OTP Bank files...")
    found_files = find_otp_bank_files()
    
    pdf_file = None
    csv_file = None
    pdf_filename = ""
    csv_filename = ""
    
    # Select PDF file
    if found_files['pdf']:
        if len(found_files['pdf']) > 1:
            print(f"📄 Found {len(found_files['pdf'])} PDF files:")
            for i, f in enumerate(found_files['pdf']):
                print(f"   {i+1}. {f.name}")
            print(f"📄 Using: {found_files['pdf'][0].name}")
        pdf_file = found_files['pdf'][0]  # Use first found PDF
        pdf_filename = pdf_file.stem
        print(f"📄 Found PDF file: {pdf_file.name}")
    else:
        print("⚠️ No OTP Bank PDF files found")
    
    # Select CSV file  
    if found_files['csv']:
        if len(found_files['csv']) > 1:
            print(f"📊 Found {len(found_files['csv'])} CSV files:")
            for i, f in enumerate(found_files['csv']):
                print(f"   {i+1}. {f.name}")
            print(f"📊 Using: {found_files['csv'][0].name}")
        csv_file = found_files['csv'][0]  # Use first found CSV
        csv_filename = csv_file.stem
        print(f"📊 Found CSV file: {csv_file.name}")
    else:
        print("⚠️ No OTP Bank CSV files found")
    
    if not pdf_file and not csv_file:
        print("❌ No OTP Bank files found to process")
        return
    
    pdf_transactions = []
    csv_transactions = []
    
    # Process PDF file first (if available)
    if pdf_file and pdf_file.exists():
        print("📄 Processing PDF file...")
        pdf_text = extract_text_from_pdf(str(pdf_file))
        if pdf_text:
            pdf_transactions = extract_transactions_from_pdf_text(pdf_text)
            print(f"✓ Processed {len(pdf_transactions)} transactions from PDF")
        else:
            print("⚠️ Could not extract text from PDF")
    
    # Process CSV file
    if csv_file and csv_file.exists():
        print("📊 Processing CSV file...")
        headers, rows = read_csv_file(str(csv_file))
    
    if rows and len(rows) > 2:  # Skip header rows
        # Find the real header row (should be row 2)
        header_row = None
        data_start_row = 0
        
        for i, row in enumerate(rows):
            if len(row) > 0 and 'Transaction date' in str(row[0]):
                header_row = row
                data_start_row = i + 1
                break
        
        if header_row:
            print(f"✓ Found CSV headers: {header_row}")
            
            # Process transactions from CSV
            processed_count = 0
            for i in range(data_start_row, len(rows)):
                row = rows[i]
                if len(row) >= 4 and row[0].strip():  # Valid transaction row
                    try:
                        transaction_date = row[0].strip()
                        beneficiary = row[1].strip() if len(row) > 1 else ""
                        inflow = row[2].strip() if len(row) > 2 else ""
                        outflow = row[3].strip() if len(row) > 3 else ""
                        details = row[4].strip() if len(row) > 4 else ""
                        
                        # Skip empty transactions
                        if not inflow and not outflow:
                            continue
                        
                        # Convert date format
                        qb_date = convert_date_format(transaction_date)
                        
                        # Determine amount and type
                        amount = ""
                        transaction_type = ""
                        
                        if outflow and outflow.strip():
                            # Outflow (debit) - keep negative sign for clarity
                            amount = clean_amount(outflow)
                            transaction_type = "Debit"
                        elif inflow and inflow.strip():
                            # Inflow (credit) - positive amount
                            amount = clean_amount(inflow)
                            transaction_type = "Credit"
                        
                        if amount and qb_date:
                            # Clean up description
                            description_parts = []
                            if beneficiary:
                                description_parts.append(beneficiary)
                            if details:
                                description_parts.append(details)
                            
                            description = " - ".join(description_parts).strip(' -')
                            
                            transaction = {
                                'Date': qb_date,
                                'Description': description,
                                'Amount': amount,
                                'Type': transaction_type
                            }
                            csv_transactions.append(transaction)
                            processed_count += 1
                            
                    except Exception as e:
                        print(f"   ⚠️ Error processing CSV row {i}: {str(e)}")
                        continue
            
            print(f"✓ Processed {processed_count} transactions from CSV")
    
    # Create separate files for PDF and CSV transactions
    output_files = []
    
    if pdf_transactions:
        # Sort PDF transactions by date
        pdf_transactions.sort(key=lambda x: datetime.strptime(x['Date'], '%d/%m/%Y'))
        # Generate PDF QuickBooks CSV using PDF filename
        pdf_output = generate_quickbooks_csv(pdf_transactions, pdf_filename, "", output_directory)
        output_files.append(f"📄 PDF: {pdf_output}")
    
    if csv_transactions:
        # Sort CSV transactions by date
        csv_transactions.sort(key=lambda x: datetime.strptime(x['Date'], '%d/%m/%Y'))
        # Generate CSV QuickBooks CSV using CSV filename
        csv_output = generate_quickbooks_csv(csv_transactions, csv_filename, "", output_directory)
        output_files.append(f"CSV: {csv_output}")
    
    print(f"\nSUCCESS!")
    if output_files:
        print("Created QuickBooks CSV files:")
        for file_info in output_files:
            print(f"   {file_info}")
    
    # Show summary
    total_transactions = len(pdf_transactions) + len(csv_transactions)
    print(f"Total transactions: {total_transactions}")
    print(f"   PDF: {len(pdf_transactions)} transactions")
    print(f"   CSV: {len(csv_transactions)} transactions")

def generate_quickbooks_csv(transactions, original_filename, source_type, output_directory=None):
    """Generate QuickBooks compatible CSV file."""
    # Ensure export directory exists
    export_dir = Path(output_directory) if output_directory else Path("export")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate base filename 
    if source_type:
        base_filename = f"{original_filename} - {source_type} - 4qbo.csv"
    else:
        base_filename = f"{original_filename} - 4qbo.csv"
    output_file = export_dir / base_filename
    
    # Check if file exists and generate incremental name if needed
    counter = 1
    while output_file.exists():
        # Generate filename with counter
        if source_type:
            name_without_ext = f"{original_filename} - {source_type} - 4qbo ({counter})"
        else:
            name_without_ext = f"{original_filename} - 4qbo ({counter})"
        output_file = export_dir / f"{name_without_ext}.csv"
        counter += 1
    
    # QuickBooks CSV headers (standard format for bank transactions)
    headers = ['Date', 'Description', 'Amount', 'Type']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for transaction in transactions:
                writer.writerow([
                    transaction['Date'],
                    transaction['Description'],
                    transaction['Amount'],
                    transaction['Type']
                ])
        
        return str(output_file)
    except Exception as e:
        print(f"Error creating CSV: {str(e)}")
        return None

def main():
    """Main function to convert OTP Bank files to QuickBooks format."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert OTP Bank statements to QuickBooks CSV format')
    parser.add_argument('--input', '-i', dest='input_file', help='Input PDF/CSV file path')
    parser.add_argument('--output', '-o', dest='output_dir', help='Output directory for CSV file')
    
    args = parser.parse_args()
    
    # If specific input file provided, process it
    if args.input_file:
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: File not found: {input_path}", flush=True)
            sys.exit(1)
        
        # Copy to import folder for processing
        import_dir = Path('import')
        import_dir.mkdir(exist_ok=True)
        import shutil
        shutil.copy2(input_path, import_dir / input_path.name)
        print(f"Processing: {input_path.name}", flush=True)
    
    convert_to_quickbooks(args.output_dir)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
ALL-BANKS-2-QBO.py
==================

Universal Bank Statement to QuickBooks CSV Converter
This script automatically detects and converts statements from all supported Albanian banks:
- OTP Bank (PDF + CSV)
- BKT Bank (PDF)
- Raiffeisen Bank (CSV)
- TABANK (CSV)
- UNION Bank (CSV)
- Albanian e-Bills (PDF)

Author: Generated for Universal QuickBooks CSV processing
Date: October 5, 2025
"""

import csv
import os
from pathlib import Path
import re
from datetime import datetime
import PyPDF2

# ============================================================================
# COMMON UTILITY FUNCTIONS
# ============================================================================

def create_export_directory():
    """Create export directory if it doesn't exist."""
    export_dir = Path("export")
    export_dir.mkdir(exist_ok=True)
    return export_dir

def get_versioned_filename(base_path):
    """Generate versioned filename if file exists."""
    file_path = Path(base_path)
    
    if not file_path.exists():
        return file_path
    
    counter = 1
    while True:
        name_without_ext = f"{file_path.stem} ({counter})"
        new_path = file_path.parent / f"{name_without_ext}{file_path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

def clean_amount(amount_str):
    """Clean and normalize amount string for all bank formats."""
    if not amount_str:
        return ""
    
    # Remove currency codes
    amount = re.sub(r'\s*(ALL|EUR|USD|LEK)\s*', '', amount_str)
    amount = amount.strip()
    
    # Handle negative signs
    is_negative = amount.startswith('-') or amount.startswith('(')
    if is_negative:
        amount = amount.lstrip('-').strip('()')
    
    # Handle European format (space/dot as thousands, comma as decimal)
    amount = amount.replace(' ', '')  # Remove spaces
    
    # If both dot and comma exist, determine decimal separator
    if '.' in amount and ',' in amount:
        last_dot = amount.rfind('.')
        last_comma = amount.rfind(',')
        
        if last_comma > last_dot:
            # Comma is decimal: 31.719,00 -> 31719.00
            amount = amount.replace('.', '').replace(',', '.')
        else:
            # Dot is decimal: keep as is, remove comma
            amount = amount.replace(',', '')
    elif ',' in amount:
        # Only comma - check if it's decimal (followed by 2 digits)
        comma_pos = amount.rfind(',')
        if comma_pos != -1 and comma_pos == len(amount) - 3:
            amount = amount.replace(',', '.')
        else:
            amount = amount.replace(',', '')
    
    # Remove any remaining non-numeric characters except decimal point
    amount = re.sub(r'[^\d.]', '', amount)
    
    try:
        num = float(amount)
        result = f"{num:.2f}"
        return f"-{result}" if is_negative else result
    except:
        return ""

def convert_date_format(date_str):
    """Convert various date formats to DD/MM/YYYY."""
    if not date_str:
        return ""
    
    try:
        # Handle DD/MM/YYYY format
        if '/' in date_str and len(date_str.split('/')[2]) == 4:
            return date_str
        
        # Handle DD/MM/YY format
        if '/' in date_str and len(date_str.split('/')[2]) == 2:
            parts = date_str.split('/')
            year = '20' + parts[2]
            return f"{parts[0]}/{parts[1]}/{year}"
        
        # Handle DD.MM.YYYY format
        if '.' in date_str:
            parts = date_str.split('.')
            if len(parts) == 3:
                return f"{parts[0]}/{parts[1]}/{parts[2]}"
        
        # Handle YYYY-MM-DD format
        if '-' in date_str and len(date_str.split('-')[0]) == 4:
            parts = date_str.split('-')
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
        
        return date_str
    except:
        return date_str

def generate_quickbooks_csv(transactions, filename, bank_type=""):
    """Generate QuickBooks compatible CSV file."""
    export_dir = create_export_directory()
    
    if bank_type:
        output_file = export_dir / f"{filename} - {bank_type} - 4qbo.csv"
    else:
        output_file = export_dir / f"{filename} - 4qbo.csv"
    
    # Handle versioning
    output_file = get_versioned_filename(output_file)
    
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

# ============================================================================
# BANK-SPECIFIC PROCESSING FUNCTIONS
# ============================================================================

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

def process_otp_bank_pdf(pdf_text):
    """Process OTP Bank PDF transactions."""
    transactions = []
    lines = pdf_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for date pattern (DD/MM/YY format)
        date_pattern = r'^(\d{1,2}/\d{1,2}/\d{2})\s+'
        date_match = re.match(date_pattern, line)
        
        if date_match:
            try:
                date_str = date_match.group(1)
                line_after_date = line[len(date_match.group(0)):].strip()
                
                description_parts = [line_after_date]
                amount_str = ""
                transaction_date = ""
                
                amount_pattern = r'(\d{1,3}(?:\s\d{3})*,\d{2})'
                j = i
                found_amount = False
                
                while j < len(lines) and j < i + 10 and not found_amount:
                    check_line = lines[j].strip()
                    amount_match = re.search(amount_pattern, check_line)
                    
                    if amount_match:
                        amount_str = amount_match.group(1)
                        
                        trans_date_pattern = r'(\d{1,2}/\d{1,2}/\d{2})\s*$'
                        trans_date_match = re.search(trans_date_pattern, check_line)
                        if trans_date_match:
                            transaction_date = trans_date_match.group(1)
                        
                        if j != i:
                            for k in range(i + 1, j):
                                desc_line = lines[k].strip()
                                if desc_line and not re.match(r'^\d{1,2}/\d{1,2}/\d{2}', desc_line):
                                    description_parts.append(desc_line)
                            
                            amount_pos = check_line.rfind(amount_str)
                            desc_part = check_line[:amount_pos].strip()
                            if desc_part:
                                description_parts.append(desc_part)
                        else:
                            amount_pos = check_line.rfind(amount_str)
                            desc_part = check_line[len(date_match.group(0)):amount_pos].strip()
                            description_parts = [desc_part] if desc_part else description_parts
                        
                        found_amount = True
                        i = j
                        break
                    else:
                        if j != i and check_line and not re.match(r'^\d{1,2}/\d{1,2}/\d{2}', check_line):
                            description_parts.append(check_line)
                    j += 1
                
                if amount_str and any(part.strip() for part in description_parts):
                    description = ' '.join(filter(lambda x: x.strip(), description_parts)).strip()
                    final_date = transaction_date if transaction_date else date_str
                    qb_date = convert_date_format(final_date)
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

def process_bkt_bank_pdf(pdf_text):
    """Process BKT Bank PDF transactions."""
    transactions = []
    lines = pdf_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # BKT Bank transaction pattern
        date_pattern = r'^(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})'
        date_match = re.match(date_pattern, line)
        
        if date_match:
            try:
                date_str = date_match.group(1).replace('.', '/')
                
                # Look for amount in the line
                amount_pattern = r'([\-]?\d{1,3}(?:[.,\s]\d{3})*[.,]\d{2})'
                amount_matches = re.findall(amount_pattern, line)
                
                if amount_matches:
                    amount_str = amount_matches[-1]
                    
                    desc_start = len(date_match.group(1))
                    amount_start = line.rfind(amount_str)
                    description = line[desc_start:amount_start].strip()
                    
                    if description and amount_str:
                        clean_amount_val = clean_amount(amount_str)
                        if clean_amount_val:
                            transaction = {
                                'Date': convert_date_format(date_str),
                                'Description': description,
                                'Amount': clean_amount_val,
                                'Type': 'Debit' if clean_amount_val.startswith('-') else 'Credit'
                            }
                            transactions.append(transaction)
                            
            except Exception:
                continue
    
    return transactions

def process_ebill_pdf(pdf_text):
    """Process Albanian e-Bill PDF."""
    transactions = []
    
    # Look for e-bill patterns
    if 'NIVF' in pdf_text or 'NSLF' in pdf_text or 'Faturë' in pdf_text:
        lines = pdf_text.split('\n')
        
        # Extract NIVF/NSLF and amount
        nivf = ""
        nslf = ""
        amount = ""
        date = ""
        
        for line in lines:
            line = line.strip()
            
            # Extract NIVF
            nivf_match = re.search(r'NIVF[:\s]*([A-Z0-9]+)', line)
            if nivf_match:
                nivf = nivf_match.group(1)
            
            # Extract NSLF
            nslf_match = re.search(r'NSLF[:\s]*([A-Z0-9]+)', line)
            if nslf_match:
                nslf = nslf_match.group(1)
            
            # Extract amount
            amount_match = re.search(r'(\d{1,3}(?:[\s.]\d{3})*,\d{2})', line)
            if amount_match and not amount:
                amount = amount_match.group(1)
            
            # Extract date
            date_match = re.search(r'(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})', line)
            if date_match and not date:
                date = date_match.group(1)
        
        if amount and (nivf or nslf):
            description = f"E-Bill"
            if nivf:
                description += f" - NIVF: {nivf}"
            if nslf:
                description += f" - NSLF: {nslf}"
            
            transaction = {
                'Date': convert_date_format(date) if date else datetime.now().strftime('%d/%m/%Y'),
                'Description': description,
                'Amount': '-' + clean_amount(amount),
                'Type': 'Debit'
            }
            transactions.append(transaction)
    
    return transactions

def process_bank_csv(csv_path, bank_type):
    """Process bank CSV files based on bank type."""
    transactions = []
    
    try:
        # Try different encodings
        for encoding in ['utf-8', 'cp1252', 'iso-8859-1']:
            try:
                with open(csv_path, 'r', encoding=encoding, newline='') as csvfile:
                    sample = csvfile.read(1024)
                    csvfile.seek(0)
                    
                    # Detect delimiter
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
                    
                    reader = csv.reader(csvfile, delimiter=delimiter)
                    rows = list(reader)
                    break
            except UnicodeDecodeError:
                continue
        else:
            print(f"Could not read CSV file: {csv_path}")
            return transactions
        
        if not rows:
            return transactions
        
        # Process based on bank type
        if bank_type.upper() == "OTP":
            return process_otp_csv(rows)
        elif bank_type.upper() == "RAIFFEISEN":
            return process_raiffeisen_csv(rows)
        elif bank_type.upper() == "TABANK":
            return process_tabank_csv(rows)
        elif bank_type.upper() == "UNION":
            return process_union_csv(rows)
        else:
            # Generic CSV processing
            return process_generic_csv(rows)
            
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return transactions

def process_otp_csv(rows):
    """Process OTP Bank CSV format."""
    transactions = []
    
    # Find header row
    header_row = None
    data_start_row = 0
    
    for i, row in enumerate(rows):
        if len(row) > 0 and 'Transaction date' in str(row[0]):
            header_row = row
            data_start_row = i + 1
            break
    
    if not header_row:
        return transactions
    
    for i in range(data_start_row, len(rows)):
        row = rows[i]
        if len(row) >= 4 and row[0].strip():
            try:
                transaction_date = row[0].strip()
                beneficiary = row[1].strip() if len(row) > 1 else ""
                inflow = row[2].strip() if len(row) > 2 else ""
                outflow = row[3].strip() if len(row) > 3 else ""
                details = row[4].strip() if len(row) > 4 else ""
                
                if not inflow and not outflow:
                    continue
                
                qb_date = convert_date_format(transaction_date)
                
                if outflow and outflow.strip():
                    amount = clean_amount(outflow)
                    transaction_type = "Debit"
                elif inflow and inflow.strip():
                    amount = clean_amount(inflow)
                    transaction_type = "Credit"
                else:
                    continue
                
                description_parts = []
                if beneficiary:
                    description_parts.append(beneficiary)
                if details:
                    description_parts.append(details)
                
                description = " - ".join(description_parts).strip(' -')
                
                if amount and qb_date:
                    transaction = {
                        'Date': qb_date,
                        'Description': description,
                        'Amount': amount,
                        'Type': transaction_type
                    }
                    transactions.append(transaction)
                    
            except Exception:
                continue
    
    return transactions

def process_raiffeisen_csv(rows):
    """Process Raiffeisen Bank CSV format with proper header detection."""
    transactions = []
    
    # Find the header row (contains "No","Value Date","Processing Date", etc.)
    header_index = -1
    header_row = None
    
    for i, row in enumerate(rows):
        # Convert row to string to check
        row_str = ','.join([str(cell) for cell in row])
        if 'Processing Date' in row_str and 'Value Date' in row_str and 'Amount' in row_str:
            header_index = i
            header_row = row
            break
    
    if header_index == -1:
        return transactions  # No valid header found
    
    # Create column mapping from header
    col_map = {}
    for idx, col_name in enumerate(header_row):
        col_name_clean = str(col_name).strip()
        col_map[col_name_clean] = idx
    
    # Process transactions starting after header
    for i in range(header_index + 1, len(rows)):
        row = rows[i]
        
        try:
            # Get Processing Date column
            proc_date_idx = col_map.get('Processing Date', -1)
            if proc_date_idx == -1 or proc_date_idx >= len(row):
                continue
            
            processing_date = str(row[proc_date_idx]).strip()
            if not processing_date or processing_date == '':
                continue
            
            # Skip summary rows
            no_col_idx = col_map.get('No', -1)
            if no_col_idx != -1 and no_col_idx < len(row):
                if 'Previous Balance' in str(row[no_col_idx]):
                    continue
            
            # Extract fields
            transaction_type = str(row[col_map.get('Transaction Type', -1)]).strip() if col_map.get('Transaction Type', -1) < len(row) else ''
            beneficiary = str(row[col_map.get('Beneficairy/Ordering name and account number', -1)]).strip() if col_map.get('Beneficairy/Ordering name and account number', -1) < len(row) else ''
            description = str(row[col_map.get('Description', -1)]).strip() if col_map.get('Description', -1) < len(row) else ''
            reference = str(row[col_map.get('Reference', -1)]).strip() if col_map.get('Reference', -1) < len(row) else ''
            amount = str(row[col_map.get('Amount', -1)]).strip() if col_map.get('Amount', -1) < len(row) else ''
            
            # Merge description fields
            desc_parts = []
            if transaction_type: desc_parts.append(transaction_type)
            if beneficiary: desc_parts.append(beneficiary)
            if description: desc_parts.append(description)
            if reference: desc_parts.append(f"Ref: {reference}")
            merged_desc = ' '.join(desc_parts)
            
            # Clean amount (remove spaces, currency codes)
            cleaned_amount = amount.replace(' ', '').replace('ALL', '').replace('USD', '').replace('EUR', '').strip()
            
            # Convert date using global convert_date_format function
            qb_date = convert_date_format(processing_date)
            
            if qb_date and merged_desc and cleaned_amount:
                try:
                    amount_float = float(cleaned_amount)
                    transaction = {
                        'Date': qb_date,
                        'Description': merged_desc,
                        'Amount': str(amount_float),
                        'Type': 'Debit' if amount_float < 0 else 'Credit'
                    }
                    transactions.append(transaction)
                except ValueError:
                    continue
                    
        except Exception:
            continue
    
    return transactions

def process_tabank_csv(rows):
    """Process TABANK CSV format."""
    transactions = []
    
    for i, row in enumerate(rows):
        if i == 0 or len(row) < 4:  # Skip header
            continue
            
        try:
            # TABANK format: Date, Description, Debit, Credit
            date_str = row[0].strip()
            description = row[1].strip()
            debit = row[2].strip()
            credit = row[3].strip()
            
            if date_str and description:
                qb_date = convert_date_format(date_str)
                
                if debit:
                    amount = '-' + clean_amount(debit)
                    transaction_type = 'Debit'
                elif credit:
                    amount = clean_amount(credit)
                    transaction_type = 'Credit'
                else:
                    continue
                
                if qb_date and amount:
                    transaction = {
                        'Date': qb_date,
                        'Description': description,
                        'Amount': amount,
                        'Type': transaction_type
                    }
                    transactions.append(transaction)
                    
        except Exception:
            continue
    
    return transactions

def process_union_csv(rows):
    """Process UNION Bank CSV format."""
    transactions = []
    
    for i, row in enumerate(rows):
        if i == 0 or len(row) < 3:  # Skip header
            continue
            
        try:
            # UNION format: Date, Description, Amount
            date_str = row[0].strip()
            description = row[1].strip()
            amount_str = row[2].strip()
            
            if date_str and description and amount_str:
                qb_date = convert_date_format(date_str)
                amount = clean_amount(amount_str)
                
                if qb_date and amount:
                    transaction = {
                        'Date': qb_date,
                        'Description': description,
                        'Amount': amount,
                        'Type': 'Debit' if amount.startswith('-') else 'Credit'
                    }
                    transactions.append(transaction)
                    
        except Exception:
            continue
    
    return transactions

def process_generic_csv(rows):
    """Process generic CSV format."""
    transactions = []
    
    for i, row in enumerate(rows):
        if i == 0 or len(row) < 3:  # Skip header
            continue
            
        try:
            # Generic format: assume Date, Description, Amount in first 3 columns
            date_str = row[0].strip()
            description = row[1].strip()
            amount_str = row[2].strip()
            
            if date_str and description and amount_str:
                qb_date = convert_date_format(date_str)
                amount = clean_amount(amount_str)
                
                if qb_date and amount:
                    transaction = {
                        'Date': qb_date,
                        'Description': description,
                        'Amount': amount,
                        'Type': 'Debit' if amount.startswith('-') else 'Credit'
                    }
                    transactions.append(transaction)
                    
        except Exception:
            continue
    
    return transactions

# ============================================================================
# FILE DETECTION AND MAIN PROCESSING
# ============================================================================

def detect_bank_type(file_path, content=""):
    """Detect bank type from filename or content."""
    filename = file_path.name.upper()
    content_upper = content.upper()
    
    # Check filename patterns
    if "OTP" in filename:
        return "OTP"
    elif "BKT" in filename:
        return "BKT"
    elif "RAIFFEISEN" in filename or "RAIFF" in filename:
        return "RAIFFEISEN"
    elif "TABANK" in filename or "TIRANA" in filename:
        return "TABANK"
    elif "UNION" in filename:
        return "UNION"
    elif "EBILL" in filename or "FATURE" in filename:
        return "EBILL"
    
    # Check content patterns
    if "OTP BANK" in content_upper or "AL64902117734531230220932969" in content_upper:
        return "OTP"
    elif ("BKT" in content_upper and "STATEMENT" in content_upper) or "BANKA KOMBETARE TREGTARE" in content_upper or ("BKT" in content_upper and "DEGA" in content_upper):
        return "BKT"
    elif "RAIFFEISEN" in content_upper:
        return "RAIFFEISEN"
    elif "TIRANA BANK" in content_upper or "TABANK" in content_upper:
        return "TABANK"
    elif "UNION BANK" in content_upper:
        return "UNION"
    elif "NIVF" in content_upper or "NSLF" in content_upper:
        return "EBILL"
    
    return "UNKNOWN"

def find_bank_files():
    """Find all bank statement files in current directory and import folder."""
    found_files = []
    
    search_paths = [
        Path("."),  # Current directory (root folder)
        Path("import"),  # Import folder
    ]
    
    print("🔍 Searching for bank files in current directory and import folder...")
    
    for search_path in search_paths:
        if search_path.exists():
            # Find PDF files
            for pdf_file in search_path.glob("*.pdf"):
                try:
                    with open(pdf_file, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        if len(pdf_reader.pages) > 0:
                            pdf_text = pdf_reader.pages[0].extract_text()
                            bank_type = detect_bank_type(pdf_file, pdf_text)
                            
                            if bank_type != "UNKNOWN":
                                found_files.append({
                                    'path': pdf_file,
                                    'type': 'PDF',
                                    'bank': bank_type,
                                    'content': pdf_text
                                })
                except Exception:
                    continue
            
            # Find CSV files
            for csv_file in search_path.glob("*.csv"):
                try:
                    with open(csv_file, 'r', encoding='utf-8') as file:
                        content = file.read(1000)
                        bank_type = detect_bank_type(csv_file, content)
                        
                        if bank_type != "UNKNOWN":
                            found_files.append({
                                'path': csv_file,
                                'type': 'CSV',
                                'bank': bank_type,
                                'content': content
                            })
                except Exception:
                    continue
    
    return found_files

def main():
    """Main function to process all bank statements."""
    print("=" * 80)
    print("UNIVERSAL BANK STATEMENT TO QUICKBOOKS CONVERTER")
    print("=" * 80)
    print()
    
    # Find all bank files
    print("🔍 Searching for bank statement files...")
    found_files = find_bank_files()
    
    if not found_files:
        print("❌ No bank statement files found")
        return
    
    print(f"✓ Found {len(found_files)} bank statement files:")
    
    # Group by bank type
    banks = {}
    for file_info in found_files:
        bank = file_info['bank']
        if bank not in banks:
            banks[bank] = []
        banks[bank].append(file_info)
    
    # Show summary
    for bank, files in banks.items():
        print(f"  📋 {bank}: {len(files)} files")
        for file_info in files:
            print(f"    📄 {file_info['type']}: {file_info['path'].name}")
    
    print()
    
    # Process each bank's files
    total_processed = 0
    output_files = []
    
    for bank, files in banks.items():
        print(f"🏦 Processing {bank} Bank files...")
        
        for file_info in files:
            file_path = file_info['path']
            file_type = file_info['type']
            
            print(f"  📄 Processing {file_type}: {file_path.name}")
            
            transactions = []
            
            try:
                if file_type == 'PDF':
                    # Extract full PDF text
                    pdf_text = extract_text_from_pdf(str(file_path))
                    
                    if bank == "OTP":
                        transactions = process_otp_bank_pdf(pdf_text)
                    elif bank == "BKT":
                        transactions = process_bkt_bank_pdf(pdf_text)
                    elif bank == "EBILL":
                        transactions = process_ebill_pdf(pdf_text)
                    
                elif file_type == 'CSV':
                    transactions = process_bank_csv(str(file_path), bank)
                
                if transactions:
                    # Sort by date
                    transactions.sort(key=lambda x: datetime.strptime(x['Date'], '%d/%m/%Y'))
                    
                    # Generate output file
                    filename = file_path.stem
                    output_file = generate_quickbooks_csv(transactions, filename, bank)
                    
                    if output_file:
                        output_files.append(f"  📄 {bank}: {Path(output_file).name} ({len(transactions)} transactions)")
                        total_processed += len(transactions)
                        print(f"    ✓ Created: {Path(output_file).name} ({len(transactions)} transactions)")
                    else:
                        print(f"    ❌ Failed to create output file")
                else:
                    print(f"    ⚠️ No transactions found")
                    
            except Exception as e:
                print(f"    ❌ Error processing file: {str(e)}")
    
    # Final summary
    print()
    print("=" * 80)
    print("✅ PROCESSING COMPLETE!")
    print("=" * 80)
    print(f"📊 Total transactions processed: {total_processed}")
    print(f"📁 Output files created: {len(output_files)}")
    print()
    
    if output_files:
        print("📋 Generated QuickBooks CSV files:")
        for file_info in output_files:
            print(file_info)
    
    print()
    print("💡 All files saved in the 'export' folder and ready for QuickBooks import!")

if __name__ == "__main__":
    main()
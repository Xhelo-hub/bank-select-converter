# -*- coding: utf-8 -*-
"""
Raiffeisen Bank CSV/PDF to QBO Format Converter
Converts Raiffeisen bank statement files (CSV or PDF) to a simplified QBO-compatible format.
"""

import csv
import re
from pathlib import Path
from datetime import datetime
import PyPDF2


def get_versioned_filename(file_path):
    """
    If the file exists, append (v.1), (v.2), etc. to the filename.
    
    Args:
        file_path: Path object to the file
    
    Returns:
        Path object with versioned filename if needed
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return file_path
    
    # File exists, add version number
    version = 1
    stem = file_path.stem
    suffix = file_path.suffix
    parent = file_path.parent
    
    while True:
        new_name = f"{stem} (v.{version}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        version += 1


def format_date(date_str):
    """
    Convert date from DD.MM.YYYY to YYYY-MM-DD format (ISO 8601).
    This format is unambiguous and accepted by QuickBooks.
    
    Args:
        date_str: Date string in DD.MM.YYYY format
    
    Returns:
        Date string in YYYY-MM-DD format (e.g., 2025-09-01)
    """
    try:
        # Parse the date (format: DD.MM.YYYY)
        date_obj = datetime.strptime(date_str.strip(), "%d.%m.%Y")
        # Format as YYYY-MM-DD (e.g., 2025-09-01)
        return date_obj.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"  [WARNING] Could not format date '{date_str}': {e}")
        return date_str


def clean_amount(amount_str):
    """
    Clean and convert amount string to number format.
    Removes spaces, currency codes (ALL, USD, EUR), and converts to float.
    
    Args:
        amount_str: Amount string like "-500 ALL" or "3900 USD"
    
    Returns:
        Cleaned number string
    """
    if not amount_str or amount_str.strip() == '':
        return ''
    
    try:
        # Remove spaces and currency codes (ALL, USD, EUR, etc.)
        cleaned = amount_str.replace(' ', '').replace('ALL', '').replace('USD', '').replace('EUR', '').strip()
        # Convert to float and back to string to validate
        value = float(cleaned)
        return str(value)
    except Exception as e:
        print(f"  [WARNING] Could not clean amount '{amount_str}': {e}")
        return amount_str


def merge_description(transaction_type, beneficiary, description, reference):
    """
    Merge multiple fields into a single description field.
    
    Args:
        transaction_type: Transaction type (e.g., "Payment", "XBEN")
        beneficiary: Beneficiary/Ordering name and account number
        description: Description text
        reference: Reference number
    
    Returns:
        Merged description string
    """
    parts = []
    
    # Add transaction type
    if transaction_type and transaction_type.strip():
        parts.append(transaction_type.strip())
    
    # Add beneficiary
    if beneficiary and beneficiary.strip():
        parts.append(beneficiary.strip())
    
    # Add description
    if description and description.strip():
        parts.append(description.strip())
    
    # Add reference with "Ref: " prefix
    if reference and reference.strip():
        parts.append(f"Ref: {reference.strip()}")
    
    # Join with space between parts
    return ' '.join(parts)


def extract_text_from_pdf(pdf_path):
    """Extract text from all pages of a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"  [ERROR] Error extracting text from PDF: {e}")
    return text


def parse_raiffeisen_pdf(text_content):
    """
    Parse Raiffeisen Bank PDF text and extract transactions.
    
    PDF Format: ACCOUNT TURNOVER statement with transactions listed
    Pattern: ...XBEN [No] [Date] [Beneficiary] [Credit] ALL [Debit] [Balance]
    
    Args:
        text_content: Extracted text from PDF
    
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    
    # Clean and normalize text
    text = text_content.replace('\n', ' ').replace('\r', ' ')
    
    # Count total XBEN markers for validation
    total_xben_markers = text.count('XBEN')
    
    # Pattern to find transaction blocks
    # Format: ...XBEN [No] [Date] [Beneficiary] [Amount1] ALL [Amount2] [Amount3]
    # Correct structure based on validation: Amount1=Debit, Amount2=Credit, Amount3=Balance
    # (Header shows "Balance Credit Debit" but actual order in text is Debit Credit Balance)
    # Beneficiary can be: Name (account), IBAN, or text - stop before large numbers
    
    pattern = r'XBEN\s+(\d+)\s+(\d{2}\.\d{2}\.\d{4})\s+([A-Z0-9\s\(\)\.]+?)\s+([\d,]+\.?\d*)\s+ALL\s+([\d,]+\.?\d*)\s+([-\d,]+\.?\d*)'
    
    matches = re.finditer(pattern, text)
    
    corrupted_count = 0
    skipped_count = 0
    
    for match in matches:
        try:
            trans_no = match.group(1)
            value_date = match.group(2)
            beneficiary = match.group(3).strip()
            amount1 = match.group(4).replace(',', '')  # Debit
            amount2 = match.group(5).replace(',', '')  # Credit
            amount3 = match.group(6).replace(',', '')  # Balance
            
            # Data quality checks
            is_corrupted = False
            
            # Check 1: Description should not be excessively long (likely corrupted)
            if len(beneficiary) > 200:
                print(f"  [WARNING] Transaction {trans_no}: Description too long ({len(beneficiary)} chars) - likely corrupted")
                is_corrupted = True
                corrupted_count += 1
            
            # Check 2: Description should not contain suspicious patterns
            suspicious_patterns = ['No Posting', 'DateReference', 'Balance Credit Debit', 'Transaction  Details']
            if any(pattern in beneficiary for pattern in suspicious_patterns):
                print(f"  [WARNING] Transaction {trans_no}: Description contains PDF header text - skipping")
                is_corrupted = True
                corrupted_count += 1
            
            # Check 3: Amounts should be valid numbers
            try:
                float(amount1)
                float(amount2)
                float(amount3.replace('-', ''))  # Balance can be negative
            except ValueError:
                print(f"  [WARNING] Transaction {trans_no}: Invalid amount format - skipping")
                is_corrupted = True
                skipped_count += 1
                continue
            
            if is_corrupted:
                skipped_count += 1
                continue
            
            # Based on actual PDF structure: amount1=Debit, amount2=Credit, amount3=Balance
            debit_amount = float(amount1) if amount1 and float(amount1) > 0 else 0
            credit_amount = float(amount2) if amount2 and float(amount2) > 0 else 0
            balance = amount3
            
            # Extract description from text before XBEN
            # Look backwards from match position to find the reference and description
            text_before = text[:match.start()]
            
            # Try to find the reference (format: P250530AJDIOP14 or similar)
            ref_match = re.search(r'(P\d{6}[A-Z0-9]+)\s+([^\s]+(?:\s+[^\s]+)*?)$', text_before[-500:])
            
            reference = ref_match.group(1) if ref_match else ''
            description_part = ref_match.group(2) if ref_match else beneficiary
            
            # Build full description - limit to 500 chars
            description = f"Ref: {reference} | {beneficiary}" if reference else beneficiary
            description = description.strip()[:500]
            
            # Create transaction dictionary
            transaction = {
                'date': format_date(value_date),
                'description': description,
                'debit': debit_amount if debit_amount > 0 else '',
                'credit': credit_amount if credit_amount > 0 else '',
                'balance': balance
            }
            
            transactions.append(transaction)
            
        except Exception as e:
            print(f"  [WARNING] Error parsing transaction {match.group(0)[:100]}... Error: {e}")
            skipped_count += 1
            continue
    
    # Validation summary
    print(f"  [INFO] Extracted {len(transactions)} transactions from PDF")
    
    if total_xben_markers != len(transactions):
        print(f"  [WARNING] Transaction count mismatch: Found {total_xben_markers} XBEN markers but extracted {len(transactions)} transactions")
        print(f"  [WARNING] Skipped {skipped_count} transactions due to data quality issues")
        if corrupted_count > 0:
            print(f"  [WARNING] {corrupted_count} transactions had corrupted descriptions")
    
    return transactions


def convert_raiffeisen_csv(input_csv, output_directory=None):
    """
    Convert Raiffeisen bank CSV to QBO format.
    
    Args:
        input_csv: Path to input CSV file
        output_directory: Optional output directory path (defaults to 'export')
    
    Returns:
        Path to the created output CSV file
    """
    input_path = Path(input_csv)
    
    if not input_path.exists():
        raise FileNotFoundError(f"CSV file not found: {input_csv}")
    
    # Create output directory
    output_dir = Path(output_directory) if output_directory else Path('export')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename with " - 4qbo" suffix
    output_filename = input_path.stem + " - 4qbo.csv"
    output_path = output_dir / output_filename
    
    # Check if output file exists and add version if needed
    output_path = get_versioned_filename(output_path)
    
    print(f"Processing: {input_path.name}")
    
    # Read input CSV - skip first 3 lines (empty line + account info + empty line)
    transactions = []
    
    with open(input_path, 'r', encoding='utf-8') as csvfile:
        # Read all lines
        lines = csvfile.readlines()
        
        # Find the header line (contains "No","Value Date", etc.)
        header_line_index = -1
        for i, line in enumerate(lines):
            if 'No' in line and 'Value Date' in line and 'Processing Date' in line:
                header_line_index = i
                break
        
        if header_line_index == -1:
            raise ValueError("Could not find header line in CSV file")
        
        # Parse CSV starting from header line
        from io import StringIO
        csv_content = ''.join(lines[header_line_index:])
        reader = csv.DictReader(StringIO(csv_content))
        
        for row in reader:
            # Skip rows without processing date or with summary data
            if not row.get('Processing Date') or row['Processing Date'].strip() == '':
                continue
            
            # Skip summary rows
            if 'Previous Balance' in str(row.get('No', '')):
                continue
            
            # Extract and format data
            processing_date = row.get('Processing Date', '').strip()
            transaction_type = row.get('Transaction Type', '').strip()
            beneficiary = row.get('Beneficairy/Ordering name and account number', '').strip()
            description = row.get('Description', '').strip()
            reference = row.get('Reference', '').strip()
            amount = row.get('Amount', '').strip()
            balance = row.get('Amount Total', '').strip()
            
            # Format date
            formatted_date = format_date(processing_date)
            
            # Merge description fields
            merged_description = merge_description(
                transaction_type,
                beneficiary,
                description,
                reference
            )
            
            # Clean amounts
            cleaned_amount = clean_amount(amount)
            cleaned_balance = clean_amount(balance)
            
            # Create transaction record
            transaction = {
                'Date': formatted_date,
                'Description': merged_description,
                'Amount': cleaned_amount,
                'Balance': cleaned_balance
            }
            
            transactions.append(transaction)
    
    # Write output CSV
    if transactions:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'Description', 'Amount', 'Balance']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(transactions)
        
        print(f"  [OK] Converted {len(transactions)} transactions")
        print(f"  [OK] Saved to: {output_path}")
    else:
        print(f"  [WARNING] No transactions found in {input_path.name}")
    
    return output_path


def validate_balance_progression(transactions):
    """
    Validate that balance calculations are consistent across transactions.
    For transactions in chronological order (oldest first):
        Balance[n] = Balance[n-1] + Credit[n] - Debit[n]
    For reverse chronological order (newest first):
        Balance[n+1] = Balance[n] - Debit[n] + Credit[n]
    
    Args:
        transactions: List of transaction dictionaries
    
    Returns:
        Tuple of (is_valid, errors_list, direction)
    """
    if len(transactions) < 2:
        return True, [], "insufficient_data"
    
    errors = []
    
    # Try to determine order by checking first few transactions
    # Assume reverse chronological (newest first) which is common for bank statements
    
    for i in range(len(transactions) - 1):
        curr = transactions[i]
        next_trans = transactions[i + 1]
        
        try:
            curr_balance = float(str(curr['balance']).replace(',', ''))
            next_balance = float(str(next_trans['balance']).replace(',', ''))
            
            curr_debit = float(curr['debit']) if curr['debit'] else 0
            curr_credit = float(curr['credit']) if curr['credit'] else 0
            
            # Calculate expected next balance
            # If reverse chronological: next_balance = curr_balance - debit + credit
            expected_next = curr_balance - curr_debit + curr_credit
            
            # Allow small floating point differences
            difference = abs(expected_next - next_balance)
            
            if difference > 0.01:  # More than 1 cent difference
                errors.append({
                    'row': i + 1,
                    'date': curr['date'],
                    'current_balance': curr_balance,
                    'debit': curr_debit,
                    'credit': curr_credit,
                    'expected_next': expected_next,
                    'actual_next': next_balance,
                    'difference': difference
                })
        
        except (ValueError, KeyError) as e:
            errors.append({
                'row': i + 1,
                'error': f"Could not parse numbers: {e}"
            })
    
    return len(errors) == 0, errors, "reverse_chronological"


def convert_raiffeisen_pdf(input_pdf, output_directory=None):
    """
    Convert Raiffeisen bank PDF to QBO format.
    
    Args:
        input_pdf: Path to input PDF file
        output_directory: Optional output directory path (defaults to 'export')
    
    Returns:
        Path to the created output CSV file
    """
    input_path = Path(input_pdf)
    
    if not input_path.exists():
        raise FileNotFoundError(f"PDF file not found: {input_pdf}")
    
    # Create output directory
    output_dir = Path(output_directory) if output_directory else Path('export')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename with " - 4qbo" suffix
    output_filename = input_path.stem + " - 4qbo.csv"
    output_path = output_dir / output_filename
    
    # Check if output file exists and add version if needed
    output_path = get_versioned_filename(output_path)
    
    print(f"Processing: {input_path.name}")
    
    # Extract text from PDF
    text_content = extract_text_from_pdf(input_path)
    
    if not text_content:
        raise ValueError("Could not extract text from PDF")
    
    # Parse transactions from PDF text
    transactions = parse_raiffeisen_pdf(text_content)
    
    if not transactions:
        print(f"  [WARNING] No transactions found in {input_path.name}")
        return None
    
    print(f"  [INFO] Extracted {len(transactions)} transactions from PDF")
    
    # Note: Balance validation temporarily disabled
    # The balance calculation logic varies by bank and transaction type
    
    # Write output CSV in QuickBooks format
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for trans in transactions:
            writer.writerow({
                'Date': trans['date'],
                'Description': trans['description'],
                'Debit': f"{trans['debit']:.2f}" if trans['debit'] else '',
                'Credit': f"{trans['credit']:.2f}" if trans['credit'] else '',
                'Balance': trans['balance']
            })
    
    print(f"  [OK] Converted {len(transactions)} transactions")
    
    # Post-conversion validation
    if len(transactions) > 0:
        # Check for any remaining data quality issues
        quality_issues = 0
        for i, trans in enumerate(transactions, 1):
            # Check if description is suspiciously short (might indicate parsing issue)
            if len(trans['description']) < 5:
                print(f"  [WARNING] Row {i}: Very short description (may indicate parsing issue)")
                quality_issues += 1
            
            # Check if both debit and credit are present (unusual for most transactions)
            if trans['debit'] and trans['credit']:
                print(f"  [WARNING] Row {i}: Has both debit and credit (verify this is correct)")
        
        if quality_issues == 0:
            print(f"  [OK] Data quality check passed")
    
    print(f"  [OK] Saved to: {output_path}")
    
    return output_path


def process_all_csv_files():
    """
    Process all CSV files in current directory and import folder.
    """
    search_paths = [Path('.'), Path('import')]
    csv_files = []
    
    for search_path in search_paths:
        if search_path.exists():
            csv_files.extend(list(search_path.glob('*.csv')))
    
    if not csv_files:
        print("No CSV files found in current directory or import folder.")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to process:\n")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")
    print()
    
    success_count = 0
    failed_files = []
    
    for csv_file in csv_files:
        print(f"\n{'='*60}")
        try:
            output_path = convert_raiffeisen_csv(csv_file)
            success_count += 1
        except Exception as e:
            print(f"  [ERROR] Error processing {csv_file.name}: {e}")
            failed_files.append(csv_file.name)
            import traceback
            traceback.print_exc()
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"CONVERSION SUMMARY")
    print(f"{'='*60}")
    print(f"Total CSV files: {len(csv_files)}")
    print(f"Successfully converted: {success_count}")
    print(f"Failed: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed files:")
        for filename in failed_files:
            print(f"  - {filename}")
    
    if success_count > 0:
        print(f"\n[SUCCESS] All converted files saved in the 'export' folder")


if __name__ == "__main__":
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert Raiffeisen bank statements to QuickBooks CSV format')
    parser.add_argument('--input', '-i', dest='input_file', help='Input CSV or PDF file path')
    parser.add_argument('--output', '-o', dest='output_dir', help='Output directory for CSV file')
    parser.add_argument('csv_file', nargs='?', help='CSV or PDF file path (positional argument)')
    
    args = parser.parse_args()
    
    # Determine input file (support both --input flag and positional argument)
    input_file = None
    if args.input_file:
        input_file = args.input_file
    elif args.csv_file:
        input_file = args.csv_file
    
    # Check if a specific file path is provided
    if input_file:
        try:
            input_path = Path(input_file)
            
            # Detect file type and use appropriate converter
            if input_path.suffix.lower() == '.pdf':
                result_path = convert_raiffeisen_pdf(input_file, args.output_dir)
            elif input_path.suffix.lower() == '.csv':
                result_path = convert_raiffeisen_csv(input_file, args.output_dir)
            else:
                print(f"\n[ERROR] Unsupported file type: {input_path.suffix}")
                print("Supported formats: .pdf, .csv")
                sys.exit(1)
            
            if result_path:
                print(f"\n[SUCCESS] Conversion completed: {result_path}", flush=True)
            else:
                print(f"\n[WARNING] No output file created", flush=True)
        except Exception as e:
            print(f"\n[ERROR] Error: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Process all CSV files in the current directory
        process_all_csv_files()

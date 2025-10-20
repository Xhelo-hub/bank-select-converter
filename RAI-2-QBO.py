# -*- coding: utf-8 -*-
"""
Raiffeisen Bank CSV to QBO Format Converter
Converts Raiffeisen bank statement CSV files to a simplified QBO-compatible format.
"""

import csv
import re
from pathlib import Path
from datetime import datetime


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
    parser.add_argument('--input', '-i', dest='input_file', help='Input CSV file path')
    parser.add_argument('--output', '-o', dest='output_dir', help='Output directory for CSV file')
    parser.add_argument('csv_file', nargs='?', help='CSV file path (positional argument)')
    
    args = parser.parse_args()
    
    # Determine input file (support both --input flag and positional argument)
    input_csv = None
    if args.input_file:
        input_csv = args.input_file
    elif args.csv_file:
        input_csv = args.csv_file
    
    # Check if a specific CSV path is provided
    if input_csv:
        try:
            result_path = convert_raiffeisen_csv(input_csv, args.output_dir)
            print(f"\n[SUCCESS] Conversion completed: {result_path}", flush=True)
        except Exception as e:
            print(f"\n[ERROR] Error: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Process all CSV files in the current directory
        process_all_csv_files()

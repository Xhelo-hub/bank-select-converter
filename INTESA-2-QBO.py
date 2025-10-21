"""
INTESA BANK TO QUICKBOOKS CONVERTER
Converts Intesa Bank (Albania) CSV statements to QuickBooks compatible format.

Author: AI Assistant
Date: October 2025
"""

import csv
import re
from datetime import datetime
from pathlib import Path


def parse_albanian_date(date_str):
    """
    Parse Albanian date format (D.M.YY or DD.MM.YY) to YYYY-MM-DD.
    
    Args:
        date_str: Date string in format like "30.9.25" or "1.9.25"
    
    Returns:
        ISO formatted date string (YYYY-MM-DD)
    """
    try:
        # Split by dot
        parts = date_str.strip().split('.')
        if len(parts) != 3:
            return date_str
        
        day = parts[0].zfill(2)  # Pad with zero if single digit
        month = parts[1].zfill(2)
        year = parts[2]
        
        # Handle 2-digit year (assume 20xx)
        if len(year) == 2:
            year = f"20{year}"
        
        # Create date object and format
        date_obj = datetime(int(year), int(month), int(day))
        return date_obj.strftime('%Y-%m-%d')
    
    except Exception as e:
        print(f"  [WARNING] Could not parse date '{date_str}': {e}")
        return date_str


def clean_description(description):
    """
    Clean and simplify Intesa Bank description field.
    Extracts main beneficiary/debtor and key information.
    
    Args:
        description: Raw description with || separators
    
    Returns:
        Cleaned description string
    """
    if not description:
        return ""
    
    # Split by || separator
    parts = [p.strip() for p in description.split('||')]
    
    # Extract key components
    main_party = parts[0] if parts else ""
    
    # Look for Rem Info which usually has the main transaction details
    rem_info = ""
    for part in parts:
        if part.startswith('Rem Info::'):
            rem_info = part.replace('Rem Info::', '').strip()
            break
    
    # Build clean description
    if rem_info:
        # Limit length and combine
        clean_desc = f"{main_party} | {rem_info}"
    else:
        clean_desc = main_party
    
    # Limit to 500 chars for QuickBooks compatibility
    return clean_desc[:500].strip()


def clean_amount(amount_str):
    """
    Clean amount string and convert to float.
    
    Args:
        amount_str: Amount string (may have commas, spaces)
    
    Returns:
        Float value
    """
    if not amount_str or amount_str.strip() == '':
        return 0.0
    
    # Remove spaces and convert comma to dot if needed
    cleaned = amount_str.strip().replace(' ', '').replace(',', '')
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def get_versioned_filename(file_path):
    """
    Generate a versioned filename if the file already exists.
    
    Args:
        file_path: Path object for the output file
    
    Returns:
        Path object with versioned filename if needed
    """
    if not file_path.exists():
        return file_path
    
    # File exists, add version number
    stem = file_path.stem
    suffix = file_path.suffix
    parent = file_path.parent
    
    version = 1
    while True:
        new_name = f"{stem} (v.{version}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        version += 1


def convert_intesa_csv(input_csv, output_directory=None):
    """
    Convert Intesa Bank CSV to QuickBooks format.
    
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
    
    transactions = []
    header_found = False
    skipped_lines = 0
    data_quality_issues = 0
    
    # Read the CSV file
    with open(input_path, 'r', encoding='utf-8') as csvfile:
        lines = csvfile.readlines()
        
        # Skip first 3 lines (account info, opening balance, closing balance)
        if len(lines) < 4:
            raise ValueError("CSV file too short - expected at least 4 lines")
        
        # Line 4 should be the header
        header_line = lines[3].strip()
        if not header_line.startswith('Data,'):
            print(f"  [WARNING] Expected header at line 4, got: {header_line[:50]}")
        
        # Parse transaction lines (starting from line 5)
        reader = csv.DictReader(lines[3:])  # Start from header line
        
        for row_num, row in enumerate(reader, start=5):
            try:
                # Extract fields
                date = row.get('Data', '').strip()
                description = row.get('Përshkrimi', '').strip()
                reference = row.get('Numri i referencës', '').strip()
                trans_type = row.get('Transaction Type', '').strip().upper()
                amount_str = row.get('Shuma', '').strip()
                balance_str = row.get('Balance Amount', '').strip()
                
                # Skip empty rows
                if not date or not amount_str:
                    skipped_lines += 1
                    continue
                
                # Data quality checks
                if len(description) > 1000:
                    print(f"  [WARNING] Row {row_num}: Very long description ({len(description)} chars)")
                    data_quality_issues += 1
                
                # Parse date
                formatted_date = parse_albanian_date(date)
                
                # Clean description
                clean_desc = clean_description(description)
                
                # Add reference to description
                if reference:
                    full_description = f"Ref: {reference} | {clean_desc}"
                else:
                    full_description = clean_desc
                
                # Parse amount
                amount = clean_amount(amount_str)
                balance = balance_str
                
                # Determine debit/credit based on transaction type
                if trans_type == 'DEBIT':
                    debit = amount
                    credit = 0
                elif trans_type == 'KREDIT':
                    debit = 0
                    credit = amount
                else:
                    print(f"  [WARNING] Row {row_num}: Unknown transaction type '{trans_type}'")
                    debit = amount  # Default to debit
                    credit = 0
                    data_quality_issues += 1
                
                # Create transaction record
                transaction = {
                    'Date': formatted_date,
                    'Description': full_description,
                    'Debit': debit,
                    'Credit': credit,
                    'Balance': balance
                }
                
                transactions.append(transaction)
            
            except Exception as e:
                print(f"  [WARNING] Error processing row {row_num}: {e}")
                skipped_lines += 1
                continue
    
    if not transactions:
        print(f"  [ERROR] No transactions found in {input_path.name}")
        return None
    
    print(f"  [INFO] Extracted {len(transactions)} transactions from CSV")
    
    if skipped_lines > 0:
        print(f"  [WARNING] Skipped {skipped_lines} lines due to errors or empty data")
    
    if data_quality_issues > 0:
        print(f"  [WARNING] Found {data_quality_issues} data quality issues")
    
    # Write output CSV in QuickBooks format
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for trans in transactions:
            writer.writerow({
                'Date': trans['Date'],
                'Description': trans['Description'],
                'Debit': f"{trans['Debit']:.2f}" if trans['Debit'] > 0 else '',
                'Credit': f"{trans['Credit']:.2f}" if trans['Credit'] > 0 else '',
                'Balance': trans['Balance']
            })
    
    print(f"  [OK] Converted {len(transactions)} transactions")
    
    # Post-conversion validation
    dual_transactions = sum(1 for t in transactions if t['Debit'] > 0 and t['Credit'] > 0)
    if dual_transactions > 0:
        print(f"  [WARNING] {dual_transactions} transactions have both debit and credit (verify this is correct)")
    else:
        print(f"  [OK] Data quality check passed")
    
    print(f"  [OK] Saved to: {output_path}")
    
    return output_path


def main():
    """Main entry point for the converter."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert Intesa Bank CSV to QuickBooks format')
    parser.add_argument('input_file', nargs='?', help='Input CSV file path')
    parser.add_argument('--input', '-i', dest='input_alt', help='Input CSV file path (alternative)')
    parser.add_argument('--output', '--output-dir', '-o', dest='output_dir', help='Output directory (default: export)')
    
    args = parser.parse_args()
    
    # Determine input file (support both positional and --input flag)
    input_file = args.input_file or args.input_alt
    
    if input_file:
        # Process single file
        try:
            result_path = convert_intesa_csv(input_file, args.output_dir)
            if result_path:
                print(f"\n[SUCCESS] Conversion completed: {result_path}")
                sys.exit(0)
            else:
                print(f"\n[ERROR] Conversion failed")
                sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Process all CSV files in current directory and import folder
        search_paths = [Path('.'), Path('import')]
        csv_files = []
        
        for search_path in search_paths:
            if search_path.exists():
                csv_files.extend([f for f in search_path.glob('*.csv') if 'Intesa' in f.name])
        
        if not csv_files:
            print("No Intesa CSV files found in current directory or import folder.")
            print("Usage: python INTESA-2-QBO.py <input_file.csv>")
            sys.exit(1)
        
        print(f"Found {len(csv_files)} Intesa CSV file(s) to process:\n")
        for csv_file in csv_files:
            print(f"  - {csv_file.name}")
        print()
        
        success_count = 0
        failed_files = []
        
        for csv_file in csv_files:
            print("=" * 60)
            try:
                result_path = convert_intesa_csv(csv_file)
                if result_path:
                    success_count += 1
                else:
                    failed_files.append(csv_file.name)
            except Exception as e:
                print(f"  [ERROR] Error processing {csv_file.name}: {e}")
                failed_files.append(csv_file.name)
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("CONVERSION SUMMARY")
        print("=" * 60)
        print(f"Total CSV files: {len(csv_files)}")
        print(f"Successfully converted: {success_count}")
        print(f"Failed: {len(failed_files)}")
        
        if failed_files:
            print("\nFailed files:")
            for filename in failed_files:
                print(f"  - {filename}")
        
        sys.exit(0 if len(failed_files) == 0 else 1)


if __name__ == "__main__":
    main()

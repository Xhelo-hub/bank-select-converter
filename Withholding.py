"""
Withholding Tax Processor
Extracts withholding tax transactions from bank statement CSVs.
Searches for transactions containing "TnBurim" or "withholding" (case-insensitive).
Creates a separate CSV report named "Tatim ne Burim" with the date range.
"""

import csv
import re
from pathlib import Path
from datetime import datetime
import sys
import argparse
from collections import defaultdict


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


def parse_date(date_str):
    """
    Parse date from various formats to datetime object.
    
    Args:
        date_str: Date string in various formats
    
    Returns:
        datetime object or None if parsing fails
    """
    date_formats = [
        '%Y-%m-%d',      # 2025-06-05 (ISO format)
        '%d-%m-%Y',      # 05-06-2025
        '%d/%m/%Y',      # 05/06/2025
        '%d.%m.%Y',      # 05.06.2025
    ]
    
    # Try formats that don't need case conversion first
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    # Try formats with month abbreviations (case-insensitive)
    month_formats = [
        '%d-%b-%Y',      # 05-JUN-2025
        '%d-%b-%y',      # 05-JUN-25
    ]
    
    for fmt in month_formats:
        try:
            return datetime.strptime(date_str.strip().upper(), fmt.upper())
        except ValueError:
            continue
    
    return None


def get_date_range_string(dates):
    """
    Get a string representation of the date range (months and year).
    
    Args:
        dates: List of datetime objects
    
    Returns:
        String like "Jan-Mar 2025" or "Dec 2024-Jan 2025"
    """
    if not dates:
        return "Unknown"
    
    dates = sorted(dates)
    start_date = dates[0]
    end_date = dates[-1]
    
    # Month names in Albanian/English
    month_names = ['Jan', 'Shk', 'Mar', 'Pri', 'Maj', 'Qer', 
                   'Kor', 'Gus', 'Sht', 'Tet', 'Nën', 'Dhj']
    
    start_month = month_names[start_date.month - 1]
    end_month = month_names[end_date.month - 1]
    
    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            # Same month and year
            return f"{start_month} {start_date.year}"
        else:
            # Different months, same year
            return f"{start_month}-{end_month} {start_date.year}"
    else:
        # Different years
        return f"{start_month} {start_date.year}-{end_month} {end_date.year}"


def extract_withholding_transactions(input_csv):
    """
    Extract withholding tax transactions from bank statement CSV.
    Looks for "TnBurim" or "withholding" in the description (case-insensitive).
    
    Args:
        input_csv: Path to the input CSV file
    
    Returns:
        Tuple of (withholding_transactions, date_range_string)
    """
    input_path = Path(input_csv)
    
    if not input_path.exists():
        raise FileNotFoundError(f"CSV file not found: {input_csv}")
    
    withholding_transactions = []
    all_dates = []
    
    print(f"Processing: {input_path.name}")
    
    # Read input CSV
    with open(input_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Check if required columns exist
        if 'Description' not in reader.fieldnames:
            raise ValueError("CSV file must contain 'Description' column")
        
        for row in reader:
            description = row.get('Description', '')
            
            # Case-insensitive search for "TnBurim" or "withholding"
            if re.search(r'tnburim|withholding', description, re.IGNORECASE):
                withholding_transactions.append(row)
                
                # Parse date for date range
                date_str = row.get('Date', '')
                if date_str:
                    date_obj = parse_date(date_str)
                    if date_obj:
                        all_dates.append(date_obj)
    
    # Get date range string
    date_range = get_date_range_string(all_dates)
    
    return withholding_transactions, date_range


def calculate_totals(transactions):
    """
    Calculate total withholding tax (debit amounts only).
    Withholding tax transactions are always debits (money deducted from account).
    
    Args:
        transactions: List of transaction dictionaries
    
    Returns:
        Float representing total withholding tax amount
    """
    total_withholding = 0.0
    
    for trans in transactions:
        debit = trans.get('Debit', '').strip()
        
        if debit:
            try:
                total_withholding += float(debit)
            except ValueError:
                pass
    
    return total_withholding


def create_withholding_report(transactions, date_range, output_path):
    """
    Create a CSV report with withholding tax transactions.
    Calculates Gross and Tax amounts based on 15% withholding tax rate.
    
    Formula:
    - Debit = Amount received (85% of gross)
    - Gross = Debit / 0.85 (100% of original amount)
    - Tax = Gross - Debit (15% withheld)
    
    Args:
        transactions: List of transaction dictionaries
        date_range: String representing the date range
        output_path: Path to the output CSV file
    
    Returns:
        Path to the created CSV file
    """
    if not transactions:
        print("WARNING: No withholding tax transactions found.", flush=True)
        return None
    
    # Check for versioning
    output_path = get_versioned_filename(output_path)
    
    print(f"\nFound {len(transactions)} withholding tax transaction(s)", flush=True)
    
    # Calculate totals
    total_debit = 0.0
    total_gross = 0.0
    total_tax = 0.0
    
    # Write to CSV with new columns
    fieldnames = ['Date', 'Description', 'Debit', 'Gross', 'Tax']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for trans in transactions:
            debit_str = trans.get('Debit', '').strip()
            
            if debit_str:
                try:
                    debit = float(debit_str)
                    # Calculate gross (debit represents 85% of gross)
                    gross = debit / 0.85
                    # Calculate tax (15% withholding)
                    tax = gross - debit
                    
                    # Add to totals
                    total_debit += debit
                    total_gross += gross
                    total_tax += tax
                    
                    # Write row with calculated values
                    row = {
                        'Date': trans.get('Date', ''),
                        'Description': trans.get('Description', ''),
                        'Debit': f'{debit:.2f}',
                        'Gross': f'{gross:.2f}',
                        'Tax': f'{tax:.2f}'
                    }
                    writer.writerow(row)
                except ValueError:
                    # If debit can't be converted to float, skip calculation
                    row = {
                        'Date': trans.get('Date', ''),
                        'Description': trans.get('Description', ''),
                        'Debit': debit_str,
                        'Gross': '',
                        'Tax': ''
                    }
                    writer.writerow(row)
    
    # Display summary
    print(f"Total Amount Received (Debit): {total_debit:,.2f} LEK", flush=True)
    print(f"Total Gross Amount: {total_gross:,.2f} LEK", flush=True)
    print(f"Total Withholding Tax (15%): {total_tax:,.2f} LEK", flush=True)
    
    print(f"\nSuccess! Withholding tax report created: {output_path}", flush=True)
    return output_path


def process_withholding_from_csv(input_csv, output_dir=None):
    """
    Process withholding tax from bank statement CSV.
    
    Args:
        input_csv: Path to the input CSV file
        output_dir: Optional output directory (default: 'export')
    
    Returns:
        Path to the created withholding report
    """
    input_path = Path(input_csv)
    
    # Create output directory
    if output_dir is None:
        output_dir = Path('export')
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract withholding transactions
    transactions, date_range = extract_withholding_transactions(input_csv)
    
    if not transactions:
        return None
    
    # Generate output filename: "Tatim ne Burim [date_range].csv"
    output_filename = f"Tatim ne Burim {date_range}.csv"
    output_path = output_dir / output_filename
    
    # Create the report
    return create_withholding_report(transactions, date_range, output_path)


def main():
    """
    Main function to process withholding tax from bank statement CSV.
    If no arguments provided, automatically processes all CSV files in export folder.
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Extract withholding tax transactions from bank statements')
    parser.add_argument('--input', '-i', dest='input_file', help='Input CSV file path')
    parser.add_argument('--output', '-o', dest='output_dir', help='Output directory for CSV file')
    parser.add_argument('csv_file', nargs='?', help='CSV file path (positional argument)')
    parser.add_argument('output_directory', nargs='?', help='Output directory (positional argument)')
    
    args = parser.parse_args()
    
    # Determine input file and output directory
    input_file = args.input_file or args.csv_file
    output_dir = args.output_dir or args.output_directory
    
    if not input_file:
        # No arguments - automatically process all CSV files in current directory and import folder
        print("Withholding Tax Processor")
        print("="*60)
        print("\nScanning current directory and import folder for bank statement CSV files...\n")
        
        search_paths = [Path('.'), Path('import')]
        csv_files = []
        
        for search_path in search_paths:
            if search_path.exists():
                # Find all CSV files (exclude "Tatim ne Burim" files)
                csv_files.extend([f for f in search_path.glob('*.csv') 
                                 if not f.name.startswith('Tatim ne Burim')])
        
        if not csv_files:
            print("Error: No CSV files found in current directory or import folder.", flush=True)
            sys.exit(1)
        
        print(f"Found {len(csv_files)} CSV file(s):\n", flush=True)
        for i, csv_file in enumerate(csv_files, 1):
            print(f"  {i}. {csv_file.name}", flush=True)
        
        print("\nProcessing all files...\n", flush=True)
        print("-" * 60, flush=True)
        
        total_processed = 0
        total_withholding_found = 0
        
        for csv_file in csv_files:
            print(f"\nProcessing: {csv_file.name}", flush=True)
            try:
                result = process_withholding_from_csv(str(csv_file))
                if result:
                    total_processed += 1
                    total_withholding_found += 1
            except Exception as e:
                print(f"WARNING: Error processing {csv_file.name}: {e}", flush=True)
            print("-" * 60, flush=True)
        
        print(f"\nSuccess! Processed {total_processed} file(s).", flush=True)
        print(f"  Found withholding transactions in {total_withholding_found} file(s).", flush=True)
        return
    
    # Arguments provided - process specific file
    try:
        result = process_withholding_from_csv(input_file, output_dir)
        
        if result:
            print(f"\nSuccess! Withholding tax report created.", flush=True)
        else:
            print("\nWARNING: No withholding tax transactions found in the input file.", flush=True)
            sys.exit(0)
    
    except FileNotFoundError as e:
        print(f"\nError: {e}", flush=True)
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: Unexpected error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

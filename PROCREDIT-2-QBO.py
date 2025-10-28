#!/usr/bin/env python3
"""
ProCredit Bank Albania to QuickBooks CSV Converter
==================================================
Converts ProCredit Bank Albania statements (CSV format) to QuickBooks-compatible CSV.

Bank: ProCredit Bank Albania
Input: CSV export from ProCredit online banking
Output: QuickBooks CSV (Date, Description, Debit, Credit, Balance)

Features:
- Handles Albanian date format (DD.MM.YYYY)
- Processes amounts with comma as decimal separator
- Supports debit/credit columns (Amount, Amount1)
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
        description='Convert ProCredit Bank Albania CSV to QuickBooks format'
    )
    parser.add_argument(
        '--input',
        help='Input CSV file path',
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
        # Look for CSV files in current directory and import folder
        search_paths = [Path('.'), Path('import')]
        input_files = []
        for search_path in search_paths:
            if search_path.exists():
                input_files.extend(search_path.glob('*.csv'))
        
        if not input_files:
            print("Error: No CSV files found. Please provide --input parameter or place CSV in current/import folder.")
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
        
        # Parse the CSV
        transactions = parse_procredit_csv(input_path)
        
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

"""
PDF to CSV Converter for Bank Statements
Extracts text from PDF and converts bank statement data directly to CSV format.
"""

import PyPDF2
import csv
import re
from pathlib import Path
import sys
from datetime import datetime


def extract_text_from_pdf(pdf_path):
    """
    Extract text content from PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        String containing all text from the PDF
    """
    text_content = []
    
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        print(f"Reading PDF: {pdf_path}")
        print(f"Total pages: {num_pages}")
        
        for page_num in range(num_pages):
            print(f"Processing page {page_num + 1}/{num_pages}...", end='\r')
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            text_content.append(text)
    
    print(f"\nText extraction completed!")
    return '\n'.join(text_content)


def parse_bank_statement(text_content):
    """
    Parse bank statement text and extract transaction data.
    
    Args:
        text_content: String containing the bank statement text
    
    Returns:
        List of dictionaries containing transaction data
    """
    transactions = []
    lines = text_content.split('\n')
    
    # Extract account information
    account_no = None
    account_holder = None
    opening_balance = None
    closing_balance = None
    
    # Find account details
    for i, line in enumerate(lines):
        if 'IBAN:' in line:
            iban_match = re.search(r'IBAN:\s*(\S+)', line)
            if iban_match:
                account_no = iban_match.group(1)
        
        if 'AccountNo:' in line:
            acc_match = re.search(r'AccountNo:(\S+)', line)
            if acc_match:
                account_no = acc_match.group(1)
        
        # Find account holder name
        if i > 0 and '111050731' in lines[i-1] and 'MISSION POSSIBLE' in line:
            account_holder = line.strip()
        
        # Find opening balance
        if 'OPENING BALANCE:' in line:
            balance_match = re.search(r'OPENING BALANCE:\s+([\d,\.]+)', line)
            if balance_match:
                opening_balance = balance_match.group(1).replace(',', '')
        
        # Find closing balance
        if 'CLOSING BALANCE' in line:
            balance_match = re.search(r'CLOSING BALANCE\s+([\d,\.]+)', line)
            if balance_match:
                closing_balance = balance_match.group(1).replace(',', '')
    
    # Parse transactions
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if line starts with a date (DD-MMM-YY format)
        date_match = re.match(r'^\s*(\d{2}-[A-Z]{3}-\d{2})\s+(.+)', line)
        
        if date_match:
            date = date_match.group(1)
            rest_of_line = date_match.group(2).strip()
            
            # Parse the transaction line
            parts = rest_of_line.split()
            
            if len(parts) >= 2:
                description = parts[0]
                reference = parts[1] if len(parts) > 1 else ''
                
                # Try to extract value date and amounts
                value_date = ''
                debit = ''
                credit = ''
                balance = ''
                
                # Look for date pattern (value date)
                for part in parts[2:]:
                    if re.match(r'\d{2}-[A-Z]{3}-\d{2}', part):
                        value_date = part
                        break
                
                # Extract amounts (look for numbers with commas/dots)
                amounts = []
                for part in parts:
                    if re.match(r'[\d,\.]+$', part) and '.' in part:
                        clean_amount = part.replace(',', '')
                        amounts.append(clean_amount)
                
                # Assign amounts to debit, credit, balance
                if len(amounts) == 1:
                    balance = amounts[0]
                elif len(amounts) == 2:
                    if description in ['COMMISSION', 'TRANSFER', 'CASH WITHDRAWAL', 'UTILITY PAYMENT', 
                                      'ACCOUNT TO ACCOUNT', 'PAGESE PER', 'KOMISION PER']:
                        debit = amounts[0]
                        balance = amounts[1]
                    else:
                        credit = amounts[0]
                        balance = amounts[1]
                elif len(amounts) >= 3:
                    debit = amounts[0] if amounts[0] else ''
                    credit = amounts[1] if amounts[1] else ''
                    balance = amounts[2] if len(amounts) > 2 else amounts[-1]
                
                # Collect additional details from next lines
                details = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    # Stop if we hit another transaction date or a separator line
                    if re.match(r'^\d{2}-[A-Z]{3}-\d{2}', next_line) or '---' in next_line:
                        break
                    # Stop at page markers
                    if 'PAGE NO' in next_line or 'AccountNo:' in next_line:
                        break
                    if next_line and not next_line.startswith('Shënim:'):
                        # Clean up the detail line
                        detail_clean = re.sub(r'\s+', ' ', next_line)
                        if detail_clean and len(detail_clean) > 3:
                            details.append(detail_clean)
                    j += 1
                
                # Merge description, reference, and details into one field
                merged_description = description
                if reference:
                    merged_description += f" - {reference}"
                if details:
                    detail_text = ' | '.join(details[:5])
                    if detail_text:
                        merged_description += f" | {detail_text}"
                
                # Create transaction record
                transaction = {
                    'Date': date,
                    'Description': merged_description,
                    'Debit': debit,
                    'Credit': credit,
                    'Balance': balance
                }
                
                transactions.append(transaction)
                i = j - 1
        
        i += 1
    
    # Add summary information
    summary = {
        'Account Number': account_no or 'N/A',
        'Account Holder': account_holder or 'N/A',
        'Opening Balance': opening_balance or 'N/A',
        'Closing Balance': closing_balance or 'N/A',
        'Total Transactions': len(transactions)
    }
    
    return transactions, summary


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
    Convert date from DD-MMM-YY format to YYYY-MM-DD format (ISO 8601).
    This format is unambiguous and accepted by QuickBooks.
    
    Args:
        date_str: Date string in DD-MMM-YY format (e.g., "05-JAN-25")
    
    Returns:
        Date string in YYYY-MM-DD format (e.g., "2025-01-05")
    """
    try:
        # Parse DD-MMM-YY format
        date_obj = datetime.strptime(date_str, '%d-%b-%y')
        # Convert to YYYY-MM-DD format
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        # If parsing fails, return original
        return date_str


def validate_and_fix_transactions(transactions):
    """
    Validate transactions by checking if balance calculations are correct.
    If previous_balance - debit + credit != current_balance, swap debit and credit.
    
    Args:
        transactions: List of transaction dictionaries
    
    Returns:
        List of corrected transactions and count of corrections made
    """
    corrections_made = 0
    
    for i in range(len(transactions)):
        # Skip first transaction (no previous balance to compare)
        if i == 0:
            continue
        
        current = transactions[i]
        previous = transactions[i - 1]
        
        # Get values, default to 0 if empty
        try:
            prev_balance = float(previous['Balance']) if previous['Balance'] else 0
            current_balance = float(current['Balance']) if current['Balance'] else 0
            debit = float(current['Debit']) if current['Debit'] else 0
            credit = float(current['Credit']) if current['Credit'] else 0
        except (ValueError, TypeError):
            # Skip if values can't be converted to float
            continue
        
        # Calculate expected balance: previous_balance - debit + credit
        expected_balance = prev_balance - debit + credit
        
        # Allow small rounding differences (0.01)
        if abs(expected_balance - current_balance) > 0.01:
            # Try swapping debit and credit
            expected_balance_swapped = prev_balance - credit + debit
            
            if abs(expected_balance_swapped - current_balance) <= 0.01:
                # Swap debit and credit
                current['Debit'], current['Credit'] = current['Credit'], current['Debit']
                corrections_made += 1
                print(f"  WARNING: Row {i+1}: Swapped debit/credit for '{current['Date']}' - {current['Description'][:30]}...")
    
    return transactions, corrections_made


def pdf_to_csv(pdf_path, output_csv=None):
    """
    Convert PDF bank statement directly to CSV.
    
    Args:
        pdf_path: Path to the input PDF file
        output_csv: Path to the output CSV file (optional)
    
    Returns:
        Path to the created CSV file
    """
    # Convert to Path object
    pdf_path = Path(pdf_path)
    
    # Check if PDF exists
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Generate output path if not provided
    if output_csv is None:
        output_csv = pdf_path.with_suffix('.csv')
    else:
        output_csv = Path(output_csv)
    
    # Check if output file exists and add version if needed
    output_csv = get_versioned_filename(output_csv)
    
    # Extract text from PDF
    text_content = extract_text_from_pdf(pdf_path)
    
    # Parse the bank statement
    print("\nParsing bank statement...")
    transactions, summary = parse_bank_statement(text_content)
    
    print(f"\nStatement Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Validate and fix transactions
    if transactions:
        print(f"\nValidating transactions...")
        transactions, corrections = validate_and_fix_transactions(transactions)
        if corrections > 0:
            print(f"Made {corrections} correction(s) by swapping debit/credit columns")
        else:
            print(f"All transactions validated successfully")
        
        # Remove first row if it has only balance (no debit or credit)
        if transactions and len(transactions) > 0:
            first_row = transactions[0]
            if (not first_row.get('Debit') or first_row['Debit'] == '') and \
               (not first_row.get('Credit') or first_row['Credit'] == ''):
                print(f"Removed first row (opening balance only)")
                transactions = transactions[1:]
        
        # Format dates to DD/MM/YYYY
        for transaction in transactions:
            transaction['Date'] = format_date(transaction['Date'])
        
        # Remove Balance column from all transactions
        for transaction in transactions:
            if 'Balance' in transaction:
                del transaction['Balance']
    
    # Write to CSV
    if transactions:
        print(f"\nWriting {len(transactions)} transactions to CSV...")
        
        fieldnames = ['Date', 'Description', 'Debit', 'Credit']
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(transactions)
        
        print(f"CSV file saved: {output_csv}")
        print(f"Success! {len(transactions)} transactions exported.")
    else:
        print("Warning: No transactions found in the PDF.")
    
    return output_csv


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert BKT bank statements to QuickBooks CSV format')
    parser.add_argument('--input', '-i', dest='input_file', help='Input PDF file path')
    parser.add_argument('--output', '-o', dest='output_dir', help='Output directory for CSV file')
    parser.add_argument('pdf_file', nargs='?', help='PDF file path (positional argument)')
    parser.add_argument('output_file', nargs='?', help='Output file path (positional argument)')
    
    args = parser.parse_args()
    
    # Determine input file (support both --input flag and positional argument)
    input_pdf = None
    if args.input_file:
        input_pdf = Path(args.input_file)
    elif args.pdf_file:
        input_pdf = Path(args.pdf_file)
    
    # Check if a specific PDF path is provided
    if input_pdf:
        # Process single PDF file
        pdf_file = input_pdf
        
        # Determine output path
        if args.output_file:
            output_file = Path(args.output_file)
        elif args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            csv_filename = pdf_file.stem + " - 4qbo.csv"
            output_file = output_dir / csv_filename
        else:
            output_dir = Path('export')
            output_dir.mkdir(parents=True, exist_ok=True)
            csv_filename = pdf_file.stem + " - 4qbo.csv"
            output_file = output_dir / csv_filename
        
        try:
            result_path = pdf_to_csv(pdf_file, output_file)
            print(f"\nSuccess! CSV file created at: {result_path}", flush=True)
        except Exception as e:
            print(f"\nError: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Process all PDF files in current directory and import folder
        search_paths = [Path('.'), Path('import')]
        pdf_files = []
        
        for search_path in search_paths:
            if search_path.exists():
                pdf_files.extend(list(search_path.glob('*.pdf')))
        
        if not pdf_files:
            print("No PDF files found in current directory or import folder.")
            sys.exit(1)
        
        print(f"Found {len(pdf_files)} PDF file(s) to process:\n")
        for pdf in pdf_files:
            print(f"  - {pdf.name}")
        print()
        
        success_count = 0
        failed_files = []
        
        for pdf_file in pdf_files:
            print(f"\n{'='*60}")
            print(f"Processing: {pdf_file.name}")
            print(f"{'='*60}")
            
            try:
                # Generate output CSV in export folder
                output_dir = Path('export')
                output_dir.mkdir(parents=True, exist_ok=True)
                # Add " - 4qbo" to the filename
                csv_filename = pdf_file.stem + " - 4qbo.csv"
                output_csv = output_dir / csv_filename
                
                result_path = pdf_to_csv(pdf_file, output_csv)
                print(f"\nSuccess! CSV file created at: {result_path}")
                success_count += 1
            except Exception as e:
                print(f"\nError processing {pdf_file.name}: {e}")
                failed_files.append(pdf_file.name)
                import traceback
                traceback.print_exc()
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"CONVERSION SUMMARY")
        print(f"{'='*60}")
        print(f"Total PDF files: {len(pdf_files)}")
        print(f"Successfully converted: {success_count}")
        print(f"Failed: {len(failed_files)}")
        
        if failed_files:
            print("\nFailed files:")
            for filename in failed_files:
                print(f"  - {filename}")
        
        if success_count > 0:
            print(f"\nAll CSV files saved in the 'export' folder")
        
        sys.exit(0 if len(failed_files) == 0 else 1)

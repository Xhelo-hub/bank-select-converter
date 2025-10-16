"""
UNION Bank PDF to QBO Format Converter
Converts Union Bank PDF statements to QBO-compatible CSV format.
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


def parse_union_statement(text_content):
    """
    Parse Union Bank statement text and extract transaction data.
    Union Bank format has transactions followed by details on next lines.
    
    Args:
        text_content: String containing the bank statement text
    
    Returns:
        List of dictionaries containing transaction data
    """
    transactions = []
    lines = text_content.split('\n')
    
    # Union Bank date format: DD-MMM-YYYY (date can be alone on line or with more text)
    date_pattern = r'^(\d{2}-[A-Z]{3}-\d{4})'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for opening balance line specifically
        if 'BALANCA E FILLIMIT' in line:
            # Extract opening balance
            date_match = re.match(date_pattern, line)
            if date_match:
                date_found = date_match.group(1)
                # Extract the balance amount from the end of the line
                balance_match = re.search(r'([\d,]+\.\d{2})\s*$', line)
                if balance_match:
                    balance = balance_match.group(1).replace(',', '')
                    transactions.append({
                        'Date': date_found,
                        'Description': 'BALANCA E FILLIMIT',
                        'Debit': '',
                        'Credit': '',
                        'Balance': balance
                    })
            i += 1
            continue
        
        # Skip headers, footers, empty lines
        if not line or any(skip in line for skip in [
            'NXJERRJE LLOGARIE', 'STATEMENT', 'NUMERI I KLIENTIT', 'KLIENTI:',
            'ADRESA:', 'LLOGARIA:', 'PERIUDHA', 'DATA  TIPI I TRANSAKSIONIT',
            'PERSHKRIMI', 'REFERENCA        SHUMA', 'BALANCA E MBARIMIT', 
            'UNION BANK', 'Firefox', 'https://', 'FAQE NR', 'Dega UB',
            '--------------------------------------------------',
            'DATA E PRINTIMIT', 'DATA E FILLIMIT', 'DATA E MBARIMIT',
            'DATA  TIPI', 'DEBI            KREDI                BALANCA'
        ]):
            i += 1
            continue
        
        # Check if line starts with a date
        date_match = re.match(date_pattern, line)
        
        if date_match:
            date_found = date_match.group(1)
            rest_of_line = line[date_match.end():].strip()
            
            # Now look for the next lines to gather transaction details
            # Next line often starts with transaction type (e.g., "Transferte ne mberritje")
            description_lines = []
            debit = ''
            credit = ''
            balance = ''
            
            j = i + 1
            
            # Collect lines until we hit another date or section break
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Stop if we hit another date (start of next transaction)
                if re.match(date_pattern, next_line):
                    break
                
                # Skip empty lines but keep processing
                if not next_line:
                    j += 1
                    continue
                
                # Stop at headers/footers
                if any(skip in next_line for skip in [
                    'NXJERRJE LLOGARIE', 'LLOGARIA:', 'PERIUDHA',
                    'DATA  TIPI', 'PERSHKRIMI', 'BALANCA E',
                    'UNION BANK', 'Firefox', 'FAQE NR',
                    '--------------------------------------------------'
                ]):
                    break
                
                # Check if this line has amounts (3 columns: DEBI, KREDI, BALANCA)
                # Format: "... reference date debit credit balance"
                amounts_match = re.search(r'(\d{2}-[A-Z]{3}-\d{4})\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$', next_line)
                
                if amounts_match:
                    # Found transaction line with date and two amounts at end
                    trans_date = amounts_match.group(1)
                    amt1 = amounts_match.group(2).replace(',', '')
                    amt2 = amounts_match.group(3).replace(',', '')
                    
                    # Description is everything before the date
                    desc_part = next_line[:amounts_match.start()].strip()
                    if desc_part:
                        description_lines.append(desc_part)
                    
                    # Determine debit/credit: check which column has value
                    # Often one is empty, or we can check the pattern
                    # The format seems to be: TYPE REFERENCE DATE DEBIT CREDIT BALANCE
                    # Try to extract one more amount before these two
                    before_date = next_line[:amounts_match.start()].strip()
                    third_amt_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+$', before_date)
                    
                    if third_amt_match:
                        # Found 3 amounts: debit, credit, balance
                        debit_val = third_amt_match.group(1).replace(',', '')
                        if debit_val and debit_val != '0.00':
                            debit = debit_val
                        if amt1 and amt1 != '0.00':
                            credit = amt1
                        balance = amt2
                    else:
                        # Only 2 amounts found
                        # Assume first is transaction amount, second is balance
                        # Look for pattern to determine if debit or credit
                        if not credit:  # If credit not yet set
                            credit = amt1
                        balance = amt2
                    
                    # Don't break yet - continue collecting description lines AFTER the amounts line
                    j += 1
                    continue
                else:
                    # This is a description/details line - collect it
                    if next_line:
                        description_lines.append(next_line)
                    j += 1
            
            # Merge description and clean up multiple spaces
            merged_description = ' '.join(description_lines).strip()
            # Replace multiple spaces with single space
            merged_description = ' '.join(merged_description.split())
            
            # Create transaction
            transaction = {
                'Date': date_found,
                'Description': merged_description,
                'Debit': debit,
                'Credit': credit,
                'Balance': balance
            }
            
            transactions.append(transaction)
            i = j
        else:
            i += 1
    
    return transactions


def format_date(date_str):
    """
    Convert various date formats to YYYY-MM-DD format (ISO 8601).
    This format is unambiguous and accepted by QuickBooks.
    
    Args:
        date_str: Date string in various formats
    
    Returns:
        Date string in YYYY-MM-DD format (e.g., 2025-06-05)
    """
    # Check if already in DD-MMM-YYYY format (Union Bank format)
    if re.match(r'^\d{2}-[A-Z]{3}-\d{4}$', date_str):
        try:
            date_obj = datetime.strptime(date_str, '%d-%b-%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # Try different date formats
    date_formats = [
        '%d/%m/%Y',
        '%d.%m.%Y',
        '%d-%m-%Y',
        '%d/%m/%y',
        '%d.%m.%y',
        '%d-%m-%y',
        '%d-%b-%Y',
        '%d-%b-%y',
        '%Y-%m-%d'  # Already in correct format
    ]
    
    for in_fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str, in_fmt)
            # If year is 2-digit, ensure it's in 2000s
            if date_obj.year < 100:
                date_obj = date_obj.replace(year=date_obj.year + 2000)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If no format matches, return original
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
                print(f"  ⚠ Row {i+1}: Swapped debit/credit for '{current['Date']}' - {current['Description'][:30]}...")
    
    return transactions, corrections_made


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


def pdf_to_csv(pdf_path, output_csv=None):
    """
    Convert Union Bank PDF statement to CSV.
    
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
    transactions = parse_union_statement(text_content)
    
    print(f"Found {len(transactions)} transactions")
    
    # Format dates
    for transaction in transactions:
        transaction['Date'] = format_date(transaction['Date'])
    
    # Validate and fix transactions
    if transactions:
        print(f"\nValidating transactions...")
        transactions, corrections = validate_and_fix_transactions(transactions)
        if corrections > 0:
            print(f"✓ Made {corrections} correction(s) by swapping debit/credit columns")
        else:
            print(f"✓ All transactions validated successfully")
        
        # Check overall balance (before removing opening balance row)
        print(f"\nVerifying overall balance...")
        beginning_balance = 0.0
        ending_balance = 0.0
        
        if transactions and len(transactions) > 0:
            # Get beginning balance (first transaction should be opening balance or first real transaction)
            first_row = transactions[0]
            if (not first_row.get('Debit') or first_row['Debit'] == '') and \
               (not first_row.get('Credit') or first_row['Credit'] == ''):
                # This is the opening balance row
                beginning_balance = float(first_row.get('Balance', 0))
                print(f"  Beginning Balance: {beginning_balance:,.2f}")
                
                # Get ending balance from last transaction
                if len(transactions) > 1:
                    ending_balance = float(transactions[-1].get('Balance', 0))
                    print(f"  Ending Balance: {ending_balance:,.2f}")
                    
                    # Calculate sum of debits and credits (excluding opening balance row)
                    total_debits = sum(float(t.get('Debit', 0) or 0) for t in transactions[1:])
                    total_credits = sum(float(t.get('Credit', 0) or 0) for t in transactions[1:])
                    
                    print(f"  Total Debits: {total_debits:,.2f}")
                    print(f"  Total Credits: {total_credits:,.2f}")
                    
                    # Calculate expected ending balance: beginning + credits - debits
                    calculated_balance = beginning_balance + total_credits - total_debits
                    print(f"  Calculated Ending Balance: {calculated_balance:,.2f}")
                    
                    # Check if they match (with small tolerance for rounding)
                    if abs(calculated_balance - ending_balance) < 0.01:
                        print(f"  ✓ Balance verification PASSED!")
                    else:
                        difference = ending_balance - calculated_balance
                        print(f"  ⚠ Balance verification FAILED!")
                        print(f"  ⚠ Difference: {difference:,.2f}")
            else:
                # No opening balance row, just verify the last balance
                if len(transactions) > 0:
                    ending_balance = float(transactions[-1].get('Balance', 0))
                    print(f"  Final Balance: {ending_balance:,.2f}")
        
        # Remove first row if it has only balance (no debit or credit)
        if transactions and len(transactions) > 0:
            first_row = transactions[0]
            if (not first_row.get('Debit') or first_row['Debit'] == '') and \
               (not first_row.get('Credit') or first_row['Credit'] == ''):
                print(f"\n✓ Removed first row (opening balance only)")
                transactions = transactions[1:]
        
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
        print(f"✓ Success! {len(transactions)} transactions exported.")
    else:
        print("⚠ Warning: No transactions found in the PDF.")
    
    return output_csv


if __name__ == "__main__":
    # Check if a specific PDF path is provided as argument
    if len(sys.argv) > 1:
        # Process single PDF file
        pdf_file = Path(sys.argv[1])
        
        # Generate output path in export folder with " - 4qbo" suffix if not provided
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        else:
            output_dir = Path('export')
            output_dir.mkdir(exist_ok=True)
            csv_filename = pdf_file.stem + " - 4qbo.csv"
            output_file = output_dir / csv_filename
        
        try:
            result_path = pdf_to_csv(pdf_file, output_file)
            print(f"\n✓ CSV file created at: {result_path}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
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
                output_dir.mkdir(exist_ok=True)
                # Add " - 4qbo" to the filename
                csv_filename = pdf_file.stem + " - 4qbo.csv"
                output_csv = output_dir / csv_filename
                
                result_path = pdf_to_csv(pdf_file, output_csv)
                print(f"\n✓ CSV file created at: {result_path}")
                success_count += 1
            except Exception as e:
                print(f"\n✗ Error processing {pdf_file.name}: {e}")
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
            print(f"\n✓ All CSV files saved in the 'export' folder")
        
        sys.exit(0 if len(failed_files) == 0 else 1)

"""
TABANK PDF to QBO Format Converter
Converts TABANK (Tirana Bank) PDF statements to QBO-compatible CSV format.
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


def parse_tabank_statement(text_content):
    """
    Parse TABANK statement text and extract transaction data.
    
    Args:
        text_content: String containing the bank statement text
    
    Returns:
        List of dictionaries containing transaction data
    """
    transactions = []
    lines = text_content.split('\n')
    
    # Transaction line pattern: starts with time HH:MM followed by date
    # Format: "07:51   01 Kor 25 01 Kor 25 DESCRIPTION -amount  balance"
    # or:     "14:40   04 Kor 25 04 Kor 25 DESCRIPTION amount  balance"
    transaction_pattern = r'^\d{2}:\d{2}\s+(\d{2}\s+\w{3}\s+\d{2})\s+\d{2}\s+\w{3}\s+\d{2}\s+'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line starts a transaction
        match = re.match(transaction_pattern, line)
        
        if match:
            # Extract date (from first date column, ignore time)
            date_found = match.group(1)  # e.g., "01 Kor 25"
            
            # Get the rest of the line after the dates
            rest_of_line = line[match.end():].strip()
            
            # Find debit (negative amount) and credit (positive amount) and balance
            # Pattern: description [-]amount  balance
            # Debit has negative sign: -22,000.00  33,923.15
            # Credit has no sign: 335,877.50  338,600.65
            
            debit = ''
            credit = ''
            balance = ''
            description_text = rest_of_line
            
            # Look for negative amount (debit) followed by balance
            debit_pattern = r'-(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$'
            debit_match = re.search(debit_pattern, rest_of_line)
            
            if debit_match:
                # This is a debit transaction
                debit = debit_match.group(1).replace(',', '')
                balance = debit_match.group(2).replace(',', '')
                description_text = rest_of_line[:debit_match.start()].strip()
            else:
                # Look for credit (positive amount) followed by balance
                credit_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$'
                credit_match = re.search(credit_pattern, rest_of_line)
                
                if credit_match:
                    credit = credit_match.group(1).replace(',', '')
                    balance = credit_match.group(2).replace(',', '')
                    description_text = rest_of_line[:credit_match.start()].strip()
            
            # Collect all description lines until next transaction
            details = [description_text] if description_text else []
            j = i + 1
            
            # Look ahead for continuation lines
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Stop if we hit another transaction (starts with time)
                if re.match(transaction_pattern, next_line):
                    break
                
                # Stop if empty line
                if not next_line:
                    j += 1
                    continue
                
                # Skip header/footer lines and balance summary lines
                if any(skip in next_line for skip in [
                    'Numri i llogarisë', 'Data e Veprimit', 'Datë Valuta', 'Përshkrimi',
                    'Debi', 'Kredi', 'Balance', 'Nxjerrje Llogarie', 'Faqe :',
                    'Teprica e mbartur', 'Teprica që do te mbartet',
                    'Shënim:', 'Data e printimit', 'Nga :', 'Deri :', 'Printuar për',
                    'Monedha:', 'Adresa :', 'Tel:', 'Status', 'nga'
                ]):
                    break
                
                # Add this line to description
                details.append(next_line)
                j += 1
            
            # Merge all description lines with space separator
            merged_description = ' '.join(details).strip()
            
            # Create transaction record
            transaction = {
                'Date': date_found,
                'Description': merged_description,
                'Debit': debit,
                'Credit': credit,
                'Balance': balance
            }
            
            transactions.append(transaction)
            i = j - 1
        
        i += 1
    
    return transactions


def format_date(date_str):
    """
    Convert various date formats to YYYY-MM-DD format (ISO 8601).
    Handles both Albanian and English month names.
    This format is unambiguous and accepted by QuickBooks.
    
    Args:
        date_str: Date string in various formats
    
    Returns:
        Date string in YYYY-MM-DD format (e.g., 2025-07-05)
    """
    # Albanian month abbreviations mapping to month numbers
    albanian_months = {
        'Jan': '01', 'Shk': '02', 'Mar': '03', 'Pri': '04', 'Maj': '05', 'Qer': '06',
        'Kor': '07', 'Gus': '08', 'Sht': '09', 'Tet': '10', 'Nën': '11', 'Nen': '11', 'Dhj': '12'
    }
    
    # English month abbreviations mapping to month numbers
    english_months = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    # Try Albanian/English format: "01 Kor 25" -> "2025-07-01"
    alb_match = re.match(r'(\d{2})\s+(\w{3})\s+(\d{2})', date_str)
    if alb_match:
        day = alb_match.group(1)
        month_abbr = alb_match.group(2)
        year = alb_match.group(3)
        
        # Convert 2-digit year to 4-digit (assume 20xx)
        full_year = f"20{year}"
        
        # Check Albanian months
        if month_abbr in albanian_months:
            return f"{full_year}-{albanian_months[month_abbr]}-{day}"
        
        # Check English months
        if month_abbr in english_months:
            return f"{full_year}-{english_months[month_abbr]}-{day}"
    
    # Try different numeric date formats
    date_formats = [
        '%d/%m/%Y',
        '%d.%m.%Y',
        '%d-%m-%Y',
        '%d/%m/%y',
        '%d.%m.%y',
        '%d-%m-%y',
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
                print(f"  WARNING: Row {i+1}: Swapped debit/credit for '{current['Date']}' - {current['Description'][:30]}...", flush=True)
    
    return transactions, corrections_made


def pdf_to_csv(pdf_path, output_csv=None):
    """
    Convert TABANK PDF statement to CSV.
    
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
    
    # Extract text from PDF
    text_content = extract_text_from_pdf(pdf_path)
    
    # Debug: Save extracted text to file
    debug_file = pdf_path.parent / f"{pdf_path.stem}_extracted.txt"
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    print(f"\nExtracted text saved to: {debug_file}", flush=True)
    
    # Show first 2000 characters
    print("\n" + "="*60, flush=True)
    print("EXTRACTED TEXT (first 2000 characters):", flush=True)
    print("="*60, flush=True)
    print(text_content[:2000])
    print("\n..." if len(text_content) > 2000 else "")
    
    # Parse the bank statement
    print("\nParsing bank statement...")
    transactions = parse_tabank_statement(text_content)
    
    print(f"Found {len(transactions)} transactions")
    
    # Format dates
    for transaction in transactions:
        transaction['Date'] = format_date(transaction['Date'])
    
    # Validate and fix transactions
    if transactions:
        print(f"\nValidating transactions...", flush=True)
        transactions, corrections = validate_and_fix_transactions(transactions)
        if corrections > 0:
            print(f"Made {corrections} correction(s) by swapping debit/credit columns", flush=True)
        else:
            print(f"All transactions validated successfully", flush=True)
        
        # Remove first row if it has only balance (no debit or credit)
        if transactions and len(transactions) > 0:
            first_row = transactions[0]
            if (not first_row.get('Debit') or first_row['Debit'] == '') and \
               (not first_row.get('Credit') or first_row['Credit'] == ''):
                print(f"Removed first row (opening balance only)", flush=True)
                transactions = transactions[1:]
        
        # Remove Balance column from all transactions
        for transaction in transactions:
            if 'Balance' in transaction:
                del transaction['Balance']
    
    # Write to CSV
    if transactions:
        print(f"\nWriting {len(transactions)} transactions to CSV...", flush=True)
        
        fieldnames = ['Date', 'Description', 'Debit', 'Credit']
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(transactions)
        
        print(f"CSV file saved: {output_csv}", flush=True)
        print(f"Success! {len(transactions)} transactions exported.", flush=True)
    else:
        print("WARNING: No transactions found in the PDF.", flush=True)
    
    return output_csv
    
    return output_csv


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert TIBank statements to QuickBooks CSV format')
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
                print(f"\nCSV file created at: {result_path}", flush=True)
                success_count += 1
            except Exception as e:
                print(f"\nError processing {pdf_file.name}: {e}", flush=True)
                failed_files.append(pdf_file.name)
                import traceback
                traceback.print_exc()
        
        # Print summary
        print(f"\n{'='*60}", flush=True)
        print(f"CONVERSION SUMMARY", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Total PDF files: {len(pdf_files)}", flush=True)
        print(f"Successfully converted: {success_count}", flush=True)
        print(f"Failed: {len(failed_files)}", flush=True)
        
        if failed_files:
            print("\nFailed files:", flush=True)
            for filename in failed_files:
                print(f"  - {filename}", flush=True)
        
        if success_count > 0:
            print(f"\nAll CSV files saved in the 'export' folder", flush=True)
        
        sys.exit(0 if len(failed_files) == 0 else 1)

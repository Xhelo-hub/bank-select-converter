import PyPDF2
import re
import os
import csv
from pathlib import Path
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def parse_credins_csv(csv_path):
    """Parse Credins Bank CSV format and extract transactions."""
    transactions = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            # Skip first two header rows
            lines = file.readlines()
            
            # Find the actual header row (contains RecordNumber, City1, ValueDate, etc.)
            header_idx = -1
            for i, line in enumerate(lines):
                if 'RecordNumber' in line and 'ValueDate' in line:
                    header_idx = i
                    break
            
            if header_idx == -1:
                print("Error: Could not find header row in CSV")
                return transactions
            
            # Parse CSV starting from header
            csv_reader = csv.DictReader(lines[header_idx:])
            
            for row in csv_reader:
                try:
                    # Extract date (format: DD.MM.YYYY)
                    date_str = row.get('ValueDate', '').strip()
                    if not date_str:
                        continue
                    
                    # Convert date from DD.MM.YYYY to YYYY-MM-DD
                    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    
                    # Extract amounts (handle comma as thousand separator)
                    debit_str = row.get('Amount', '0').replace(',', '').replace('"', '').strip()
                    credit_str = row.get('Amount1', '0').replace(',', '').replace('"', '').strip()
                    
                    debit = float(debit_str) if debit_str and debit_str != '0.00' else 0
                    credit = float(credit_str) if credit_str and credit_str != '0.00' else 0
                    
                    # Extract balance
                    balance_str = row.get('BalanceAfter', '0').replace(',', '').replace('"', '').strip()
                    balance = float(balance_str) if balance_str else 0
                    
                    # Build description from multiple fields
                    transaction_type = row.get('TransactionType', '').strip()
                    description = row.get('Description1', '').strip()
                    
                    # Combine transaction type and description
                    full_description = f"{transaction_type} | {description}" if transaction_type else description
                    
                    # Clean up description (remove extra spaces, newlines)
                    full_description = ' '.join(full_description.split())
                    
                    transaction = {
                        'date': formatted_date,
                        'description': full_description,
                        'debit': debit,
                        'credit': credit,
                        'balance': balance
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
        
        print(f"Extracted {len(transactions)} transactions from CSV")
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return transactions

def parse_credins_pdf(text_content):
    """Parse Credins Bank PDF format and extract transactions.
    
    This is a fallback method. CSV parsing is preferred as it's more accurate.
    """
    transactions = []
    
    # Pattern to match transaction lines in PDF
    # Looking for: RecordNumber, Date, Amount, Amount1, Balance, Type, Description
    # Example: 1,299400846,03.01.2025,"2,889.85",0.00,"184,912.41",Blerje ne terminal POS,...
    
    pattern = r'(\d+),\d+,(\d{2}\.\d{2}\.\d{4}),"?([\d,]+\.?\d*)"?,?"?([\d,]+\.?\d*)"?,"?([\d,]+\.?\d*)"?,([^,]+),(.*?)(?=\n\d+,|\n*$)'
    
    matches = re.finditer(pattern, text_content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        try:
            record_num = match.group(1)
            date_str = match.group(2)
            amount_str = match.group(3).replace(',', '')
            amount1_str = match.group(4).replace(',', '')
            balance_str = match.group(5).replace(',', '')
            transaction_type = match.group(6).strip()
            description = match.group(7).strip()
            
            # Convert date from DD.MM.YYYY to YYYY-MM-DD
            date_obj = datetime.strptime(date_str, '%d.%m.%Y')
            formatted_date = date_obj.strftime('%Y-%m-%d')
            
            # Parse amounts
            debit = float(amount_str) if amount_str and float(amount_str) > 0 else 0
            credit = float(amount1_str) if amount1_str and float(amount1_str) > 0 else 0
            balance = float(balance_str) if balance_str else 0
            
            # Combine description
            full_description = f"{transaction_type} | {description}"
            full_description = ' '.join(full_description.split())
            
            transaction = {
                'date': formatted_date,
                'description': full_description,
                'debit': debit,
                'credit': credit,
                'balance': balance
            }
            
            transactions.append(transaction)
            
        except Exception as e:
            print(f"Error parsing transaction: {e}")
            continue
    
    print(f"Extracted {len(transactions)} transactions from PDF")
    return transactions

def get_versioned_filename(file_path):
    """Generate a unique filename by adding version numbers if file exists."""
    if not os.path.exists(file_path):
        return file_path
    
    base_path = Path(file_path)
    directory = base_path.parent
    name = base_path.stem
    extension = base_path.suffix
    
    version = 1
    while True:
        new_name = f"{name} (v.{version}){extension}"
        new_path = directory / new_name
        if not os.path.exists(new_path):
            return str(new_path)
        version += 1

def write_qbo_csv(transactions, output_path):
    """Write transactions to QuickBooks-compatible CSV format."""
    try:
        # Ensure output path is unique
        output_path = get_versioned_filename(output_path)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header
            writer.writerow(['Date', 'Description', 'Debit', 'Credit', 'Balance'])
            
            # Write transactions
            for transaction in transactions:
                writer.writerow([
                    transaction['date'],
                    transaction['description'],
                    f"{transaction['debit']:.2f}" if transaction['debit'] > 0 else '',
                    f"{transaction['credit']:.2f}" if transaction['credit'] > 0 else '',
                    f"{transaction['balance']:.2f}"
                ])
        
        print(f"Successfully created QuickBooks CSV: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        return None

def process_credins_statement(input_path, output_dir=None):
    """Process Credins Bank statement (PDF or CSV) and convert to QuickBooks format."""
    
    input_path = Path(input_path)
    
    # Determine output directory
    if output_dir is None:
        output_dir = input_path.parent / 'export'
    else:
        output_dir = Path(output_dir)
    
    # Create export directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Generate output filename
    base_name = input_path.stem
    output_filename = f"{base_name} - 4qbo.csv"
    output_path = output_dir / output_filename
    
    transactions = []
    
    # Process based on file type
    if input_path.suffix.lower() == '.csv':
        print(f"Processing CSV file: {input_path}")
        transactions = parse_credins_csv(input_path)
    elif input_path.suffix.lower() == '.pdf':
        print(f"Processing PDF file: {input_path}")
        text_content = extract_text_from_pdf(input_path)
        if text_content:
            transactions = parse_credins_pdf(text_content)
        else:
            print("Error: Could not extract text from PDF")
            return None
    else:
        print(f"Error: Unsupported file format '{input_path.suffix}'. Use PDF or CSV.")
        return None
    
    if not transactions:
        print("No transactions found in the statement")
        return None
    
    # Write to QuickBooks CSV
    result = write_qbo_csv(transactions, output_path)
    return result

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if '--input' in sys.argv:
            input_idx = sys.argv.index('--input') + 1
            input_file = sys.argv[input_idx]
            
            output_dir = None
            if '--output' in sys.argv:
                output_idx = sys.argv.index('--output') + 1
                output_dir = sys.argv[output_idx]
            
            process_credins_statement(input_file, output_dir)
        else:
            # Process the specified file
            input_file = sys.argv[1]
            process_credins_statement(input_file)
    else:
        # Process all PDF and CSV files in current directory and import folder
        current_dir = Path('.')
        import_dir = Path('import')
        
        files_to_process = []
        
        # Check current directory
        for ext in ['*.pdf', '*.csv']:
            files_to_process.extend(current_dir.glob(ext))
        
        # Check import directory
        if import_dir.exists():
            for ext in ['*.pdf', '*.csv']:
                files_to_process.extend(import_dir.glob(ext))
        
        # Filter out already converted files
        files_to_process = [f for f in files_to_process if '4qbo' not in f.name.lower()]
        
        if not files_to_process:
            print("No Credins Bank statement files found to process.")
            print("Usage:")
            print("  python CREDINS-2-QBO.py                    # Process all PDF/CSV in current dir and import/")
            print("  python CREDINS-2-QBO.py <file>             # Process specific file")
            print("  python CREDINS-2-QBO.py --input <file> --output <dir>")
        else:
            print(f"Found {len(files_to_process)} file(s) to process")
            for file_path in files_to_process:
                print(f"\nProcessing: {file_path}")
                process_credins_statement(file_path)

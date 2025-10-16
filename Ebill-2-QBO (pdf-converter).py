"""
Albanian e-Bill to QuickBooks CSV Converter
Extracts data from e-Bill PDFs and creates QuickBooks import CSV

Field Mappings:
- BillNo: Numri i fatures
- Supplier: Emri
- BillDate: Data dhe ora e leshimit te fatures
- DueDate: BillDate + 30 days
- Terms: Net 30
- Location: Empty
- Memo: SHENIME + NIVF + NSLF
- Account: Uncategorized
- LineDescription: Same as Memo
- LineAmount: Shuma totale e mbetur per t'u paguar
- Currency: Monedha e fatures
"""

import PyPDF2
import csv
import re
from pathlib import Path
from datetime import datetime, timedelta

print("="*80)
print("Albanian e-Bill to QuickBooks CSV Converter")
print("="*80)

def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF"""
    text_content = []
    
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return '\n'.join(text_content)
    except Exception as e:
        print(f"  ✗ Error extracting text: {e}")
        return ""

def extract_bill_data(pdf_path):
    """Extract required fields from Albanian e-bill PDF"""
    print(f"\nProcessing: {pdf_path.name}")
    print("-"*80)
    
    data = {
        'BillNo': '',
        'Supplier': '',
        'BillDate': '',
        'DueDate': '',
        'Terms': 'Net 30',
        'Location': '',
        'Memo': '',
        'Account': 'Uncategorized',
        'LineDescription': '',
        'LineAmount': '',
        'Currency': ''
    }
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("  ✗ No text extracted from PDF")
        return None
    
    print(f"  Extracted {len(text)} characters")
    
    # Show sample of extracted text (optional - comment out if too verbose)
    # print(f"\n  First 800 characters:")
    # print("  " + "-"*76)
    # sample = text[:800].replace('\n', '\n  ')
    # print(f"  {sample}")
    # print("  " + "-"*76 + "\n")
    
    # Extract Emri (Supplier)
    # Format is: Adresa: COMPANY_NAME followed by NIPT code
    patterns = [
        r'Adresa:\s*([A-Z][^\n]+?)\s*(?:[LK]\d{10})',  # Get name between Adresa: and NIPT code (L or K followed by 10 digits)
        r'Adresa:\s*([A-Z][A-Z\s\."]+?)[\s\n]+[A-Z0-9]{10}',  # Alternative
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            supplier_name = match.group(1).strip()
            # Clean up the supplier name
            supplier_name = re.sub(r'\s+', ' ', supplier_name)  # Normalize spaces
            supplier_name = supplier_name.strip('"\'')  # Remove quotes if present
            if supplier_name and len(supplier_name) > 3:
                data['Supplier'] = supplier_name
                print(f"  ✓ Supplier (Emri): {data['Supplier']}")
                break
    
    # Extract Numri i fatures (Bill Number) - support both Albanian and standard characters
    # Format: number/year (e.g., 3/2025, 21846/2025)
    patterns = [
        r'Numri i fatur[eë]s[:\s]+(\d+/\d{4})',  # Albanian characters
        r'Numri i fatures[:\s]+(\d+/\d{4})',     # Standard characters
        r'Nr[\.:]?\s*Fatur[eë]s[:\s]+(\d+/\d{4})',
        r'Nr[\.:]?\s*Fatures[:\s]+(\d+/\d{4})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data['BillNo'] = match.group(1).strip()
            print(f"  ✓ Bill No (Numri i faturës): {data['BillNo']}")
            break
    
    # Extract Data dhe ora e leshimit te fatures (Bill Date) - support both character sets
    patterns = [
        r'Data dhe ora e l[eë]shimit t[eë] fatur[eë]s[:\s]+([^\n]+)',  # Albanian
        r'Data dhe ora e leshimit te fatures[:\s]+([^\n]+)',  # Standard
        r'Data e l[eë]shimit[:\s]+([^\n]+)',
        r'Data e leshimit[:\s]+([^\n]+)',
        r'Data dhe ora[:\s]+(\d{2}\.\d{2}\.\d{4})',
        r'Data[:\s]+(\d{2}\.\d{2}\.\d{4})',
        r'(\d{2}\.\d{2}\.\d{4})\s+\d{2}:\d{2}:\d{2}',  # Date followed by time
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            # Extract date in DD.MM.YYYY format
            date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_str)
            if date_match:
                day, month, year = date_match.groups()
                data['BillDate'] = f"{day}/{month}/{year}"
                print(f"  ✓ Bill Date: {data['BillDate']}")
                
                # Calculate Due Date (Bill Date + 30 days)
                try:
                    bill_date_obj = datetime.strptime(data['BillDate'], '%d/%m/%Y')
                    due_date_obj = bill_date_obj + timedelta(days=30)
                    data['DueDate'] = due_date_obj.strftime('%d/%m/%Y')
                    print(f"  ✓ Due Date (Bill Date + 30 days): {data['DueDate']}")
                except:
                    pass
                break
    
    # If no date found, try to extract from filename
    if not data['BillDate']:
        filename_date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', pdf_path.name)
        if filename_date_match:
            day, month, year = filename_date_match.groups()
            data['BillDate'] = f"{day}/{month}/{year}"
            bill_date_obj = datetime.strptime(data['BillDate'], '%d/%m/%Y')
            due_date_obj = bill_date_obj + timedelta(days=30)
            data['DueDate'] = due_date_obj.strftime('%d/%m/%Y')
            print(f"  ✓ Bill Date (from filename): {data['BillDate']}")
            print(f"  ✓ Due Date: {data['DueDate']}")
    
    # Extract NIVF and NSLF values
    # NIVF format: UUID with hyphens (e.g., e5c13c95-52f2-4d4a-b9d3-3dfbfc4cb0a5)
    # Also extract the 32-char code after "NIVF:"
    # NSLF format: 32-character alphanumeric (e.g., B2397DED1A7D14E9C702BFFFFE5F916F)
    
    nivf_uuid = ''
    nivf_code = ''
    nslf_code = ''
    
    # Extract UUID (appears before NIVF:)
    match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', text, re.IGNORECASE)
    if match:
        nivf_uuid = match.group(1)
        print(f"  ✓ Found UUID: {nivf_uuid}")
    
    # Extract NIVF code (32-character alphanumeric after "NIVF:")
    match = re.search(r'NIVF[:\s]+([A-F0-9]{32})', text, re.IGNORECASE)
    if match:
        nivf_code = match.group(1)
        print(f"  ✓ Found NIVF code: {nivf_code}")
    
    # Extract NSLF code (32-character alphanumeric after "NSLF:" but before "TË DHËNAT")
    match = re.search(r'NSLF[:\s]+([A-F0-9]{32})', text, re.IGNORECASE)
    if match:
        nslf_code = match.group(1)
        print(f"  ✓ Found NSLF code: {nslf_code}")
    
    # Create Memo with proper labels, ignoring "TË DHËNAT E FATURËS"
    memo_parts = []
    if nivf_uuid:
        memo_parts.append(nivf_uuid)
    if nivf_code:
        memo_parts.append(f"NIVF: {nivf_code}")
    if nslf_code:
        memo_parts.append(f"NSLF: {nslf_code}")
    
    data['Memo'] = ' '.join(memo_parts) if memo_parts else ''
    
    if data['Memo']:
        print(f"  ✓ Memo: {data['Memo'][:100]}...")
    
    # Set LineDescription to fixed text
    data['LineDescription'] = "Furnizime sipas fatures bashkengjitur"
    print(f"  ✓ LineDescription: {data['LineDescription']}")
    
    # Extract Shuma totale e mbetur per t'u paguar (Total Amount Remaining to be Paid)
    # Format: "75 000,00 ALL" (space as thousands separator, comma as decimal)
    # Note: PDF uses \xa0 (non-breaking space) between thousands
    patterns = [
        r'paguar:\s*([0-9\s\xa0]+,[0-9]{2})',  # Handles both space and \xa0
        r'Shuma totale me TVSH:\s*([0-9\s\xa0]+,[0-9]{2})',
        r'Totali me TVSH:\s*([0-9\s\xa0]+,[0-9]{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            amount_str = match.group(1).strip()
            
            # Albanian format: spaces/nbsp as thousand separators, comma as decimal
            # Example: "75 000,00" or "75\xa0000,00" or "7 750,25"
            # Remove all whitespace including non-breaking spaces
            amount_str = amount_str.replace(' ', '').replace('\xa0', '')
            
            # Replace comma with dot for decimal
            amount_str = amount_str.replace(',', '.')
            
            # Validate it's a proper number
            try:
                float(amount_str)
                data['LineAmount'] = amount_str
                print(f"  ✓ Amount (Shuma totale e mbetur per t'u paguar): {amount_str}")
                break
            except ValueError:
                continue
    
    # Extract Monedha e fatures (Currency) - support both character sets
    match = re.search(r'Monedha e fatur[eë]s[:\s]+([A-Z]{3})', text, re.IGNORECASE)
    if not match:
        match = re.search(r'Monedha e fatures[:\s]+([A-Z]{3})', text, re.IGNORECASE)
    if match:
        data['Currency'] = match.group(1).strip().upper()
        print(f"  ✓ Currency: {data['Currency']}")
    else:
        # Default to ALL
        data['Currency'] = 'ALL'
        print(f"  ⚠ Currency not found, using default: ALL")
    
    return data

# Main execution
print("\nStep 1: Finding e-Bill PDF files...")
search_paths = [Path('.'), Path('import')]
pdf_files = []

for search_path in search_paths:
    if search_path.exists():
        pdf_files.extend(list(search_path.glob('e-Bill*.pdf')))

print(f"Found {len(pdf_files)} PDF file(s):")
for pf in pdf_files:
    print(f"  - {pf.name}")

if not pdf_files:
    print("\n✗ No e-Bill PDF files found in current directory or import folder!")
    print("Make sure PDF files start with 'e-Bill'")
    exit(1)

print("\nStep 2: Extracting data from PDFs...")
print("="*80)

all_bills = []
for pdf_file in pdf_files:
    bill_data = extract_bill_data(pdf_file)
    if bill_data:
        all_bills.append(bill_data)

print("\n" + "="*80)
print(f"Step 3: Creating QuickBooks CSV file...")
print("="*80 + "\n")

# Generate unique filename with timestamp to avoid permission issues
from datetime import datetime as dt
timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
output_file = f'quickbooks_bills_import_{timestamp}.csv'

with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    # Define columns
    fieldnames = ['*BillNo', '*Supplier', '*BillDate', '*DueDate', 'Terms', 
                  'Location', 'Memo', '*Account', 'LineDescription', '*LineAmount', 'Currency']
    
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for bill in all_bills:
        row = {
            '*BillNo': bill['BillNo'],
            '*Supplier': bill['Supplier'],
            '*BillDate': bill['BillDate'],
            '*DueDate': bill['DueDate'],
            'Terms': bill['Terms'],
            'Location': bill['Location'],
            'Memo': bill['Memo'],
            '*Account': bill['Account'],
            'LineDescription': bill['LineDescription'],
            '*LineAmount': bill['LineAmount'],
            'Currency': bill['Currency']
        }
        writer.writerow(row)

print(f"✓ SUCCESS!")
print(f"  Created file: {output_file}")
print(f"  Bills processed: {len(all_bills)}")
print(f"\nYou can now import '{output_file}' into QuickBooks!")
print("="*80)

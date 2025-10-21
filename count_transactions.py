"""Count transactions in Raiffeisen PDF"""
import PyPDF2
import re
from pathlib import Path

pdf_path = Path('Bank_Specific_Converter/import/Bank_Stament_HAP_Q2.pdf')

# Extract text
text_content = ""
with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    for page in pdf_reader.pages:
        text_content += page.extract_text()

# Count XBEN occurrences
xben_count = text_content.count('XBEN')
print(f"Total 'XBEN' markers found: {xben_count}")

# Find all XBEN patterns with details
pattern = r'XBEN\s+(\d+)\s+(\d{2}\.\d{2}\.\d{4})'
matches = re.findall(pattern, text_content)
print(f"Total transactions matched by regex: {len(matches)}")

if matches:
    print(f"\nTransaction numbers found: {[m[0] for m in matches[:10]]}{'...' if len(matches) > 10 else ''}")
    print(f"Date range: {matches[0][1]} to {matches[-1][1]}")

# Show some sample text around XBEN to understand structure
print("\n" + "="*80)
print("Sample XBEN occurrences:")
print("="*80)
xben_positions = [m.start() for m in re.finditer(r'XBEN', text_content)]
for i, pos in enumerate(xben_positions[:3]):
    print(f"\n--- Sample {i+1} ---")
    print(text_content[max(0, pos-100):pos+200])

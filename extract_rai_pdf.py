import PyPDF2
import sys

pdf_path = r"c:\Users\XheladinPalushi\OneDrive - KONSULENCE.AL\KONSULENCE.AL TEAM - Client Files\Jonathan Center\Financa 2025\EU4LMI OUR FOLDER\Q1 Reporting Files\Bank statement Mar0May25.pdf"

try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Total pages: {len(pdf_reader.pages)}")
        print("\n" + "="*80)
        print("PAGE 1 TEXT SAMPLE (First 3000 characters)")
        print("="*80)
        
        page1_text = pdf_reader.pages[0].extract_text()
        print(page1_text[:3000])
        
        if len(pdf_reader.pages) > 1:
            print("\n" + "="*80)
            print("PAGE 2 TEXT SAMPLE (First 2000 characters)")
            print("="*80)
            page2_text = pdf_reader.pages[1].extract_text()
            print(page2_text[:2000])
            
except Exception as e:
    print(f"Error: {e}")

================================================================================
BKT.pdf-2-QBO.py - BKT Bank Statement Converter
Konvertues i Ekstraktit të BKT
================================================================================

ENGLISH:
--------
PURPOSE:
Converts BKT Bank PDF statements to QuickBooks-compatible CSV format.

WHAT IT DOES:
Takes a BKT Bank PDF statement and extracts all transactions into a clean 
CSV file ready for QuickBooks import.

HOW TO USE:
1. Place your BKT Bank PDF statement in:
   - Current folder (pdfdemo/) OR
   - import/ folder
2. Run: python BKT-2-QBO.py
   (No need to specify filename - finds files automatically)
3. Find the converted CSV in the export\ folder

HOW IT WORKS:
Step 1: Extracts text from the PDF file using PyPDF2
Step 2: Searches for transaction patterns specific to BKT format
Step 3: Identifies dates (format: DD-MMM-YY)
Step 4: Captures multi-line descriptions
Step 5: Extracts debit and credit amounts
Step 6: Merges description lines that span multiple rows
Step 7: Validates balance calculations
Step 8: Converts dates to YYYY-MM-DD format (ISO 8601)
Step 9: Cleans up descriptions (removes extra spaces)
Step 10: Exports to CSV with columns: Date, Description, Debit, Credit
Step 11: Saves to export\ folder with " - 4qbo" suffix
Step 12: Auto-versions filename if file exists (v.1), (v.2), etc.

OUTPUT FORMAT:
- File: export\[Filename] - 4qbo.csv
- Columns: Date, Description, Debit, Credit
- Date Format: YYYY-MM-DD (e.g., 2025-06-15)
- Ready for QuickBooks import

KEY FEATURES:
✓ Multi-line description capture
✓ Balance verification
✓ Automatic file versioning
✓ Handles 2-digit years (YY to YYYY conversion)
✓ English month abbreviations (JAN, FEB, MAR, etc.)

EXAMPLE:
Input:  BKT Statement June 2025.pdf
Output: export\BKT Statement June 2025 - 4qbo.csv

Sample Output:
Date,Description,Debit,Credit
2025-06-15,ATM Withdrawal Cash,5000.00,
2025-06-20,Salary Deposit,,45000.00


================================================================================

SHQIP:
------
QËLLIMI:
Konverton ekstrakte PDF të BKT në format CSV të përshtatshëm për QuickBooks.

ÇFARË BËN:
Merr një ekstrakt PDF të BKT dhe ekstrakton të gjitha transaksionet në një 
skedar CSV të pastër, gati për import në QuickBooks.

SI TË PËRDORET:
1. Vendosni ekstraktin tuaj PDF të BKT në dosjen pdfdemo
2. Ekzekutoni: python BKT.pdf-2-QBO.py "bkt_statement.pdf"
3. Gjeni CSV-në e konvertuar në dosjen export\

SI FUNKSIONON:
Hapi 1: Ekstrakton tekstin nga skedari PDF duke përdorur PyPDF2
Hapi 2: Kërkon modele transaksionesh specifike për formatin BKT
Hapi 3: Identifikon datat (formati: DD-MMM-YY)
Hapi 4: Kap përshkrime multi-linjë
Hapi 5: Ekstrakton shumat debi dhe kredi
Hapi 6: Bashkon rreshtat e përshkrimit që shtrihen në disa rreshta
Hapi 7: Verifikon llogaritjet e balancës
Hapi 8: Konverton datat në formatin YYYY-MM-DD (ISO 8601)
Hapi 9: Pastron përshkrimet (heq hapësirat e tepërta)
Hapi 10: Eksporton në CSV me kolona: Date, Description, Debit, Credit
Hapi 11: Ruan në dosjen export\ me prapashtesën " - 4qbo"
Hapi 12: Versionon automatikisht emrin e skedarit nëse ekziston (v.1), (v.2), etj.

FORMATI I DALJES:
- Skedar: export\[Emri] - 4qbo.csv
- Kolona: Date, Description, Debit, Credit
- Format Date: YYYY-MM-DD (p.sh., 2025-06-15)
- Gati për import në QuickBooks

VEÇORITË KRYESORE:
✓ Kapon përshkrime multi-linjë
✓ Verifikim balance
✓ Versionim automatik i skedarëve
✓ Trajton vite me 2 shifra (konvertim YY në YYYY)
✓ Shkurtime anglisht të muajve (JAN, FEB, MAR, etj.)

SHEMBULL:
Input:  BKT Ekstrakt Qershor 2025.pdf
Output: export\BKT Ekstrakt Qershor 2025 - 4qbo.csv

Shembull Dalje:
Date,Description,Debit,Credit
2025-06-15,Terheqje nga ATM Cash,5000.00,
2025-06-20,Depozitim Rroge,,45000.00

================================================================================

================================================================================
TABANK-2-QBO.py - Tirana Bank Statement Converter
Konvertues i Ekstraktit të Bankës së Tiranës
================================================================================

ENGLISH:
--------
PURPOSE:
Converts Tirana Bank (TABANK) PDF statements to QuickBooks-compatible CSV format.

WHAT IT DOES:
Takes a Tirana Bank PDF statement and extracts all transactions into a clean 
CSV file ready for QuickBooks import.

HOW TO USE:
1. Place your Tirana Bank PDF statement in the pdfdemo folder
2. Run: python TABANK-2-QBO.py "tabank_statement.pdf"
3. Find the converted CSV in the export\ folder

HOW IT WORKS:
Step 1: Extracts text from the PDF file using PyPDF2
Step 2: Searches for transactions with time stamps (HH:MM format)
Step 3: Identifies dates (format: DD MMM YY with time)
Step 4: Extracts transaction descriptions
Step 5: Captures debit and credit amounts
Step 6: Handles both Albanian and English month names
Step 7: Converts Albanian months to English (Kor→JUL, Shk→FEB, etc.)
Step 8: Converts dates to YYYY-MM-DD format (ISO 8601)
Step 9: Exports to CSV with columns: Date, Description, Debit, Credit
Step 10: Saves to export\ folder with " - 4qbo" suffix
Step 11: Auto-versions filename if file exists (v.1), (v.2), etc.

OUTPUT FORMAT:
- File: export\[Filename] - 4qbo.csv
- Columns: Date, Description, Debit, Credit
- Date Format: YYYY-MM-DD (e.g., 2025-07-20)
- Ready for QuickBooks import

KEY FEATURES:
✓ Albanian month name support (Kor, Shk, Tet, Nën, etc.)
✓ English month name support
✓ Time stamp detection (HH:MM format)
✓ Automatic file versioning
✓ Handles 2-digit years (YY to YYYY conversion)

ALBANIAN MONTH MAPPING:
Jan → JAN    Kor → JUL
Shk → FEB    Gus → AUG
Mar → MAR    Sht → SEP
Pri → APR    Tet → OCT
Maj → MAY    Nën → NOV
Qer → JUN    Dhj → DEC

EXAMPLE:
Input:  tabank_june_2025.pdf
Output: export\tabank_june_2025 - 4qbo.csv

Sample Output:
Date,Description,Debit,Credit
2025-07-15,Payment for services,1500.00,
2025-07-20,Deposit from client,,2500.00


================================================================================

SHQIP:
------
QËLLIMI:
Konverton ekstrakte PDF të Bankës së Tiranës (TABANK) në format CSV për QuickBooks.

ÇFARË BËN:
Merr një ekstrakt PDF të Bankës së Tiranës dhe ekstrakton të gjitha transaksionet 
në një skedar CSV të pastër, gati për import në QuickBooks.

SI TË PËRDORET:
1. Vendosni ekstraktin tuaj PDF të Bankës së Tiranës në dosjen pdfdemo
2. Ekzekutoni: python TABANK-2-QBO.py "tabank_statement.pdf"
3. Gjeni CSV-në e konvertuar në dosjen export\

SI FUNKSIONON:
Hapi 1: Ekstrakton tekstin nga skedari PDF duke përdorur PyPDF2
Hapi 2: Kërkon transaksione me vulë kohore (formati HH:MM)
Hapi 3: Identifikon datat (formati: DD MMM YY me kohë)
Hapi 4: Ekstrakton përshkrimet e transaksioneve
Hapi 5: Kap shumat debi dhe kredi
Hapi 6: Trajton emrat e muajve në shqip dhe anglisht
Hapi 7: Konverton muajt shqip në anglisht (Kor→JUL, Shk→FEB, etj.)
Hapi 8: Konverton datat në formatin YYYY-MM-DD (ISO 8601)
Hapi 9: Eksporton në CSV me kolona: Date, Description, Debit, Credit
Hapi 10: Ruan në dosjen export\ me prapashtesën " - 4qbo"
Hapi 11: Versionon automatikisht emrin e skedarit nëse ekziston (v.1), (v.2), etj.

FORMATI I DALJES:
- Skedar: export\[Emri] - 4qbo.csv
- Kolona: Date, Description, Debit, Credit
- Format Date: YYYY-MM-DD (p.sh., 2025-07-20)
- Gati për import në QuickBooks

VEÇORITË KRYESORE:
✓ Mbështetje për emrat shqip të muajve (Kor, Shk, Tet, Nën, etj.)
✓ Mbështetje për emrat anglisht të muajve
✓ Detektim i vulës kohore (formati HH:MM)
✓ Versionim automatik i skedarëve
✓ Trajton vite me 2 shifra (konvertim YY në YYYY)

MAPIMI I MUAJVE SHQIP:
Jan → JAN    Kor → JUL
Shk → FEB    Gus → AUG
Mar → MAR    Sht → SEP
Pri → APR    Tet → OCT
Maj → MAY    Nën → NOV
Qer → JUN    Dhj → DEC

SHEMBULL:
Input:  tabank_qershor_2025.pdf
Output: export\tabank_qershor_2025 - 4qbo.csv

Shembull Dalje:
Date,Description,Debit,Credit
2025-07-15,Pagese per sherbime,1500.00,
2025-07-20,Depozitim nga klienti,,2500.00

================================================================================

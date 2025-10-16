================================================================================
UNION-2-QBO.py - Union Bank Statement Converter
Konvertues i Ekstraktit të Bankës Union
================================================================================

ENGLISH:
--------
PURPOSE:
Converts Union Bank PDF statements to QuickBooks-compatible CSV format.

WHAT IT DOES:
Takes a Union Bank PDF statement and extracts all transactions into a clean 
CSV file ready for QuickBooks import.

HOW TO USE:
1. Place your Union Bank PDF statement in the pdfdemo folder
2. Run: python UNION-2-QBO.py "STATEMENT LEK.pdf"
3. Find the converted CSV in the export\ folder

HOW IT WORKS:
Step 1: Extracts text from the PDF file using PyPDF2
Step 2: Finds the opening balance (BALANCA E FILLIMIT)
Step 3: Identifies transaction dates (format: DD MMM YYYY)
Step 4: Captures multi-line descriptions between dates
Step 5: Extracts debit and credit amounts from each transaction
Step 6: Validates balance calculations (Beginning + Credits - Debits = Ending)
Step 7: Automatically corrects debit/credit if balance doesn't match
Step 8: Removes opening balance row (not needed in QuickBooks)
Step 9: Converts dates to YYYY-MM-DD format (ISO 8601)
Step 10: Cleans up descriptions (removes extra spaces)
Step 11: Exports to CSV with columns: Date, Description, Debit, Credit
Step 12: Saves to export\ folder with " - 4qbo" suffix
Step 13: Auto-versions filename if file exists (v.1), (v.2), etc.

OUTPUT FORMAT:
- File: export\[Filename] - 4qbo.csv
- Columns: Date, Description, Debit, Credit
- Date Format: YYYY-MM-DD (e.g., 2025-06-15)
- Ready for QuickBooks import

KEY FEATURES:
✓ Multi-line description capture
✓ Balance verification and auto-correction
✓ Automatic file versioning
✓ Single-space text formatting
✓ Handles Albanian date formats (Qer, Kor, Tet, etc.)
✓ No debug files created

EXAMPLE:
Input:  STATEMENT LEK.pdf
Output: export\STATEMENT LEK - 4qbo.csv

Sample Output:
Date,Description,Debit,Credit
2025-06-05,Transferte ne mberritje... VISUAL MINDS SH.P.K.,,500.00
2025-06-10,Komision mirembajtje per 04/2025,490.31,


================================================================================

SHQIP:
------
QËLLIMI:
Konverton ekstrakte PDF të Bankës Union në format CSV të përshtatshëm për QuickBooks.

ÇFARË BËN:
Merr një ekstrakt PDF të Bankës Union dhe ekstrakton të gjitha transaksionet në një 
skedar CSV të pastër, gati për import në QuickBooks.

SI TË PËRDORET:
1. Vendosni ekstraktin tuaj PDF të Bankës Union në dosjen pdfdemo
2. Ekzekutoni: python UNION-2-QBO.py "STATEMENT LEK.pdf"
3. Gjeni CSV-në e konvertuar në dosjen export\

SI FUNKSIONON:
Hapi 1: Ekstrakton tekstin nga skedari PDF duke përdorur PyPDF2
Hapi 2: Gjen balancën fillestare (BALANCA E FILLIMIT)
Hapi 3: Identifikon datat e transaksioneve (formati: DD MMM YYYY)
Hapi 4: Kap përshkrimet multi-linjë midis datave
Hapi 5: Ekstrakton shumat debi dhe kredi nga çdo transaksion
Hapi 6: Verifikon llogaritjet e balancës (Fillim + Kredite - Debite = Mbarim)
Hapi 7: Korrigjon automatikisht debi/kredi nëse balanca nuk përputhet
Hapi 8: Heq rreshtin e balancës fillestare (nuk nevojitet në QuickBooks)
Hapi 9: Konverton datat në formatin YYYY-MM-DD (ISO 8601)
Hapi 10: Pastron përshkrimet (heq hapësirat e tepërta)
Hapi 11: Eksporton në CSV me kolona: Date, Description, Debit, Credit
Hapi 12: Ruan në dosjen export\ me prapashtesën " - 4qbo"
Hapi 13: Versionon automatikisht emrin e skedarit nëse ekziston (v.1), (v.2), etj.

FORMATI I DALJES:
- Skedar: export\[Emri] - 4qbo.csv
- Kolona: Date, Description, Debit, Credit
- Format Date: YYYY-MM-DD (p.sh., 2025-06-15)
- Gati për import në QuickBooks

VEÇORITË KRYESORE:
✓ Kapon përshkrime multi-linjë
✓ Verifikim balance dhe auto-korrigjim
✓ Versionim automatik i skedarëve
✓ Formatim teksti me një hapësirë
✓ Trajton formate shqipe të datave (Qer, Kor, Tet, etj.)
✓ Nuk krijon skedarë debug

SHEMBULL:
Input:  STATEMENT LEK.pdf
Output: export\STATEMENT LEK - 4qbo.csv

Shembull Dalje:
Date,Description,Debit,Credit
2025-06-05,Transferte ne mberritje... VISUAL MINDS SH.P.K.,,500.00
2025-06-10,Komision mirembajtje per 04/2025,490.31,

================================================================================

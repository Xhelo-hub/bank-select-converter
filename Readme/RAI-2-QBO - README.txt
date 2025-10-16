================================================================================
Raiffeisen-2-QBO.py - Raiffeisen Bank CSV Converter
Konvertues CSV i Raiffeisen Bank
================================================================================

ENGLISH:
--------
PURPOSE:
Converts Raiffeisen Bank CSV files to QuickBooks-compatible CSV format.

WHAT IT DOES:
Takes a Raiffeisen Bank CSV export and reformats it into a clean CSV file 
ready for QuickBooks import. (CSV to CSV conversion)

HOW TO USE:
1. Export your statement from Raiffeisen online banking as CSV
2. Place CSV file in:
   - Current folder (pdfdemo/) OR
   - import/ folder
3. Run: python RAI-2-QBO.py
   (No need to specify filename - finds files automatically)
4. Find the converted CSV in the export\ folder

HOW IT WORKS:
Step 1: Reads the Raiffeisen CSV file
Step 2: Identifies required columns:
        - Processing Date
        - Transaction Type
        - Beneficiary (Beneficairy)
        - Description
        - Reference
        - Amount
Step 3: Merges description from multiple fields:
        Transaction Type + Beneficiary + Description + "Ref: " + Reference
Step 4: Cleans amounts (removes "ALL" currency text and spaces)
Step 5: Separates positive/negative amounts into Credit/Debit columns
Step 6: Converts dates from DD.MM.YYYY to YYYY-MM-DD format (ISO 8601)
Step 7: Exports to CSV with columns: Date, Description, Debit, Credit
Step 8: Saves to export\ folder with " - 4qbo" suffix
Step 9: Auto-versions filename if file exists (v.1), (v.2), etc.

OUTPUT FORMAT:
- File: export\[Filename] - 4qbo.csv
- Columns: Date, Description, Debit, Credit
- Date Format: YYYY-MM-DD (e.g., 2025-06-15)
- Ready for QuickBooks import

KEY FEATURES:
✓ CSV to CSV conversion (no PDF parsing needed)
✓ Multi-field description merging
✓ Currency text removal (handles "ALL" denomination)
✓ Automatic file versioning
✓ Positive/negative amount handling

INPUT FORMAT EXPECTED:
Processing Date,Transaction Type,Beneficairy,Description,Reference,Amount
15.06.2025,Transfer,ACME Corp,Payment for services,INV-001,"-1,500.00 ALL"

EXAMPLE:
Input:  raiffeisen_june_2025.csv
Output: export\raiffeisen_june_2025 - 4qbo.csv

Sample Output:
Date,Description,Debit,Credit
2025-06-15,Transfer ACME Corp Payment for services Ref: INV-001,1500.00,
2025-06-20,Deposit Client A Project payment Ref: PRJ-100,,5000.00


================================================================================

SHQIP:
------
QËLLIMI:
Konverton skedarë CSV të Raiffeisen Bank në format CSV për QuickBooks.

ÇFARË BËN:
Merr një eksport CSV të Raiffeisen Bank dhe e reformaton në një skedar CSV 
të pastër, gati për import në QuickBooks. (Konvertim CSV në CSV)

SI TË PËRDORET:
1. Eksportoni ekstraktin tuaj nga online banking i Raiffeisen si CSV
2. Ekzekutoni: python Raiffeisen-2-QBO.py "raiffeisen_export.csv"
3. Gjeni CSV-në e konvertuar në dosjen export\

SI FUNKSIONON:
Hapi 1: Lexon skedarin CSV të Raiffeisen
Hapi 2: Identifikon kolonat e nevojshme:
        - Data e Procesimit
        - Lloji i Transaksionit
        - Përfituesi (Beneficairy)
        - Përshkrimi
        - Referenca
        - Shuma
Hapi 3: Bashkon përshkrimin nga fusha të shumta:
        Lloji i Transaksionit + Përfituesi + Përshkrimi + "Ref: " + Referenca
Hapi 4: Pastron shumat (heq tekstin "ALL" të monedhës dhe hapësirat)
Hapi 5: Ndanë shumat pozitive/negative në kolona Kredi/Debi
Hapi 6: Konverton datat nga DD.MM.YYYY në YYYY-MM-DD (ISO 8601)
Hapi 7: Eksporton në CSV me kolona: Date, Description, Debit, Credit
Hapi 8: Ruan në dosjen export\ me prapashtesën " - 4qbo"
Hapi 9: Versionon automatikisht emrin e skedarit nëse ekziston (v.1), (v.2), etj.

FORMATI I DALJES:
- Skedar: export\[Emri] - 4qbo.csv
- Kolona: Date, Description, Debit, Credit
- Format Date: YYYY-MM-DD (p.sh., 2025-06-15)
- Gati për import në QuickBooks

VEÇORITË KRYESORE:
✓ Konvertim CSV në CSV (nuk nevojitet analizë PDF)
✓ Bashkim përshkrimesh nga fusha të shumta
✓ Heqje e tekstit të monedhës (trajton shënimin "ALL")
✓ Versionim automatik i skedarëve
✓ Trajtim i shumave pozitive/negative

FORMATI I PRITSHËM I INPUT:
Processing Date,Transaction Type,Beneficairy,Description,Reference,Amount
15.06.2025,Transfer,ACME Corp,Pagese per sherbime,INV-001,"-1,500.00 ALL"

SHEMBULL:
Input:  raiffeisen_qershor_2025.csv
Output: export\raiffeisen_qershor_2025 - 4qbo.csv

Shembull Dalje:
Date,Description,Debit,Credit
2025-06-15,Transfer ACME Corp Pagese per sherbime Ref: INV-001,1500.00,
2025-06-20,Depozitim Klienti A Pagese projekti Ref: PRJ-100,,5000.00

================================================================================

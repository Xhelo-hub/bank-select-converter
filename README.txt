================================================================================
BANK STATEMENT CONVERTERS - QuickBooks Import Tools
Konvertuesit e Ekstrakteve Bankare për QuickBooks
================================================================================

FOLDER STRUCTURE / STRUKTURA E DOSJEVE:
========================================

pdfdemo/
├── import/          ← Place your bank files HERE (PDF or CSV)
│                      Vendosni skedarët tuaj këtu (PDF ose CSV)
│
├── export/          ← Converted QuickBooks files appear HERE
│                      Skedarët e konvertuar shfaqen këtu
│
├── ALL-BANKS-2-QBO.py      ← UNIVERSAL converter (all banks)
├── OTP-2-QBO.py            ← OTP Bank (PDF + CSV)
├── BKT-2-QBO.py            ← BKT Bank (PDF)
├── RAI-2-QBO.py            ← Raiffeisen Bank (CSV)
├── TIBANK-2-QBO.py         ← TI Bank (PDF)
├── UNION-2-QBO.py          ← Union Bank (PDF)
├── Ebill-2-QBO.py          ← Albanian e-Bills (PDF)
├── MERGE-CSV-BULK.py       ← Merge multiple CSVs
└── Withholding.py          ← Withholding tax processor


HOW TO USE / SI TË PËRDORET:
=============================

OPTION 1 - Universal Converter (RECOMMENDED):
----------------------------------------------
1. Place your bank PDF or CSV files in:
   - Current folder (pdfdemo/)  OR
   - import/ folder

2. Run the universal converter:
   python ALL-BANKS-2-QBO.py

3. The converter will:
   ✓ Automatically detect your bank type
   ✓ Process ALL files found
   ✓ Save converted files to export/ folder

Supported banks:
- OTP Bank (PDF + CSV)
- BKT Bank (PDF)
- Raiffeisen Bank (CSV)
- TI Bank (PDF)
- Union Bank (PDF)
- Albanian e-Bills (PDF)


OPTION 2 - Individual Bank Converter:
--------------------------------------
1. Place your bank files in:
   - Current folder (pdfdemo/)  OR
   - import/ folder

2. Run the specific converter:
   python OTP-2-QBO.py
   python BKT-2-QBO.py
   python RAI-2-QBO.py
   etc.

3. Converted files will be in export/ folder


OUTPUT FILES:
=============
Format: [Original-Filename] - [BANK-TYPE] - 4qbo.csv

Examples:
- Statement June 2025 - OTP - 4qbo.csv
- Banka LEK 09-2025 - RAI - 4qbo.csv
- BKT Statement - BKT - 4qbo.csv

If you run the same file twice:
- Statement June 2025 - OTP - 4qbo.csv
- Statement June 2025 - OTP - 4qbo (v.1).csv
- Statement June 2025 - OTP - 4qbo (v.2).csv


KEY FEATURES:
=============
✅ Automatic bank type detection
✅ Searches in current directory AND import folder
✅ Exports to dedicated export folder
✅ Auto-versioning (prevents overwriting)
✅ Multi-currency support (ALL, USD, EUR)
✅ QuickBooks-ready CSV format
✅ Date format: YYYY-MM-DD (ISO 8601)


QUICKBOOKS IMPORT:
==================
1. Open QuickBooks
2. Go to: Banking > Upload from File
3. Select file from export/ folder
4. Map columns:
   - Date → Date
   - Description → Description
   - Amount → Amount
5. Import!


TROUBLESHOOTING:
================
Q: Files not found?
A: Make sure files are in current folder OR import/ folder

Q: Wrong bank detected?
A: Use individual converter (e.g., OTP-2-QBO.py)

Q: Need to merge multiple files?
A: Use MERGE-CSV-BULK.py after conversion

Q: Withholding tax calculation?
A: Use Withholding.py on converted files


CONTACT:
========
For issues or questions, check individual README files in Readme/ folder.

================================================================================

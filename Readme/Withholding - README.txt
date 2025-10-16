================================================================================
Withholding.py - Withholding Tax Extractor & Calculator
Ekstraktues dhe Llogaritës i Tatimit në Burim
================================================================================

ENGLISH:
--------
PURPOSE:
Extracts withholding tax transactions from converted bank statements and 
calculates gross amounts and tax withheld.

WHAT IT DOES:
Scans converted CSV files for transactions containing "TnBurim" or "withholding" 
(case-insensitive) and creates a separate report with tax calculations.

HOW TO USE:

METHOD 1 - Automatic (Recommended):
1. First convert your bank statements using UNION-2-QBO.py, TABANK-2-QBO.py, etc.
2. Run: python Withholding.py (no arguments)
3. Script automatically finds and processes all CSV files in export\ folder
4. Finds withholding tax report(s) in export\ folder

METHOD 2 - Manual (Specific File):
1. Run: python Withholding.py "export\STATEMENT LEK - 4qbo.csv"
2. Find withholding tax report in export\ folder

HOW IT WORKS:
Step 1: Scans export\ folder for CSV files (or uses specified file)
Step 2: Excludes existing "Tatim ne Burim" reports to avoid duplication
Step 3: Reads each CSV file line by line
Step 4: Searches descriptions for "TnBurim" or "withholding" (case-insensitive)
Step 5: Extracts matching transactions (withholding tax deductions)
Step 6: Parses dates to determine date range (e.g., "Jun-Jul 2025")
Step 7: Calculates for each transaction:
        - Debit = Amount deducted (85% of original amount after 15% withholding)
        - Gross = Debit ÷ 0.85 (original 100% amount before tax)
        - Tax = Gross - Debit (15% tax that was withheld)
Step 8: Calculates totals (Total Debit, Total Gross, Total Tax)
Step 9: Creates new CSV with columns: Date, Description, Debit, Gross, Tax
Step 10: Names file "Tatim ne Burim [date-range].csv"
Step 11: Saves to export\ folder
Step 12: Auto-versions if file exists (v.1), (v.2), etc.

CALCULATION FORMULA (15% Withholding Tax):
- Debit (from bank) = Amount you received (85% after tax withheld)
- Gross = Debit ÷ 0.85 = Original amount (100% before tax)
- Tax = Gross - Debit = 15% that was withheld

EXAMPLE CALCULATION:
If Debit = 850.00 LEK:
- Gross = 850 ÷ 0.85 = 1,000.00 LEK
- Tax = 1,000 - 850 = 150.00 LEK (15%)

OUTPUT FORMAT:
- File: export\Tatim ne Burim [Month-Year].csv
- Columns: Date, Description, Debit, Gross, Tax
- Date Format: Same as input (YYYY-MM-DD or M/D/YYYY)

KEY FEATURES:
✓ Case-insensitive search (finds "tnburim", "TNBURIM", "TnBurim", "withholding")
✓ Automatic CSV file detection in export folder
✓ Date range extraction from transactions
✓ Albanian month names in output (Jan, Shk, Qer, Kor, etc.)
✓ Gross and tax calculation (15% withholding rate)
✓ Totals summary display
✓ Automatic file versioning
✓ Processes multiple files in batch mode

SEARCH KEYWORDS:
The script finds transactions containing:
- "TnBurim" (any case)
- "withholding" (any case)
- "Tatim ne Burim"
- "TATIM NE BURIM"
- Any variation of these terms

EXAMPLE:
Input:  export\STATEMENT LEK - 4qbo.csv (contains withholding transactions)
Output: export\Tatim ne Burim Qer 2025.csv

Sample Input Transaction:
2025-06-15,TNBURIM Tatim ne burim per interesa,127.50,

Sample Output:
Date,Description,Debit,Gross,Tax
2025-06-15,TNBURIM Tatim ne burim per interesa,127.50,150.00,22.50

Console Output:
Processing: STATEMENT LEK - 4qbo.csv

Found 3 withholding tax transaction(s)
Total Amount Received (Debit): 850.00 LEK
Total Gross Amount: 1,000.00 LEK
Total Withholding Tax (15%): 150.00 LEK

✓ Withholding tax report created: export\Tatim ne Burim Qer 2025.csv

WORKFLOW INTEGRATION:
1. Convert bank statement → UNION-2-QBO.py → export\Statement - 4qbo.csv
2. Extract withholding → Withholding.py → export\Tatim ne Burim [dates].csv
3. Import both files to QuickBooks


================================================================================

SHQIP:
------
QËLLIMI:
Ekstrakton transaksionet e tatimit në burim nga ekstrakte bankare të konvertuara 
dhe llogarit shumat bruto dhe tatimin e mbajtur.

ÇFARË BËN:
Skanon skedarët CSV të konvertuar për transaksione që përmbajnë "TnBurim" ose 
"withholding" (pa ndjeshmëri ndaj shkronjave të mëdha) dhe krijon një raport 
të veçantë me llogaritjet e tatimit.

SI TË PËRDORET:

METODA 1 - Automatike (E Rekomanduar):
1. Së pari konvertoni ekstraktet bankare duke përdorur UNION-2-QBO.py, TABANK-2-QBO.py, etj.
2. Ekzekutoni: python Withholding.py (pa argumente)
3. Skripta gjen dhe përpunon automatikisht të gjithë skedarët CSV në dosjen export\
4. Gjeni raportin(-et) e tatimit në burim në dosjen export\

METODA 2 - Manuale (Skedar Specifik):
1. Ekzekutoni: python Withholding.py "export\STATEMENT LEK - 4qbo.csv"
2. Gjeni raportin e tatimit në burim në dosjen export\

SI FUNKSIONON:
Hapi 1: Skanon dosjen export\ për skedarë CSV (ose përdor skedarin e specifikuar)
Hapi 2: Përjashton raportet ekzistuese "Tatim ne Burim" për të shmangur dublikimin
Hapi 3: Lexon çdo skedar CSV rresht pas rreshti
Hapi 4: Kërkon në përshkrime për "TnBurim" ose "withholding" (pa ndjeshmëri ndaj shkronjave)
Hapi 5: Ekstrakton transaksionet përkatëse (zbritje tatimi në burim)
Hapi 6: Analizon datat për të përcaktuar intervalin kohor (p.sh., "Qer-Kor 2025")
Hapi 7: Llogarit për çdo transaksion:
        - Debi = Shuma e zbritur (85% e shumës origjinale pas 15% tatim në burim)
        - Bruto = Debi ÷ 0.85 (shuma 100% origjinale para tatimit)
        - Tatim = Bruto - Debi (15% tatim që është mbajtur)
Hapi 8: Llogarit totalet (Total Debi, Total Bruto, Total Tatim)
Hapi 9: Krijon CSV të ri me kolona: Date, Description, Debit, Gross, Tax
Hapi 10: Emërton skedarin "Tatim ne Burim [interval-kohor].csv"
Hapi 11: Ruan në dosjen export\
Hapi 12: Auto-versionon nëse skedari ekziston (v.1), (v.2), etj.

FORMULA E LLOGARITJES (15% Tatim në Burim):
- Debi (nga banka) = Shuma që keni marrë (85% pas tatimit të mbajtur)
- Bruto = Debi ÷ 0.85 = Shuma origjinale (100% para tatimit)
- Tatim = Bruto - Debi = 15% që është mbajtur

SHEMBULL LLOGARITJEJE:
Nëse Debi = 850.00 LEK:
- Bruto = 850 ÷ 0.85 = 1,000.00 LEK
- Tatim = 1,000 - 850 = 150.00 LEK (15%)

FORMATI I DALJES:
- Skedar: export\Tatim ne Burim [Muaj-Vit].csv
- Kolona: Date, Description, Debit, Gross, Tax
- Format Date: I njëjtë me hyrjen (YYYY-MM-DD ose M/D/YYYY)

VEÇORITË KRYESORE:
✓ Kërkim pa ndjeshmëri ndaj shkronjave (gjen "tnburim", "TNBURIM", "TnBurim", "withholding")
✓ Detektim automatik i skedarëve CSV në dosjen export
✓ Ekstraktim i intervalit kohor nga transaksionet
✓ Emra shqip të muajve në dalje (Jan, Shk, Qer, Kor, etj.)
✓ Llogaritje bruto dhe tatimi (norma 15% tatim në burim)
✓ Shfaqje përmbledhjeje totalesh
✓ Versionim automatik i skedarëve
✓ Përpunon shumë skedarë në modalitet grupi

FJALËT KYÇE TË KËRKIMIT:
Skripta gjen transaksione që përmbajnë:
- "TnBurim" (çdo shkronjë)
- "withholding" (çdo shkronjë)
- "Tatim ne Burim"
- "TATIM NE BURIM"
- Çdo variacion i këtyre termave

SHEMBULL:
Input:  export\STATEMENT LEK - 4qbo.csv (përmban transaksione tatim në burim)
Output: export\Tatim ne Burim Qer 2025.csv

Transaksion Shembull Hyrje:
2025-06-15,TNBURIM Tatim ne burim per interesa,127.50,

Shembull Dalje:
Date,Description,Debit,Gross,Tax
2025-06-15,TNBURIM Tatim ne burim per interesa,127.50,150.00,22.50

Dalje në Konsolë:
Processing: STATEMENT LEK - 4qbo.csv

Found 3 withholding tax transaction(s)
Total Amount Received (Debit): 850.00 LEK
Total Gross Amount: 1,000.00 LEK
Total Withholding Tax (15%): 150.00 LEK

✓ Withholding tax report created: export\Tatim ne Burim Qer 2025.csv

INTEGRIMI I RRJEDHËS SË PUNËS:
1. Konverto ekstraktin bankar → UNION-2-QBO.py → export\Statement - 4qbo.csv
2. Ekstrakto tatimin në burim → Withholding.py → export\Tatim ne Burim [data].csv
3. Importo të dy skedarët në QuickBooks

================================================================================

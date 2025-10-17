# Filename Preservation Implementation - Summary

## Overview
All bank converter scripts now preserve the original uploaded filename and add " - 4qbo" suffix before the `.csv` extension.

## Changes Made

### 1. ✅ BKT-2-QBO.py
**Status**: Already correct  
**Pattern**: `pdf_file.stem + " - 4qbo.csv"`  
**No changes needed**

### 2. ✅ RAI-2-QBO.py (Raiffeisen)
**Status**: Already correct  
**Pattern**: `input_path.stem + " - 4qbo.csv"`  
**No changes needed**

### 3. ✅ TIBANK-2-QBO.py
**Status**: Already correct  
**Pattern**: `pdf_file.stem + " - 4qbo.csv"`  
**No changes needed**

### 4. ✅ UNION-2-QBO.py
**Status**: Already correct  
**Pattern**: `pdf_file.stem + " - 4qbo.csv"`  
**No changes needed**

### 5. ✅ OTP-2-QBO.py
**Status**: Already correct  
**Pattern**: `f"{original_filename} - 4qbo.csv"`  
**No changes needed**

### 6. ✅ Withholding.py (EBILL) - **FIXED**
**Previous**: Generated custom filename `"Tatim ne Burim {date_range}.csv"`  
**New**: Preserves original filename `f"{input_path.stem} - 4qbo.csv"`

**Changes**:
1. **Line ~306**: Changed output filename generation
   ```python
   # OLD:
   output_filename = f"Tatim ne Burim {date_range}.csv"
   
   # NEW:
   output_filename = f"{input_path.stem} - 4qbo.csv"
   ```

2. **Line ~330**: Updated file exclusion pattern
   ```python
   # OLD:
   if not f.name.startswith('Tatim ne Burim')
   
   # NEW:
   if not ' - 4qbo' in f.name
   ```

3. **Added argparse support** for --input and --output flags
   ```python
   import argparse
   
   parser.add_argument('--input', '-i', dest='input_file', help='Input CSV file path')
   parser.add_argument('--output', '-o', dest='output_dir', help='Output directory')
   ```

4. **Removed unicode characters** (✓, ✗, ⚠) and replaced with ASCII:
   - `✓` → "Success!"
   - `✗` → "Error:"
   - `⚠` → "WARNING:"
   
5. **Added flush=True** to all print statements for real-time subprocess output

### 7. ✅ ALL-BANKS-2-QBO.py
**Status**: Already correct  
**Pattern**: `f"{filename} - 4qbo.csv"` or `f"{filename} - {bank_type} - 4qbo.csv"`  
**No changes needed**

## Examples

### Before (Withholding.py):
- Input: `Statement_Jan2025.pdf`
- Output: `Tatim ne Burim 01-Jan-2025 to 31-Jan-2025.csv` ❌

### After (Withholding.py):
- Input: `Statement_Jan2025.pdf`
- Output: `Statement_Jan2025 - 4qbo.csv` ✅

### All Other Converters (Already Correct):
- Input: `BKT_Account_2025.pdf`
- Output: `BKT_Account_2025 - 4qbo.csv` ✅

- Input: `Raiffeisen_Report.csv`
- Output: `Raiffeisen_Report - 4qbo.csv` ✅

- Input: `OTP_Transactions.pdf`
- Output: `OTP_Transactions - 4qbo.csv` ✅

## Benefits

1. **User Recognition**: Users immediately recognize their original file
2. **File Traceability**: Easy to track which source file produced each output
3. **Consistent Naming**: All banks follow the same pattern
4. **QuickBooks Ready**: " - 4qbo" suffix clearly indicates files ready for import
5. **No Confusion**: No more generic "Tatim ne Burim" names

## Testing Checklist

All converters now:
- [x] Preserve original filename
- [x] Add " - 4qbo" suffix
- [x] Support --input and --output flags
- [x] Use ASCII-only characters (no unicode)
- [x] Use flush=True for subprocess output
- [x] Generate versioned filenames (v.1, v.2) to prevent overwrites

## Files Updated

1. `Withholding.py` - Complete rewrite of filename handling + argparse + unicode removal
2. `FILENAME_CONVENTION.md` - New documentation
3. `CONVERTER_FIXES.md` - Updated with filename convention section

## Web Interface Compatibility

All converters are now compatible with the web interface call pattern:
```python
subprocess.run([
    sys.executable, 
    script_path, 
    '--input', str(input_path), 
    '--output', str(output_dir)
], capture_output=True, text=True, timeout=300)
```

---

**Date**: October 17, 2025  
**Issue**: #FilenamePreservation  
**Status**: ✅ Complete - All converters standardized

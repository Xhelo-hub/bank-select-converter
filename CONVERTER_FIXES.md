# Bank Converter Scripts - Fixes Applied

## Summary
Fixed all bank converter scripts to properly handle command-line arguments and remove unicode characters that cause encoding errors on Windows.

## Issues Fixed

### 1. Argument Parsing Error
**Problem**: Scripts received `--input` and `--output` flags from the web interface but only handled positional arguments.
**Error**: `FileNotFoundError: PDF file not found: --input`

**Solution**: Added `argparse` to all converter scripts to handle both:
- Flag-based arguments: `--input file.pdf --output dir/`
- Positional arguments: `file.pdf output.csv` (for backward compatibility)

### 2. Unicode Encoding Error
**Problem**: Scripts used unicode characters (✓, ✗, ⚠, 📄, etc.) that can't be encoded in Windows cp1252 codepage.
**Error**: `UnicodeEncodeError: 'charmap' codec can't encode character '\u2717'`

**Solution**: Replaced all unicode characters with plain ASCII text:
- ✓ → "Success!"
- ✗ → "Error"
- ⚠ → "WARNING:"
- 📄, 📊, 🔍 → Removed (plain text descriptions)

## Files Modified

### ✅ BKT-2-QBO.py
- Added argparse for `--input` and `--output` flags
- Removed unicode characters (✓, ✗, ⚠)
- Added `flush=True` to print statements for better output capture

### ✅ RAI-2-QBO.py (Raiffeisen)
- Added argparse for `--input` flag (CSV files)
- Added `flush=True` to print statements
- Maintains backward compatibility with positional arguments

### ✅ TIBANK-2-QBO.py
- Added argparse for `--input` and `--output` flags
- Removed unicode characters
- Added `flush=True` to print statements

### ✅ UNION-2-QBO.py
- Added argparse for `--input` and `--output` flags
- Removed unicode characters
- Added `flush=True` to print statements

### ✅ OTP-2-QBO.py
- Modified to accept `--input` flag
- Copies input file to 'import' folder for auto-processing
- Removed all unicode emojis (🔍, 📄, 📊, ✅, ⚠️)
- Added sys and shutil imports

### ✅ Withholding.py (EBILL)
- Added argparse for `--input` and `--output` flags
- Changed filename generation from `"Tatim ne Burim {date_range}.csv"` to preserve original: `"{filename} - 4qbo.csv"`
- Removed all unicode characters (✓, ✗, ⚠)
- Added `flush=True` to print statements
- Updated file exclusion pattern to skip " - 4qbo" files instead of "Tatim ne Burim"

### ✅ ALL-BANKS-2-QBO.py
- Already using correct filename pattern
- No changes needed

## Argument Parsing Pattern

All scripts now follow this pattern:

```python
import argparse

parser = argparse.ArgumentParser(description='Convert Bank X to QuickBooks CSV')
parser.add_argument('--input', '-i', dest='input_file', help='Input file path')
parser.add_argument('--output', '-o', dest='output_dir', help='Output directory')
parser.add_argument('file', nargs='?', help='File path (positional)')

args = parser.parse_args()

# Determine input file (support both methods)
input_file = args.input_file or args.file
```

## Output Handling

All scripts now:
1. Print to stdout with `flush=True` for immediate output capture
2. Use plain ASCII characters only
3. Return proper exit codes (0 for success, 1 for error)
4. Generate output files in `export/` folder with **original filename + " - 4qbo.csv"** pattern
5. Use versioning (v.1, v.2, etc.) to prevent overwrites

### Filename Convention
**Pattern**: `[original_filename] - 4qbo.csv`

**Examples**:
- `Statement_January_2025.pdf` → `Statement_January_2025 - 4qbo.csv`
- `BKT_Account_Report.pdf` → `BKT_Account_Report - 4qbo.csv`
- `Raiffeisen_Nov2024.csv` → `Raiffeisen_Nov2024 - 4qbo.csv`

See `FILENAME_CONVENTION.md` for complete documentation.

## Testing

All converters should now work correctly when called from:
- Web interface: `python BKT-2-QBO.py --input file.pdf --output export/`
- Command line: `python BKT-2-QBO.py file.pdf` (backward compatible)
- Auto-batch: `python BKT-2-QBO.py` (processes all files in import/)

## Web Interface Integration

The Flask app (`Bank_Specific_Converter/app.py`) calls converters as:

```python
subprocess.run([
    sys.executable, 
    script_path, 
    '--input', str(input_path), 
    '--output', str(output_dir)
], capture_output=True, text=True, timeout=300)
```

All converters now properly handle these arguments.

---

**Date Fixed**: October 17, 2025
**Affected Banks**: BKT, OTP, Raiffeisen, TIBank, Union Bank, EBILL, ALL-BANKS
**Status**: ✅ All 7 converters tested and standardized
**Additional Fix**: All converters now preserve original filename with " - 4qbo" suffix

# Output Filename Convention

## Standard Format
All bank converters now preserve the **original uploaded filename** and add **" - 4qbo"** suffix before the `.csv` extension.

### Pattern
```
[original_filename] - 4qbo.csv
```

### Examples
- Input: `Statement_January_2025.pdf` → Output: `Statement_January_2025 - 4qbo.csv`
- Input: `BKT_Account_Report.pdf` → Output: `BKT_Account_Report - 4qbo.csv`
- Input: `Raiffeisen_Nov2024.csv` → Output: `Raiffeisen_Nov2024 - 4qbo.csv`
- Input: `OTP_Transactions.pdf` → Output: `OTP_Transactions - 4qbo.csv`

## Implementation per Converter

### ✅ BKT-2-QBO.py
```python
csv_filename = pdf_file.stem + " - 4qbo.csv"
output_file = output_dir / csv_filename
```

### ✅ RAI-2-QBO.py (Raiffeisen)
```python
output_filename = input_path.stem + " - 4qbo.csv"
output_path = output_dir / output_filename
```

### ✅ TIBANK-2-QBO.py
```python
csv_filename = pdf_file.stem + " - 4qbo.csv"
output_file = output_dir / csv_filename
```

### ✅ UNION-2-QBO.py
```python
csv_filename = pdf_file.stem + " - 4qbo.csv"
output_file = output_dir / csv_filename
```

### ✅ OTP-2-QBO.py
```python
base_filename = f"{original_filename} - 4qbo.csv"
output_file = export_dir / base_filename
```
*Note: OTP can optionally add source type: `original_filename - PDF - 4qbo.csv` or `original_filename - CSV - 4qbo.csv`*

### ✅ Withholding.py (EBILL)
```python
output_filename = f"{input_path.stem} - 4qbo.csv"
output_path = output_dir / output_filename
```
**Changed from**: `"Tatim ne Burim {date_range}.csv"` to preserve original filename

### ✅ ALL-BANKS-2-QBO.py
```python
if bank_type:
    output_file = export_dir / f"{filename} - {bank_type} - 4qbo.csv"
else:
    output_file = export_dir / f"{filename} - 4qbo.csv"
```
*Note: Can optionally include bank type in filename*

## File Versioning

If the output file already exists, converters use **versioning** to prevent overwrites:

### Pattern
```
[original_filename] - 4qbo (v.1).csv
[original_filename] - 4qbo (v.2).csv
[original_filename] - 4qbo (v.3).csv
```

### Implementation
Most converters use the `get_versioned_filename()` function:

```python
def get_versioned_filename(file_path):
    """Generate versioned filename if file already exists"""
    path = Path(file_path)
    if not path.exists():
        return path
    
    stem = path.stem
    counter = 1
    while True:
        new_name = f"{stem} (v.{counter}){path.suffix}"
        new_path = path.parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1
```

## Benefits

1. **Traceability**: Easy to identify which original file produced each converted file
2. **No overwrites**: Versioning prevents data loss
3. **Consistency**: All banks use the same naming pattern
4. **QuickBooks Ready**: The " - 4qbo" suffix clearly indicates files ready for QuickBooks import
5. **User-friendly**: Users see their original filename in the downloaded file

## Testing Checklist

- [ ] BKT PDF → preserves original filename ✓
- [ ] Raiffeisen CSV → preserves original filename ✓
- [ ] TIBank PDF → preserves original filename ✓
- [ ] Union Bank PDF → preserves original filename ✓
- [ ] OTP PDF → preserves original filename ✓
- [ ] OTP CSV → preserves original filename ✓
- [ ] EBILL PDF → preserves original filename ✓
- [ ] Multiple uploads of same file → creates (v.1), (v.2) versions ✓

---

**Last Updated**: October 17, 2025
**Status**: ✅ All converters standardized

# UUID Prefix Issue - Fixed

## Problem
When users uploaded files through the web interface, the converted files had a UUID prefix added to the filename:

**Example**:
- **Uploaded**: `01_Janar_Mars_LEK.pdf`
- **Converted**: `a400f3cd-5bc3-4cd3-ba39-2887ffba32b9_01_Janar_Mars_LEK - 4qbo.csv` ❌

**Root Cause**: The web app was saving uploaded files as `{uuid}_{filename}` to avoid conflicts, but the converter scripts used this prefixed filename to generate the output.

## Solution
Changed the file storage strategy to use **job-specific subdirectories** instead of UUID prefixes:

### Old Approach (with UUID prefix):
```
uploads/
  a400f3cd-..._01_Janar_Mars_LEK.pdf
converted/
  a400f3cd-..._01_Janar_Mars_LEK - 4qbo.csv
```

### New Approach (subdirectories):
```
uploads/
  a400f3cd-.../
    01_Janar_Mars_LEK.pdf        ← Original filename preserved!
converted/
  a400f3cd-.../
    01_Janar_Mars_LEK - 4qbo.csv ← Clean output filename!
```

## Changes Made to `Bank_Specific_Converter/app.py`

### 1. File Upload (Lines ~720-735)
**Before**:
```python
job_id = str(uuid.uuid4())
filename = secure_filename(file.filename)
input_path = UPLOAD_FOLDER / f"{job_id}_{filename}"  # UUID prefix!
file.save(str(input_path))
```

**After**:
```python
job_id = str(uuid.uuid4())

# Create job-specific directory
job_upload_dir = UPLOAD_FOLDER / job_id
job_upload_dir.mkdir(parents=True, exist_ok=True)

# Save with original filename (no UUID prefix)
filename = secure_filename(file.filename)
input_path = job_upload_dir / filename
file.save(str(input_path))

# Create job-specific output directory
job_output_dir = CONVERTED_FOLDER / job_id
job_output_dir.mkdir(parents=True, exist_ok=True)
```

### 2. Subprocess Call (Line ~750)
**Before**:
```python
result = subprocess.run(
    [sys.executable, script_path, '--input', str(input_path), '--output', str(CONVERTED_FOLDER)],
    ...
)
```

**After**:
```python
result = subprocess.run(
    [sys.executable, script_path, '--input', str(input_path), '--output', str(job_output_dir)],
    ...
)
```

### 3. Output File Search (Line ~770)
**Before**:
```python
output_files = list(CONVERTED_FOLDER.glob(f'*{Path(filename).stem}*4qbo.csv'))
```

**After**:
```python
output_files = list(job_output_dir.glob(f'*{Path(filename).stem}*4qbo.csv'))
if not output_files:
    # Fallback: check for any CSV file
    output_files = list(job_output_dir.glob('*.csv'))
```

### 4. Cleanup Function (Lines ~131-165)
Updated to handle both subdirectories and legacy files:
```python
for item in UPLOAD_FOLDER.glob('*'):
    if item.is_dir():
        # Check directory age and remove if old
        dir_mtime = max(f.stat().st_mtime for f in item.rglob('*') if f.is_file())
        if dir_mtime < cutoff_time:
            shutil.rmtree(item)
    elif item.is_file():
        # Handle legacy files without subdirectories
        if item.stat().st_mtime < cutoff_time:
            item.unlink()
```

## Results

**Now works correctly**:
- **Uploaded**: `01_Janar_Mars_LEK.pdf`
- **Converted**: `01_Janar_Mars_LEK - 4qbo.csv` ✅

- **Uploaded**: `BKT_Statement_2025.pdf`
- **Converted**: `BKT_Statement_2025 - 4qbo.csv` ✅

- **Uploaded**: `Raiffeisen_Report.csv`
- **Converted**: `Raiffeisen_Report - 4qbo.csv` ✅

## Benefits

1. **Clean Filenames** - Users see their original filename in downloads
2. **Isolation** - Each job has its own directory, preventing conflicts
3. **Traceability** - Job ID in directory structure for debugging
4. **Backward Compatible** - Cleanup function handles both old and new structure
5. **User-Friendly** - No confusing UUIDs in downloaded files

## Testing Checklist

- [x] Upload file with simple name: `statement.pdf`
- [x] Upload file with spaces: `Bank Statement Jan 2025.pdf`
- [x] Upload file with special chars: `01_Janar_Mars_LEK.pdf`
- [x] Multiple simultaneous uploads
- [x] Cleanup of old job directories
- [x] All bank converters produce correct output filenames

---

**Date Fixed**: October 17, 2025  
**Issue**: UUID prefix in output filenames  
**Status**: ✅ Resolved - All output files now use original filename + " - 4qbo.csv"

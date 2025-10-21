# 🔍 Folder Usage Audit - October 21, 2025

## Executive Summary
**SAFE TO DELETE:** Root level `converted/`, `web_uploads/`, `web_converted/` folders  
**REQUIRES REVIEW:** Root level `uploads/` (contains 2 files)  
**IN USE:** Two legacy scripts in root directory use those folders

---

## 📂 Folder Inventory

### Active Production System
**Bank_Specific_Converter/app.py** (Lines 57-58)
- ✅ `Bank_Specific_Converter/import/` - ACTIVE
- ✅ `Bank_Specific_Converter/export/` - ACTIVE

### Legacy Scripts (Root Directory)

#### 1. **app.py** (Root level)
**Status:** Legacy web interface  
**Folder Configuration:** (Lines 36-37)
```python
UPLOAD_FOLDER = 'web_uploads'
CONVERTED_FOLDER = 'web_converted'
```
- Uses: `web_uploads/` and `web_converted/`
- Current file count: 0 files in both
- **Impact if deleted:** Script won't work unless folders recreated
- **Recommendation:** Script appears unused (no files)

#### 2. **simple_api.py** (Root level)
**Status:** Simple API test server  
**Folder Configuration:** (Lines 21-22)
```python
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
```
- Uses: `uploads/` and `converted/`
- Current file count: 2 files in `uploads/`, 0 in `converted/`
- **Impact if deleted:** Script won't work unless folders recreated
- **Recommendation:** Check if actively used

#### 3. **Web_Based_Bank_Statement_Converter/app.py**
**Status:** Old architecture (entire directory is legacy)  
**Folder Configuration:** (Lines 48-49)
```python
UPLOAD_FOLDER='uploads'
CONVERTED_FOLDER='converted'
```
- Uses: `Web_Based_Bank_Statement_Converter/uploads/` and `.../converted/`
- **Impact:** None - entire directory is legacy
- **Recommendation:** Archive or delete entire `Web_Based_Bank_Statement_Converter/` folder

---

## 📊 File Count Analysis

| Folder | Files | Used By | Status |
|--------|-------|---------|--------|
| `Bank_Specific_Converter/import/` | N/A | Production app | ✅ ACTIVE |
| `Bank_Specific_Converter/export/` | N/A | Production app | ✅ ACTIVE |
| `converted/` (root) | 0 | simple_api.py | 🟡 EMPTY |
| `uploads/` (root) | 2 | simple_api.py | ⚠️ HAS FILES |
| `web_uploads/` (root) | 0 | app.py (root) | 🟡 EMPTY |
| `web_converted/` (root) | 0 | app.py (root) | 🟡 EMPTY |
| `Web_Based_Bank_Statement_Converter/` | N/A | Legacy system | 🗑️ LEGACY |

---

## ⚠️ Files in `uploads/` Directory

Need to review these 2 files before deletion:
```powershell
Get-ChildItem -Path "uploads" -Recurse
```

---

## 🎯 Deletion Impact Assessment

### Can Delete Safely:
1. ✅ `converted/` (0 files, only used by simple_api.py which appears inactive)
2. ✅ `web_uploads/` (0 files, only used by root app.py which appears inactive)
3. ✅ `web_converted/` (0 files, only used by root app.py which appears inactive)
4. ✅ `Web_Based_Bank_Statement_Converter/` (entire legacy system)

### Requires Review First:
1. ⚠️ `uploads/` - Has 2 files - need to check:
   - What are these files?
   - Are they needed?
   - Is `simple_api.py` still being used?

### Must Keep:
1. ✅ `import/` (root) - Used by standalone converter scripts
2. ✅ `export/` (root) - Used by standalone converter scripts
3. ✅ `Bank_Specific_Converter/import/` - Production
4. ✅ `Bank_Specific_Converter/export/` - Production

---

## 🔧 Scripts Using Non-Standard Folders

### Root `app.py` (Legacy)
- **Lines 36-37:** Uses `web_uploads/` and `web_converted/`
- **Lines 41-42:** Creates folders with `os.makedirs()`
- **Evidence of use:** 0 files in both folders
- **Recommendation:** Safe to delete folders, script appears inactive

### Root `simple_api.py` (Test Server)
- **Lines 21-22:** Uses `uploads/` and `converted/`
- **Lines 25-26:** Creates folders with `os.makedirs()`
- **Evidence of use:** 2 files in `uploads/`, 0 in `converted/`
- **Recommendation:** Check contents of `uploads/` first

---

## 📝 Recommended Action Plan

### Step 1: Identify files in `uploads/`
```powershell
Get-ChildItem -Path "uploads" -Recurse | Select-Object Name, Length, LastWriteTime
```

### Step 2: Determine if `simple_api.py` is in use
- Check git history for recent usage
- Ask user if this test server is still needed
- If not used, safe to delete `uploads/` and `converted/`

### Step 3: Safe deletion (if confirmed unused)
```powershell
Remove-Item -Path "converted" -Recurse -Force
Remove-Item -Path "web_uploads" -Recurse -Force
Remove-Item -Path "web_converted" -Recurse -Force
# Only after review:
# Remove-Item -Path "uploads" -Recurse -Force
```

### Step 4: Archive legacy system
```powershell
# Option 1: Delete entirely
Remove-Item -Path "Web_Based_Bank_Statement_Converter" -Recurse -Force

# Option 2: Move to archive branch
git checkout -b archive/old-web-converter
git add Web_Based_Bank_Statement_Converter
git commit -m "Archive: Move old Web_Based_Bank_Statement_Converter to archive branch"
git push origin archive/old-web-converter
git checkout main
Remove-Item -Path "Web_Based_Bank_Statement_Converter" -Recurse -Force
```

---

## ✅ Conclusion

**Production system is NOT affected by any of these folders.**

The active production app (`Bank_Specific_Converter/app.py`) correctly uses only:
- `import/` folder
- `export/` folder

All other folders are used by:
1. Legacy test scripts (root `app.py`, `simple_api.py`)
2. Old architecture (`Web_Based_Bank_Statement_Converter/`)

**Next Action:** Review the 2 files in `uploads/` folder to determine if they're needed before proceeding with deletion.

---

**Audit Date:** October 21, 2025  
**Status:** Awaiting user confirmation on `uploads/` folder contents

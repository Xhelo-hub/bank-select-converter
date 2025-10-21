# 📁 Folder Structure Clarification

## ✅ CORRECT: Active System Uses Only 2 Folders

### Bank_Specific_Converter/ (ACTIVE - Production)
Uses **ONLY** these folders:
- ✅ `import/` - Input files from web uploads
- ✅ `export/` - Converted output files

**Confirmed in code:** `app.py` lines 57-58
```python
UPLOAD_FOLDER = BASE_DIR / 'import'
CONVERTED_FOLDER = BASE_DIR / 'export'
```

---

## 🗑️ OLD FOLDERS - Legacy System (Not Used)

### Root Level Folders
These exist at the root but are **NOT used** by the active converter:
- `converted/` - OLD folder from legacy system
- `uploads/` - OLD folder from legacy system  
- `web_uploads/` - OLD folder from legacy system
- `web_converted/` - OLD folder from legacy system

### Web_Based_Bank_Statement_Converter/ (LEGACY - Not Used)
This is the **OLD** system that predates `Bank_Specific_Converter/`. It uses:
- `uploads/` folder
- `converted/` folder

**This entire directory is legacy and not used in production.**

---

## 📊 Current Architecture

```
pdfdemo/
├── Bank_Specific_Converter/    ← ACTIVE (Production system)
│   ├── app.py                  ← Main Flask app
│   ├── import/                 ← ✅ Active input folder
│   └── export/                 ← ✅ Active output folder
│
├── BKT-2-QBO.py               ← Individual converters (called by app.py)
├── RAI-2-QBO.py
├── CREDINS-2-QBO.py           ← NEW
├── INTESA-2-QBO.py            ← NEW
├── ... (other converters)
│
├── import/                     ← Root level (used by standalone scripts)
├── export/                     ← Root level (used by standalone scripts)
│
├── converted/                  ← OLD (can be deleted)
├── uploads/                    ← OLD (can be deleted)
├── web_uploads/                ← OLD (can be deleted)
├── web_converted/              ← OLD (can be deleted)
│
└── Web_Based_Bank_Statement_Converter/  ← LEGACY (entire folder not used)
    └── ... (old system files)
```

---

## 🎯 Summary

### What's Actually Used:
1. **Bank_Specific_Converter/import/** - Web app uploads
2. **Bank_Specific_Converter/export/** - Web app outputs
3. **Root import/** - Standalone script inputs (optional)
4. **Root export/** - Standalone script outputs (optional)

### What Can Be Deleted:
- ❌ `converted/` (root level)
- ❌ `uploads/` (root level)  
- ❌ `web_uploads/` (root level)
- ❌ `web_converted/` (root level)
- ❌ `Web_Based_Bank_Statement_Converter/` (entire directory - legacy system)

---

## ✅ Conclusion

**You are correct!** The system IS using only 2 folders (`import/` and `export/`). The extra folders you see are:
1. **Legacy folders** from the old system (not used)
2. **Root-level copies** for standalone script usage (optional)

The **active production system** in `Bank_Specific_Converter/` uses **ONLY** `import/` and `export/` as intended.

---

**Generated:** October 21, 2025  
**Status:** System correctly configured with 2-folder structure

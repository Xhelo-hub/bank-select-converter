# 🔄 Quick Restore Guide - v1.0.0

## 📌 Milestone Information
- **Tag**: v1.0.0
- **Commit**: f21649e
- **Date**: October 20, 2025
- **Status**: ✅ STABLE & PRODUCTION-READY

---

## ⚡ Quick Restore Commands

### Local Development
```bash
# Clone repository
git clone https://github.com/Xhelo-hub/bank-select-converter.git
cd bank-select-converter

# Restore to v1.0.0
git checkout v1.0.0

# Setup environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
# OR
source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run web interface
cd Bank_Specific_Converter
python app.py
```

### Production Server
```bash
# SSH to server
ssh converter@c.konsulence.al

# Navigate to app
cd /home/converter/web/c.konsulence.al/public_html

# Restore to v1.0.0
git fetch --tags
git checkout v1.0.0

# Restart service
systemctl restart bank-converter
# OR manual restart:
pkill -f "gunicorn.*Bank_Specific_Converter"
cd Bank_Specific_Converter
../.venv/bin/gunicorn -c gunicorn.conf.py wsgi:application &
```

---

## 🎯 What This Milestone Includes

### ✅ Features
- 6 Albanian banks fully standardized (BKT, RAI, TIBANK, UNION, OTP, E-BILL)
- Clean filenames (no UUID prefix)
- Flat folder structure (import/ and export/)
- Consistent (v.1), (v.2), (v.3) versioning
- Automatic file cleanup (1 hour retention)
- QuickBooks-compatible CSV output

### ✅ Code Quality
- Removed 2,948 lines of technical debt
- 100% converter consistency
- All converters respect --output parameter
- Clean, maintainable codebase

### ✅ Production Status
- Deployed to https://c.konsulence.al
- Tested and verified working
- No known issues

---

## 📊 Key Commits in This Milestone

```
f21649e - 📌 MILESTONE v1.0.0 documentation
f58e3e0 - Standardize versioning (all converters use v.1 pattern)
f9f0a7f - Remove UUID prefix from filenames
1ab701c - Simplify folder structure (flat directories)
8516072 - Clean up 2,948 lines of backup/test files
19a5bcd - Fix converter --output parameter
```

---

## 🔍 Verify Restoration

After restoring, verify with:

```bash
# Check Git tag
git describe --tags
# Should output: v1.0.0

# Check commit
git log --oneline -1
# Should show: f21649e 📌 MILESTONE v1.0.0...

# Test a converter
python BKT-2-QBO.py --help
# Should show usage with --input and --output options

# Check web interface
cd Bank_Specific_Converter
python app.py
# Visit http://127.0.0.1:5002
```

---

## 📝 Rollback from Future Version

If you're on a newer version and need to rollback:

```bash
# Check current version
git describe --tags

# See available tags
git tag -l

# Rollback to v1.0.0
git checkout v1.0.0

# To make it permanent (creates new commit)
git checkout main
git reset --hard v1.0.0
git push origin main --force  # ⚠️ Use with caution!

# Or create a revert branch
git checkout main
git checkout -b revert-to-v1.0.0
git reset --hard v1.0.0
git push origin revert-to-v1.0.0
```

---

## 🆘 Troubleshooting

### Issue: "Tag not found"
```bash
git fetch --tags
git tag -l  # List all tags
```

### Issue: "File conflicts"
```bash
git stash  # Save current changes
git checkout v1.0.0
git stash pop  # Restore your changes (if needed)
```

### Issue: Production not working after restore
```bash
# Check Python environment
cd /home/converter/web/c.konsulence.al/public_html
source ../.venv/bin/activate
pip install -r requirements.txt

# Check process
ps aux | grep gunicorn

# Restart
systemctl restart bank-converter
```

---

## 📚 Documentation Files

- **MILESTONE_v1.0.0.md**: Complete milestone documentation
- **RESTORE_v1.0.0.md**: This quick reference guide
- **README.md**: User guide and quick start
- **DEPLOYMENT_GUIDE.md**: Production deployment instructions

---

## 🔗 Links

- **Repository**: https://github.com/Xhelo-hub/bank-select-converter
- **Tag on GitHub**: https://github.com/Xhelo-hub/bank-select-converter/releases/tag/v1.0.0
- **Production Site**: https://c.konsulence.al
- **Organization**: KONSULENCE.AL

---

## ✅ Checklist After Restore

- [ ] Git tag v1.0.0 matches commit f21649e
- [ ] All 6 converter scripts present in root directory
- [ ] Bank_Specific_Converter/app.py exists
- [ ] import/ and export/ folders exist (flat structure)
- [ ] No UUID-prefixed files in codebase
- [ ] Virtual environment activated
- [ ] Dependencies installed from requirements.txt
- [ ] Flask app runs without errors
- [ ] Test conversion produces clean filename (no UUID)
- [ ] Converted file has " - 4qbo.csv" suffix
- [ ] QuickBooks CSV format verified

---

**Last Updated**: October 20, 2025  
**Verified On**: Production server c.konsulence.al  
**Status**: ✅ STABLE

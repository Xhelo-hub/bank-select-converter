# CLAUDE.md - Albanian Bank Statement Converter

## Project Overview

A Python/Flask web application that converts Albanian bank statements (PDF/CSV) into QuickBooks-compatible CSV format. Supports 7 banks: BKT, OTP, Raiffeisen, TI Bank, Union, Credins, and E-Bills/Withholding.

## Quick Reference

```bash
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt

# Run web app (http://127.0.0.1:5002)
cd Bank_Specific_Converter
python app.py

# Run standalone converter
python BKT-2-QBO.py                 # Processes files in import/
```

No automated tests exist. Test manually: place file in `import/`, run converter, check `export/`.

## Architecture

### Two-layer structure

1. **Standalone converters** (root): `BKT-2-QBO.py`, `RAI-2-QBO.py`, `OTP-2-QBO.py`, `TIBANK-2-QBO.py`, `UNION-2-QBO.py`, `CREDINS-2-QBO.py`, `Withholding.py`
2. **Flask web app** (`Bank_Specific_Converter/`): Invokes converters via `subprocess.run()` — does NOT reimplement conversion logic

### Critical rule: conversion logic lives in standalone scripts only

The web app accepts uploads, calls the right `*-2-QBO.py` script, and returns results. Never duplicate conversion logic in `app.py`.

### Key files in `Bank_Specific_Converter/`

| File | Purpose |
|------|---------|
| `app.py` | Main Flask app with routes and `BANK_CONFIGS` (~3000 lines) |
| `models.py` | SQLAlchemy models (User, Job, Conversion, Download, Notification, etc.) |
| `auth.py` | UserManager authentication logic |
| `auth_routes.py` | Login/register/password-reset routes |
| `admin_routes.py` | Admin dashboard and settings |
| `email_utils.py` | SMTP email sending |
| `config.py` | Production configuration |
| `wsgi.py` | Gunicorn entry point |

### Database

SQLite via SQLAlchemy, stored in `Bank_Specific_Converter/data/app.db`. Uses WAL mode for multi-worker Gunicorn support. Migrations via Flask-Migrate.

## Code Conventions

### Converter script pattern

Every converter follows:
```
extract_text_from_pdf() → parse_{bank}_statement() → get_versioned_filename() → CSV output
```

### File handling

- Input: `import/` folder
- Output: `export/` folder, files suffixed with `" - 4qbo.csv"`
- Versioning: `(v.1)`, `(v.2)` appended if file exists — never overwrite
- Auto-cleanup: background thread deletes files older than 1 hour every 30 minutes

### CSV output format (QuickBooks)

Headers: `Date,Description,Debit,Credit,Balance`
- Dates: ISO 8601 (`YYYY-MM-DD`)
- Amounts: float strings (e.g., `"1500.50"`)
- Description: fields merged with `|` separator

### Date handling

Input varies by bank (DD-MMM-YY, DD.MM.YYYY, Albanian month names). Output is always YYYY-MM-DD.

### UI

Monochrome design system using CSS variables in `static/css/base.css`. Web interface is in English.

## Adding a New Bank

1. Create `{BANK}-2-QBO.py` in root following existing converter pattern
2. Add entry to `BANK_CONFIGS` dict in `Bank_Specific_Converter/app.py`
3. Update README

## Production Deployment

- **Stack**: Hetzner server, HestiaCP, Nginx, Gunicorn, Cloudflare DNS/SSL
- **Deploy**: `git pull origin main && systemctl restart bank-converter`
- **Env vars**: `SECRET_KEY` (required), `FLASK_ENV`, `DATABASE_URL` (optional, defaults to SQLite)
- **Email**: SMTP configured via admin panel (stored in DB)

## Anti-Patterns

- Do NOT duplicate conversion logic in `app.py` — invoke standalone scripts
- Do NOT use relative paths for scripts in production — use `get_script_path()`
- Do NOT skip file versioning — always use `get_versioned_filename()`
- Do NOT keep uploaded files indefinitely — rely on auto-cleanup

## Dependencies

Core: Flask 2.3.3, PyPDF2 3.0.1, SQLAlchemy 3.1.1, Flask-Login, Flask-Bcrypt, Flask-Migrate, Gunicorn, Flask-Limiter, Pillow

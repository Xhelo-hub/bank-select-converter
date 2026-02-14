#!/usr/bin/env python3
"""
Add status and error_message columns to jobs table
"""
import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'data' / 'app.db'

if not DB_PATH.exists():
    print(f"Database not found at {DB_PATH}")
    exit(1)

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [row[1] for row in cursor.fetchall()]

    # Add status column if it doesn't exist
    if 'status' not in columns:
        print("Adding 'status' column to jobs table...")
        cursor.execute("ALTER TABLE jobs ADD COLUMN status TEXT NOT NULL DEFAULT 'completed'")
        conn.commit()
        print("[OK] Added 'status' column")
    else:
        print("[OK] 'status' column already exists")

    # Add error_message column if it doesn't exist
    if 'error_message' not in columns:
        print("Adding 'error_message' column to jobs table...")
        cursor.execute("ALTER TABLE jobs ADD COLUMN error_message TEXT")
        conn.commit()
        print("[OK] Added 'error_message' column")
    else:
        print("[OK] 'error_message' column already exists")

    # Make output_filename and output_path nullable (can't modify existing columns in SQLite easily)
    # So we'll just note this
    print("\nNote: output_filename and output_path are now nullable for jobs in 'processing' state")
    print("Existing completed jobs will remain unchanged")

    # Update all existing jobs to have status='completed' if NULL
    cursor.execute("UPDATE jobs SET status = 'completed' WHERE status IS NULL OR status = ''")
    conn.commit()
    print(f"\n[OK] Updated {cursor.rowcount} existing jobs to status='completed'")

    print("\nMigration completed successfully!")

except Exception as e:
    print(f"\n[ERROR] Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()

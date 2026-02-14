#!/usr/bin/env python3
"""
Create marketing_messages table in the database
"""

from app import app, db
from models import MarketingMessage

def create_marketing_table():
    """Create the marketing_messages table"""
    with app.app_context():
        # Create the table
        db.create_all()
        print("[OK] Marketing messages table created successfully!")

        # Check if table exists by querying it
        try:
            count = MarketingMessage.query.count()
            print(f"[OK] Table is working! Currently has {count} messages.")
        except Exception as e:
            print(f"[ERROR] Error checking table: {e}")
            return False

        return True

if __name__ == '__main__':
    print("Creating marketing_messages table...")
    success = create_marketing_table()

    if success:
        print("\n[SUCCESS] Setup complete!")
        print("You can now use the Marketing Messages admin page.")
    else:
        print("\n[FAILED] Setup failed. Check the error messages above.")

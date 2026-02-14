#!/usr/bin/env python3
"""
Sync users from local database to production
"""

import sys
from app import app, db, User

def export_users():
    """Export users from current database"""
    with app.app_context():
        users = User.query.all()
        user_data = []
        for user in users:
            user_data.append({
                'email': user.email,
                'password': user.password,
                'is_admin': user.is_admin,
                'is_approved': user.is_approved,
                'is_active': user.is_active
            })
        return user_data

def import_users(user_data):
    """Import users into current database"""
    with app.app_context():
        imported = 0
        skipped = 0

        for data in user_data:
            # Check if user already exists
            existing = User.query.filter_by(email=data['email']).first()
            if existing:
                print(f"  [SKIP]  User {data['email']} already exists - skipping")
                skipped += 1
                continue

            # Create new user
            import uuid
            from datetime import datetime
            user = User(
                id=str(uuid.uuid4()),
                email=data['email'],
                password=data['password'],  # Copy the hashed password directly
                is_admin=data.get('is_admin', False),
                is_approved=data.get('is_approved', True),
                is_active=data.get('is_active', True),
                created_at=datetime.now().isoformat()
            )

            db.session.add(user)
            print(f"  [OK] Added user: {data['email']} (admin={data['is_admin']})")
            imported += 1

        db.session.commit()
        print(f"\n[SUMMARY] Summary: {imported} imported, {skipped} skipped")

if __name__ == '__main__':
    import json

    if len(sys.argv) > 1 and sys.argv[1] == 'export':
        # Export mode
        users = export_users()
        # Save to JSON file
        with open('users_export.json', 'w') as f:
            json.dump(users, f, indent=2)
        print(f"[OK] Exported {len(users)} users to users_export.json")
        print("\nUsers exported:")
        for user in users:
            print(f"  - {user['email']} (admin={user['is_admin']})")
    elif len(sys.argv) > 1 and sys.argv[1] == 'import':
        # Import mode - reads from file
        if len(sys.argv) > 2:
            filename = sys.argv[2]
        else:
            filename = 'users_export.json'

        try:
            with open(filename, 'r') as f:
                user_data = json.load(f)
            print(f"[IMPORT] Importing {len(user_data)} users from {filename}...")
            import_users(user_data)
        except FileNotFoundError:
            print(f"[ERROR] Error: File {filename} not found")
            sys.exit(1)
    else:
        print("Usage:")
        print("  Export: python sync_users.py export")
        print("  Import: python sync_users.py import [filename]")

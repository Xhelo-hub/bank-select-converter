#!/usr/bin/env python3
"""
JSON to SQLite Migration Script
================================
Migrates data from JSON files to SQLite database.
This script is idempotent and can be run multiple times safely.

Usage:
    python migrate_json_to_sqlite.py
"""

import sys
import json
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from models import db, User, Conversion, Download, EmailConfig, Notification, NotificationRead
from datetime import datetime

def load_json_file(filename):
    """Load JSON file, return empty dict if not found"""
    filepath = Path(__file__).parent / filename
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error reading {filename}: {e}")
            return {}
    else:
        print(f"ℹ️  File not found: {filename} (skipping)")
        return {}

def migrate_users(users_data):
    """Migrate users from JSON to database"""
    if not users_data:
        print("ℹ️  No users to migrate")
        return 0

    migrated = 0
    skipped = 0

    # Handle both list and dict formats
    if isinstance(users_data, list):
        # List format: [{"id": "...", "email": "...", ...}, ...]
        users_list = users_data
    else:
        # Dict format: {"user_id": {"email": "...", ...}, ...}
        users_list = [{"id": user_id, **user_data} for user_id, user_data in users_data.items()]

    for user_data in users_list:
        user_id = user_data.get('id')
        email = user_data.get('email')

        # Check if user already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"  ⏭️  Skipping {email} (already exists)")
            skipped += 1
            continue

        # Create new user
        user = User(
            id=user_id,
            email=email,
            password=user_data.get('password'),  # Preserve bcrypt hash exactly
            created_at=user_data.get('created_at'),
            is_admin=user_data.get('is_admin', False),
            is_approved=user_data.get('is_approved', False),
            _is_active=user_data.get('is_active', True),
            reset_token=user_data.get('reset_token'),
            reset_token_expiry=user_data.get('reset_token_expiry')
        )

        db.session.add(user)
        print(f"  ✅ Migrated user: {email} (admin={user.is_admin})")
        migrated += 1

    db.session.commit()
    print(f"\n📊 Users: {migrated} migrated, {skipped} skipped")
    return migrated

def migrate_conversions(stats_data):
    """Migrate conversion records from stats JSON to database"""
    conversions_list = stats_data.get('conversions', [])

    if not conversions_list:
        print("ℹ️  No conversions to migrate")
        return 0

    migrated = 0

    for conv_data in conversions_list:
        # Create conversion record
        conversion = Conversion(
            user_email=conv_data.get('user_email', 'unknown'),
            bank=conv_data.get('bank'),
            timestamp=conv_data.get('timestamp')
        )
        db.session.add(conversion)
        migrated += 1

    db.session.commit()
    print(f"📊 Conversions: {migrated} migrated")
    return migrated

def migrate_downloads(stats_data):
    """Migrate download records from stats JSON to database"""
    downloads_list = stats_data.get('downloads', [])

    if not downloads_list:
        print("ℹ️  No downloads to migrate")
        return 0

    migrated = 0

    for dl_data in downloads_list:
        # Create download record
        download = Download(
            user_email=dl_data.get('user_email', 'unknown'),
            job_id=dl_data.get('job_id'),
            timestamp=dl_data.get('timestamp')
        )
        db.session.add(download)
        migrated += 1

    db.session.commit()
    print(f"📊 Downloads: {migrated} migrated")
    return migrated

def migrate_email_config(config_data):
    """Migrate email configuration from JSON to database"""
    if not config_data:
        print("ℹ️  No email config to migrate")
        return False

    # Check if email config already exists
    existing = db.session.get(EmailConfig, 1)
    if existing:
        print("  ⏭️  Email config already exists (skipping)")
        return False

    # Create email config
    email_config = EmailConfig(
        id=1,
        smtp_server=config_data.get('smtp_server', 'smtp.office365.com'),
        smtp_port=config_data.get('smtp_port', 587),
        smtp_username=config_data.get('smtp_username', ''),
        smtp_password=config_data.get('smtp_password', ''),
        from_email=config_data.get('from_email', ''),
        enabled=config_data.get('enabled', False),
        test_email=config_data.get('test_email', '')
    )

    db.session.add(email_config)
    db.session.commit()

    print(f"✅ Email config migrated (SMTP: {email_config.smtp_server})")
    return True

def migrate_notifications(notifs_data):
    """Migrate notifications from JSON to database"""
    if not notifs_data:
        print("ℹ️  No notifications to migrate")
        return 0

    notifications_list = notifs_data.get('notifications', [])
    read_status = notifs_data.get('read_status', {})

    migrated = 0

    for notif_data in notifications_list:
        notif_id = notif_data.get('id')

        # Check if notification already exists
        existing = Notification.query.filter_by(id=notif_id).first()
        if existing:
            continue

        # Create notification
        notification = Notification(
            id=notif_id,
            title=notif_data.get('title'),
            message=notif_data.get('message'),
            type=notif_data.get('type', 'info'),
            recipients=json.dumps(notif_data.get('recipients', [])),
            created_at=notif_data.get('created_at'),
            created_by=notif_data.get('created_by')
        )
        db.session.add(notification)

        # Migrate read status for this notification
        notif_read_status = read_status.get(notif_id, {})
        for user_email, read_time in notif_read_status.items():
            read_record = NotificationRead(
                notification_id=notif_id,
                user_email=user_email,
                read_at=read_time
            )
            db.session.add(read_record)

        migrated += 1

    db.session.commit()
    print(f"📊 Notifications: {migrated} migrated")
    return migrated

def main():
    """Main migration function"""
    print("\n" + "="*60)
    print("  JSON to SQLite Migration")
    print("="*60 + "\n")

    with app.app_context():
        # Create all tables
        print("📦 Creating database tables...")
        db.create_all()
        print("✅ Tables created\n")

        # Load JSON files
        print("📂 Loading JSON files...\n")
        users_data = load_json_file('users.json')
        stats_data = load_json_file('conversion_stats.json')
        email_config_data = load_json_file('email_config.json')
        notifications_data = load_json_file('notifications.json')

        # Perform migrations
        print("\n🔄 Starting migration...\n")

        print("1️⃣  Migrating users...")
        migrate_users(users_data)

        print("\n2️⃣  Migrating conversions...")
        migrate_conversions(stats_data)

        print("\n3️⃣  Migrating downloads...")
        migrate_downloads(stats_data)

        print("\n4️⃣  Migrating email configuration...")
        migrate_email_config(email_config_data)

        print("\n5️⃣  Migrating notifications...")
        migrate_notifications(notifications_data)

        # Summary
        print("\n" + "="*60)
        print("  Migration Complete!")
        print("="*60)

        # Show summary
        user_count = User.query.count()
        conversion_count = Conversion.query.count()
        download_count = Download.query.count()
        notification_count = Notification.query.count()

        print(f"\n📊 Database Summary:")
        print(f"  • Users: {user_count}")
        print(f"  • Conversions: {conversion_count}")
        print(f"  • Downloads: {download_count}")
        print(f"  • Notifications: {notification_count}")

        print("\n✅ You can now start the application with the SQLite database")
        print("💡 The old JSON files are still present as backups\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

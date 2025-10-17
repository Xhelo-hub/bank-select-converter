#!/usr/bin/env python3
"""
Script to create the initial admin user for the bank statement converter.
Run this once to create the first admin account.
"""

import sys
from pathlib import Path

# Add parent directory to path to import auth module
sys.path.insert(0, str(Path(__file__).parent))

from auth import UserManager

def create_admin():
    """Create the initial admin user"""
    user_manager = UserManager()
    
    print("\n=== Create Initial Admin User ===\n")
    
    # Check if admin already exists
    all_users = user_manager.get_all_users()
    if any(u.is_admin for u in all_users):
        print("❌ An admin user already exists!")
        print("\nExisting admin users:")
        for user in all_users:
            if user.is_admin:
                print(f"  - {user.email}")
        return False
    
    # Get admin details
    email = input("Enter admin email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return False
    
    password = input("Enter admin password (min 6 characters): ").strip()
    if len(password) < 6:
        print("❌ Password must be at least 6 characters")
        return False
    
    confirm_password = input("Confirm password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match")
        return False
    
    # Create admin
    admin, message = user_manager.create_initial_admin(email, password)
    
    if admin:
        print(f"\n✅ {message}")
        print(f"\nAdmin user created:")
        print(f"  Email: {admin.email}")
        print(f"  ID: {admin.id}")
        print(f"  Admin: {admin.is_admin}")
        print(f"  Approved: {admin.is_approved}")
        print(f"\nYou can now log in and manage user registrations at /admin/dashboard")
        return True
    else:
        print(f"\n❌ {message}")
        return False

if __name__ == "__main__":
    try:
        success = create_admin()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

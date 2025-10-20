#!/usr/bin/env python3
"""
Simple script to reset admin password
Usage: python reset_admin_password.py <email> <new_password>
"""
import sys
import json
from flask_bcrypt import Bcrypt
import os

def reset_admin_password(email, new_password):
    """Reset admin password"""
    
    # Initialize bcrypt
    bcrypt = Bcrypt()
    
    # Load users
    users_file = 'users.json'
    if not os.path.exists(users_file):
        print(f"Error: {users_file} not found")
        return False
    
    with open(users_file, 'r') as f:
        users_data = json.load(f)
    
    # Find user
    user_found = False
    for user in users_data:
        if user['email'] == email:
            user_found = True
            # Hash new password
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user['password'] = hashed_password
            
            # Ensure user is active and approved
            user['is_approved'] = True
            user['is_active'] = True
            
            print(f"Updated user: {email}")
            print(f"- is_admin: {user.get('is_admin', False)}")
            print(f"- is_approved: {user.get('is_approved', False)}")
            print(f"- is_active: {user.get('is_active', True)}")
            break
    
    if not user_found:
        print(f"Error: User {email} not found")
        return False
    
    # Save users
    with open(users_file, 'w') as f:
        json.dump(users_data, f, indent=2)
    
    print(f"Password reset successfully for {email}")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_admin_password.py <email> <new_password>")
        print("Example: python reset_admin_password.py kontakt@konsulence.al newpassword123")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    reset_admin_password(email, new_password)
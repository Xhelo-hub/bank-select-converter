"""
Authentication Module with Flask-Login Support
==============================================
Provides user authentication with Flask-Login integration
"""

import os
import json
import uuid
from datetime import datetime
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

# Initialize bcrypt
bcrypt = Bcrypt()

# User database file
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, email, password, created_at=None, is_admin=False, is_approved=False):
        self.id = id
        self.email = email
        self.password = password
        self.created_at = created_at or datetime.now().isoformat()
        self.is_admin = is_admin
        self.is_approved = is_approved
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at,
            'is_admin': self.is_admin,
            'is_approved': self.is_approved
        }
    
    @staticmethod
    def from_dict(data):
        """Create user from dictionary"""
        return User(
            id=data['id'],
            email=data['email'],
            password=data['password'],
            created_at=data.get('created_at'),
            is_admin=data.get('is_admin', False),
            is_approved=data.get('is_approved', False)
        )

class UserManager:
    """Manage user database operations"""
    
    def __init__(self, db_file=None):
        self.db_file = db_file or USERS_FILE
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database file if it doesn't exist"""
        if not os.path.exists(self.db_file):
            with open(self.db_file, 'w') as f:
                json.dump([], f)
    
    def _load_users(self):
        """Load all users from database"""
        try:
            with open(self.db_file, 'r') as f:
                data = json.load(f)
                return [User.from_dict(u) for u in data]
        except:
            return []
    
    def _save_users(self, users):
        """Save all users to database"""
        with open(self.db_file, 'w') as f:
            json.dump([u.to_dict() for u in users], f, indent=2)
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        users = self._load_users()
        for user in users:
            if user.id == user_id:
                return user
        return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        users = self._load_users()
        for user in users:
            if user.email.lower() == email.lower():
                return user
        return None
    
    def create_user(self, email, password):
        """Create a new user"""
        # Check if user exists
        if self.get_user_by_email(email):
            return None, "Email already registered"
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password=hashed_password
        )
        
        # Save to database
        users = self._load_users()
        users.append(user)
        self._save_users(users)
        
        return user, "User created successfully"
    
    def verify_password(self, user, password):
        """Verify user's password"""
        return bcrypt.check_password_hash(user.password, password)
    
    def get_all_users(self):
        """Get all users (for admin purposes)"""
        return self._load_users()
    
    def delete_user(self, user_id):
        """Delete a user"""
        users = self._load_users()
        users = [u for u in users if u.id != user_id]
        self._save_users(users)
        return True
    
    def get_pending_users(self):
        """Get all users pending approval"""
        users = self._load_users()
        return [u for u in users if not u.is_approved]
    
    def approve_user(self, user_id):
        """Approve a user registration"""
        users = self._load_users()
        for user in users:
            if user.id == user_id:
                user.is_approved = True
                self._save_users(users)
                return True, "User approved successfully"
        return False, "User not found"
    
    def reject_user(self, user_id):
        """Reject a user registration (deletes the user)"""
        return self.delete_user(user_id)
    
    def create_initial_admin(self, email, password):
        """Create the first admin user (approved by default)"""
        # Check if any admin already exists
        users = self._load_users()
        if any(u.is_admin for u in users):
            return None, "Admin user already exists"
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create admin user
        admin = User(
            id=str(uuid.uuid4()),
            email=email,
            password=hashed_password,
            is_admin=True,
            is_approved=True
        )
        
        # Save to database
        users.append(admin)
        self._save_users(users)
        
        return admin, "Admin user created successfully"

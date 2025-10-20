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
    def __init__(self, id, email, password, created_at=None, is_admin=False, is_approved=False, is_active=True, reset_token=None, reset_token_expiry=None):
        self.id = id
        self.email = email
        self.password = password
        self.created_at = created_at or datetime.now().isoformat()
        self.is_admin = is_admin
        self.is_approved = is_approved
        self.is_active = is_active
        self.reset_token = reset_token
        self.reset_token_expiry = reset_token_expiry
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at,
            'is_admin': self.is_admin,
            'is_approved': self.is_approved,
            'is_active': self.is_active,
            'reset_token': self.reset_token,
            'reset_token_expiry': self.reset_token_expiry
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
            is_approved=data.get('is_approved', False),
            is_active=data.get('is_active', True),
            reset_token=data.get('reset_token'),
            reset_token_expiry=data.get('reset_token_expiry')
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
    
    def generate_reset_token(self, email):
        """Generate password reset token for user"""
        from datetime import datetime, timedelta
        
        users = self._load_users()
        for user in users:
            if user.email.lower() == email.lower():
                # Generate 6-digit code
                import random
                reset_token = str(random.randint(100000, 999999))
                
                # Token expires in 30 minutes
                expiry = (datetime.now() + timedelta(minutes=30)).isoformat()
                
                user.reset_token = reset_token
                user.reset_token_expiry = expiry
                self._save_users(users)
                
                return reset_token, "Reset token generated"
        
        return None, "User not found"
    
    def verify_reset_token(self, email, token):
        """Verify password reset token"""
        from datetime import datetime
        
        users = self._load_users()
        for user in users:
            if user.email.lower() == email.lower():
                if not user.reset_token or not user.reset_token_expiry:
                    return False, "No reset token found"
                
                # Check if token expired
                expiry = datetime.fromisoformat(user.reset_token_expiry)
                if datetime.now() > expiry:
                    return False, "Reset token expired"
                
                # Check if token matches
                if user.reset_token == token:
                    return True, "Token verified"
                else:
                    return False, "Invalid token"
        
        return False, "User not found"
    
    def reset_password(self, email, token, new_password):
        """Reset user password with token"""
        # Verify token first
        verified, message = self.verify_reset_token(email, token)
        if not verified:
            return False, message
        
        # Update password
        users = self._load_users()
        for user in users:
            if user.email.lower() == email.lower():
                user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                user.reset_token = None
                user.reset_token_expiry = None
                self._save_users(users)
                return True, "Password reset successfully"
        
        return False, "User not found"
    
    def promote_to_admin(self, user_id):
        """Promote a user to admin"""
        users = self._load_users()
        for user in users:
            if user.id == user_id:
                user.is_admin = True
                self._save_users(users)
                return True, "User promoted to admin"
        return False, "User not found"
    
    def demote_from_admin(self, user_id):
        """Remove admin privileges from a user"""
        users = self._load_users()
        for user in users:
            if user.id == user_id:
                user.is_admin = False
                self._save_users(users)
                return True, "Admin privileges removed"
        return False, "User not found"
    
    def generate_admin_removal_code(self, admin_email):
        """Generate verification code for admin removal (sent to the admin being removed)"""
        import random
        from datetime import datetime, timedelta
        
        users = self._load_users()
        for user in users:
            if user.email.lower() == admin_email.lower() and user.is_admin:
                # Generate 6-digit verification code
                verification_code = str(random.randint(100000, 999999))
                
                # Store temporarily (we'll use reset_token field for this)
                expiry = (datetime.now() + timedelta(minutes=15)).isoformat()
                
                user.reset_token = verification_code
                user.reset_token_expiry = expiry
                self._save_users(users)
                
                return verification_code, "Verification code generated"
        
        return None, "Admin user not found"
    
    def verify_admin_removal_code(self, admin_email, code):
        """Verify the admin removal code"""
        from datetime import datetime
        
        users = self._load_users()
        for user in users:
            if user.email.lower() == admin_email.lower() and user.is_admin:
                if not user.reset_token or not user.reset_token_expiry:
                    return False, "No verification code found"
                
                # Check if code expired
                expiry = datetime.fromisoformat(user.reset_token_expiry)
                if datetime.now() > expiry:
                    return False, "Verification code expired"
                
                # Check if code matches
                if user.reset_token == code:
                    # Clear the token
                    user.reset_token = None
                    user.reset_token_expiry = None
                    self._save_users(users)
                    return True, "Code verified"
                else:
                    return False, "Invalid verification code"
        
        return False, "Admin user not found"
    
    def activate_user(self, user_id):
        """Activate a user account"""
        users = self._load_users()
        for user in users:
            if user.id == user_id:
                user.is_active = True
                self._save_users(users)
                return True, "User activated successfully"
        return False, "User not found"
    
    def deactivate_user(self, user_id):
        """Deactivate a user account"""
        users = self._load_users()
        for user in users:
            if user.id == user_id:
                user.is_active = False
                self._save_users(users)
                return True, "User deactivated successfully"
        return False, "User not found"
    
    def delete_user(self, user_id):
        """Delete a user permanently"""
        users = self._load_users()
        initial_count = len(users)
        users = [u for u in users if u.id != user_id]
        
        if len(users) < initial_count:
            self._save_users(users)
            return True, "User deleted successfully"
        return False, "User not found"

"""
Authentication Module with Flask-Login Support
==============================================
Provides user authentication with Flask-Login integration.
Uses SQLAlchemy database backend.
"""

import uuid
import secrets
import random
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from models import db, User

# Initialize bcrypt
bcrypt = Bcrypt()


class UserManager:
    """Manage user database operations via SQLAlchemy"""

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return db.session.get(User, user_id)

    def get_user_by_email(self, email):
        """Get user by email (case-insensitive)"""
        return User.query.filter(db.func.lower(User.email) == email.lower()).first()

    def create_user(self, email, password):
        """Create a new user"""
        if self.get_user_by_email(email):
            return None, "Email already registered"

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password=hashed_password,
            created_at=datetime.now().isoformat()
        )
        db.session.add(user)
        db.session.commit()
        return user, "User created successfully"

    def verify_password(self, user, password):
        """Verify user's password"""
        return bcrypt.check_password_hash(user.password, password)

    def get_all_users(self):
        """Get all users"""
        return User.query.all()

    def delete_user(self, user_id):
        """Delete a user permanently"""
        user = db.session.get(User, user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True, "User deleted successfully"
        return False, "User not found"

    def get_pending_users(self):
        """Get all users pending approval"""
        return User.query.filter_by(is_approved=False).all()

    def approve_user(self, user_id):
        """Approve a user registration"""
        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"
        user.is_approved = True
        db.session.commit()
        return True, "User approved successfully"

    def reject_user(self, user_id):
        """Reject a user registration (deletes the user)"""
        return self.delete_user(user_id)

    def create_initial_admin(self, email, password):
        """Create the first admin user (approved by default)"""
        if User.query.filter_by(is_admin=True).first():
            return None, "Admin user already exists"

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = User(
            id=str(uuid.uuid4()),
            email=email,
            password=hashed_password,
            created_at=datetime.now().isoformat(),
            is_admin=True,
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin, "Admin user created successfully"

    def generate_reset_token(self, email):
        """Generate password reset token for user"""
        user = self.get_user_by_email(email)
        if not user:
            return None, "User not found"

        reset_token = secrets.token_urlsafe(32)
        expiry = (datetime.now() + timedelta(minutes=30)).isoformat()

        user.reset_token = reset_token
        user.reset_token_expiry = expiry
        db.session.commit()
        return reset_token, "Reset token generated"

    def admin_reset_password(self, user_id, new_password):
        """Admin reset user password (no token required)"""
        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"

        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        return True, "Password reset successfully"

    def verify_reset_token(self, email, token):
        """Verify password reset token"""
        user = self.get_user_by_email(email)
        if not user:
            return False, "User not found"

        if not user.reset_token or not user.reset_token_expiry:
            return False, "No reset token found"

        expiry = datetime.fromisoformat(user.reset_token_expiry)
        if datetime.now() > expiry:
            return False, "Reset token expired"

        if user.reset_token == token:
            return True, "Token verified"
        return False, "Invalid token"

    def reset_password(self, email, token, new_password):
        """Reset user password with token"""
        verified, message = self.verify_reset_token(email, token)
        if not verified:
            return False, message

        user = self.get_user_by_email(email)
        if not user:
            return False, "User not found"

        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        return True, "Password reset successfully"

    def promote_to_admin(self, user_id):
        """Promote a user to admin"""
        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"
        user.is_admin = True
        db.session.commit()
        return True, "User promoted to admin"

    def demote_from_admin(self, user_id):
        """Remove admin privileges from a user"""
        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"
        user.is_admin = False
        db.session.commit()
        return True, "Admin privileges removed"

    def generate_admin_removal_code(self, admin_email):
        """Generate verification code for admin removal"""
        user = self.get_user_by_email(admin_email)
        if not user or not user.is_admin:
            return None, "Admin user not found"

        verification_code = str(random.randint(100000, 999999))
        expiry = (datetime.now() + timedelta(minutes=15)).isoformat()

        user.reset_token = verification_code
        user.reset_token_expiry = expiry
        db.session.commit()
        return verification_code, "Verification code generated"

    def verify_admin_removal_code(self, admin_email, code):
        """Verify the admin removal code"""
        user = self.get_user_by_email(admin_email)
        if not user or not user.is_admin:
            return False, "Admin user not found"

        if not user.reset_token or not user.reset_token_expiry:
            return False, "No verification code found"

        expiry = datetime.fromisoformat(user.reset_token_expiry)
        if datetime.now() > expiry:
            return False, "Verification code expired"

        if user.reset_token == code:
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            return True, "Code verified"
        return False, "Invalid verification code"

    def activate_user(self, user_id):
        """Activate a user account"""
        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"
        user.is_active = True
        db.session.commit()
        return True, "User activated successfully"

    def deactivate_user(self, user_id):
        """Deactivate a user account"""
        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"
        user.is_active = False
        db.session.commit()
        return True, "User deactivated successfully"

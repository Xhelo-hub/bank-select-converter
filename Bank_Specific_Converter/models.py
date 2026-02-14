"""
Database Models for Bank Statement Converter
=============================================
SQLAlchemy models replacing JSON file storage.
"""

import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=True, default='')
    last_name = db.Column(db.String(100), nullable=True, default='')
    display_name = db.Column(db.String(150), nullable=True, default='')
    created_at = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    _is_active = db.Column('is_active', db.Boolean, default=True)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.String(50), nullable=True)

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @property
    def full_name(self):
        """Return full name from first_name + last_name"""
        parts = [self.first_name or '', self.last_name or '']
        return ' '.join(p for p in parts if p).strip()

    @property
    def system_name(self):
        """Return the name to display in the system (display_name > full_name > email username)"""
        if self.display_name:
            return self.display_name
        if self.full_name:
            return self.full_name
        return self.email.split('@')[0]

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'created_at': self.created_at,
            'is_admin': self.is_admin,
            'is_approved': self.is_approved,
            'is_active': self.is_active,
            'reset_token': self.reset_token,
            'reset_token_expiry': self.reset_token_expiry
        }


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.String(36), primary_key=True)
    bank = db.Column(db.String(50), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    output_filename = db.Column(db.String(255), nullable=True)  # Nullable until conversion completes
    output_path = db.Column(db.String(512), nullable=True)  # Nullable until conversion completes
    status = db.Column(db.String(20), nullable=False, default='processing', index=True)  # processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)  # Store error if conversion fails
    timestamp = db.Column(db.Float, nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)


class Conversion(db.Model):
    __tablename__ = 'conversions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False)
    bank = db.Column(db.String(50), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    output_filename = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    success = db.Column(db.Boolean, nullable=False)


class Download(db.Model):
    __tablename__ = 'downloads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)
    user_id = db.Column(db.String(36), nullable=False)
    job_id = db.Column(db.String(36), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.String(50), nullable=False)
    created_by = db.Column(db.String(255), nullable=False)
    recipients = db.Column(db.Text, nullable=False)  # JSON-encoded list
    send_email = db.Column(db.Boolean, default=False)

    reads = db.relationship('NotificationRead', backref='notification',
                            lazy='dynamic', cascade='all, delete-orphan')

    def get_recipients_list(self):
        return json.loads(self.recipients)

    def set_recipients_list(self, recipients_list):
        self.recipients = json.dumps(recipients_list)


class NotificationRead(db.Model):
    __tablename__ = 'notification_reads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    notification_id = db.Column(db.String(36), db.ForeignKey('notifications.id'), nullable=False, index=True)
    user_email = db.Column(db.String(255), nullable=False, index=True)

    __table_args__ = (
        db.UniqueConstraint('notification_id', 'user_email', name='uq_notif_read_user'),
    )


class EmailConfig(db.Model):
    __tablename__ = 'email_config'

    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(255), default='smtp.office365.com')
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(255), default='')
    smtp_password = db.Column(db.String(255), default='')
    from_email = db.Column(db.String(255), default='')
    enabled = db.Column(db.Boolean, default=False)
    test_email = db.Column(db.String(255), default='')


class MarketingMessage(db.Model):
    """Marketing messages/announcements shown on login page"""
    __tablename__ = 'marketing_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    link_url = db.Column(db.String(500), nullable=True)
    link_text = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.String(50), nullable=False)
    created_by = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'link_url': self.link_url,
            'link_text': self.link_text,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'created_at': self.created_at,
            'created_by': self.created_by
        }


class ContactMessage(db.Model):
    """User-to-admin contact messages"""
    __tablename__ = 'contact_messages'

    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    user_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'subject': self.subject,
            'message': self.message,
            'created_at': self.created_at,
            'is_read': self.is_read
        }

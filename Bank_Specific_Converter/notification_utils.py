"""
Notification Management Module
===============================
Provides notification storage and management functionality
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# Cross-process file locking for multi-worker gunicorn
if os.name == 'posix':
    import fcntl
    class FileLock:
        """File-based lock using fcntl.flock - works across gunicorn workers"""
        def __init__(self, lock_path):
            self.lock_path = str(lock_path) + '.lock'
        def __enter__(self):
            self._fd = open(self.lock_path, 'w')
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX)
            return self
        def __exit__(self, *args):
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            self._fd.close()
else:
    import threading
    class FileLock:
        """Thread-based lock fallback for Windows development"""
        _locks = {}
        _meta_lock = threading.Lock()
        def __init__(self, lock_path):
            self.lock_path = str(lock_path)
            with FileLock._meta_lock:
                if self.lock_path not in FileLock._locks:
                    FileLock._locks[self.lock_path] = threading.Lock()
                self._lock = FileLock._locks[self.lock_path]
        def __enter__(self):
            self._lock.acquire()
            return self
        def __exit__(self, *args):
            self._lock.release()

# Notification storage file
BASE_DIR = Path(__file__).parent.absolute()
NOTIFICATIONS_FILE = BASE_DIR / 'notifications.json'
notifications_lock = FileLock(NOTIFICATIONS_FILE)

def load_notifications():
    """Load notifications from JSON file (shared across gunicorn workers)"""
    try:
        if NOTIFICATIONS_FILE.exists():
            with open(NOTIFICATIONS_FILE, 'r') as f:
                data = json.load(f)
                return data
    except Exception as e:
        print(f"Error loading notifications: {e}")
    return {"notifications": []}

def save_notifications(data):
    """Save notifications to JSON file (shared across gunicorn workers) - atomic write"""
    try:
        tmp_path = str(NOTIFICATIONS_FILE) + '.tmp'
        with open(tmp_path, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, str(NOTIFICATIONS_FILE))
    except Exception as e:
        print(f"Error saving notifications: {e}")

def create_notification(title, message, notification_type, recipients, send_email, created_by):
    """
    Create a new notification
    
    Args:
        title: Notification title
        message: Notification message
        notification_type: Type (info, warning, important, success)
        recipients: List of recipient emails or ['all']
        send_email: Boolean - whether to send email notification
        created_by: Email of admin who created the notification
    
    Returns:
        str: Notification ID
    """
    with notifications_lock:
        data = load_notifications()
        
        notification = {
            'id': str(uuid.uuid4()),
            'title': title,
            'message': message,
            'type': notification_type,
            'created_at': datetime.now().isoformat(),
            'created_by': created_by,
            'recipients': recipients,
            'send_email': send_email,
            'read_by': []
        }
        
        data['notifications'].append(notification)
        save_notifications(data)
        
        return notification['id']

def get_user_notifications(user_email):
    """
    Get all notifications for a specific user
    
    Args:
        user_email: User's email address
    
    Returns:
        list: List of notifications with is_read flag
    """
    with notifications_lock:
        data = load_notifications()
        
        user_notifications = []
        for notif in data['notifications']:
            # Check if user is a recipient
            if 'all' in notif['recipients'] or user_email in notif['recipients']:
                notif_copy = notif.copy()
                notif_copy['is_read'] = user_email in notif.get('read_by', [])
                user_notifications.append(notif_copy)
        
        # Sort by created_at (newest first)
        user_notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        return user_notifications

def mark_as_read(notification_id, user_email):
    """
    Mark a notification as read for a specific user
    
    Args:
        notification_id: Notification ID
        user_email: User's email address
    
    Returns:
        bool: True if successful, False otherwise
    """
    with notifications_lock:
        data = load_notifications()
        
        for notif in data['notifications']:
            if notif['id'] == notification_id:
                if user_email not in notif.get('read_by', []):
                    if 'read_by' not in notif:
                        notif['read_by'] = []
                    notif['read_by'].append(user_email)
                    save_notifications(data)
                return True
        
        return False

def mark_all_as_read(user_email):
    """
    Mark all notifications as read for a specific user
    
    Args:
        user_email: User's email address
    
    Returns:
        int: Number of notifications marked as read
    """
    with notifications_lock:
        data = load_notifications()
        count = 0
        
        for notif in data['notifications']:
            # Check if user is a recipient
            if 'all' in notif['recipients'] or user_email in notif['recipients']:
                if user_email not in notif.get('read_by', []):
                    if 'read_by' not in notif:
                        notif['read_by'] = []
                    notif['read_by'].append(user_email)
                    count += 1
        
        if count > 0:
            save_notifications(data)
        
        return count

def get_unread_count(user_email):
    """
    Get count of unread notifications for a specific user
    
    Args:
        user_email: User's email address
    
    Returns:
        int: Count of unread notifications
    """
    with notifications_lock:
        data = load_notifications()
        count = 0
        
        for notif in data['notifications']:
            # Check if user is a recipient
            if 'all' in notif['recipients'] or user_email in notif['recipients']:
                if user_email not in notif.get('read_by', []):
                    count += 1
        
        return count

def delete_notification(notification_id):
    """
    Delete a notification (admin only)
    
    Args:
        notification_id: Notification ID
    
    Returns:
        bool: True if successful, False otherwise
    """
    with notifications_lock:
        data = load_notifications()
        
        original_count = len(data['notifications'])
        data['notifications'] = [n for n in data['notifications'] if n['id'] != notification_id]
        
        if len(data['notifications']) < original_count:
            save_notifications(data)
            return True
        
        return False

def get_all_notifications():
    """
    Get all notifications (admin only)
    
    Returns:
        list: List of all notifications
    """
    with notifications_lock:
        data = load_notifications()
        # Sort by created_at (newest first)
        notifications = sorted(data['notifications'], key=lambda x: x['created_at'], reverse=True)
        return notifications

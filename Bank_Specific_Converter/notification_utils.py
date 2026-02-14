"""
Notification Management Module
===============================
Provides notification storage and management via SQLAlchemy.
"""

import uuid
import json
from datetime import datetime
from models import db, Notification, NotificationRead


def create_notification(title, message, notification_type, recipients, send_email, created_by):
    """Create a new notification."""
    notif = Notification(
        id=str(uuid.uuid4()),
        title=title,
        message=message,
        type=notification_type,
        created_at=datetime.now().isoformat(),
        created_by=created_by,
        recipients=json.dumps(recipients),
        send_email=send_email
    )
    db.session.add(notif)
    db.session.commit()
    return notif.id


def get_user_notifications(user_email):
    """Get all notifications for a specific user, newest first."""
    all_notifs = Notification.query.order_by(Notification.created_at.desc()).all()
    result = []

    for n in all_notifs:
        recipients = json.loads(n.recipients)
        if 'all' in recipients or user_email in recipients:
            is_read = NotificationRead.query.filter_by(
                notification_id=n.id, user_email=user_email).first() is not None
            result.append({
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.type,
                'created_at': n.created_at,
                'created_by': n.created_by,
                'recipients': recipients,
                'send_email': n.send_email,
                'is_read': is_read,
                'read_by': [r.user_email for r in n.reads.all()]
            })

    return result


def mark_as_read(notification_id, user_email):
    """Mark a notification as read for a specific user."""
    existing = NotificationRead.query.filter_by(
        notification_id=notification_id, user_email=user_email).first()
    if not existing:
        read = NotificationRead(notification_id=notification_id, user_email=user_email)
        db.session.add(read)
        db.session.commit()
    return True


def mark_all_as_read(user_email):
    """Mark all notifications as read for a specific user."""
    all_notifs = Notification.query.all()
    count = 0

    for n in all_notifs:
        recipients = json.loads(n.recipients)
        if 'all' in recipients or user_email in recipients:
            existing = NotificationRead.query.filter_by(
                notification_id=n.id, user_email=user_email).first()
            if not existing:
                read = NotificationRead(notification_id=n.id, user_email=user_email)
                db.session.add(read)
                count += 1

    if count > 0:
        db.session.commit()
    return count


def get_unread_count(user_email):
    """Get count of unread notifications for a specific user."""
    all_notifs = Notification.query.all()
    count = 0

    for n in all_notifs:
        recipients = json.loads(n.recipients)
        if 'all' in recipients or user_email in recipients:
            existing = NotificationRead.query.filter_by(
                notification_id=n.id, user_email=user_email).first()
            if not existing:
                count += 1

    return count


def delete_notification(notification_id):
    """Delete a notification (admin only)."""
    notif = db.session.get(Notification, notification_id)
    if notif:
        db.session.delete(notif)
        db.session.commit()
        return True
    return False


def get_all_notifications():
    """Get all notifications (admin only), newest first."""
    notifs = Notification.query.order_by(Notification.created_at.desc()).all()
    result = []
    for n in notifs:
        result.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'created_at': n.created_at,
            'created_by': n.created_by,
            'recipients': json.loads(n.recipients),
            'send_email': n.send_email,
            'read_by': [r.user_email for r in n.reads.all()]
        })
    return result

"""YugKrit - Notification service."""

from database.database import db
from database.models import Notification


def notify(user, title, message, link=None):
    if not user:
        return None
    note = Notification(user_id=user.id, title=title, message=message, link=link)
    db.session.add(note)
    db.session.commit()
    return note


def notify_many(users, title, message, link=None):
    for u in users:
        notify(u, title, message, link)


def unread_count(user):
    if not user:
        return 0
    return Notification.query.filter_by(user_id=user.id, is_read=False).count()


def mark_read(user, notification_id):
    note = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if note:
        note.is_read = True
        db.session.commit()
    return note


def mark_all_read(user):
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()

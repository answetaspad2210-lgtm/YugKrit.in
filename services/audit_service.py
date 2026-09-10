"""YugKrit - Audit logging service. Every important state change goes through here."""

from database.database import db
from database.models import AuditLog


def log_action(user, action, entity, entity_id, previous_value=None, new_value=None, reason=None):
    entry = AuditLog(
        user_id=user.id if user else None,
        role_name=user.role_name() if user else "SYSTEM",
        action=action,
        entity=entity,
        entity_id=entity_id,
        previous_value=str(previous_value) if previous_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        reason=reason,
    )
    db.session.add(entry)
    db.session.commit()
    return entry

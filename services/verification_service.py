"""YugKrit - Organization (University / ULB / NGO) verification service."""

from datetime import datetime
from database.database import db
from services.audit_service import log_action
from services.notification_service import notify_many


def set_organization_status(org, gov_user, status, reason=None):
    previous = org.status
    org.status = status
    if status == "VERIFIED":
        org.verified_by_id = gov_user.id
        org.verified_at = datetime.utcnow()
    if status == "REJECTED":
        org.rejection_reason = reason
    db.session.commit()

    log_action(gov_user, f"ORGANIZATION_{status}", "Organization", org.id, previous, status, reason)

    label = {"VERIFIED": "approved", "REJECTED": "rejected", "SUSPENDED": "suspended",
              "UNDER_REVIEW": "put under review"}.get(status, status.lower())
    notify_many(org.users, f"Verification update: {org.name}",
                f"Your organization's verification has been {label}.",
                link="/dashboard")
    return org

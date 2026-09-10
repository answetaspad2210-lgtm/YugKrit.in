"""YugKrit - Notification UI routes (bell dropdown)."""

from flask import Blueprint, redirect, url_for, request
from database.models import Notification
from utils.decorators import login_required, get_current_user
from services import notification_service

notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("/")
@login_required
def list_notifications():
    user = get_current_user()
    notes = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(50).all()
    from flask import render_template
    return render_template("shared/notifications.html", notifications=notes)


@notification_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    user = get_current_user()
    notification_service.mark_read(user, notification_id)
    note = Notification.query.get(notification_id)
    return redirect(note.link if note and note.link else url_for("notifications.list_notifications"))


@notification_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    user = get_current_user()
    notification_service.mark_all_read(user)
    return redirect(request.referrer or url_for("notifications.list_notifications"))
